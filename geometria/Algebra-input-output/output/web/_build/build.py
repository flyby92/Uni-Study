#!/usr/bin/env python3
"""Genera output/web/geometria.html dalla dispensa di Geometria e Algebra Lineare.

Uso:  python3 build.py            (scrive ../geometria.html)
      python3 build.py --out F    (scrive altrove, ad es. per prove)

Pipeline: mdparse (blocchi) -> group (ambienti, dimostrazioni, figure, callout)
-> render (HTML con formule TeX in <span class="m">, rese da KaTeX nel browser)
-> assemble (template + CSS + JS + font + KaTeX incorporati: file unico, offline).
Le verifiche di fedeltà testo/formule sono in checks.py (eseguite in coda).
"""
import base64
import html
import json
import os
import re
import sys

import mdparse

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, '..', '..', 'Dispensa-Definitiva', 'dispensa_definitiva.md'))
FIGDIR = os.path.join(os.path.dirname(SRC), 'figure')
OUT = os.path.normpath(os.path.join(HERE, '..', 'geometria.html'))
TPL = os.path.join(HERE, 'tpl')
KATEX = os.path.join(HERE, 'vendor', 'katex-0.16.47', 'dist')
FONTS = os.path.join(HERE, 'fonts')

# ---------------------------------------------------------------- regex
ENV_NAMES = ('Definizione', 'Teorema', 'Proposizione', 'Corollario', 'Lemma', 'Esempio',
             'Esercizio', 'Osservazione', 'Costruzione', 'Procedimento', 'Principio di induzione')
LABEL_RE = re.compile(r'^\*\*(' + '|'.join(ENV_NAMES) + r')(?:\s+(\d+\.\d+))?\s*(?:\((.*?)\))?\s*[.:]?\*\*\s*(.*)$')
PROOF_RE = re.compile(r'^\*(Dimostrazione[^*]*|Spiegazione\.|Giustificazione\.)\*\s*(.*)$')
SOL_RE = re.compile(r'^\*Soluzione\.\*\s*(.*)$')
ITSTEP_RE = re.compile(r'^\*[^*]+\*')
LEAD_RE = re.compile(r'^\*\*([^*]+?)\*\*\s*(.*)$')
DOMANDE_RE = re.compile(r"^\*\*Domande tipiche d'esame\.\*\*\s*$")
FIGCAP_RE = re.compile(r'^\*(Figura (\d+\.\d+)) — (.*)\*$')
CONNECTIVE_RE = re.compile(r'^(Dunque|Quindi|Pertanto|Allora|In tutto|Ne segue|Si ottiene|Infatti|Risulta)\b')
DEFVERB_RE = re.compile(r'(si dic[eo]|se ne dice|si chiam[ao]|è \*\*[^*]+\*\* se)')
QED = '\\blacksquare'

ENV_ABBR = {'Definizione': 'def', 'Teorema': 'teo', 'Proposizione': 'prop', 'Corollario': 'cor',
            'Lemma': 'lem', 'Esempio': 'es', 'Esercizio': 'ex', 'Osservazione': 'oss',
            'Costruzione': 'costr', 'Procedimento': 'proc', 'Principio di induzione': 'princ'}
# famiglia grafica (colore del riquadro)
ENV_FAMILY = {'def': 'def', 'teo': 'thm', 'prop': 'thm', 'cor': 'thm', 'lem': 'thm', 'princ': 'thm',
              'es': 'es', 'ex': 'ex', 'oss': 'oss', 'costr': 'proc', 'proc': 'proc'}
# blocchi in più da includere nel riquadro, oltre alla regola generale
ENV_EXTRA = {'Definizione 2.3': 1}

# ---------------------------------------------------------------- utilità

def esc(s):
    return html.escape(s, quote=False)


def attr(s):
    return html.escape(s, quote=True)


def slug(text, seen):
    """Identico ad assemble.py: gli id coincidono con i link dell'Indice."""
    s = text.strip().lower()
    s = re.sub(r'[^\w\- ]', '', s)
    s = s.replace(' ', '-')
    base = s
    k = seen.get(base, 0)
    seen[base] = k + 1
    return base if k == 0 else f'{base}-{k}'


def num_id(prefix, num):
    return f'{prefix}-{num.replace(".", "-")}'


GREEK = {'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'theta': 'θ', 'lambda': 'λ', 'mu': 'μ',
         'rho': 'ρ', 'sigma': 'σ', 'pi': 'π', 'ell': 'ℓ', 'wedge': '∧', 'cdot': '·', 'perp': '⟂',
         'parallel': '∥', 'nparallel': '∦', 'in': '∈', 'notin': '∉', 'to': '→', 'le': '≤', 'ge': '≥',
         'neq': '≠', 'ne': '≠', 'times': '×', 'infty': '∞', 'sum': 'Σ', 'subseteq': '⊆', 'subset': '⊂',
         'cup': '∪', 'cap': '∩', 'emptyset': '∅', 'varnothing': '∅', 'sqrt': '√', 'pm': '±',
         'iff': '⇔', 'Rightarrow': '⇒', 'det': 'det', 'cos': 'cos', 'sin': 'sin', 'tan': 'tan',
         'arctan': 'arctan', 'ln': 'ln', 'exists': '∃', 'forall': '∀', 'cong': '≅', 'approx': '≈',
         'setminus': '∖', 'circ': '∘', 'mapsto': '↦', 'cdots': '…', 'dots': '…', 'ldots': '…',
         'blacksquare': '∎'}
BB = {'R': 'ℝ', 'C': 'ℂ', 'N': 'ℕ', 'Z': 'ℤ', 'Q': 'ℚ', 'K': '𝕂'}


SUB = str.maketrans('0123456789+-=()nijkhpt', '₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙᵢⱼₖₕₚₜ')
SUP = str.maketrans('0123456789+-=()ni', '⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱ')


def tex_plain(tex):
    """Versione testuale approssimata di una formula (per ricerca e anteprime)."""
    s = re.sub(r'_(?:\{([0-9nijkhpt])\}|([0-9nijkhpt]))', lambda m: (m.group(1) or m.group(2)).translate(SUB), tex)
    s = re.sub(r'\^(?:\{(-?[0-9ni])\}|([0-9ni]))', lambda m: (m.group(1) or m.group(2)).translate(SUP), s)
    s = re.sub(r'\\mathbb\{(\w)\}', lambda m: BB.get(m.group(1), m.group(1)), s)
    s = re.sub(r'\\[dt]?frac\{([^{}]*)\}\{([^{}]*)\}', r'(\1)/(\2)', s)
    s = re.sub(r'\\sqrt\{([^{}]*)\}', r'√(\1)', s)
    s = re.sub(r'\\mathcal\{V\}', '𝒱', s)
    s = re.sub(r'\\operatorname\{(\w+)\}', r'\1', s)
    s = re.sub(r'\\text\{([^}]*)\}', r' \1 ', s)
    s = re.sub(r'\\([A-Za-z]+)', lambda m: GREEK.get(m.group(1), ' '), s)
    s = s.replace('\\\\', ' ').replace('\\,', ' ').replace('\\;', ' ').replace('\\!', '').replace('\\ ', ' ')
    s = s.replace('\\{', '{').replace('\\}', '}')
    s = re.sub(r'[{}]', '', s)
    s = s.replace('&', ' ').replace('_', '').replace('^', '')
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def md_plain(text):
    """Testo semplice di una riga Markdown (formule semplificate)."""
    t = re.sub(r'\$(.+?)\$', lambda m: tex_plain(m.group(1)), text)
    t = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', t)
    t = t.replace('**', '').replace('*', '')
    return re.sub(r'\s+', ' ', t).strip()


# ---------------------------------------------------------------- raggruppamento

def contains_qed(b):
    if b['type'] == 'para':
        return QED in b['text']
    if b['type'] == 'dmath':
        return QED in b['tex']
    return False


def group(blocks):
    """Trasforma la sequenza di blocchi in nodi semantici."""
    nodes = []
    i, n = 0, len(blocks)
    while i < n:
        b = blocks[i]
        t = b['type']
        if t == 'image':
            cap = None
            if i + 1 < n and blocks[i + 1]['type'] == 'para' and FIGCAP_RE.match(blocks[i + 1]['text']):
                cap = blocks[i + 1]
                i += 1
            nodes.append({'kind': 'figure', 'img': b, 'cap': cap, 'line': b['line']})
            i += 1
            continue
        if t == 'code':
            cap = None
            if (i + 1 < n and blocks[i + 1]['type'] == 'para'
                    and re.match(r'^\*[^*].*\*$', blocks[i + 1]['text'])
                    and not FIGCAP_RE.match(blocks[i + 1]['text'])):
                cap = blocks[i + 1]
                i += 1
            nodes.append({'kind': 'diagram', 'code': b, 'cap': cap, 'line': b['line']})
            i += 1
            continue
        if t == 'quote':
            nodes.append({'kind': 'callout', 'q': b, 'line': b['line']})
            i += 1
            continue
        if t == 'para':
            txt = b['text']
            m = LABEL_RE.match(txt)
            if m:
                env, i = absorb_env(blocks, i, m)
                nodes.append(env)
                continue
            if PROOF_RE.match(txt):
                pr, i = absorb_proof(blocks, i)
                nodes.append(pr)
                continue
            if DOMANDE_RE.match(txt) and i + 1 < n and blocks[i + 1]['type'] == 'list':
                nodes.append({'kind': 'exam', 'list': blocks[i + 1], 'line': b['line']})
                i += 2
                continue
        nodes.append({'kind': 'block', 'b': b, 'line': b['line']})
        i += 1
    return nodes


