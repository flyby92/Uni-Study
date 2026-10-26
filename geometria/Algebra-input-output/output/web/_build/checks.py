"""Controlli di fedeltà del sito rispetto alla dispensa.

1. le formule (inline e display) compaiono tutte, identiche e nello stesso ordine;
2. il testo (parole) coincide, a meno della punteggiatura delle etichette;
3. ogni figura compare una volta; gli id sono unici; ogni link interno ha un bersaglio;
4. l'HTML è ben annidato.
"""
import difflib
import html
import re
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


# ------------------------------------------------------------------ dalla dispensa
def md_text_and_math(path):
    text = open(path, encoding='utf-8').read()
    text = re.sub(r'```.*?```', '\n', text, flags=re.S)
    words, maths = [], []
    for line in text.split('\n'):
        s = line.strip()
        if not s or s == '---' or re.match(r'^\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?$', s):
            continue
        s = re.sub(r'^>\s?', '', s)
        if re.match(r'^#{1,6}\s+', s):
            s = re.sub(r'^#{1,6}\s+', '', s)
        else:
            s = re.sub(r'^(-|\d+\.)\s+', '', s)
        if s.startswith('![') and s.endswith(')'):
            continue  # testo alternativo delle immagini: è un attributo, non testo
        if s.startswith('$$') and s.endswith('$$') and len(s) > 4:
            maths.append(s[2:-2].strip())
            words.append('⟦M⟧')
            continue
        s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)

        def mrep(m):
            maths.append(m.group(1).strip())
            return ' ⟦M⟧ '
        s = re.sub(r'\$(.+?)\$', mrep, s)
        s = s.replace('|', ' ')
        words.extend(tokenize(s))
    return words, maths


def tokenize(s):
    s = s.replace('**', '').replace('*', '').replace('📌', ' ')
    s = html.unescape(s)
    toks = re.findall(r'⟦M⟧|[\w’\'.]+', s)
    out = []
    for t in toks:
        if t == '⟦M⟧':
            out.append(t)
            continue
        t = t.strip(".'’")
        if t:
            out.append(t)
    return out


# ------------------------------------------------------------------ dal sito
class Extract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []          # (tag, skip, math)
        self.in_main = 0
        self.words = []
        self.maths = []
        self.ids = {}
        self.hrefs = []
        self.imgs = 0
        self.errors = []
        self.buf = []
        self.math_buf = None

    def skipping(self):
        return any(x[1] for x in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids[a['id']] = self.ids.get(a['id'], 0) + 1
        if tag == 'a' and a.get('href', '').startswith('#'):
            self.hrefs.append(a['href'][1:])
        if tag == 'a' and any(x[0] == 'a' for x in self.stack):
            self.errors.append(f'link annidato in un altro link a {self.getpos()}')
        if tag in VOID:
            if tag == 'img' and self.in_main and not self.skipping():
                self.imgs += 1
            return
        skip = ('data-x' in a or tag in ('script', 'style', 'svg', 'template')
                or 'lab' in (a.get('class') or '').split())
        cls = (a.get('class') or '').split()
        is_math = tag in ('span', 'div') and ('m' in cls or 'dm' in cls)
        if a.get('id') == 'doc':
            self.in_main += 1
            self.stack.append((tag, skip, False, True))
            return
        if is_math and self.in_main and not self.skipping() and not skip:
            self.flush()
            self.math_buf = []
        self.stack.append((tag, skip, is_math, False))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f'chiusura senza apertura: </{tag}> a {self.getpos()}')
            return
        t, skip, is_math, is_main = self.stack.pop()
        if t != tag:
            self.errors.append(f'annidamento errato: <{t}> chiuso da </{tag}> a {self.getpos()}')
        if is_math and self.math_buf is not None:
            self.maths.append(html.unescape(''.join(self.math_buf)).strip())
            self.words.append('⟦M⟧')
            self.math_buf = None
        if is_main:
            self.flush()
            self.in_main -= 1
        if tag in ('p', 'li', 'div', 'h2', 'h3', 'h4', 'h5', 'th', 'td', 'figcaption', 'section', 'aside', 'button'):
            self.flush()

    def handle_data(self, data):
        if not self.in_main or self.skipping():
            return
        if self.math_buf is not None:
            self.math_buf.append(data)
        else:
            self.buf.append(data)

    def flush(self):
        if self.buf:
            self.words.extend(tokenize(''.join(self.buf)))
            self.buf = []


def run(src, page, R=None):
    ok = True
    md_words, md_maths = md_text_and_math(src)
    ex = Extract()
    ex.feed(page)
    ex.close()
    ex.flush()
    # 4. annidamento
    if ex.errors:
        ok = False
        print(f'HTML: {len(ex.errors)} errori di annidamento, ad es.:', ex.errors[:5])
    if ex.stack:
        ok = False
        print('HTML: elementi non chiusi:', [x[0] for x in ex.stack][:10])
    # 1. formule
    if md_maths != ex.maths:
        ok = False
        sm = difflib.SequenceMatcher(a=md_maths, b=ex.maths, autojunk=False)
        print(f'FORMULE: dispensa {len(md_maths)}, sito {len(ex.maths)}')
        for op in sm.get_opcodes():
            if op[0] != 'equal':
                print('  ', op[0], md_maths[op[1]:op[2]][:3], '->', ex.maths[op[3]:op[4]][:3])
                break
    else:
        print(f'formule: {len(md_maths)} identiche e nello stesso ordine')
    # 2. testo
    sm = difflib.SequenceMatcher(a=md_words, b=ex.words, autojunk=False)
    diffs = [op for op in sm.get_opcodes() if op[0] != 'equal']
    if diffs:
        ok = False
        print(f'TESTO: {len(diffs)} differenze (parole dispensa {len(md_words)}, sito {len(ex.words)})')
        for op in diffs[:25]:
            a = ' '.join(md_words[max(0, op[1] - 6):op[2] + 6])
            b = ' '.join(ex.words[max(0, op[3] - 6):op[4] + 6])
            print(f'  {op[0]}: «{" ".join(md_words[op[1]:op[2]])}» -> «{" ".join(ex.words[op[3]:op[4]])}»')
            print(f'      dispensa: …{a}…')
            print(f'      sito:     …{b}…')
    else:
        print(f'testo: {len(md_words)} parole identiche e nello stesso ordine')
    # 3. figure, id, link
    n_fig = len(re.findall(r'!\[', open(src, encoding='utf-8').read()))
    if ex.imgs != n_fig:
        ok = False
        print(f'FIGURE: dispensa {n_fig}, sito {ex.imgs}')
    else:
        print(f'figure: {n_fig}')
    dup = [k for k, v in ex.ids.items() if v > 1]
    if dup:
        ok = False
        print('ID duplicati:', dup[:10])
    missing = sorted({h for h in ex.hrefs if h and h not in ex.ids})
    if missing:
        ok = False
        print('LINK senza bersaglio:', missing[:10])
    else:
        print(f'link interni: {len(ex.hrefs)}, tutti con bersaglio; id unici: {len(ex.ids)}')
    print('CONTROLLI SUPERATI' if ok else 'CONTROLLI FALLITI')
    return ok
