"""Parser Markdown su misura per la dispensa (sottoinsieme usato dal file).

Produce una lista di blocchi (dict) con i tipi:
  heading(level, text)          # da '#' a '####'
  para(text, cont)              # una riga di testo (nel file ogni paragrafo è una riga);
                                # cont=True se segue un blocco senza riga vuota in mezzo
  dmath(tex, cont)              # formula in display '$$...$$' su riga propria
  list(ordered, start, items)   # items = [[blocchi], ...]; liste annidate dentro gli item
  table(head, align, rows)      # celle come testo Markdown inline
  quote(blocks)                 # contenuto di un blocco '>'
  code(lang, text)              # recinto ``` (solo mermaid nella dispensa)
  image(alt, src)
  hr
Ogni blocco porta 'line' (numero di riga 1-based nel sorgente) per i messaggi.
"""
import re

ITEM_RE = re.compile(r'^(\s*)(-|\d+\.)\s+(.*)$')
HEAD_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
IMG_RE = re.compile(r'^!\[(.*)\]\((.*)\)\s*$')
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$")


def B(kind, line, **kw):
    d = {'type': kind, 'line': line}
    d.update(kw)
    return d


def split_row(line):
    """Divide una riga di tabella sulle '|' che non stanno dentro $...$."""
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|'):
        s = s[:-1]
    cells, cur, in_math = [], [], False
    for ch in s:
        if ch == '$':
            in_math = not in_math
        if ch == '|' and not in_math:
            cells.append(''.join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    cells.append(''.join(cur).strip())
    return cells


def parse_list(lines, i, base):
    """Legge una lista (con annidamenti e righe di continuazione) a partire da i."""
    n = len(lines)
    m = ITEM_RE.match(lines[i])
    first_indent = len(m.group(1))
    ordered = m.group(2)[0].isdigit()
    root = B('list', base + i + 1, ordered=ordered,
             start=int(m.group(2)[:-1]) if ordered else 1, items=[])
    stack = [(first_indent, root)]
    last_item = None
    while i < n:
        line = lines[i]
        if not line.strip():
            break
        m = ITEM_RE.match(line)
        if m and (last_item is None or len(m.group(1)) >= first_indent):
            ind = len(m.group(1))
            marker = m.group(2)
            text = m.group(3)
            while len(stack) > 1 and ind < stack[-1][0]:
                stack.pop()
            if ind > stack[-1][0]:
                # lista annidata dentro l'ultimo item
                ordered = marker[0].isdigit()
                sub = B('list', base + i + 1, ordered=ordered,
                        start=int(marker[:-1]) if ordered else 1, items=[])
                last_item.append(sub)
                stack.append((ind, sub))
            lst = stack[-1][1]
            item = [B('para', base + i + 1, text=text, cont=False)]
            lst['items'].append(item)
            last_item = item
        else:
            # riga di continuazione (pigra) dell'ultimo item
            s = line.strip()
            if s.startswith('$$'):
                last_item.append(B('dmath', base + i + 1, tex=s[2:-2].strip(), cont=True))
            else:
                last_item.append(B('para', base + i + 1, text=s, cont=True))
        i += 1
    return root, i


def parse_blocks(lines, base=0):
    blocks = []
    i, n = 0, len(lines)
    blank_before = True
    while i < n:
        line = lines[i]
        s = line.strip()
        ln = base + i + 1
        if not s:
            blank_before = True
            i += 1
            continue
        if s.startswith('```'):
            lang = s[3:].strip()
            j = i + 1
            while j < n and not lines[j].strip().startswith('```'):
                j += 1
            blocks.append(B('code', ln, lang=lang, text='\n'.join(lines[i + 1:j])))
            i = j + 1
            blank_before = False
            continue
        m = HEAD_RE.match(line)
        if m:
            blocks.append(B('heading', ln, level=len(m.group(1)), text=m.group(2)))
            i += 1
            blank_before = False
            continue
        if s == '---':
            blocks.append(B('hr', ln))
            i += 1
            blank_before = False
            continue
        if line.startswith('>'):
            j = i
            inner = []
            while j < n and lines[j].startswith('>'):
                inner.append(re.sub(r'^> ?', '', lines[j]))
                j += 1
            blocks.append(B('quote', ln, blocks=parse_blocks(inner, base + i)))
            i = j
            blank_before = False
            continue
        m = IMG_RE.match(s)
        if m:
            blocks.append(B('image', ln, alt=m.group(1), src=m.group(2)))
            i += 1
            blank_before = False
            continue
        if s.startswith('|') and i + 1 < n and TABLE_SEP_RE.match(lines[i + 1]):
            head = split_row(lines[i])
            align = []
            for c in split_row(lines[i + 1]):
                c = c.strip()
                if c.startswith(':') and c.endswith(':'):
                    align.append('center')
                elif c.endswith(':'):
                    align.append('right')
                elif c.startswith(':'):
                    align.append('left')
                else:
                    align.append('')
            j = i + 2
            rows = []
            while j < n and lines[j].strip().startswith('|'):
                rows.append(split_row(lines[j]))
                j += 1
            blocks.append(B('table', ln, head=head, align=align, rows=rows))
            i = j
            blank_before = False
            continue
        if ITEM_RE.match(line):
            lst, i = parse_list(lines, i, base)
            blocks.append(lst)
            blank_before = False
            continue
        if s.startswith('$$') and s.endswith('$$') and len(s) > 4:
            blocks.append(B('dmath', ln, tex=s[2:-2].strip(), cont=not blank_before))
        else:
            blocks.append(B('para', ln, text=s, cont=not blank_before))
        blank_before = False
        i += 1
    return blocks


def parse_file(path):
    with open(path, encoding='utf-8') as fh:
        text = fh.read()
    return parse_blocks(text.split('\n'))


def walk(blocks):
    """Visita in profondità tutti i blocchi (anche dentro liste e citazioni)."""
    for b in blocks:
        yield b
        if b['type'] == 'list':
            for it in b['items']:
                yield from walk(it)
        elif b['type'] == 'quote':
            yield from walk(b['blocks'])