def absorb_env(blocks, i, m):
    n = len(blocks)
    etype, num, title, rest = m.group(1), m.group(2), m.group(3), m.group(4)
    label = etype + (' ' + num if num else '')
    exlike = etype in ('Esempio', 'Esercizio')
    env = {'kind': 'env', 'etype': etype, 'num': num, 'title': title, 'label': label,
           'first': rest, 'body': [], 'sol': None, 'line': blocks[i]['line']}
    extra = ENV_EXTRA.get(label, 0)
    j = i + 1
    sol_mode = False
    only_label = True          # finora solo il paragrafo-etichetta (e sue continuazioni)
    last_text = rest
    prev = 'label'
    target = env['body']

    def take(c, kind):
        nonlocal last_text, prev, only_label
        target.append(c)
        if c['type'] == 'para':
            last_text = c['text']
        if not c.get('cont'):
            only_label = False
        prev = kind

    while j < n:
        c = blocks[j]
        ct = c['type']
        if ct in ('heading', 'hr', 'code', 'quote'):
            break
        if ct == 'para':
            txt = c['text']
            if LABEL_RE.match(txt) or DOMANDE_RE.match(txt) or PROOF_RE.match(txt):
                break
            if c['cont']:
                take(c, 'para')
            elif exlike and SOL_RE.match(txt):
                sol_mode = True
                env['sol'] = []
                target = env['sol']
                take(c, 'para')
            elif exlike and ITSTEP_RE.match(txt):
                sol_mode = True
                take(c, 'para')
            elif sol_mode and not LEAD_RE.match(txt):
                take(c, 'para')
            elif prev in ('list', 'dmath', 'table') and txt[:1].islower():
                take(c, 'para')
            elif exlike and prev in ('list', 'dmath') and CONNECTIVE_RE.match(txt):
                take(c, 'para')
            elif etype == 'Definizione' and prev == 'list' and DEFVERB_RE.search(txt):
                take(c, 'para')
            elif extra > 0:
                extra -= 1
                take(c, 'para')
            else:
                break
        elif ct == 'dmath':
            if c['cont'] or exlike or last_text.rstrip().endswith(':') or sol_mode:
                take(c, 'dmath')
            else:
                break
        elif ct == 'list':
            if only_label or last_text.rstrip().endswith(':') or sol_mode or extra > 0:
                take(c, 'list')
            else:
                break
        elif ct == 'table':
            if last_text.rstrip().endswith(':') or sol_mode or extra > 0:
                take(c, 'table')
            else:
                break
        elif ct == 'image':
            if sol_mode:
                target.append({'kind_fig': True, 'img': c,
                               'cap': blocks[j + 1] if j + 1 < n and blocks[j + 1]['type'] == 'para'
                               and FIGCAP_RE.match(blocks[j + 1]['text']) else None})
                if target[-1]['cap'] is not None:
                    j += 1
                prev = 'image'
            else:
                break
        else:
            break
        j += 1
    return env, j


def absorb_proof(blocks, i):
    n = len(blocks)
    m = PROOF_RE.match(blocks[i]['text'])
    pr = {'kind': 'proof', 'label': m.group(1), 'first': m.group(2), 'body': [], 'line': blocks[i]['line'],
          'qed': False}
    if contains_qed(blocks[i]):
        pr['qed'] = True
        return pr, i + 1
    j = i + 1
    while j < n:
        c = blocks[j]
        ct = c['type']
        if ct in ('heading', 'hr', 'code', 'quote', 'image'):
            break
        if ct == 'para' and (LABEL_RE.match(c['text']) or DOMANDE_RE.match(c['text'])
                             or PROOF_RE.match(c['text']) or SOL_RE.match(c['text'])):
            break
        pr['body'].append(c)
        j += 1
        if contains_qed(c):
            pr['qed'] = True
            break
    return pr, j


# ---------------------------------------------------------------- diagrammi (Mermaid -> JSON)
# Etichette con simboli matematici riscritte in TeX (stesse parole e simboli).
DIAGRAM_LABELS = {
    'Gruppo<br/>es. (ℤ,+), (ℝ∖{0},·)': r'Gruppo<br/>es. $(\mathbb{Z},+)$, $(\mathbb{R}\setminus\{0\},\cdot)$',
    'Gruppo commutativo<br/>es. (ℝⁿ,+), (ℂ,+)': r'Gruppo commutativo<br/>es. $(\mathbb{R}^n,+)$, $(\mathbb{C},+)$',
    '+ secondo prodotto<br/>(K∖{0},·) gruppo comm.<br/>+ distributività':
        r'+ secondo prodotto<br/>$(\mathbb{K}\setminus\{0\},\cdot)$ gruppo comm.<br/>+ distributività',
    'Campo 𝕂<br/>ℚ, ℝ, ℂ, ℤₚ (p primo)':
        r'Campo $\mathbb{K}$<br/>$\mathbb{Q}$, $\mathbb{R}$, $\mathbb{C}$, $\mathbb{Z}_p$ ($p$ primo)',
    '+ prodotto per scalari di 𝕂<br/>con 4 proprietà': r'+ prodotto per scalari di $\mathbb{K}$<br/>con 4 proprietà',
    'Spazio vettoriale su 𝕂<br/>(Capp. 6 e 14–19)': r'Spazio vettoriale su $\mathbb{K}$<br/>(Capp. 6 e 14–19)',
    'ℕ': r'$\mathbb{N}$', 'ℤ': r'$\mathbb{Z}$', 'ℚ': r'$\mathbb{Q}$', 'ℝ': r'$\mathbb{R}$', 'ℂ': r'$\mathbb{C}$',
    'x+1=0': r'$x+1=0$', '2x+1=0': r'$2x+1=0$', 'x²−2=0': r'$x^2-2=0$', 'x²+1=0': r'$x^2+1=0$',
    'Forma algebrica<br/>z = a + bi': r'Forma algebrica<br/>$z = a + bi$',
    'ρ = √(a²+b²)<br/>θ dalla (3.9)': r'$\rho = \sqrt{a^2+b^2}$<br/>$\theta$ dalla (3.9)',
    'Forma trigonometrica<br/>z = ρ(cos θ + i sen θ)':
        r'Forma trigonometrica<br/>$z = \rho(\cos\theta + i\,\mathrm{sen}\,\theta)$',
    'a = ρ cos θ, b = ρ sen θ': r'$a = \rho\cos\theta$, $b = \rho\,\mathrm{sen}\,\theta$',
    'Eulero: e^{iθ} = cos θ + i sen θ': r'Eulero: $e^{i\theta} = \cos\theta + i\,\mathrm{sen}\,\theta$',
    'Forma esponenziale<br/>z = ρ e^{iθ}': r'Forma esponenziale<br/>$z = \rho\, e^{i\theta}$',
    'Le otto proprietà<br/>somma: neutro, opposto, associativa, commutativa<br/>scalari: 1·v = v, due distributività, associatività mista':
        r'Le otto proprietà<br/>somma: neutro, opposto, associativa, commutativa<br/>scalari: $1\cdot\underline{v} = \underline{v}$, due distributività, associatività mista',
    'Matrici M(m×n, 𝕂)': r'Matrici $M(m\times n, \mathbb{K})$',
    'Vettori liberi 𝒱 (su ℝ)': r'Vettori liberi $\mathcal{V}$ (su $\mathbb{R}$)',
    'n-uple 𝕂ⁿ': r'$n$-uple $\mathbb{K}^n$',
    'Polinomi 𝕂ₙ[x], funzioni, …': r'Polinomi $\mathbb{K}_n[x]$, funzioni, …',
    '(v, w) ∈ 𝒱 × 𝒱': r'$(\underline{v}, \underline{w}) \in \mathcal{V} \times \mathcal{V}$',
    'somma in 𝒱': r'somma in $\mathcal{V}$',
    'v + w ∈ 𝒱': r'$\underline{v} + \underline{w} \in \mathcal{V}$',
    'f × f': r'$f \times f$',
    '(f(v), f(w)) ∈ ℝ³ × ℝ³': r'$(f(\underline{v}), f(\underline{w})) \in \mathbb{R}^3 \times \mathbb{R}^3$',
    'f': r'$f$',
    'f(v + w) ∈ ℝ³': r'$f(\underline{v} + \underline{w}) \in \mathbb{R}^3$',
    'somma in ℝ³': r'somma in $\mathbb{R}^3$',
    'parametrica<br/>punto + direzione v': r'parametrica<br/>punto + direzione $\underline{v}$',
    'cartesiana<br/>ax+by+cz+d=0': r'cartesiana<br/>$ax+by+cz+d=0$',
    'eliminare t': r'eliminare $t$',
    'v = M ∧ M′ e un punto,<br/>oppure 2 incognite in funzione della 3ª':
        r"$\underline{v} = \underline{M} \wedge \underline{M}'$ e un punto,<br/>oppure 2 incognite in funzione della 3ª",
    'M = v₁ ∧ v₂ e un punto,<br/>oppure eliminare t, s':
        r'$\underline{M} = \underline{v}_1 \wedge \underline{v}_2$ e un punto,<br/>oppure eliminare $t$, $s$',
    '3 punti, oppure punto +<br/>2 vettori ⟂ M': r'3 punti, oppure punto +<br/>2 vettori $\perp \underline{M}$',
    'Due rette r, r′<br/>(punti P₀, P₁; direzioni v, w)':
        r"Due rette $r$, $r'$<br/>(punti $P_0$, $P_1$; direzioni $\underline{v}$, $\underline{w}$)",
    'det(P₁−P₀; v; w) = 0 ?': r'$\det(P_1 - P_0;\, \underline{v};\, \underline{w}) = 0$ ?',
    'v ∧ w = 0 ?': r'$\underline{v} \wedge \underline{w} = \underline{0}$ ?',
    'P₁ ∈ r ?': r'$P_1 \in r$ ?',
    # Capitolo 15: Rouché–Capelli
    'Sistema Ax = b<br/>m equazioni, n incognite': r'Sistema $Ax = b$<br/>$m$ equazioni, $n$ incognite',
    "Calcolare p = rango(A)<br/>e p' = rango(A|b)": r"Calcolare $p = \operatorname{rango}(A)$<br/>e $p' = \operatorname{rango}(A\mid b)$",
    "p = p' ?": r"$p = p'$ ?",
    'p = n ?': r'$p = n$ ?',
    'Infinite soluzioni<br/>dipendenti da n − p parametri': r'Infinite soluzioni<br/>dipendenti da $n - p$ parametri',
    # Capitolo 17: matrice associata
    'v ∈ V': r'$v \in V$',
    'f(v) ∈ W': r'$f(v) \in W$',
    'x ∈ 𝕂ⁿ': r'$x \in \mathbb{K}^n$',
    'y = A x ∈ 𝕂ᵐ': r'$y = A x \in \mathbb{K}^m$',
    'coordinate rispetto a 𝒫': r'coordinate rispetto a $\mathcal{P}$',
    'moltiplicazione per A': r'moltiplicazione per $A$',
    'vettore di W con coordinate y rispetto ad 𝒜': r'vettore di $W$ con coordinate $y$ rispetto ad $\mathcal{A}$',
    # Capitolo 18: diagonalizzazione
    'Matrice A di f<br/>(rispetto a una base)': r'Matrice $A$ di $f$<br/>(rispetto a una base)',
    'Polinomio caratteristico<br/>p(λ) = det(A − λI)': r'Polinomio caratteristico<br/>$p(\lambda) = \det(A - \lambda I)$',
    'p ha n radici in 𝕂<br/>(con molteplicità)?': r'$p$ ha $n$ radici in $\mathbb{K}$<br/>(con molteplicità)?',
    'per ogni autovalore multiplo λ:<br/>m_g(λ) = n − rango(A − λI)':
        r'per ogni autovalore multiplo $\lambda$:<br/>$m_g(\lambda) = n - \operatorname{rango}(A - \lambda I)$',
    'm_g(λ) = m_a(λ)<br/>per ogni λ?': r'$m_g(\lambda) = m_a(\lambda)$<br/>per ogni $\lambda$?',
    'diagonalizzabile:<br/>base di autovettori, P⁻¹AP diagonale':
        r'diagonalizzabile:<br/>base di autovettori, $P^{-1}AP$ diagonale',
}

NODE_RE = re.compile(r'([A-Za-z][A-Za-z0-9_]*)\s*(\[\s*"(.*?)"\s*\]|\{\s*"(.*?)"\s*\}|\(\s*"(.*?)"\s*\))?')


def parse_mermaid(src):
    lines = [l.strip() for l in src.split('\n') if l.strip()]
    head = lines[0].split()
    direction = head[1] if len(head) > 1 else 'TD'
    nodes, order, edges, groups = {}, [], [], []
    cur_group = None

    def node(tok):
        m = NODE_RE.fullmatch(tok.strip())
        if not m:
            raise ValueError('nodo mermaid non riconosciuto: ' + tok)
        nid = m.group(1)
        label = m.group(3) or m.group(4) or m.group(5)
        shape = 'diamond' if m.group(4) is not None else 'round' if m.group(5) is not None else 'rect'
        if nid not in nodes:
            nodes[nid] = {'id': nid, 'label': label if label is not None else nid, 'shape': shape}
            order.append(nid)
        elif label is not None:
            nodes[nid]['label'] = label
            nodes[nid]['shape'] = shape
        if cur_group is not None and nid not in cur_group['nodes']:
            cur_group['nodes'].append(nid)
        return nid

    EDGE_RE = re.compile(r'^(.*?)\s*(-->|---|-\.->|==>|--\s*"(.*?)"\s*-->)\s*(?:\|"(.*?)"\|)?\s*(.*)$')
    for l in lines[1:]:
        if l.startswith('subgraph'):
            m = re.match(r'subgraph\s+(\w+)\s*\[\s*"(.*?)"\s*\]', l)
            cur_group = {'id': m.group(1), 'label': m.group(2), 'nodes': []}
            groups.append(cur_group)
            continue
        if l == 'end':
            cur_group = None
            continue
        m = EDGE_RE.match(l)
        if m and m.group(2):
            a = node(m.group(1))
            op = m.group(2)
            lab = m.group(3) if m.group(3) is not None else m.group(4)
            b = node(m.group(5))
            style = {'-->': 'solid', '---': 'line', '-.->': 'dotted', '==>': 'thick'}.get(op, 'solid')
            edges.append({'from': a, 'to': b, 'label': lab, 'style': style})
        else:
            node(l)
    for nd in nodes.values():
        nd['label'] = DIAGRAM_LABELS.get(nd['label'], nd['label'])
    for e in edges:
        if e['label'] is not None:
            e['label'] = DIAGRAM_LABELS.get(e['label'], e['label'])
    for g in groups:
        g['label'] = DIAGRAM_LABELS.get(g['label'], g['label'])
    return {'dir': direction, 'nodes': [nodes[k] for k in order], 'edges': edges, 'groups': groups}


# ---------------------------------------------------------------- inline + riferimenti incrociati
REF_RE = re.compile(r'\b(Definizion[ei]|Teorem[ai]|Proposizion[ei]|Corollari[oi]|Lemm[ai]|Esemp(?:io|i)|'
                    r'Esercizi[o]?|Osservazion[ei]|Costruzione|Procedimento|Figur[ae])(\s+)'
                    r'(\d+\.\d+(?:\s*(?:,|e|ed|–|-)\s*\d+\.\d+)*)')
KW_NORM = {'Definizion': 'Definizione', 'Teorem': 'Teorema', 'Proposizion': 'Proposizione',
           'Corollari': 'Corollario', 'Lemm': 'Lemma', 'Esemp': 'Esempio', 'Esercizi': 'Esercizio',
           'Osservazion': 'Osservazione', 'Costruzione': 'Costruzione', 'Procedimento': 'Procedimento',
           'Figur': 'Figura'}
CHAP_RE = re.compile(r'\b(Capitol[oi])(\s+)(\d+(?:\s*(?:,|e)\s*\d+)*)')
SECT_RE = re.compile(r'§\s?(\d+\.\d+)(?:–(\d+\.\d+))?')
EQREF_RE = re.compile(r'\((\d+\.\d+)\)')


class Ctx:
    def __init__(self):
        self.targets = {}      # chiave -> id
        self.ref_kinds = {}    # id -> tipo per lo stile del link
        self.self_id = None
        self.links = 0
        self.no_refs = False

    def norm_kw(self, kw):
        for k, v in KW_NORM.items():
            if kw.startswith(k):
                return v
        return kw


def link(href, text, cls='xr'):
    return f'<a class="{cls}" href="#{attr(href)}">{text}</a>'


def crossref(t, ctx):
    if ctx.no_refs:
        return t

    def rep_env(m):
        kw = ctx.norm_kw(m.group(1))

        def rep_num(mm):
            tid = ctx.targets.get((kw, mm.group(0)))
            if tid and tid != ctx.self_id:
                ctx.links += 1
                return link(tid, mm.group(0))
            return mm.group(0)
        nums = re.sub(r'\d+\.\d+', rep_num, m.group(3))
        return m.group(1) + m.group(2) + nums
    t = REF_RE.sub(rep_env, t)

    def rep_chap(m):
        def rep_num(mm):
            tid = ctx.targets.get(('Capitolo', mm.group(0)))
            if tid:
                ctx.links += 1
                return link(tid, mm.group(0))
            return mm.group(0)
        return m.group(1) + m.group(2) + re.sub(r'\d+', rep_num, m.group(3))
    t = CHAP_RE.sub(rep_chap, t)

    def rep_sec(m):
        out = []
        a = ctx.targets.get(('§', m.group(1)))
        out.append(link(a, '§' + m.group(1)) if a else '§' + m.group(1))
        if a:
            ctx.links += 1
        if m.group(2):
            b = ctx.targets.get(('§', m.group(2)))
            out.append('–' + (link(b, m.group(2)) if b else m.group(2)))
            if b:
                ctx.links += 1
        return ''.join(out)
    t = SECT_RE.sub(rep_sec, t)

    def rep_eq(m):
        tid = ctx.targets.get(('eq', m.group(1)))
        if tid:
            ctx.links += 1
            return '(' + link(tid, m.group(1), 'xr xr-eq') + ')'
        return m.group(0)
    t = EQREF_RE.sub(rep_eq, t)
    return t


def inline(text, ctx, math_list=None):
    """Markdown inline -> HTML. Le formule diventano <span class="m">TeX</span>."""
    maths = []

    def mrep(m):
        maths.append(m.group(1))
        return f'\x00{len(maths) - 1}\x00'
    t = re.sub(r'\$(.+?)\$', mrep, text)
    t = esc(t)
    # link Markdown
    t = re.sub(r'\[([^\]]+)\]\(#([^)]+)\)', lambda m: f'<a href="#{attr(m.group(2))}">{m.group(1)}</a>', t)
    t = crossref(t, ctx)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
    if math_list is not None:
        math_list.extend(maths)
    t = re.sub('\x00(\\d+)\x00', lambda m: f'<span class="m">{esc(maths[int(m.group(1))])}</span>', t)
    # niente a capo fra una formula e la punteggiatura che la segue (o la parentesi che la precede)
    t = re.sub(r'([(«\[]?)(<span class="m">[^<]*</span>)([.,;:!?)»\]]+)', r'<span class="nw">\1\2\3</span>', t)
    t = re.sub(r'([(«\[])(<span class="m">[^<]*</span>)(?![^<]*</span>)', r'<span class="nw">\1\2</span>', t)
    return t


# ---------------------------------------------------------------- rendering

class Renderer:
    def __init__(self, ctx):
        self.ctx = ctx
        self.math_seq = []     # sequenza delle formule nell'ordine del documento (per i controlli)
        self.bid = 0
        self.search = []       # voci per la ricerca
        self.cur_path = []     # [part, chapter, section] per i risultati
        self.cur_env = ''      # etichetta del riquadro corrente (per il formulario)
        self.keyf = []         # formule chiave (\\boxed) per il formulario
        self.cur_anchor = 'top'
        self.figs = {}
        self.stats = {'env': {}, 'figs': 0, 'labs': 0, 'proofs': 0, 'notes': 0}

    # --- elementi base
    def new_id(self):
        self.bid += 1
        return f'b{self.bid}'

    def il(self, text):
        return inline(text, self.ctx, self.math_seq)

    def add_search(self, kind, text, anchor, title=None):
        if not text:
            return
        self.search.append({'k': kind, 't': title or '', 'x': text, 'a': anchor,
                            'p': ' › '.join(p for p in self.cur_path if p)})

    def para(self, b, cls=None, search=True):
        pid = self.new_id()
        c = []
        if cls:
            c.append(cls)
        if b.get('cont'):
            c.append('cont')
        if search:
            self.add_search('p', md_plain(b['text']), pid)
        ca = f' class="{" ".join(c)}"' if c else ''
        return f'<p id="{pid}"{ca}>{self.il(b["text"])}</p>'

    def dmath(self, b):
        tex = b['tex']
        self.math_seq.append(tex)
        m = re.search(r'\\tag\{(\d+\.\d+)\}', tex)
        did = num_id("eq", m.group(1)) if m else None
        cls = ' cont' if b.get('cont') else ''
        if '\\boxed' in tex:
            # formula chiave: riquadro evidenziato e voce del formulario
            cls += ' key'
            if did is None:
                did = f'kf{len(self.keyf) + 1}'
            chap = self.cur_path[1] if len(self.cur_path) > 1 else ''
            if not chap.startswith('20.'):
                self.keyf.append({'a': did, 'x': tex, 'c': chap,
                                  's': self.cur_path[2] if len(self.cur_path) > 2 else '',
                                  'e': self.cur_env, 'g': m.group(1) if m else ''})
        idattr = f' id="{did}"' if did else ''
        return f'<div class="dm{cls}"{idattr}>{esc(tex)}</div>'

    def lst(self, b, cls=None):
        tag = 'ol' if b['ordered'] else 'ul'
        start = f' start="{b["start"]}"' if b['ordered'] and b['start'] != 1 else ''
        ca = f' class="{cls}"' if cls else ''
        out = [f'<{tag}{start}{ca}>']
        for it in b['items']:
            out.append('<li>' + self.blocks(it, in_list=True) + '</li>')
        out.append(f'</{tag}>')
        return ''.join(out)

    def table(self, b):
        out = ['<div class="tbl"><table>']
        out.append('<thead><tr>')
        for k, h in enumerate(b['head']):
            al = b['align'][k] if k < len(b['align']) else ''
            st = f' style="text-align:{al}"' if al else ''
            out.append(f'<th{st}>{self.il(h)}</th>')
        out.append('</tr></thead><tbody>')
        for r in b['rows']:
            out.append('<tr>')
            for k, cell in enumerate(r):
                al = b['align'][k] if k < len(b['align']) else ''
                st = f' style="text-align:{al}"' if al else ''
                if k == 0:
                    out.append(f'<th scope="row"{st}>{self.il(cell)}</th>')
                else:
                    out.append(f'<td{st}>{self.il(cell)}</td>')
            out.append('</tr>')
        out.append('</tbody></table></div>')
        return ''.join(out)

    def blocks(self, bl, in_list=False):
        out = []
        for b in bl:
            if 'kind_fig' in b:
                out.append(self.figure({'img': b['img'], 'cap': b['cap']}))
                continue
            t = b['type']
            if t == 'para':
                txt = b['text']
                m = LEAD_RE.match(txt)
                if m and not in_list and not LABEL_RE.match(txt):
                    pid = self.new_id()
                    self.add_search('p', md_plain(txt), pid)
                    cont = ' class="cont"' if b.get('cont') else ''
                    out.append(f'<p id="{pid}"{cont}><strong class="runin">{self.il(m.group(1))}</strong> '
                               f'{self.il(m.group(2))}</p>')
                else:
                    out.append(self.para(b))
            elif t == 'dmath':
                out.append(self.dmath(b))
            elif t == 'list':
                out.append(self.lst(b))
            elif t == 'table':
                out.append(self.table(b))
            elif t == 'quote':
                out.append(self.callout({'q': b}))
            else:
                raise ValueError(f'blocco inatteso {t} alla riga {b["line"]}')
        return ''.join(out)

    # --- nodi semantici
    def figure(self, nd):
        img = nd['img']
        src = os.path.join(os.path.dirname(SRC), img['src'])
        with open(src, 'rb') as fh:
            data = fh.read()
        w = h = None
        mw = re.search(rb'<svg[^>]*\swidth="([\d.]+)"', data)
        mh = re.search(rb'<svg[^>]*\sheight="([\d.]+)"', data)
        if mw and mh:
            w, h = float(mw.group(1)), float(mh.group(1))
        uri = 'data:image/svg+xml;base64,' + base64.b64encode(data).decode('ascii')
        cap = nd.get('cap')
        fid = None
        caphtml = ''
        if cap is not None:
            m = FIGCAP_RE.match(cap['text'])
            fid = num_id('fig', m.group(2))
            caphtml = (f'<figcaption><span class="fig-n">{esc(m.group(1))}</span> — '
                       f'{self.il(m.group(3))}</figcaption>')
            self.add_search('f', md_plain(m.group(3)), fid, m.group(1))
        self.stats['figs'] += 1
        idattr = f' id="{fid}"' if fid else ''
        size = ''
        if w:
            # ingrandite per la colonna larga, ma mai più alte di ~540 px
            disp = round(min(w * 1.5, w * 540 / h))
            size = f' width="{round(w)}" height="{round(h)}" style="width:{disp}px"'
        return (f'<figure class="fig"{idattr}><button class="fig-zoom" type="button" '
                f'aria-label="Ingrandisci: {attr(img["alt"])}"><img src="{uri}" alt="{attr(img["alt"])}"'
                f'{size} decoding="async"></button>{caphtml}</figure>')

    def diagram(self, nd):
        code = nd['code']
        if code['lang'] != 'mermaid':
            return f'<pre>{esc(code["text"])}</pre>'
        g = parse_mermaid(code['text'])
        # le etichette passano dal renderer inline (formule incluse)
        for x in g['nodes']:
            x['html'] = '<br>'.join(inline(part, self.ctx) for part in x['label'].split('<br/>'))
        for e in g['edges']:
            if e['label'] is not None:
                e['html'] = '<br>'.join(inline(part, self.ctx) for part in e['label'].split('<br/>'))
        for gr in g['groups']:
            gr['html'] = inline(gr['label'], self.ctx)
        data = json.dumps(g, ensure_ascii=False)
        cap = ''
        if nd.get('cap') is not None:
            t = nd['cap']['text'].strip()[1:-1]
            cap = f'<figcaption>{self.il(t)}</figcaption>'
        did = self.new_id()
        return (f'<figure class="dgm" id="{did}"><div class="dgm-c" data-graph="{attr(data)}"></div>'
                f'{cap}</figure>')

    def callout(self, nd):
        q = nd['q']
        bl = q['blocks']
        first = bl[0]
        txt = first['text']
        m = re.match(r'^\*\*(📌 )?(.+?)\*\*\s*(.*)$', txt)
        head, rest = m.group(2), m.group(3)
        cid = self.new_id()
        sub = ''
        if head.startswith('Nota del professore'):
            ctype = 'prof'
            extra = head[len('Nota del professore'):].strip()
            extra = re.sub(r'[.:]$', '', extra).strip()
            if extra:
                sub = f' <span class="call-st">{self.il(extra)}</span>'
            ttl = 'Nota del professore'
            self.stats['notes'] += 1
        else:
            mo = re.match(r'^(Osservazione)\s+(\d+\.\d+)(?:\s*\((.*)\))?\.?$', head)
            if mo:
                ctype = 'oss'
                cid = num_id('oss', mo.group(2))
                ttl = f'Osservazione {mo.group(2)}'
                if mo.group(3):
                    sub = f' <span class="call-st">({self.il(mo.group(3))})</span>'
            elif head.startswith('Attenzione'):
                ctype, ttl = 'warn', 'Attenzione'
            else:
                ctype, ttl = 'note', re.sub(r'[.:]$', '', head)
        self.add_search('n', md_plain(rest), cid, ttl)
        body = []
        if rest:
            pid = self.new_id()
            body.append(f'<p id="{pid}">{self.il(rest)}</p>')
        body.append(self.blocks(bl[1:]))
        icon = {'prof': 'pin', 'oss': 'eye', 'warn': 'alert', 'note': 'info'}[ctype]
        return (f'<aside class="call call-{ctype}" id="{cid}"><div class="call-h">'
                f'<svg class="ic" aria-hidden="true"><use href="#i-{icon}"/></svg>'
                f'<span class="call-t">{ttl}</span>{sub}</div><div class="call-b">{"".join(body)}</div></aside>')

    def env(self, nd):
        etype, num, title = nd['etype'], nd['num'], nd['title']
        abbr = ENV_ABBR[etype]
        fam = ENV_FAMILY[abbr]
        eid = num_id(abbr, num) if num else 'principio-induzione'
        self.stats['env'][etype] = self.stats['env'].get(etype, 0) + 1
        prev_self = self.ctx.self_id
        self.ctx.self_id = eid
        prev_env = self.cur_env
        self.cur_env = nd['label']
        th = f' <span class="env-t">({self.il(title)})</span>' if title else ''
        out = [f'<div class="env env-{fam}" id="{eid}" data-kind="{abbr}">',
               f'<div class="env-h"><span class="env-k">{esc(nd["label"])}</span>{th}</div>',
               '<div class="env-b">']
        plain = md_plain(nd['first']) + ' ' + ' '.join(md_plain(b['text']) for b in nd['body']
                                                       if b.get('type') == 'para')
        self.add_search('e', plain.strip(), eid, nd['label'] + (f' ({md_plain(title)})' if title else ''))
        if nd['first']:
            pid = self.new_id()
            out.append(f'<p id="{pid}">{self.il(nd["first"])}</p>')
        out.append(self.blocks(nd['body']))
        out.append('</div>')
        if nd['sol'] is not None:
            sol = nd['sol']
            m = SOL_RE.match(sol[0]['text'])
            first = m.group(1)
            sid = eid + '-sol'
            out.append(f'<div class="sol closed" id="{sid}"><button class="sol-tog" type="button" aria-expanded="false">'
                       f'<svg class="ic" aria-hidden="true"><use href="#i-chev"/></svg>'
                       f'<span class="sol-k">Soluzione</span><span class="sol-hint" data-x>mostra</span></button>'
                       f'<div class="sol-b"><div class="sol-in">')
            if first:
                pid = self.new_id()
                self.add_search('p', md_plain(first), pid)
                out.append(f'<p id="{pid}">{self.il(first)}</p>')
            out.append(self.blocks(sol[1:]))
            out.append('</div></div></div>')
        out.append('</div>')
        self.ctx.self_id = prev_self
        self.cur_env = prev_env
        return ''.join(out)

    def proof(self, nd):
        self.stats['proofs'] += 1
        lab = nd['label'].rstrip('.')
        m = re.match(r'^(Dimostrazione|Spiegazione|Giustificazione)(.*)$', lab)
        k, extra = m.group(1), m.group(2).strip()
        sub = f' <span class="prf-st">{self.il(extra)}</span>' if extra else ''
        out = [f'<div class="prf"><button class="prf-tog" type="button" aria-expanded="true">'
               f'<svg class="ic" aria-hidden="true"><use href="#i-chev"/></svg>'
               f'<span class="prf-k">{k}</span>{sub}</button><div class="prf-b"><div class="prf-in">']
        if nd['first']:
            pid = self.new_id()
            self.add_search('p', md_plain(nd['first']), pid)
            out.append(f'<p id="{pid}">{self.il(nd["first"])}</p>')
        out.append(self.blocks(nd['body']))
        out.append('</div></div></div>')
        return ''.join(out)

    def exam(self, nd, chap):
        lst = nd['list']
        out = [f'<section class="exam" data-chap="{chap}"><div class="exam-h">'
               f'<svg class="ic" aria-hidden="true"><use href="#i-target"/></svg>'
               f'<span class="exam-t">Domande tipiche d\'esame</span></div><ol class="exam-l">']
        for k, it in enumerate(lst['items'], 1):
            qid = f'q{chap}-{k}'
            self.add_search('q', md_plain(it[0]['text']), qid, f"Domanda d'esame {chap}.{k}")
            out.append(f'<li id="{qid}"><div class="exam-q">{self.blocks(it, True)}</div></li>')
        out.append('</ol></section>')
        return ''.join(out)


# ---------------------------------------------------------------- struttura (titoli)

def analyse_headings(blocks):
    """Assegna gli id ai titoli e costruisce l'albero dell'indice."""
    seen = {}
    heads = []
    for b in blocks:
        if b['type'] != 'heading':
            continue
        text = b['text']
        if b['level'] == 1 and text == 'Geometria e Algebra Lineare':
            b['id'] = 'top'
            b['kind'] = 'title'
            continue
        if b['level'] == 2 and text == 'Indice':
            b['id'] = 'indice'
            b['kind'] = 'indice'
        else:
            b['id'] = slug(text, seen)
        heads.append(b)
        if b['level'] == 1:
            m = re.match(r'^Parte\s+([IVXL]+)\s+—\s+(.*)$', text)
            b['kind'] = 'part'
            b['num'], b['ttl'] = m.group(1), m.group(2)
        elif b['level'] == 2 and b.get('kind') != 'indice':
            m = re.match(r'^(\d+)\.\s+(.*)$', text)
            if m:
                b['kind'], b['num'], b['ttl'] = 'chapter', m.group(1), m.group(2)
            else:
                b['kind'], b['num'], b['ttl'] = 'intro', None, text
        elif b['level'] == 3:
            m = re.match(r'^(\d+\.\d+)\s+(.*)$', text)
            if m:
                b['kind'], b['num'], b['ttl'] = 'section', m.group(1), m.group(2)
            else:
                b['kind'], b['num'], b['ttl'] = 'riepilogo', None, text
        elif b['level'] == 4:
            b['kind'], b['num'], b['ttl'] = 'sub', None, text
    # albero: nella sidebar i capitoli sono le Parti; i capitoli numerati diventano
    # sottosezioni di ciascuna Parte, le sezioni (N.M) e i sottotitoli scendono di un livello
    root = []
    part = chap = sec = None
    for h in heads:
        node = {'h': h, 'kids': []}
        k = h['kind']
        if k == 'indice':
            root.append(node)
        elif k == 'part':
            node['newpart'] = True   # riga di separazione prima di ogni Parte
            root.append(node)
            part, chap, sec = node, None, None
        elif k == 'intro':
            root.append(node)
            chap, sec = node, None
        elif k == 'chapter':
            if part is None:
                node['newpart'] = True
                root.append(node)
            else:
                part['kids'].append(node)
            chap, sec = node, None
        elif k in ('section', 'riepilogo'):
            chap['kids'].append(node)
            sec = node
        elif k == 'sub':
            sec['kids'].append(node)
    return heads, root


CHEV = '<svg class="ic" aria-hidden="true"><use href="#i-chev"/></svg>'


def render_tree(nodes, ctx, depth=0, labs_by_sec=None):
    if not depth:
        ctx.no_refs = True      # niente link annidati dentro le voci dell'indice
    out = ['<ul class="t-l">' if depth else '<ul class="t-l t-root">']
    for nd in nodes:
        h = nd['h']
        k = h['kind']
        kids = nd['kids']
        hid = h['id']
        if k == 'part':
            label = f'<span class="t-n">{esc(h["num"])}</span><span class="t-tx">{inline(h["ttl"], ctx)}</span>'
        elif k == 'chapter':
            label = f'<span class="t-n">{esc(h["num"])}</span><span class="t-tx">{inline(h["ttl"], ctx)}</span>'
        elif k == 'section':
            label = f'<span class="t-n">{esc(h["num"])}</span><span class="t-tx">{inline(h["ttl"], ctx)}</span>'
        elif k == 'riepilogo':
            label = (f'<span class="t-n t-ic"><svg class="ic" aria-hidden="true"><use href="#i-list"/></svg>'
                     f'</span><span class="t-tx">{inline(h["ttl"], ctx)}</span>')
        elif k == 'sub':
            label = f'<span class="t-dot" aria-hidden="true"></span><span class="t-tx">{inline(h["ttl"], ctx)}</span>'
        else:  # indice, intro
            label = f'<span class="t-tx">{inline(h["text"], ctx)}</span>'
        extra = ''
        if labs_by_sec and hid in labs_by_sec:
            extra = (f'<span class="t-lab" title="Contiene {labs_by_sec[hid]} laboratori interattivi">'
                     f'<svg class="ic" aria-hidden="true"><use href="#i-flask"/></svg></span>')
        tog = (f'<button class="t-tog" type="button" aria-expanded="false" tabindex="-1" '
               f'aria-label="Espandi o comprimi">{CHEV}</button>') if kids else ''
        if nd.get('newpart'):
            out.append('<li class="t-sep" role="presentation"></li>')
        cls = f't-{k}' + (' t-chapter' if k == 'part' else '')
        out.append(f'<li class="t-i {cls}" data-id="{attr(hid)}"{" data-has" if kids else ""}>'
                   f'<div class="t-row"><a class="t-a" href="#{attr(hid)}">{label}{extra}</a>{tog}</div>')
        if kids:
            out.append('<div class="t-kids"><div class="t-kin">')
            out.append(render_tree(kids, ctx, depth + 1, labs_by_sec))
            out.append('</div></div>')
        out.append('</li>')
    out.append('</ul>')
    if not depth:
        ctx.no_refs = False
    return ''.join(out)


# ---------------------------------------------------------------- laboratori interattivi
# id -> (ancora dopo cui inserirlo, titolo, istruzioni)
LABS = [
    ('es-1-13', 'zp-classi', 'Classi di resto modulo $p$',
     'Scegli $p$: ogni intero viene colorato con la sua classe di resto. Passa sopra un numero (o toccalo) per evidenziare tutta la sua classe.'),
    ("p:L'idea è una catena", 'induzione', 'La catena dell’induzione',
     'La base fa cadere la prima tessera, il passo induttivo fa cadere ogni tessera successiva. Prova a togliere la base o il passo.'),
    ('es-2-4', 'zp-tabella', 'La tabella moltiplicativa di $\\mathbb{Z}_p$',
     'Con $p$ primo ogni riga (tranne quella di $[0]$) contiene un $[1]$: l’inverso. Con $p$ composto compaiono divisori dello zero, evidenziati in rosso.'),
    ('fig-3-2', 'c-piano', 'Il piano complesso',
     'Trascina $z$: leggi parte reale e immaginaria, modulo, argomento principale, coniugato e inverso.'),
    ('fig-3-6', 'c-arg', 'Argomento principale e quadranti',
     'Trascina $z$ in tutti i quadranti e osserva quale caso della formula (3.9) si applica.'),
    ('fig-3-8', 'c-prodotto', 'Somma e prodotto nel piano complesso',
     'Trascina $z_1$ e $z_2$. In modalità prodotto, «Anima» mostra la rotazione di $\\arg z_2$ e la dilatazione di fattore $|z_2|$.'),
    ('teo-3-5', 'c-demoivre', 'Le potenze $z^n$ (De Moivre)',
     'Muovi $z$ e il numero di potenze: i moduli si elevano a potenza, gli argomenti si sommano.'),
    ('teo-3-6', 'c-eulero', 'La serie di $e^{i\\theta}$',
     'Le somme parziali della serie di $e^{i\\theta}$ formano una spezzata che si avvicina al punto $(\\cos\\theta,\\sin\\theta)$.'),
    ('fig-3-11', 'c-radici', 'Radici $n$-esime',
     'Scegli $n$ e trascina $a$: le $n$ radici sono i vertici di un poligono regolare di raggio $\\sqrt[n]{|a|}$.'),
    ('es-4-8', 'm-prodotto', 'Il prodotto righe per colonne, passo per passo',
     'Clicca una casella di $AB$ (o premi «Anima») per vedere quale riga di $A$ e quale colonna di $B$ la producono.'),
    ('fig-4-2', 'm-trasf', 'Matrici $2\\times2$ come trasformazioni del piano',
     'Scegli una matrice o modifica i coefficienti: le colonne sono le immagini dei vettori $V_1, V_2$; il determinante misura l’area con segno.'),
    ("p:**Un'applicazione: un processo di Markov.**", 'm-markov', 'Il processo di Markov degli occupati',
     'Applica ripetutamente $A$ al vettore $X_0$ e osserva come cambiano occupati e disoccupati anno dopo anno.'),
    ('es-5-5', 'det-laplace', 'Sviluppo di Laplace interattivo',
     'Scegli la riga o la colonna lungo cui sviluppare: i segni seguono la scacchiera e i termini con un elemento nullo non si calcolano.'),
    ('fig-5-3', 'det-area', 'Il determinante come area con segno',
     'Trascina le punte delle colonne $u$ e $v$: l’area del parallelogramma è $|\\det A|$, il segno indica l’orientazione.'),
    ('fig-6-2', 'v-liberi', 'Un vettore libero e i suoi rappresentanti',
     'Trascina la punta della freccia evidenziata per cambiare $\\underline{v}$; trascina $P$ per vedere l’unico rappresentante applicato in $P$.'),
    ('fig-6-5', 'v-somma', 'Somma, differenza e prodotto per uno scalare',
     'Trascina $\\underline{v}$ e $\\underline{w}$ e scegli la costruzione: triangolo, parallelogramma, differenza o multiplo $\\lambda\\underline{v}$.'),
    ('fig-7-4', 'v-comb', 'Combinazioni lineari e reticolo obliquo',
     'Trascina $\\underline{v}_1$, $\\underline{v}_2$ e $\\underline{t}$: i coefficienti $\\lambda_1,\\lambda_2$ sono le coordinate di $\\underline{t}$ nel reticolo costruito su $\\underline{v}_1,\\underline{v}_2$.'),
    ('fig-7-5', 'v-basi3d', 'Il teorema delle basi nello spazio',
     'Trascina la scena per ruotarla. La costruzione $OQPR$ scompone $\\underline{v}$ lungo il piano di $\\underline{v}_1,\\underline{v}_2$ e la retta di $\\underline{v}_3$.'),
    ('es-8-3', 'ps-parametro', 'Trovare $h$ per l’ortogonalità (Esempio 8.3)',
     'Muovi $h$: $\\underline{w}_2=3\\underline{v}_1+h\\underline{v}_2$ cambia direzione e $\\underline{w}_1\\cdot\\underline{w}_2=15h+6$ si annulla per $h=-\\frac25$.'),
    ('fig-8-4', 'ps-proiezione', 'Prodotto scalare e proiezione ortogonale',
     'Trascina $\\underline{v}$ e $\\underline{w}$: osserva il segno del prodotto scalare, la componente orientata e la scomposizione $\\underline{w}=\\underline{t}_1+\\underline{t}_2$.'),
    ('fig-9-2', 'pv-vettoriale', 'Prodotto vettoriale e regola della mano destra',
     'Modifica $\\underline{u}$ e $\\underline{v}$ e ruota la scena: $\\underline{u}\\wedge\\underline{v}$ è perpendicolare a entrambi e il suo modulo è l’area del parallelogramma.'),
    ('fig-9-3', 'pv-misto', 'Prodotto misto e volume',
     'Il prodotto misto è il volume con segno del parallelepipedo: si annulla quando $\\underline{t}$ entra nel piano di $\\underline{u}$ e $\\underline{v}$.'),
    ('es-10-9', 'base-on', 'Costruire una base ortonormale positiva',
     'Segui i tre passi del Procedimento 10.7: normalizzare, togliere la proiezione, completare con il prodotto vettoriale.'),
    ('fig-11-3', 'r-retta', 'La retta parametrica',
     'Muovi $t$: il punto $P(t)=P_0+t\\,\\underline{v}$ percorre la retta; $t=0$ dà $P_0$, $t=1$ dà $P_1$.'),
    ('fig-11-8', 'r-piano', 'Il piano: parametri, normale ed equazione cartesiana',
     'Muovi $t$ e $s$ per percorrere il piano; la normale $\\underline{M}=\\underline{v}_1\\wedge\\underline{v}_2$ fornisce i coefficienti dell’equazione cartesiana.'),
    ('es-12-5', 'r-complanari', 'Rette complanari o sghembe (Esempio 12.5)',
     'Muovi $h$: il determinante $3h-2$ decide se $P_1$ sta sul piano ausiliario $\\alpha$; per $h=\\frac23$ le rette si incontrano.'),
    ('fig-12-6', 'r-tre-piani', 'Tre piani e il sistema lineare',
     'Scegli una configurazione: il determinante delle normali decide se esiste un solo punto comune.'),
    ('fig-12-7', 'r-fascio', 'Il fascio di piani di asse $r$',
     'Muovi il parametro: il piano $\\lambda(\\dots)+\\mu(\\dots)=0$ ruota attorno alla retta $r$.'),
    ('es-12-18', 'r-sghembe', 'Distanza fra rette sghembe',
     'Muovi $P$ su $r$ e $Q$ su $s$: la distanza minima si raggiunge sulla perpendicolare comune.'),
]


def lab_html(lid, title, desc, ctx):
    return (f'<section class="lab" id="lab-{lid}" data-lab="{lid}" aria-label="Laboratorio: {attr(md_plain(title))}" data-x>'
            f'<div class="lab-h"><span class="lab-k"><svg class="ic" aria-hidden="true"><use href="#i-flask"/></svg>'
            f'Laboratorio</span><h5 class="lab-t">{inline(title, ctx)}</h5></div>'
            f'<p class="lab-d">{inline(desc, ctx)}</p><div class="lab-m"></div></section>')


# ---------------------------------------------------------------- documento

def render_document(blocks):
    heads, tree = analyse_headings(blocks)
    ctx = Ctx()
    # bersagli dei riferimenti
    for h in heads:
        if h['kind'] == 'chapter':
            ctx.targets[('Capitolo', h['num'])] = h['id']
        elif h['kind'] == 'section':
            ctx.targets[('§', h['num'])] = h['id']
    nodes = group(blocks)
    for nd in nodes:
        if nd['kind'] == 'env' and nd['num']:
            ctx.targets[(nd['etype'], nd['num'])] = num_id(ENV_ABBR[nd['etype']], nd['num'])
        elif nd['kind'] == 'figure' and nd['cap'] is not None:
            m = FIGCAP_RE.match(nd['cap']['text'])
            ctx.targets[('Figura', m.group(2))] = num_id('fig', m.group(2))
        elif nd['kind'] == 'callout':
            m = re.match(r'^\*\*Osservazione (\d+\.\d+)', nd['q']['blocks'][0]['text'])
            if m:
                ctx.targets[('Osservazione', m.group(1))] = num_id('oss', m.group(1))
    for nd in nodes:  # figure annidate negli esempi
        if nd['kind'] == 'env':
            for b in (nd['body'] + (nd['sol'] or [])):
                if 'kind_fig' in b and b['cap'] is not None:
                    m = FIGCAP_RE.match(b['cap']['text'])
                    ctx.targets[('Figura', m.group(2))] = num_id('fig', m.group(2))
    for b in mdparse.walk(blocks):
        if b['type'] == 'dmath':
            m = re.search(r'\\tag\{(\d+\.\d+)\}', b['tex'])
            if m:
                ctx.targets[('eq', m.group(1))] = num_id('eq', m.group(1))

    R = Renderer(ctx)
    lab_after = {a: (lid, t, d) for a, lid, t, d in LABS}
    used_labs = []
    labs_by_sec = {}
    out = []
    part_title = chap_title = sec_title = ''
    chap_num = None
    cur_sec_id = None
    chap_open = False
    in_riep = False
    i = 0
    pending = []          # laboratori in attesa: si inseriscono dopo eventuali dimostrazioni
    p_anchors = {a[2:]: a for a in lab_after if a.startswith('p:')}

    def ids_in(nd):
        ids = []
        if nd['kind'] == 'env':
            ids.append(num_id(ENV_ABBR[nd['etype']], nd['num']) if nd['num'] else 'principio-induzione')
            for b in (nd['body'] + (nd['sol'] or [])):
                if 'kind_fig' in b and b['cap'] is not None:
                    ids.append(num_id('fig', FIGCAP_RE.match(b['cap']['text']).group(2)))
        elif nd['kind'] == 'figure' and nd['cap'] is not None:
            ids.append(num_id('fig', FIGCAP_RE.match(nd['cap']['text']).group(2)))
        return ids

    while i < len(nodes):
        nd = nodes[i]
        k = nd['kind']
        if k == 'block' and nd['b']['type'] == 'heading':
            if pending:
                out.extend(pending)
                pending = []
            h = nd['b']
            ctx.no_refs = True
            hk = h['kind']
            in_riep = False
            if hk == 'title':
                # titolo + sottotitolo: diventano l'intestazione
                sub = ''
                if i + 1 < len(nodes) and nodes[i + 1]['kind'] == 'block' and nodes[i + 1]['b']['type'] == 'para':
                    sub = nodes[i + 1]['b']['text'].strip('*')
                    i += 1
                out.append(('HERO', h['text'], sub))
                ctx.no_refs = False
                i += 1
                continue
            if hk == 'indice':
                # l'indice Markdown: lista successiva
                lst = nodes[i + 1]['b']
                ctx.no_refs = True
                out.append(f'<section class="indice" aria-labelledby="indice"><h2 class="h-indice" id="indice">'
                           f'Indice</h2>{R.lst(lst, "idx")}</section>')
                ctx.no_refs = False
                i += 2
                continue
            if hk == 'part':
                if chap_open:
                    out.append('</section>')
                    chap_open = False
                part_title = f'Parte {h["num"]}'
                chap_title = sec_title = ''
                R.cur_path = [part_title, '', '']
                out.append(f'<section class="part" aria-labelledby="{attr(h["id"])}"><h2 class="h-part" id="{attr(h["id"])}">'
                           f'<span class="h-part-k">Parte {esc(h["num"])}</span><span class="h-part-sep" aria-hidden="true"> — </span>'
                           f'<span class="h-part-t">{R.il(h["ttl"])}</span></h2></section>')
                R.add_search('h', md_plain(h['text']), h['id'], h['text'])
            elif hk in ('chapter', 'intro'):
                if chap_open:
                    out.append('</section>')
                chap_open = True
                chap_num = h['num']
                chap_title = (h['num'] + '. ' + md_plain(h['ttl'])) if h['num'] else md_plain(h['ttl'])
                sec_title = ''
                if hk == 'intro':
                    R.cur_path = ['', chap_title, '']
                else:
                    R.cur_path = [part_title, chap_title, '']
                cnum = f'data-chap="{h["num"]}"' if h['num'] else 'data-chap="0"'
                eyebrow = (f'<span class="h-chap-k"><span data-x>Capitolo </span>{esc(h["num"])}</span>'
                           if h['num'] else '')
                ttl = R.il(h['ttl']) if h['num'] else R.il(h['text'])
                out.append(f'<section class="chap" {cnum}><h3 class="h-chap" id="{attr(h["id"])}">{eyebrow} '
                           f'<span class="h-chap-t">{ttl}</span></h3>')
                R.add_search('h', md_plain(h['text']), h['id'], md_plain(h['text']))
                cur_sec_id = h['id']
            elif hk in ('section', 'riepilogo'):
                sec_title = (h['num'] + ' ' + md_plain(h['ttl'])) if h['num'] else md_plain(h['ttl'])
                R.cur_path = [part_title, chap_title, sec_title]
                cur_sec_id = h['id']
                if hk == 'section':
                    inner = f'<span class="h-sec-n">{esc(h["num"])}</span> <span class="h-sec-t">{R.il(h["ttl"])}</span>'
                else:
                    inner = f'<span class="h-sec-t">{R.il(h["ttl"])}</span>'
                    in_riep = True
                out.append(f'<h4 class="h-sec{" h-riep" if hk == "riepilogo" else ""}" id="{attr(h["id"])}" '
                           f'data-sec>{inner}</h4>')
                R.add_search('h', md_plain(h['text']), h['id'], md_plain(h['text']))
            elif hk == 'sub':
                out.append(f'<h5 class="h-sub" id="{attr(h["id"])}">{R.il(h["ttl"])}</h5>')
                R.add_search('h', md_plain(h['text']), h['id'], md_plain(h['text']))
            ctx.no_refs = False
            i += 1
            continue
        if k == 'block':
            b = nd['b']
            if b['type'] == 'hr':
                out.append('<hr class="sep">')
            elif in_riep and b['type'] == 'list':
                out.append(f'<div class="riep">{R.lst(b, "riep-l")}</div>')
            else:
                out.append(R.blocks([b]))
                if b['type'] == 'para':
                    for pre, key in p_anchors.items():
                        if b['text'].startswith(pre):
                            pending.append(('LAB', key, cur_sec_id))
        elif k == 'env':
            out.append(R.env(nd))
        elif k == 'proof':
            out.append(R.proof(nd))
        elif k == 'figure':
            out.append(R.figure(nd))
        elif k == 'diagram':
            out.append(R.diagram(nd))
        elif k == 'callout':
            out.append(R.callout(nd))
        elif k == 'exam':
            out.append(R.exam(nd, chap_num or '0'))
        for aid in ids_in(nd):
            if aid in lab_after:
                pending.append(('LAB', aid, cur_sec_id))
        nxt = nodes[i + 1] if i + 1 < len(nodes) else None
        if pending and not (nxt is not None and nxt['kind'] == 'proof'):
            out.extend(pending)
            pending = []
        i += 1
    out.extend(pending)
    if chap_open:
        out.append('</section>')

    # sostituisce i segnaposto dei laboratori
    final = []
    hero = None
    for piece in out:
        if isinstance(piece, tuple) and piece[0] == 'HERO':
            hero = piece
            continue
        if isinstance(piece, tuple) and piece[0] == 'LAB':
            anchor, sec = piece[1], piece[2]
            lid, t, d = lab_after[anchor]
            used_labs.append(lid)
            labs_by_sec[sec] = labs_by_sec.get(sec, 0) + 1
            R.stats['labs'] += 1
            R.add_search('l', md_plain(d), 'lab-' + lid, 'Laboratorio: ' + md_plain(t))
            final.append(lab_html(lid, t, d, ctx))
            continue
        final.append(piece)
    missing = [a for a, *_ in LABS if (lab_after[a][0] not in used_labs)]
    dup = {x for x in used_labs if used_labs.count(x) > 1}
    if dup:
        print('ATTENZIONE: laboratori duplicati:', dup)
    if missing:
        print('ATTENZIONE: laboratori senza ancora:', missing)
    # le sezioni che contengono un laboratorio sono segnate anche sui capitoli? solo sezioni.
    tree_html = render_tree(tree, ctx, 0, labs_by_sec)
    return {'hero': hero, 'body': ''.join(final), 'tree': tree_html, 'R': R, 'ctx': ctx, 'heads': heads,
            'tree_data': tree, 'labs': used_labs}


def font_face(name, family, style, wght, rng):
    with open(os.path.join(FONTS, name), 'rb') as fh:
        b64 = base64.b64encode(fh.read()).decode('ascii')
    return (f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{wght};font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2');unicode-range:{rng};}}")


def katex_css():
    with open(os.path.join(KATEX, 'katex.min.css'), encoding='utf-8') as fh:
        css = fh.read()

    def rep(m):
        path = os.path.join(KATEX, m.group(1))
        if not path.endswith('.woff2'):
            return ''
        with open(path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return f'url(data:font/woff2;base64,{b64}) format("woff2")'
    # tiene solo i woff2 (incorporati) e scarta woff/ttf
    css = re.sub(r'url\((fonts/[^)]+?\.woff2)\)\s*format\("woff2"\)', rep, css)
    css = re.sub(r',\s*url\(fonts/[^)]+?\.(?:woff|ttf)\)\s*format\("(?:woff|truetype)"\)', '', css)
    return css


def assemble(doc, out_path):
    R = doc['R']
    with open(os.path.join(TPL, 'page.tpl'), encoding='utf-8') as fh:
        page = fh.read()
    with open(os.path.join(TPL, 'style.css'), encoding='utf-8') as fh:
        css = fh.read()
    js_parts = []
    for name in ('diagrams.js', 'widgets.js', 'labs3d.js', 'app.js'):
        p = os.path.join(TPL, name)
        if os.path.exists(p):
            with open(p, encoding='utf-8') as fh:
                js_parts.append(fh.read())
    with open(os.path.join(KATEX, 'katex.min.js'), encoding='utf-8') as fh:
        katex_js = fh.read()
    with open(os.path.join(FONTS, 'fonts.json'), encoding='utf-8') as fh:
        fonts = json.load(fh)
    faces = []
    for name, family, style, wght, rng in fonts:
        if 'greek' in name:
            continue
        faces.append(font_face(name, family, style, wght.replace(' ', ' '), rng))
    hero = doc['hero']
    st = R.stats
    n_es = st['env'].get('Esempio', 0)
    n_ex = st['env'].get('Esercizio', 0)
    n_th = sum(st['env'].get(k, 0) for k in ('Teorema', 'Proposizione', 'Corollario', 'Lemma'))
    n_def = st['env'].get('Definizione', 0)
    chapters = sum(1 for h in doc['heads'] if h['kind'] == 'chapter')
    sections = sum(1 for h in doc['heads'] if h['kind'] == 'section')
    stats_html = (f'<li><b>{chapters}</b> capitoli</li><li><b>{sections}</b> sezioni</li>'
                  f'<li><b>{n_def}</b> definizioni</li><li><b>{n_th}</b> teoremi e proposizioni</li>'
                  f'<li><b>{n_es}</b> esempi</li><li><b>{n_ex}</b> esercizi svolti</li>'
                  f'<li><b>{st["figs"]}</b> figure</li><li><b>{st["labs"]}</b> laboratori interattivi</li>')
    search_json = json.dumps(R.search, ensure_ascii=False, separators=(',', ':'))
    keyf_json = json.dumps(R.keyf, ensure_ascii=False, separators=(',', ':'))
    rep = {
        '{{TITLE}}': esc(hero[1]),
        '{{SUBTITLE}}': esc(hero[2]),
        '{{FONTS}}': '\n'.join(faces),
        '{{KATEX_CSS}}': katex_css(),
        '{{CSS}}': css,
        '{{TREE}}': doc['tree'],
        '{{BODY}}': doc['body'],
        '{{STATS}}': stats_html,
        '{{CHAPS}}': f'Capitoli 1–{chapters}',
        '{{SEARCH}}': search_json.replace('</', '<\\/'),
        '{{FORMULE}}': keyf_json.replace('</', '<\\/'),
        '{{KATEX_JS}}': katex_js.replace('</script', '<\\/script'),
        '{{APP_JS}}': '\n'.join(js_parts).replace('</script', '<\\/script'),
    }
    for k, v in rep.items():
        if k not in page:
            raise SystemExit('segnaposto mancante nel template: ' + k)
        page = page.replace(k, v)
    with open(out_path, 'w', encoding='utf-8') as fh:
        fh.write(page)
    return page


def main():
    out = OUT
    if '--out' in sys.argv:
        out = os.path.abspath(sys.argv[sys.argv.index('--out') + 1])
    blocks = mdparse.parse_file(SRC)
    doc = render_document(blocks)
    page = assemble(doc, out)
    R = doc['R']
    print(f'scritto {out}: {len(page) / 1e6:.2f} MB, {len(R.math_seq)} formule, '
          f'{doc["ctx"].links} riferimenti incrociati, {R.stats["figs"]} figure, {R.stats["labs"]} laboratori')
    print('ambienti:', R.stats['env'], 'dimostrazioni:', R.stats['proofs'], 'note:', R.stats['notes'])
    if '--no-check' not in sys.argv:
        import checks
        ok = checks.run(SRC, page, R)
        if not ok:
            sys.exit(1)


if __name__ == '__main__':
    main()
