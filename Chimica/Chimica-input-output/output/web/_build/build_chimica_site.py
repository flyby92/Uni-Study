#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera il sito ipermediale a pagina unica dalla dispensa definitiva di Chimica."""
import re, os, unicodedata, html as htmlmod, math

SRC = "/home/aser/Video/Primo-semestre/Chimica/Chimica-input-output/output/Dispensa-Definitiva/dispensa_definitiva.md"
OUT = "/home/aser/Video/Primo-semestre/Chimica/Chimica-input-output/output/web/chimica.html"

# ---------------------------------------------------------------- utilities
def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def slug(t, seen={}):
    s = unicodedata.normalize('NFKD', t)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r'[^A-Za-z0-9]+', '-', s.lower()).strip('-')
    if not s:
        s = 'sec'
    base = s; i = 2
    while s in seen:
        s = f'{base}-{i}'; i += 1
    seen[s] = 1
    return s

MATH_RE = re.compile(r'\$[^$]+\$')
def inline_md(t):
    """Inline markdown su testo già escaped; protegge i segmenti matematici con segnaposto."""
    maths = []
    def stash(m):
        maths.append(m.group(0))
        return f'\x00{len(maths)-1}\x00'
    t = MATH_RE.sub(stash, t)
    def fmt(x):
        x = re.sub(r'`([^`]+)`', r'<code>\1</code>', x)
        x = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', x)
        x = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<em>\1</em>', x)
        return x
    t = fmt(t)
    def restore(mm):
        return maths[int(mm.group(1))]
    t = re.sub(r'\x00(\d+)\x00', restore, t)
    t = re.sub(r'\[da verificare:\s*([^\]]+)\]',
               r'<span class="verify" title="Punto segnalato dalle fonti: verificare">&#9883; da verificare: \1</span>', t)
    t = t.replace('[sic]', '<em>[sic]</em>')
    return t

# ---------------------------------------------------------------- SVG figures
INK, BLUE, GREEN, RED, AMBER, VIOLET = '#3a3833', '#3b5b92', '#4a7c59', '#a04343', '#a86f2d', '#6b5b95'
GRID = '#d8d1c2'
FS = 'font-family="Inter,system-ui,sans-serif" font-size="13"'

def arrow_defs():
    return ('<defs>'
            '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0L10 5L0 10z" fill="{INK}"/></marker>'
            '<marker id="ahr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0L10 5L0 10z" fill="{RED}"/></marker>'
            '<marker id="ahg" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M0 0L10 5L0 10z" fill="{GREEN}"/></marker>'
            '</defs>')

def svg_livelli():
    # Figura 11.1 — scala dei livelli energetici discreti
    return f'''<svg viewBox="0 0 600 360" role="img" aria-label="Scala dei livelli energetici discreti">
  {arrow_defs()}
  <line x1="80" y1="300" x2="80" y2="30" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="60" y="26" {FS} fill="{INK}" font-weight="600">E</text>
  <line x1="130" y1="270" x2="290" y2="270" stroke="{BLUE}" stroke-width="3"/>
  <text x="302" y="274" {FS} fill="{INK}">n = 1 — stato fondamentale</text>
  <line x1="130" y1="185" x2="290" y2="185" stroke="{BLUE}" stroke-width="3"/>
  <text x="302" y="189" {FS} fill="{INK}">n = 2</text>
  <line x1="130" y1="100" x2="290" y2="100" stroke="{BLUE}" stroke-width="3"/>
  <text x="302" y="104" {FS} fill="{INK}">n = 3</text>
  <line x1="80" y1="52" x2="440" y2="52" stroke="{INK}" stroke-width="1" stroke-dasharray="5 4"/>
  <text x="446" y="56" {FS} fill="{INK}">livello di vuoto (E = 0)</text>
  <line x1="170" y1="262" x2="170" y2="108" stroke="{RED}" stroke-width="2.2" marker-end="url(#ahr)"/>
  <text x="182" y="150" {FS} fill="{RED}">assorbimento ΔE = hν (salto esatto)</text>
  <line x1="248" y1="118" x2="248" y2="258" stroke="{GREEN}" stroke-width="2.2" marker-end="url(#ahg)"/>
  <text x="120" y="336" {FS} fill="{GREEN}">emissione: l’elettrone ricade emettendo un fotone</text>
  <text x="150" y="150" {FS} fill="{INK}"></text>
</svg>'''

def svg_madelung():
    cols = ['s', 'p', 'd', 'f']
    x0, y0, cw, ch = 110, 56, 108, 42
    cells = {}
    r = ''
    counts = [1, 2, 3, 4, 4, 3, 2]   # colonne presenti per riga n = 1..7
    for n in range(1, 8):
        for l in range(counts[n - 1]):
            x = x0 + l * cw; y = y0 + (n - 1) * ch
            cells[(n, l)] = (x + cw / 2, y + ch / 2)
            r += f'<rect x="{x}" y="{y}" width="{cw-8}" height="{ch-10}" rx="8" fill="#fff" stroke="{GRID}"/>'
            r += f'<text x="{x+(cw-8)/2}" y="{y+ch/2-1}" text-anchor="middle" {FS} fill="{INK}">{n}{cols[l]}</text>'
    for n in range(1, 8):
        r += f'<text x="{x0-26}" y="{y0+(n-1)*ch+ch/2-1}" text-anchor="middle" {FS} fill="{INK}" font-weight="600">n={n}</text>'
    for l, c in enumerate(cols):
        r += f'<text x="{x0+l*cw+(cw-8)/2}" y="{y0-16}" text-anchor="middle" {FS} fill="{INK}" font-weight="600">ℓ → {c}</text>'
    for key in [(1, 0), (2, 0)]:
        cx, cy = cells[key]
        r += f'<circle cx="{cx}" cy="{cy}" r="4" fill="{RED}"/>'
    arrows = [((3, 0), (2, 1)), ((4, 0), (3, 1)), ((5, 0), (3, 2)),
              ((6, 0), (4, 2)), ((7, 0), (4, 3))]
    for a, b in arrows:
        (x1, y1) = cells[a]; (x2, y2) = cells[b]
        r += f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{RED}" stroke-width="2" opacity="0.8" marker-end="url(#ahr)"/>'
    return (f'<svg viewBox="0 0 620 372" role="img" aria-label="Regola delle diagonali di Madelung">{arrow_defs()}{r}'
            f'<text x="110" y="344" {FS} fill="{INK}">Ogni freccia percorre una diagonale a costante n+ℓ: la diagonale si riempie</text>'
            f'<text x="110" y="362" {FS} fill="{INK}">dall’alto verso il basso, partendo dalla coda (l’orbitale ns).</text></svg>')

def svg_trends():
    return f'''<svg viewBox="0 0 640 430" role="img" aria-label="Mappa degli andamenti periodici">
  {arrow_defs()}
  <rect x="70" y="40" width="500" height="330" rx="14" fill="#fff" stroke="{GRID}"/>
  <text x="320" y="28" text-anchor="middle" {FS} fill="{INK}" font-weight="600">Tavola periodica (schematica)</text>
  <text x="82" y="66" {FS} fill="{INK}">↑ alto</text>
  <text x="520" y="348" {FS} fill="{INK}">basso</text>
  <text x="76" y="346" {FS} fill="{INK}">sinistra</text>
  <text x="470" y="66" {FS} fill="{INK}">destra →</text>
  <line x1="120" y1="300" x2="520" y2="300" stroke="{BLUE}" stroke-width="3" marker-end="url(#ah)"/>
  <text x="130" y="286" {FS} fill="{BLUE}" font-weight="600">→ AUMENTANO: energia di ionizzazione, affinità elettronica,</text>
  <text x="130" y="270" {FS} fill="{BLUE}" font-weight="600">elettronegatività, Z<tspan baseline-shift="sub" font-size="9">eff</tspan></text>
  <line x1="140" y1="100" x2="140" y2="330" stroke="{GREEN}" stroke-width="3" marker-end="url(#ahg)"/>
  <text x="152" y="120" {FS} fill="{GREEN}" font-weight="600">↓ AUMENTANO:</text>
  <text x="152" y="136" {FS} fill="{GREEN}" font-weight="600">raggio atomico,</text>
  <text x="152" y="152" {FS} fill="{GREEN}" font-weight="600">carattere metallico</text>
  <circle cx="536" cy="60" r="16" fill="#eef2f7" stroke="{BLUE}" stroke-width="2"/>
  <text x="536" y="64" text-anchor="middle" {FS} fill="{BLUE}" font-weight="700">F</text>
  <text x="470" y="96" text-anchor="middle" {FS} fill="{BLUE}">il più elettronegativo (χ = 4,0)</text>
  <circle cx="96" cy="316" r="16" fill="#eef5ef" stroke="{GREEN}" stroke-width="2"/>
  <text x="96" y="320" text-anchor="middle" {FS} fill="{GREEN}" font-weight="700">Fr</text>
  <text x="150" y="336" {FS} fill="{GREEN}">il più elettropositivo / metallico (χ = 0,7)</text>
  <text x="320" y="384" text-anchor="middle" {FS} fill="{INK}">Lungo il periodo → (blu): Z<tspan baseline-shift="sub" font-size="9">eff</tspan> cresce e contrae l’atomo;</text>
  <text x="320" y="402" text-anchor="middle" {FS} fill="{INK}">lungo il gruppo ↓ (verde): cresce n e l’atomo si espande.</text>
</svg>'''.replace('<tspan baseline-shift="sub" font-size="9">eff</tspan>', 'eff')

def svg_morse():
    pts = []
    x0, xmin, xmax = 250, 90, 600
    ymin, ymax, y0 = 316, 44, 150   # y0 = livello zero
    D = ymin - y0                   # profondità minimo
    k = 0.016
    x = xmin
    while x <= xmax:
        dx = (x - x0) * k
        e = (1 - math.exp(-dx)) ** 2 if dx < 3 else 1.0
        y = y0 + D * e
        if dx < 0:
            y = y0 + D * ((1 - math.exp(-dx)) ** 2)
        y = min(max(y, 36), 330)
        pts.append((x, y))
        x += 3
    d = 'M ' + ' L '.join(f'{a:.0f} {b:.1f}' for a, b in pts)
    return f'''<svg viewBox="0 0 660 380" role="img" aria-label="Curva dell'energia potenziale in funzione della distanza internucleare">
  {arrow_defs()}
  <line x1="60" y1="345" x2="60" y2="30" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <line x1="60" y1="330" x2="630" y2="330" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="34" y="26" {FS} fill="{INK}" font-weight="600">E</text>
  <text x="612" y="352" {FS} fill="{INK}" font-weight="600">r</text>
  <line x1="60" y1="{y0}" x2="620" y2="{y0}" stroke="{INK}" stroke-width="1" stroke-dasharray="6 5"/>
  <text x="34" y="{y0+4}" {FS} fill="{INK}">0</text>
  <path d="{d}" fill="none" stroke="{BLUE}" stroke-width="3"/>
  <line x1="{x0}" y1="322" x2="{x0}" y2="330" stroke="{INK}" stroke-width="1.4"/>
  <text x="{x0-8}" y="348" text-anchor="middle" {FS} fill="{INK}" font-weight="600">r<tspan font-size="9" dy="3">e</tspan></text>
  <text x="{x0-6}" y="372" text-anchor="middle" {FS} fill="{INK}">distanza di legame (≈ 74 pm per H₂)</text>
  <text x="112" y="70" {FS} fill="{RED}">repulsioni dominanti</text>
  <text x="380" y="200" {FS} fill="{GREEN}">attrazioni dominanti</text>
  <circle cx="{x0}" cy="{ymin}" r="5" fill="{BLUE}"/>
  <text x="{x0+14}" y="{ymin+22}" {FS} fill="{BLUE}">minimo: condizione di legame stabile</text>
</svg>'''

def svg_bilancio():
    def lvl(y, x1, x2, label):
        return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{BLUE}" stroke-width="3.4"/>'
                f'<text x="{(x1+x2)/2}" y="{y-10}" text-anchor="middle" {FS} fill="{INK}">{label}</text>')
    return f'''<svg viewBox="0 0 700 420" role="img" aria-label="Bilancio energetico per la formazione di due o quattro legami C–H">
  {arrow_defs()}
  <line x1="56" y1="390" x2="56" y2="36" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="20" y="30" {FS} fill="{INK}" font-weight="600">E (eV)</text>
  <line x1="50" y1="70" x2="660" y2="70" stroke="{GRID}" stroke-dasharray="4 5"/>
  <text x="28" y="74" {FS} fill="{INK}">+5</text>
  <line x1="50" y1="170" x2="660" y2="170" stroke="{GRID}" stroke-dasharray="4 5"/>
  <text x="28" y="174" {FS} fill="{INK}">0</text>
  <line x1="50" y1="270" x2="660" y2="270" stroke="{GRID}" stroke-dasharray="4 5"/>
  <text x="22" y="274" {FS} fill="{INK}">−5</text>
  <line x1="50" y1="370" x2="660" y2="370" stroke="{GRID}" stroke-dasharray="4 5"/>
  <text x="16" y="374" {FS} fill="{INK}">−10</text>
  {lvl(170, 130, 330, 'C (s²p²) + 4H')}
  {lvl(70, 260, 480, 'C (s¹p³) + 4H')}
  {lvl(248, 150, 350, 'CH₂ + 2H')}
  {lvl(312, 330, 540, 'CH₄')}
  <line x1="352" y1="166" x2="352" y2="80" stroke="{RED}" stroke-width="2.4" marker-end="url(#ahr)"/>
  <text x="360" y="128" {FS} fill="{RED}" font-weight="600">E<tspan font-size="9" dy="3">p</tspan></text>
  <line x1="222" y1="176" x2="222" y2="242" stroke="{GREEN}" stroke-width="2.4" marker-end="url(#ahg)"/>
  <text x="160" y="216" {FS} fill="{GREEN}" font-weight="600">2E<tspan font-size="9" dy="3">L</tspan></text>
  <line x1="500" y1="80" x2="500" y2="306" stroke="{GREEN}" stroke-width="2.4" marker-end="url(#ahg)"/>
  <text x="510" y="200" {FS} fill="{GREEN}" font-weight="600">4E<tspan font-size="9" dy="3">L</tspan></text>
  <text x="350" y="408" text-anchor="middle" {FS} fill="{INK}">E<tspan font-size="9" dy="3">p</tspan> = energia di promozione s→p (≈ 4,6 eV);  E<tspan font-size="9" dy="3">L</tspan> = energia di legame C–H</text>
</svg>'''

def svg_sei_casi():
    def orb(x, y, r=30, fill='#cdd9ec', stroke=BLUE, sign=None, rx=None, ry=None):
        s = ''
        if rx is None:
            s += f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" fill-opacity="0.55" stroke="{stroke}" stroke-width="1.4"/>'
        else:
            s += f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" fill-opacity="0.55" stroke="{stroke}" stroke-width="1.4"/>'
        if sign:
            s += f'<text x="{x}" y="{y+4}" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">{sign}</text>'
        return s
    def caption(cx, cy, txt, col=BLUE):
        return f'<text x="{cx}" y="{cy}" text-anchor="middle" {FS} fill="{col}" font-weight="600">{txt}</text>'
    P = '#e8c9c9'; PB = '#c9d8ea'
    one = (
      orb(70, 100, 34) + orb(126, 100, 34) +
      f'<text x="70" y="72" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">+</text>'
      f'<text x="126" y="72" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">+</text>'
      + caption(100, 175, 's–s') + caption(100, 195, 'legame σ'))
    two = (
      orb(60, 100, 36) +
      f'<text x="60" y="72" text-anchor="middle" font-size="13" font-weight="700" fill="{INK}">+</text>'
      + orb(140, 80, 22, sign='+') + orb(140, 120, 22, fill=PB, sign='−')
      + caption(105, 175, 's–pz') + caption(105, 195, 'legame σ'))
    three = (
      orb(58, 100, 36) +
      orb(140, 72, 24, sign='+') + orb(140, 128, 24, fill=PB, sign='−')
      + caption(105, 175, 's–px / s–py') + caption(105, 195, 'non legame', RED))
    four = (
      orb(45, 100, 24, fill=PB, sign='−') + orb(95, 100, 28, sign='+') +
      orb(145, 100, 28, sign='+') + orb(195, 100, 24, fill=PB, sign='−')
      + caption(120, 175, 'pz–pz') + caption(120, 195, 'legame σ'))
    five = (
      orb(48, 118, 26, fill=PB, sign='−') + orb(105, 82, 30, sign='+') +
      orb(158, 55, 22, sign='+') + orb(158, 130, 24, fill=PB, sign='−')
      + caption(105, 175, 'px–py (ortogonali)') + caption(105, 195, 'non legame', RED))
    six = (
      orb(80, 70, 26, sign='+') + orb(136, 70, 26, sign='+') +
      orb(80, 128, 26, fill=PB, sign='−') + orb(136, 128, 26, fill=PB, sign='−')
      + caption(108, 175, 'px–px / py–py') + caption(108, 195, 'legame π', GREEN))
    panels = [(one, '1'), (two, '2'), (three, '3'), (four, '4'), (five, '5'), (six, '6')]
    out = ''
    for i, (p, num) in enumerate(panels):
        col = i % 3; row = i // 3
        x = 10 + col * 250; y = 10 + row * 230
        out += f'<g transform="translate({x},{y})"><rect width="236" height="216" rx="12" fill="#fff" stroke="{GRID}"/>' \
               f'<text x="12" y="22" {FS} fill="{INK}" font-weight="700">{num}</text>' + p + '</g>'
    return f'<svg viewBox="0 0 760 470" role="img" aria-label="I sei casi di sovrapposizione tra orbitali atomici">{out}</svg>'

def svg_isoterme():
    R = 0.082057
    def curve(T, color):
        pts = []
        for i in range(3, 421):
            P = i / 10
            V = R * T / P
            if V > 10.8: continue
            pts.append(f'{70 + (P / 42) * 560:.1f},{330 - (V / 11) * 290:.1f}')
        return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.6"/>'
    legend = ''
    for j, (c, lab) in enumerate([(BLUE, 'T = 273,15 K (0 °C)'),
                                  (GREEN, 'T = 423,15 K (150 °C)'),
                                  (RED, 'T = 573,15 K (300 °C)')]):
        y = 74 + j * 25
        legend += (f'<line x1="472" y1="{y-4}" x2="502" y2="{y-4}" stroke="{c}" stroke-width="3.5"/>'
                   f'<text x="510" y="{y}" {FS} fill="{c}" font-weight="600">{lab}</text>')
    return f'''<svg viewBox="0 0 680 380" role="img" aria-label="Isoterme di un gas ideale (legge di Boyle)">
  {arrow_defs()}
  <line x1="70" y1="330" x2="650" y2="330" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <line x1="70" y1="330" x2="70" y2="24" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="380" y="358" text-anchor="middle" {FS} fill="{INK}" font-weight="600">P (atm)</text>
  <text x="30" y="20" {FS} fill="{INK}" font-weight="600">V (dm³)</text>
  {curve(273.15, BLUE)}
  {curve(423.15, GREEN)}
  {curve(573.15, RED)}
  <g>{legend}</g>
  <text x="380" y="24" text-anchor="middle" {FS} fill="{INK}" font-weight="700">Isoterme (T costante) — una mole di gas ideale</text>
  <text x="380" y="41" text-anchor="middle" {FS} fill="{INK}">P × V = costante: a T maggiore la curva si sposta verso l’alto (più urti a parità di volume)</text>
</svg>'''

def svg_maxwell():
    def curve(m, s, h, color, label, ly):
        pts = []
        x = 0.05
        while x <= 9.6:
            y = h * math.exp(-((x - m) ** 2) / s)
            px = 66 + x / 10 * 580
            py = 320 - y / 1.15 * 280
            pts.append(f'{px:.1f},{py:.1f}')
            x += 0.08
        return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.4"/>'
                f'<text x="{66 + (m - 0.9*s**0.5) / 10 * 580:.0f}" y="{ly}" {FS} fill="{color}" font-weight="600">{label}</text>')
    return f'''<svg viewBox="0 0 680 380" role="img" aria-label="Distribuzione di Maxwell–Boltzmann a tre temperature">
  {arrow_defs()}
  <line x1="66" y1="320" x2="660" y2="320" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <line x1="66" y1="320" x2="66" y2="24" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="360" y="350" text-anchor="middle" {FS} fill="{INK}" font-weight="600">Energia cinetica →</text>
  <text x="24" y="20" {FS} fill="{INK}" font-weight="600">N. molecole</text>
  {curve(1.5, 1.4, 1.0, INK, 'T₁', 66)}
  {curve(3.0, 2.4, 0.75, BLUE, 'T₂', 116)}
  {curve(4.5, 3.6, 0.60, RED, 'T₃', 150)}
  <line x1="{66 + 3.0/10*580:.0f}" y1="320" x2="{66 + 3.0/10*580:.0f}" y2="{320 - 0.78/1.15*280:.0f}" stroke="{INK}" stroke-dasharray="5 4"/>
  <text x="{66 + 3.05/10*580:.0f}" y="336" {FS} fill="{INK}">E media</text>
  <text x="360" y="24" text-anchor="middle" {FS} fill="{INK}" font-weight="700">Distribuzione di Maxwell (T₁ &lt; T₂ &lt; T₃)</text>
  <text x="360" y="41" text-anchor="middle" {FS} fill="{INK}">Eₓ = (3/2)kT: crescendo T il picco si abbassa e slitta verso energie più alte</text>
</svg>'''

def svg_stati():
    import random
    random.seed(7)
    def lattice(x0):
        s = ''
        for r_ in range(4):
            for c in range(6):
                s += f'<circle cx="{x0+28+c*33}" cy="{70+r_*30}" r="8" fill="#9db4d6"/>'
        return s
    def liquid(x0):
        pts = [(28,190),(60,172),(92,196),(124,176),(156,196),(188,170),(44,214),(78,224),(110,208),(142,226),(174,210),(28,238),(104,240),(160,238),(196,232),(58,250),(132,252)]
        return ''.join(f'<circle cx="{x0+x}" cy="{y}" r="8" fill="#9db4d6"/>' for x, y in pts) + f'<circle cx="{x0+120}" cy="70" r="8" fill="#9db4d6"/>'
    def gas(x0):
        pts = [(30,80),(150,120),(90,160),(200,60),(180,210),(60,230),(120,40),(40,180),(200,150),(110,250)]
        return ''.join(f'<circle cx="{x0+x}" cy="{y}" r="8" fill="#9db4d6"/>' for x, y in pts)
    def box(x0, label):
        return (f'<rect x="{x0}" y="46" width="225" height="230" rx="10" fill="#f6f2ea" stroke="{GRID}"/>'
                f'<text x="{x0+112}" y="300" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="14" fill="{INK}" font-weight="700">{label}</text>')
    def dbl(x1, x2, y, label, dy=0):
        return (f'<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{INK}" stroke-width="1.6" marker-start="url(#ah)" marker-end="url(#ah)"/>'
                f'<text x="{(x1+x2)/2}" y="{y+dy}" text-anchor="middle" {FS} fill="{INK}">{label}</text>')
    return f'''<svg viewBox="0 0 780 400" role="img" aria-label="Gli stati della materia e i passaggi di stato">
  {arrow_defs()}
  {box(20,'solido')}{lattice(20)}
  {box(285,'liquido')}{liquid(285)}
  {box(550,'gas')}{gas(550)}
  {dbl(252,278,96,'fusione →',-8)}
  {dbl(252,278,150,'← solidificazione',16)}
  {dbl(517,543,96,'evaporazione →',-8)}
  {dbl(517,543,150,'← condensazione',16)}
  <line x1="132" y1="330" x2="660" y2="330" stroke="{VIOLET}" stroke-width="1.5" stroke-dasharray="7 5" marker-start="url(#ah)" marker-end="url(#ah)"/>
  <text x="396" y="352" text-anchor="middle" {FS} fill="{VIOLET}">sublimazione (solido ⇌ gas)</text>
  <text x="396" y="384" text-anchor="middle" {FS} fill="{INK}">Competizione tra energia cinetica (spinge verso destra) e forze intermolecolari (verso sinistra)</text>
</svg>'''

def svg_vapore():
    def curve(k, T0, color, name, loff=18, anchor='start'):
        pts = []
        for i in range(0, 1001):
            t = i / 10
            P = 760 * math.exp(k * (t - T0))
            if P > 840: break
            x = 64 + t / 104 * 580
            y = 330 - P / 860 * 300
            pts.append(f'{x:.1f},{y:.1f}')
        lx = 64 + (T0 + loff) / 104 * 580
        if lx > 610:
            lx, anchor = 64 + (T0 + loff - 26) / 104 * 580, 'end'
        return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.4"/>'
                f'<text x="{lx:.0f}" y="{330 - (760*math.exp(k*18)/860)*300 + 24:.0f}" text-anchor="{anchor}" {FS} fill="{color}" font-weight="600">{name}</text>')
    def dot(t, color):
        x = 64 + t / 104 * 580
        y = 330 - 760 / 860 * 300
        return f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="{color}"/>'
    def dlabel(t, txt, anchor):
        x = 64 + t / 104 * 580
        y = 330 - 760 / 860 * 300
        return f'<text x="{x:.0f}" y="{y - 10:.0f}" text-anchor="{anchor}" {FS} fill="{INK}" font-weight="600">{txt}</text>'
    return f'''<svg viewBox="0 0 680 380" role="img" aria-label="Tensione di vapore di tre liquidi in funzione della temperatura">
  {arrow_defs()}
  <line x1="64" y1="330" x2="655" y2="330" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <line x1="64" y1="330" x2="64" y2="24" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>
  <text x="360" y="358" text-anchor="middle" {FS} fill="{INK}" font-weight="600">temperatura (°C)</text>
  <text x="22" y="20" {FS} fill="{INK}" font-weight="600">P (Torr)</text>
  {curve(0.0391, 34.6, AMBER, 'etere dietilico')}
  {curve(0.0382, 78.3, GREEN, 'etanolo')}
  {curve(0.0397, 100, BLUE, 'acqua')}
  <line x1="64" y1="{330 - 760/860*300:.0f}" x2="648" y2="{330 - 760/860*300:.0f}" stroke="{INK}" stroke-dasharray="6 5"/>
  <text x="200" y="{330 - 760/860*300 - 8:.0f}" {FS} fill="{INK}">760 Torr = 1 atm (ebollizione)</text>
  <line x1="64" y1="{330 - 600/860*300:.0f}" x2="648" y2="{330 - 600/860*300:.0f}" stroke="{AMBER}" stroke-dasharray="6 5"/>
  <text x="196" y="{330 - 600/860*300 - 8:.0f}" {FS} fill="{AMBER}">600 mmHg: pressione ridotta (montagna)</text>
  {dot(34.6, AMBER)}{dlabel(34.6, '35 °C', 'start')}
  {dot(78.3, GREEN)}{dlabel(78.3, '78 °C', 'start')}
  {dot(100, BLUE)}{dlabel(100, '100 °C', 'end')}
  <circle cx="{64 + 94/104*580:.0f}" cy="{330 - 600/860*300:.0f}" r="5" fill="{BLUE}"/>
  <text x="{64 + 94/104*580 - 8:.0f}" y="{330 - 600/860*300 + 18:.0f}" text-anchor="end" {FS} fill="{BLUE}" font-weight="600">≈ 93 °C</text>
</svg>'''

def svg_radiazioni():
    return f'''<svg viewBox="0 0 680 380" role="img" aria-label="Separazione delle radiazioni alfa, beta e gamma in un campo magnetico">
  <text x="340" y="26" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="13" fill="#3a3833" font-weight="700">Separazione delle radiazioni α, β, γ in un campo magnetico</text>
  <text x="340" y="44" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="13" fill="#6b675e">solo le particelle cariche vengono deviate: il β, leggerissimo, devia molto più dell'α pesante</text>
  <rect x="300" y="64" width="160" height="84" rx="8" fill="#b9c3d2" stroke="#55565c" stroke-width="1.4"/>
  <text x="380" y="114" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="24" font-weight="700" fill="#3a3833">N</text>
  <text x="380" y="138" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#6b675e">polo positivo</text>
  <rect x="300" y="272" width="160" height="84" rx="8" fill="#98a3b3" stroke="#55565c" stroke-width="1.4"/>
  <text x="380" y="322" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="24" font-weight="700" fill="#3a3833">S</text>
  <text x="380" y="346" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#6b675e">polo negativo</text>
  <g fill="#6b5b95" font-family="Inter,system-ui,sans-serif" font-size="13">
    <text x="318" y="176">⊙</text><text x="318" y="252">⊙</text>
    <text x="444" y="176">⊙</text><text x="444" y="252">⊙</text>
  </g>
  <text x="338" y="266" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#6b675e">campo magnetico (B ⊙)</text>
  <rect x="36" y="140" width="94" height="150" rx="6" fill="#7d7f86" stroke="#55565c" stroke-width="1.4"/>
  <rect x="84" y="197" width="46" height="26" fill="#faf7f1"/>
  <line x1="84" y1="197" x2="130" y2="197" stroke="#55565c" stroke-width="1"/>
  <line x1="84" y1="223" x2="130" y2="223" stroke="#55565c" stroke-width="1"/>
  <text x="83" y="312" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" fill="#6b675e">blocco di piombo</text>
  <circle cx="100" cy="210" r="5.5" fill="#a86f2d" stroke="#3a3833" stroke-width="1.2"/>
  <text x="107" y="221" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="9.5" fill="#3a3833">sorgente</text>
  <line x1="106" y1="210" x2="300" y2="210" stroke="#3a3833" stroke-width="2.5" opacity="0.7"/>
  <text x="200" y="198" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" font-style="italic" fill="#6b675e">fascio di radiazioni</text>
  <path d="M300,210 Q400,138 610,138" fill="none" stroke="#3b5b92" stroke-width="2.6"/>
  <path d="M300,210 L610,210" fill="none" stroke="#4a7c59" stroke-width="2.2"/>
  <path d="M300,210 Q400,246 610,246" fill="none" stroke="#a04343" stroke-width="2.6"/>
  <text x="540" y="114" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="600" fill="#3b5b92">β — elettroni (q=−1)</text>
  <text x="540" y="128" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#3b5b92">leggero → devia molto</text>
  <text x="520" y="189" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="600" fill="#4a7c59">γ — fotoni (q = 0)</text>
  <text x="520" y="204" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#4a7c59">non deviato</text>
  <text x="525" y="264" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" font-weight="600" fill="#a04343">α — nuclei di elio (q = +2)</text>
  <text x="530" y="280" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="11" fill="#a04343">pesante: devia poco</text>
  <rect x="610" y="90" width="12" height="240" rx="4" fill="#efe9db" stroke="#3a3833" stroke-width="1.2"/>
  <circle cx="616" cy="138" r="4.5" fill="#3b5b92" stroke="#fff" stroke-width="1"/>
  <circle cx="616" cy="210" r="4.5" fill="#4a7c59" stroke="#fff" stroke-width="1"/>
  <circle cx="616" cy="246" r="4.5" fill="#a04343" stroke="#fff" stroke-width="1"/>
  <text x="616" y="350" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="12" fill="#6b675e">lastra fotografica</text>
</svg>'''

# ---------------------------------------------------------------- SVG figure (lezione 9)
def svg_due_stati():
    # Figura 72.1 — schema a due stati dell'esercizio del gas riscaldato
    def box(x0, title):
        return (f'<rect x="{x0}" y="50" width="270" height="190" rx="10" fill="#f6f2ea" stroke="{GRID}" stroke-width="1.6"/>'
                f'<text x="{x0+135}" y="42" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="14" font-weight="700" fill="{INK}">{title}</text>')
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    return f'''<svg viewBox="0 0 720 300" role="img" aria-label="Schema a due stati dell'esercizio del gas riscaldato">
  {arrow_defs()}
  {box(20,'Stato iniziale')}
  <g {F} fill="{INK}">
    <text x="50" y="85">V₁ = 15 L</text>
    <text x="50" y="115">P₁ = 1,5 atm</text>
    <text x="50" y="145">T₁ = 25 °C = 298,15 K</text>
    <text x="50" y="185">n = P₁V₁/(RT₁) ≅ 0,92 mol</text>
  </g>
  <line x1="302" y1="145" x2="418" y2="145" stroke="{INK}" stroke-width="3" marker-end="url(#ah)"/>
  <text x="360" y="128" text-anchor="middle" {F} fill="{INK}" font-weight="600">riscaldamento</text>
  <text x="360" y="172" text-anchor="middle" {F} fill="{INK}">T₂ = 60 °C</text>
  <text x="360" y="192" text-anchor="middle" {F} fill="{INK}">V₂ = 15,5 L</text>
  {box(430,'Stato finale')}
  <g {F} fill="{INK}">
    <text x="460" y="85">V₂ = 15,5 L</text>
    <text x="460" y="115">T₂ = 60 °C = 333,15 K</text>
    <text x="460" y="145">n = 0,92 mol (invariato)</text>
    <text x="460" y="185" fill="{BLUE}" font-weight="700">P₂ = nRT₂/V₂ ≅ 1,62 atm</text>
  </g>
  <text x="360" y="278" text-anchor="middle" {F} fill="{INK}">n è costante: si calcola dallo stato iniziale e si reinserisce, con i valori finali, nell’equazione di stato</text>
</svg>'''

def svg_miscela_dalton():
    # Figura 51.1 — miscela di gas in un unico recipiente (legge di Dalton)
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    green = [(100,85),(185,150),(140,215),(245,95),(95,180),(215,205)]
    blue  = [(335,110),(425,75),(385,190),(465,150),(315,222),(445,230)]
    amber = [(525,90),(565,185),(505,205),(545,145)]
    gs = ''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{GREEN}"/>' for x, y in green)
    bs = ''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{BLUE}"/>' for x, y in blue)
    as_ = ''.join(f'<circle cx="{x}" cy="{y}" r="9" fill="{AMBER}"/>' for x, y in amber)
    return f'''<svg viewBox="0 0 680 315" role="img" aria-label="Miscela di gas in un unico recipiente: legge di Dalton">
  {arrow_defs()}
  <text x="340" y="26" text-anchor="middle" {F} fill="{INK}">P<tspan baseline-shift="sub" font-size="9">TOT</tspan> = P<tspan baseline-shift="sub" font-size="9">A</tspan> + P<tspan baseline-shift="sub" font-size="9">B</tspan> + P<tspan baseline-shift="sub" font-size="9">C</tspan> = (n<tspan baseline-shift="sub" font-size="9">A</tspan> + n<tspan baseline-shift="sub" font-size="9">B</tspan> + n<tspan baseline-shift="sub" font-size="9">C</tspan>)·RT/V = n<tspan baseline-shift="sub" font-size="9">TOT</tspan>·RT/V</text>
  <rect x="60" y="50" width="560" height="200" fill="#faf7f1" stroke="{INK}" stroke-width="3"/>
  {gs}{bs}{as_}
  <line x1="165" y1="282" x2="165" y2="256" stroke="{GREEN}" stroke-width="2" marker-end="url(#ahg)"/>
  <text x="165" y="300" text-anchor="middle" {Fsm} fill="{GREEN}" font-weight="600">gas A</text>
  <line x1="395" y1="282" x2="395" y2="256" stroke="{BLUE}" stroke-width="2"/>
  <path d="M395,256 l-4,7 h8 z" fill="{BLUE}"/>
  <text x="395" y="300" text-anchor="middle" {Fsm} fill="{BLUE}" font-weight="600">gas B</text>
  <line x1="535" y1="282" x2="535" y2="256" stroke="{AMBER}" stroke-width="2"/>
  <path d="M535,256 l-4,7 h8 z" fill="{AMBER}"/>
  <text x="535" y="300" text-anchor="middle" {Fsm} fill="{AMBER}" font-weight="600">gas C</text>
  <text x="340" y="245" text-anchor="middle" {Fsm} fill="{INK}">T e V sono gli stessi per tutte le specie: ciascuna occupa l’intero volume</text>
</svg>'''

def svg_graham_miscela():
    # Figura 50.1 — miscela di due gas a parità di temperatura
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    # (x, y, dx della freccia, pendenza dy/dx): gas A leggero -> frecce lunghe
    light = [(105, 95, 78, 0.55), (175, 168, 72, -0.5), (140, 208, 66, 0.45), (232, 122, 76, 0.5)]
    heavy = [(420, 105, 24, 0.25), (505, 172, 22, -0.3), (440, 210, 21, 0.3), (528, 118, 24, 0.25)]
    gs = ''
    for x, y, dx, k in light:
        x2, y2 = x + 9 + dx, y + k * dx
        gs += (f'<circle cx="{x}" cy="{y}" r="7" fill="{GREEN}"/>'
               f'<line x1="{x+9}" y1="{y}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{GREEN}" stroke-width="2.4" marker-end="url(#ahg)"/>')
    bs = ''
    for x, y, dx, k in heavy:
        x2, y2 = x + 15 + dx, y + k * dx
        ang = math.degrees(math.atan2(k * dx, dx))
        bs += (f'<circle cx="{x}" cy="{y}" r="12" fill="{BLUE}"/>'
               f'<line x1="{x+15}" y1="{y}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{BLUE}" stroke-width="2.2"/>'
               f'<path d="M0,0 l-8,-3.5 v7 z" fill="{BLUE}" transform="translate({x2:.0f} {y2:.0f}) rotate({ang:.0f})"/>')
    return f'''<svg viewBox="0 0 680 310" role="img" aria-label="Miscela di due gas a parità di temperatura">
  {arrow_defs()}
  <text x="340" y="26" text-anchor="middle" {F} fill="{INK}">stessa temperatura: T<tspan baseline-shift="sub" font-size="9">A</tspan> = T<tspan baseline-shift="sub" font-size="9">B</tspan> ⇒ E<tspan baseline-shift="sub" font-size="9">c</tspan>(A) = E<tspan baseline-shift="sub" font-size="9">c</tspan>(B) = (3/2)·k<tspan baseline-shift="sub" font-size="9">B</tspan>T</text>
  <rect x="60" y="50" width="560" height="190" fill="#faf7f1" stroke="{INK}" stroke-width="3"/>
  {gs}{bs}
  <text x="195" y="286" text-anchor="middle" {Fsm} fill="{GREEN}" font-weight="600">gas A: m<tspan baseline-shift="sub" font-size="8">A</tspan> piccola, v<tspan baseline-shift="sub" font-size="8">A</tspan> grande</text>
  <text x="490" y="286" text-anchor="middle" {Fsm} fill="{BLUE}" font-weight="600">gas B: m<tspan baseline-shift="sub" font-size="8">B</tspan> grande, v<tspan baseline-shift="sub" font-size="8">B</tspan> piccola</text>
</svg>'''

def svg_effusione():
    # Figura 50.2 — separazione di una miscela gassosa mediante effusione
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    green_in = [(85,90),(155,172),(112,200),(205,82),(172,132),(92,158),(232,182),(140,102)]
    blue_in  = [(122,122),(222,152),(255,92),(168,76)]
    gs = ''.join(f'<circle cx="{x}" cy="{y}" r="6" fill="{GREEN}"/>' for x, y in green_in)
    bs = ''.join(f'<circle cx="{x}" cy="{y}" r="11" fill="{BLUE}"/>' for x, y in blue_in)
    return f'''<svg viewBox="0 0 760 300" role="img" aria-label="Separazione di una miscela gassosa mediante effusione">
  {arrow_defs()}
  <text x="170" y="45" text-anchor="middle" {F} fill="{INK}" font-weight="600">contenitore</text>
  <path d="M40,60 H300 M40,220 H300 M40,60 V220 M300,60 V110 M300,150 V220" fill="none" stroke="{INK}" stroke-width="3.5"/>
  {gs}{bs}
  <line x1="300" y1="110" x2="640" y2="110" stroke="{INK}" stroke-width="3"/>
  <line x1="300" y1="150" x2="640" y2="150" stroke="{INK}" stroke-width="3"/>
  <circle cx="332" cy="130" r="9" fill="{BLUE}"/>
  <line x1="343" y1="130" x2="357" y2="130" stroke="{BLUE}" stroke-width="2"/>
  <path d="M360,130 l-6,-3 v6 z" fill="{BLUE}"/>
  <circle cx="368" cy="130" r="9" fill="{BLUE}"/>
  <circle cx="415" cy="130" r="6" fill="{GREEN}"/>
  <circle cx="465" cy="130" r="6" fill="{GREEN}"/>
  <circle cx="515" cy="130" r="6" fill="{GREEN}"/>
  <circle cx="565" cy="130" r="6" fill="{GREEN}"/>
  <circle cx="603" cy="130" r="6" fill="{GREEN}"/>
  <line x1="611" y1="130" x2="633" y2="130" stroke="{GREEN}" stroke-width="2.4" marker-end="url(#ahg)"/>
  <text x="300" y="98" text-anchor="middle" {Fsm} fill="{INK}">foro</text>
  <line x1="300" y1="102" x2="300" y2="112" stroke="{INK}" stroke-width="1.4"/>
  <text x="480" y="92" text-anchor="middle" {Fsm} fill="{GREEN}" font-weight="600">gas leggero: arriva per primo</text>
  <text x="385" y="180" text-anchor="middle" {Fsm} fill="{BLUE}" font-weight="600">gas pesante: più lento</text>
  <line x1="648" y1="130" x2="692" y2="130" stroke="{INK}" stroke-width="3" marker-end="url(#ah)"/>
  <text x="700" y="134" {Fsm} fill="{INK}" font-weight="600">raccolta</text>
  <text x="380" y="262" text-anchor="middle" {Fsm} fill="{INK}">(tubo più lungo ⇒ separazione più efficiente)</text>
</svg>'''

def svg_henry():
    # Figura 68.1 — gas a contatto con un liquido (legge di Henry)
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    dissolved = [(120,190),(180,215),(240,196),(300,220),(360,200),(410,182),(150,238),(330,240),(210,225)]
    gasdots = [(95,75),(175,112),(275,72),(310,128),(395,98),(215,142)]
    ds = ''.join(f'<circle cx="{x}" cy="{y}" r="5" fill="{AMBER}"/>' for x, y in dissolved)
    gd = ''.join(f'<circle cx="{x}" cy="{y}" r="8" fill="{AMBER}"/>' for x, y in gasdots)
    arrows = ''
    for x in (130, 235, 340):
        arrows += f'<line x1="{x}" y1="58" x2="{x}" y2="146" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>'
    return f'''<svg viewBox="0 0 560 340" role="img" aria-label="Gas a contatto con un liquido: legge di Henry">
  {arrow_defs()}
  <rect x="50" y="40" width="420" height="230" fill="#fff" stroke="{INK}" stroke-width="3"/>
  <rect x="53" y="155" width="414" height="112" fill="#d8e8f4"/>
  <line x1="53" y1="155" x2="467" y2="155" stroke="{BLUE}" stroke-width="2"/>
  <text x="462" y="150" text-anchor="end" {Fsm} fill="{BLUE}" font-weight="600">superficie del liquido</text>
  <text x="92" y="205" {F} fill="{BLUE}" font-weight="600">liquido</text>
  {ds}
  <text x="268" y="258" text-anchor="middle" {Fsm} fill="{BLUE}">gas disciolto: frazione molare x</text>
  {gd}{arrows}
  <text x="260" y="28" text-anchor="middle" {F} fill="{INK}">gas: pressione parziale p<tspan baseline-shift="sub" font-size="9">gas</tspan></text>
  <text x="260" y="312" text-anchor="middle" {F} fill="{INK}">p<tspan baseline-shift="sub" font-size="9">gas</tspan> = k<tspan baseline-shift="sub" font-size="9">H</tspan> · x &#160;&#160;—&#160;&#160; solubilità ∝ p<tspan baseline-shift="sub" font-size="9">gas</tspan></text>
</svg>'''

def svg_combinazione():
    # Figura 69.1 — la combinazione minima alla scala delle particelle
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    def ball(cx, col, label):
        return (f'<circle cx="{cx}" cy="80" r="27" fill="{col}"/>'
                f'<text x="{cx}" y="86" text-anchor="middle" font-family="Inter,system-ui,sans-serif" font-size="16" font-weight="700" fill="#fff">{label}</text>')
    return f'''<svg viewBox="0 0 680 200" role="img" aria-label="La combinazione minima alla scala delle particelle">
  {arrow_defs()}
  {ball(90, GREEN, 'A')}{ball(150, GREEN, 'A')}
  <text x="200" y="86" text-anchor="middle" {F} fill="{INK}">+</text>
  {ball(250, BLUE, 'B')}
  <line x1="300" y1="80" x2="400" y2="80" stroke="{INK}" stroke-width="3" marker-end="url(#ah)"/>
  <text x="350" y="62" text-anchor="middle" {Fsm} fill="{INK}">reazione</text>
  {ball(450, AMBER, 'C')}{ball(510, AMBER, 'C')}
  <text x="340" y="152" text-anchor="middle" {F} fill="{INK}" font-weight="600">combinazione minima: 2A + 1B → 2C</text>
  <text x="340" y="176" text-anchor="middle" {Fsm} fill="{INK}">(nell’Esercizio 5 del §81: 2 SO₂ + O₂ → 2 SO₃)</text>
</svg>'''

def svg_formula_flow():
    # Figura 69.2 — dalla composizione percentuale alla formula molecolare
    F = 'font-family="Inter,system-ui,sans-serif" font-size="13"'
    Fsm = 'font-family="Inter,system-ui,sans-serif" font-size="11"'
    steps = [
        ('composizione percentuale in massa', '(es.: 24,27% C; 4,07% H; 71,66% Cl)', False),
        ('moli per 100 g di composto: n_i = m_i / P.A._i', None, False),
        ('rapporti minimi tra le moli ⇒ formula minima', None, False),
        ('peso molecolare della formula minima: PM_min', None, False),
        ('n = PM_mol / PM_min (numero intero)', None, False),
        ('formula molecolare = n × (formula minima)', None, True),
    ]
    out = []
    y = 26
    ys = []
    for i, (t1, t2, final) in enumerate(steps):
        fill = '#e8f0e8' if final else '#f6f2ea'
        stroke = GREEN if final else GRID
        out.append(f'<rect x="110" y="{y}" width="380" height="46" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        cy = y + 23 if t2 is None else y + 19
        t1 = (t1.replace('n_i', 'n<tspan baseline-shift="sub" font-size="9">i</tspan>')
                .replace('m_i', 'm<tspan baseline-shift="sub" font-size="9">i</tspan>')
                .replace('P.A._i', 'P.A.<tspan baseline-shift="sub" font-size="9">i</tspan>')
                .replace('PM_min', 'PM<tspan baseline-shift="sub" font-size="9">min</tspan>')
                .replace('PM_mol', 'PM<tspan baseline-shift="sub" font-size="9">mol</tspan>'))
        out.append(f'<text x="300" y="{cy}" text-anchor="middle" {F} fill="{INK}">{t1}</text>')
        if t2:
            out.append(f'<text x="300" y="{y+37}" text-anchor="middle" {Fsm} fill="{INK}">{t2}</text>')
        if i < len(steps) - 1:
            out.append(f'<line x1="300" y1="{y+46}" x2="300" y2="{y+68}" stroke="{INK}" stroke-width="2.4" marker-end="url(#ah)"/>')
        ys.append(y)
        y += 70
    height = y - 70 + 46 + 26
    dashed = (f'<rect x="520" y="{ys[4]}" width="180" height="46" rx="10" fill="#fff" stroke="{INK}" stroke-width="1.6" stroke-dasharray="6 4"/>'
              f'<text x="610" y="{ys[4]+19}" text-anchor="middle" {Fsm} fill="{INK}">dato sperimentale:</text>'
              f'<text x="610" y="{ys[4]+36}" text-anchor="middle" {F} fill="{INK}" font-weight="600">PM<tspan baseline-shift="sub" font-size="9">mol</tspan></text>'
              f'<line x1="520" y1="{ys[4]+23}" x2="492" y2="{ys[4]+23}" stroke="{INK}" stroke-width="1.8" stroke-dasharray="5 4" marker-end="url(#ah)"/>')
    return (f'<svg viewBox="0 0 720 {height}" role="img" aria-label="Dalla composizione percentuale alla formula molecolare">'
            + arrow_defs() + ''.join(out) + dashed + '</svg>')

# ---------------------------------------------------------------- figure lezioni 10–12
FONT = 'font-family="Inter,system-ui,sans-serif"'
F13 = f'{FONT} font-size="13"'
F12 = f'{FONT} font-size="12"'
F11 = f'{FONT} font-size="11"'
F10 = f'{FONT} font-size="10"'

def _atom(x, y, label, r=16, fs=14, col=INK):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{col}" stroke-width="1.7"/>'
            f'<text x="{x}" y="{y+5}" text-anchor="middle" {FONT} font-size="{fs}" fill="{col}" font-weight="700">{label}</text>')

def _bond(x1, y1, x2, y2, kind=1, col=INK, w=2.0):
    import math as _m
    dx, dy = x2 - x1, y2 - y1
    L = _m.hypot(dx, dy)
    ox, oy = -dy / L * 3.4, dx / L * 3.4
    s = ''
    if kind == 1:
        s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"/>'
    elif kind == 2:
        s = (f'<line x1="{x1+ox}" y1="{y1+oy}" x2="{x2+ox}" y2="{y2+oy}" stroke="{col}" stroke-width="{w}"/>'
             f'<line x1="{x1-ox}" y1="{y1-oy}" x2="{x2-ox}" y2="{y2-oy}" stroke="{col}" stroke-width="{w}"/>')
    else:
        s = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="{w}"/>'
        s += (f'<line x1="{x1+ox}" y1="{y1+oy}" x2="{x2+ox}" y2="{y2+oy}" stroke="{col}" stroke-width="{w}"/>'
              f'<line x1="{x1-ox}" y1="{y1-oy}" x2="{x2-ox}" y2="{y2-oy}" stroke="{col}" stroke-width="{w}"/>')
    return s

def _dots(cx, cy, pairs, off=22):
    """pairs: lista di (angolo°, n_dots) — ogni voce piazza n_dots punti attorno a quell'angolo."""
    import math as _m
    s = ''
    for ang, cnt in pairs:
        for k in range(cnt):
            a = _m.radians(ang + (k - (cnt - 1) / 2) * 9)
            x, y = cx + off * _m.cos(a), cy - off * _m.sin(a)
            s += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.0" fill="{INK}"/>'
    return s

def _odots(cx, cy, base, npairs, off=22, spread=34):
    """npairs coppie di non legame a ventaglio attorno a base (direzione libera, lontana dai legami)."""
    if npairs == 1:
        angs = [base]
    elif npairs == 2:
        angs = [base - spread, base + spread]
    else:
        angs = [base, base - spread, base + spread]
    return _dots(cx, cy, [(a, 2) for a in angs], off)

def svg_dipoli():
    # Figura 53.1 — HF, CO2, H2O: risultante vettoriale dei dipoli
    s = []
    # (a) HF
    s.append(_bond(78, 170, 160, 170))
    s.append(_atom(78, 170, 'H', 17)); s.append(_atom(160, 170, 'F', 19))
    s.append(f'<text x="78" y="140" text-anchor="middle" {F11} fill="{RED}" font-weight="700">δ⁺</text>')
    s.append(f'<text x="160" y="138" text-anchor="middle" {F11} fill="{BLUE}" font-weight="700">δ⁻</text>')
    s.append(f'<line x1="96" y1="132" x2="140" y2="132" stroke="{RED}" stroke-width="2.6" marker-end="url(#ahr)"/>')
    s.append(f'<text x="118" y="122" text-anchor="middle" {F12} fill="{RED}" font-weight="700">μ</text>')
    s.append(f'<text x="119" y="212" text-anchor="middle" {F11} fill="{INK}">χ<tspan baseline-shift="sub" font-size="8">H</tspan>=2,1&#160;&#160;χ<tspan baseline-shift="sub" font-size="8">F</tspan>=4,0</text>')
    s.append(f'<text x="119" y="230" text-anchor="middle" {F12} fill="{INK}" font-weight="600">HF: dipolo permanente</text>')
    # (b) CO2
    s.append(_bond(318, 170, 392, 170, 2)); s.append(_bond(392, 170, 466, 170, 2))
    s.append(_atom(318, 170, 'O', 17)); s.append(_atom(392, 170, 'C', 16)); s.append(_atom(466, 170, 'O', 17))
    for x in (318, 466):
        s.append(f'<text x="{x}" y="138" text-anchor="middle" {F11} fill="{BLUE}" font-weight="700">δ⁻</text>')
    s.append(f'<text x="392" y="202" text-anchor="middle" {F11} fill="{RED}" font-weight="700">δ⁺</text>')
    s.append(f'<line x1="336" y1="132" x2="304" y2="132" stroke="{RED}" stroke-width="2.4" marker-end="url(#ahr)"/>')
    s.append(f'<text x="322" y="122" text-anchor="middle" {F11} fill="{RED}" font-weight="700">μ₁</text>')
    s.append(f'<line x1="448" y1="132" x2="480" y2="132" stroke="{RED}" stroke-width="2.4" marker-end="url(#ahr)"/>')
    s.append(f'<text x="462" y="122" text-anchor="middle" {F11} fill="{RED}" font-weight="700">μ₂</text>')
    s.append(f'<text x="392" y="220" text-anchor="middle" {F12} fill="{INK}">μ₁ + μ₂ = 0</text>')
    s.append(f'<text x="392" y="238" text-anchor="middle" {F12} fill="{INK}" font-weight="600">CO₂: lineare, apolare</text>')
    # (c) H2O
    s.append(_bond(636, 130, 596, 166)); s.append(_bond(636, 130, 676, 166))
    s.append(_atom(636, 130, 'O', 18)); s.append(_atom(596, 166, 'H', 16)); s.append(_atom(676, 166, 'H', 16))
    s.append(_dots(636, 130, [(150, 2), (30, 2)], 24))
    s.append(f'<line x1="600" y1="160" x2="628" y2="136" stroke="{RED}" stroke-width="2.2" marker-end="url(#ahr)"/>')
    s.append(f'<line x1="672" y1="160" x2="644" y2="136" stroke="{RED}" stroke-width="2.2" marker-end="url(#ahr)"/>')
    s.append(f'<text x="584" y="152" text-anchor="end" {F11} fill="{RED}" font-weight="700">μ₁</text>')
    s.append(f'<text x="688" y="152" {F11} fill="{RED}" font-weight="700">μ₂</text>')
    s.append(f'<line x1="636" y1="188" x2="636" y2="146" stroke="{GREEN}" stroke-width="3.4" marker-end="url(#ahg)"/>')
    s.append(f'<text x="648" y="180" {F12} fill="{GREEN}" font-weight="700">μ<tspan baseline-shift="sub" font-size="8">R</tspan></text>')
    s.append(f'<line x1="596" y1="216" x2="676" y2="216" stroke="{GRID}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    s.append(f'<text x="636" y="232" text-anchor="middle" {F10} fill="{GRID}">ipotesi lineare: μ<tspan baseline-shift="sub" font-size="8">R</tspan> = 0</text>')
    s.append(f'<text x="636" y="252" text-anchor="middle" {F12} fill="{INK}" font-weight="600">H₂O: piegata, polare</text>')
    s.append(f'<text x="636" y="268" text-anchor="middle" {F10} fill="{INK}">μ<tspan baseline-shift="sub" font-size="8">R</tspan> = 2μ·cos(θ/2) ≈ 1,2μ</text>')
    return (f'<svg viewBox="0 0 760 280" role="img" aria-label="Momenti dipolari e geometria molecolare: HF, CO2 e H2O">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_corto_raggio():
    import math as _m
    cx, cy = 210, 170
    s = []
    outer = [(52,64),(96,40),(150,56),(206,30),(262,52),(318,44),(352,84),(340,140),(322,196),(286,246),(226,262),(158,254),(96,268),(58,222),(36,160)]
    for x, y in outer:
        s.append(f'<circle cx="{x}" cy="{y}" r="8" fill="#8fa8cf"/>')
    ring = []
    for a in range(0, 360, 60):
        x, y = cx + 62 * _m.cos(_m.radians(a)), cy - 62 * _m.sin(_m.radians(a))
        ring.append((x, y))
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="#6d8fc4"/>')
    for i in range(6):
        x1, y1 = ring[i]; x2, y2 = ring[(i + 1) % 6]
        s.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{GRID}" stroke-width="1.4" stroke-dasharray="4 3"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="10" fill="{RED}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="92" fill="none" stroke="{RED}" stroke-width="1.8" stroke-dasharray="7 5"/>')
    s.append(f'<text x="18" y="30" {F12} fill="{RED}" font-weight="600">ordine a corto raggio</text>')
    s.append(f'<text x="18" y="46" {F12} fill="{RED}">(fino a poche decine di nm)</text>')
    s.append(f'<text x="386" y="120" {F12} fill="{INK}">disordine a lungo raggio</text>')
    s.append(f'<text x="386" y="136" {F12} fill="{INK}">(ordine macroscopico assente)</text>')
    return (f'<svg viewBox="0 0 560 300" role="img" aria-label="Ordine a corto raggio nello stato liquido">' + ''.join(s) + '</svg>')

def svg_grafite():
    s = []
    for row, y in enumerate((190, 120, 50)):
        pts = ''.join(f'<circle cx="{60+i*46}" cy="{y}" r="5" fill="#3d5a80"/>' for i in range(12))
        s.append(f'<line x1="60" y1="{y}" x2="566" y2="{y}" stroke="#3d5a80" stroke-width="2.6"/>' + pts)
    for x in (103, 195, 287, 379, 471, 540):
        for y1, y2 in ((56, 114), (126, 184)):
            s.append(f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{RED}" stroke-width="1.7" stroke-dasharray="5 4" marker-start="url(#ahr)" marker-end="url(#ahr)"/>')
    s.append(f'<text x="313" y="28" text-anchor="middle" {F12} fill="#3d5a80" font-weight="600">piani: legami covalenti C–C</text>')
    s.append(f'<text x="313" y="222" text-anchor="middle" {F12} fill="{RED}" font-weight="600">tra i piani: forze di van der Waals</text>')
    s.append(f'<line x1="60" y1="252" x2="240" y2="252" stroke="{GREEN}" stroke-width="3" marker-end="url(#ahg)"/>')
    s.append(f'<text x="252" y="248" {F11} fill="{GREEN}" font-weight="600">conduzione elettrica e</text>')
    s.append(f'<text x="252" y="262" {F11} fill="{GREEN}" font-weight="600">resistenza meccanica lungo i piani</text>')
    s.append(f'<line x1="604" y1="120" x2="604" y2="200" stroke="{AMBER}" stroke-width="3" marker-end="url(#ah)"/>')
    s.append(f'<text x="596" y="160" text-anchor="end" {F11} fill="{AMBER}" font-weight="600">conduzione</text>')
    s.append(f'<text x="596" y="174" text-anchor="end" {F11} fill="{AMBER}" font-weight="600">trascurabile ⊥ ai piani</text>')
    return (f'<svg viewBox="0 0 700 280" role="img" aria-label="Struttura a piani della grafite e anisotropia">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_bulk_superficie():
    s = []
    # sinistra: fase massiva
    s.append(f'<text x="130" y="36" text-anchor="middle" {F11} fill="{INK}">fase massiva (interno del liquido)</text>')
    for a in range(0, 360, 45):
        import math as _m
        x, y = 130 + 86 * _m.cos(_m.radians(a)), 170 - 86 * _m.sin(_m.radians(a))
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="9" fill="#8fa8cf"/>')
    for a in range(0, 360, 45):
        import math as _m
        x1, y1 = 130 + 16 * _m.cos(_m.radians(a)), 170 - 16 * _m.sin(_m.radians(a))
        x2, y2 = 130 + 72 * _m.cos(_m.radians(a)), 170 - 72 * _m.sin(_m.radians(a))
        s.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{AMBER}" stroke-width="2.2" marker-end="url(#ah)"/>')
    s.append(f'<circle cx="130" cy="170" r="11" fill="{RED}"/>')
    # destra: superficie
    for x, y in ((458, 76), (512, 96), (588, 66), (646, 88)):
        s.append(f'<circle cx="{x}" cy="{y}" r="5" fill="#d8a3a3"/>')
    s.append(f'<text x="560" y="52" text-anchor="middle" {F11} fill="{RED}">vapore (particelle rarefatte)</text>')
    s.append(f'<rect x="420" y="180" width="280" height="130" fill="#d8e8f4"/>')
    s.append(f'<line x1="420" y1="180" x2="700" y2="180" stroke="{BLUE}" stroke-width="3"/>')
    for x, y in ((456,210),(500,232),(548,214),(596,238),(646,212),(462,262),(530,282),(606,276),(668,258)):
        s.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#8fa8cf"/>')
    s.append(f'<circle cx="560" cy="180" r="11" fill="{RED}"/>')
    for x2, y2 in ((500, 212), (560, 210), (620, 212), (524, 248), (596, 246), (560, 276)):
        s.append(f'<line x1="560" y1="180" x2="{x2}" y2="{y2}" stroke="{AMBER}" stroke-width="2.0" marker-end="url(#ah)"/>')
    s.append(f'<line x1="560" y1="172" x2="560" y2="126" stroke="{INK}" stroke-width="1.6" stroke-dasharray="3 4"/>')
    s.append(f'<text x="572" y="130" {F10} fill="{INK}">verso il vuoto:</text>')
    s.append(f'<text x="572" y="142" {F10} fill="{INK}">nessuna interazione forte</text>')
    s.append(f'<text x="560" y="336" text-anchor="middle" {F11} fill="{INK}">molecola superficiale: interazioni sbilanciate</text>')
    s.append(f'<text x="560" y="352" text-anchor="middle" {F11} fill="{BLUE}">liquido</text>')
    return (f'<svg viewBox="0 0 720 360" role="img" aria-label="Molecola nella fase massiva e molecola in superficie">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_evap_distribuzione():
    def gauss(m, s, h, color, label, ly):
        pts = []
        x = 0.05
        while x <= 9.6:
            y = h * math.exp(-((x - m) ** 2) / s)
            px = 66 + x / 10 * 560
            py = 300 - y / 1.0 * 250
            pts.append(f'{px:.1f},{py:.1f}')
            x += 0.08
        return (f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.4"/>'
                f'<text x="{66 + m / 10 * 560 + 8:.0f}" y="{ly}" {F12} fill="{color}" font-weight="700">{label}</text>')
    def tail(m, s, h, color):
        pts = ['66,300']
        x = 5.5
        while x <= 9.6:
            y = h * math.exp(-((x - m) ** 2) / s)
            pts.append(f'{66 + x / 10 * 560:.1f},{300 - y * 250:.1f}')
            x += 0.06
        pts.append(f'{66 + 9.6 / 10 * 560:.1f},300')
        return f'<polygon points="{" ".join(pts)}" fill="{color}" opacity="0.35"/>'
    ev = 66 + 5.5 / 10 * 560
    return (f'<svg viewBox="0 0 660 360" role="img" aria-label="Distribuzione dell\'energia cinetica a due temperature e soglia di evaporazione">'
            + arrow_defs() +
            f'<line x1="66" y1="300" x2="640" y2="300" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>'
            f'<line x1="66" y1="300" x2="66" y2="30" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>'
            f'<text x="352" y="330" text-anchor="middle" {F12} fill="{INK}" font-weight="600">energia cinetica E<tspan baseline-shift="sub" font-size="9">c</tspan></text>'
            f'<text x="24" y="170" text-anchor="middle" {F12} fill="{INK}" font-weight="600" transform="rotate(-90 24 170)">numero di particelle</text>'
            + tail(2.2, 1.0, 0.95, BLUE) + tail(3.4, 3.2, 0.58, RED)
            + gauss(2.2, 1.0, 0.95, BLUE, 'T bassa', 60) + gauss(3.4, 3.2, 0.58, RED, 'T alta', 150)
            + f'<line x1="{ev:.0f}" y1="300" x2="{ev:.0f}" y2="42" stroke="{GREEN}" stroke-width="2" stroke-dasharray="6 4"/>'
            f'<text x="{ev+8:.0f}" y="52" {F12} fill="{GREEN}" font-weight="700">E<tspan baseline-shift="sub" font-size="9">v</tspan></text>'
            f'<text x="{ev+26:.0f}" y="272" {F11} fill="{BLUE}">evaporano</text>'
            f'<text x="{ev+96:.0f}" y="230" {F11} fill="{RED}">evaporano</text>'
            f'<text x="352" y="352" text-anchor="middle" {F12} fill="{INK}">evaporano le particelle con E<tspan baseline-shift="sub" font-size="9">c</tspan> &gt; E<tspan baseline-shift="sub" font-size="9">v</tspan>; l\'area cresce con la temperatura</text>'
            '</svg>')

def svg_equilibrio_dinamico():
    s = []
    s.append(f'<rect x="90" y="40" width="360" height="250" fill="none" stroke="{INK}" stroke-width="4"/>')
    s.append(f'<rect x="94" y="176" width="352" height="110" fill="#d8e8f4"/>')
    s.append(f'<line x1="94" y1="176" x2="446" y2="176" stroke="{BLUE}" stroke-width="2.4"/>')
    for x, y in ((130,206),(180,232),(240,204),(300,236),(360,210),(410,240),(150,266),(260,268),(340,262)):
        s.append(f'<circle cx="{x}" cy="{y}" r="7" fill="#6d8fc4"/>')
    for x, y in ((140,90),(210,120),(290,84),(360,130),(410,96),(250,150)):
        s.append(f'<circle cx="{x}" cy="{y}" r="6" fill="#d8a3a3"/>')
    s.append(f'<text x="408" y="72" text-anchor="end" {F11} fill="{RED}">vapore</text>')
    s.append(f'<text x="140" y="222" {F11} fill="{BLUE}">liquido</text>')
    s.append(f'<line x1="170" y1="176" x2="170" y2="96" stroke="{RED}" stroke-width="3" marker-end="url(#ahr)"/>')
    s.append(f'<text x="178" y="106" {F11} fill="{RED}" font-weight="600">evaporazione (E<tspan baseline-shift="sub" font-size="8">c</tspan> &gt; E<tspan baseline-shift="sub" font-size="8">v</tspan>)</text>')
    s.append(f'<line x1="350" y1="130" x2="350" y2="186" stroke="{BLUE}" stroke-width="3" marker-end="url(#ah)"/>')
    s.append(f'<text x="358" y="150" {F11} fill="{BLUE}" font-weight="600">condensazione (E<tspan baseline-shift="sub" font-size="8">c</tspan> &lt; E<tspan baseline-shift="sub" font-size="8">v</tspan>)</text>')
    s.append(f'<text x="270" y="326" text-anchor="middle" {F12} fill="{INK}" font-weight="600">equilibrio dinamico: velocità(evaporazione) = velocità(condensazione)</text>')
    return (f'<svg viewBox="0 0 540 350" role="img" aria-label="Equilibrio dinamico liquido-vapore in un contenitore chiuso">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_bagnabilita():
    s = []
    # sinistra: vetro
    s.append(f'<rect x="30" y="196" width="300" height="30" fill="#cfc9bd" stroke="{INK}" stroke-width="1.4"/>')
    for i in range(10):
        s.append(f'<text x="{48+i*29}" y="192" text-anchor="middle" {F10} fill="#6b675e">OH</text>')
    s.append(f'<path d="M 56 196 C 100 204, 130 148, 180 148 C 230 148, 260 204, 304 196 Z" fill="#aecde8" stroke="{BLUE}" stroke-width="1.6"/>')
    s.append(f'<text x="180" y="262" text-anchor="middle" {F11} fill="{INK}">acqua su vetro: angolo di contatto</text>')
    s.append(f'<text x="180" y="278" text-anchor="middle" {F11} fill="{INK}">piccolo, la superficie si bagna</text>')
    s.append(f'<text x="180" y="306" text-anchor="middle" {F11} fill="{INK}" font-weight="600">vetro (SiO₂ con superfici –OH):</text>')
    s.append(f'<text x="180" y="322" text-anchor="middle" {F11} fill="{INK}" font-weight="600">bassa tensione interfacciale</text>')
    # destra: TiO2/loto
    s.append(f'<rect x="390" y="196" width="300" height="30" fill="#b3ab9c" stroke="{INK}" stroke-width="1.4"/>')
    for i in range(18):
        s.append(f'<line x1="{404+i*16}" y1="196" x2="{404+i*16}" y2="172" stroke="#7a7468" stroke-width="2.4"/>')
    s.append(f'<circle cx="540" cy="128" r="62" fill="#aecde8" stroke="{BLUE}" stroke-width="1.6"/>')
    s.append(f'<text x="540" y="262" text-anchor="middle" {F11} fill="{INK}">acqua su TiO₂/loto: goccia quasi</text>')
    s.append(f'<text x="540" y="278" text-anchor="middle" {F11} fill="{INK}">sferica, area di contatto minima</text>')
    s.append(f'<text x="540" y="306" text-anchor="middle" {F11} fill="{INK}" font-weight="600">TiO₂ / foglia di loto:</text>')
    s.append(f'<text x="540" y="322" text-anchor="middle" {F11} fill="{INK}" font-weight="600">alta tensione interfacciale</text>')
    return f'<svg viewBox="0 0 720 336" role="img" aria-label="Bagnabilità e angolo di contatto: vetro contro TiO2 e loto">' + ''.join(s) + '</svg>'

def svg_menisco():
    s = []
    for x0, lbl, col in ((90, 'acqua', '#aecde8'), (330, 'mercurio', '#b9b4ab')):
        s.append(f'<line x1="{x0}" y1="60" x2="{x0}" y2="290" stroke="{INK}" stroke-width="4"/>')
        s.append(f'<line x1="{x0+130}" y1="60" x2="{x0+130}" y2="290" stroke="{INK}" stroke-width="4"/>')
        if lbl == 'acqua':
            s.append(f'<path d="M {x0+3} 150 C {x0+35} 230, {x0+95} 230, {x0+127} 150 L {x0+127} 288 L {x0+3} 288 Z" fill="{col}"/>')
            s.append(f'<path d="M {x0+3} 150 C {x0+35} 230, {x0+95} 230, {x0+127} 150" fill="none" stroke="{BLUE}" stroke-width="2.4"/>')
            s.append(f'<text x="{x0+65}" y="120" text-anchor="middle" {F12} fill="{BLUE}" font-weight="600">{lbl}</text>')
            s.append(f'<text x="{x0+65}" y="322" text-anchor="middle" {F11} fill="{INK}">menisco concavo:</text>')
            s.append(f'<text x="{x0+65}" y="338" text-anchor="middle" {F11} fill="{INK}">interfaccia liquido–vetro massimizzata</text>')
        else:
            s.append(f'<path d="M {x0+3} 226 C {x0+35} 156, {x0+95} 156, {x0+127} 226 L {x0+127} 288 L {x0+3} 288 Z" fill="{col}"/>')
            s.append(f'<path d="M {x0+3} 226 C {x0+35} 156, {x0+95} 156, {x0+127} 226" fill="none" stroke="{INK}" stroke-width="2.2"/>')
            s.append(f'<text x="{x0+65}" y="140" text-anchor="middle" {F12} fill="{INK}" font-weight="600">{lbl}</text>')
            s.append(f'<text x="{x0+65}" y="322" text-anchor="middle" {F11} fill="{INK}">menisco convesso:</text>')
            s.append(f'<text x="{x0+65}" y="338" text-anchor="middle" {F11} fill="{INK}">interfaccia liquido–vetro minimizzata</text>')
    return f'<svg viewBox="0 0 560 352" role="img" aria-label="Menisco concavo dell\'acqua e menisco convesso del mercurio">' + ''.join(s) + '</svg>'

def svg_capillarita():
    s = []
    s.append(f'<rect x="20" y="50" width="660" height="240" fill="none" stroke="{INK}" stroke-width="3.4"/>')
    s.append(f'<rect x="23" y="196" width="654" height="91" fill="#d8e8f4"/>')
    s.append(f'<line x1="23" y1="196" x2="677" y2="196" stroke="{BLUE}" stroke-width="2.2"/>')
    s.append(f'<text x="690" y="200" {F11} fill="{BLUE}">livello</text>')
    s.append(f'<text x="690" y="214" {F11} fill="{BLUE}">esterno</text>')
    tubes = [(80, 34, 240, 'd₁ grande'), (330, 22, 190, 'd₂'), (560, 13, 140, 'd₃ piccolo')]
    for x0, half, top, lbl in tubes:
        s.append(f'<line x1="{x0-half}" y1="{top-36}" x2="{x0-half}" y2="288" stroke="{INK}" stroke-width="3"/>')
        s.append(f'<line x1="{x0+half}" y1="{top-36}" x2="{x0+half}" y2="288" stroke="{INK}" stroke-width="3"/>')
        s.append(f'<path d="M {x0-half+3} {top+42} C {x0-half+half*0.4} {top+10}, {x0+half-half*0.4} {top+10}, {x0+half-3} {top+42} L {x0+half-3} 288 L {x0-half+3} 288 Z" fill="#aecde8"/>')
        s.append(f'<path d="M {x0-half+3} {top+42} C {x0-half+half*0.4} {top+10}, {x0+half-half*0.4} {top+10}, {x0+half-3} {top+42}" fill="none" stroke="{BLUE}" stroke-width="2"/>')
        s.append(f'<line x1="{x0+half+8}" y1="196" x2="{x0+half+8}" y2="{top+38}" stroke="{INK}" stroke-width="1.4" marker-start="url(#ah)" marker-end="url(#ah)"/>')
        h = lbl.split()[0]
        s.append(f'<text x="{x0+half+14}" y="{(196+top+38)/2:.0f}" {F11} fill="{INK}">h<tspan baseline-shift="sub" font-size="8">{h[-1]}</tspan></text>')
        s.append(f'<text x="{x0}" y="{top-46}" text-anchor="middle" {F11} fill="{INK}">{lbl}</text>')
    s.append(f'<text x="350" y="322" text-anchor="middle" {F12} fill="{INK}" font-weight="600">d₁ &gt; d₂ &gt; d₃ &#160;⇒&#160; h₁ &lt; h₂ &lt; h₃: al diminuire del diametro il livello sale</text>')
    return (f'<svg viewBox="0 0 730 336" role="img" aria-label="Capillarità: tre tubi di diametro decrescente e livelli crescenti">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_viscosita():
    s = []
    s.append(f'<rect x="60" y="120" width="400" height="150" fill="#d8e8f4"/>')
    s.append(f'<line x1="40" y1="270" x2="480" y2="270" stroke="{INK}" stroke-width="5"/>')
    s.append(f'<text x="260" y="296" text-anchor="middle" {F12} fill="{INK}">piano fisso</text>')
    s.append(f'<line x1="40" y1="120" x2="480" y2="120" stroke="{BLUE}" stroke-width="5"/>')
    s.append(f'<text x="260" y="106" text-anchor="middle" {F12} fill="{BLUE}" font-weight="600">piano mobile</text>')
    s.append(f'<line x1="492" y1="120" x2="576" y2="120" stroke="{RED}" stroke-width="3.4" marker-end="url(#ahr)"/>')
    s.append(f'<text x="534" y="110" text-anchor="middle" {F12} fill="{RED}" font-weight="700">F</text>')
    s.append(f'<line x1="240" y1="84" x2="340" y2="84" stroke="{INK}" stroke-width="2.6" marker-end="url(#ah)"/>')
    s.append(f'<text x="292" y="74" text-anchor="middle" {F12} fill="{INK}" font-weight="600">v</text>')
    s.append(f'<line x1="26" y1="120" x2="26" y2="270" stroke="{INK}" stroke-width="1.6" marker-start="url(#ah)" marker-end="url(#ah)"/>')
    s.append(f'<text x="16" y="200" text-anchor="middle" {F12} fill="{INK}" transform="rotate(-90 16 200)">Δy</text>')
    s.append(f'<text x="410" y="204" text-anchor="middle" {F11} fill="{BLUE}">liquido</text>')
    s.append(f'<line x1="90" y1="136" x2="170" y2="136" stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ah)"/>')
    s.append(f'<text x="178" y="140" {F11} fill="{BLUE}">v grande</text>')
    s.append(f'<line x1="90" y1="254" x2="130" y2="254" stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ah)"/>')
    s.append(f'<text x="138" y="258" {F11} fill="{BLUE}">v → 0</text>')
    s.append(f'<text x="300" y="330" text-anchor="middle" {F12} fill="{INK}" font-weight="600">F = η · (Δv/Δy) · S</text>')
    return (f'<svg viewBox="0 0 620 348" role="img" aria-label="Definizione meccanica della viscosità: piani di scorrimento">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_solubilita_pressioni():
    X0, X1, Y0, Y1 = 64, 560, 300, 40
    def px(t): return X0 + t / 10 * (X1 - X0)
    def py(g): return Y0 - g / 10 * (Y0 - Y1)
    s = [f'<line x1="{X0}" y1="{Y0}" x2="{X1+16}" y2="{Y0}" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>',
         f'<line x1="{X0}" y1="{Y0}" x2="{X0}" y2="{Y1-8}" stroke="{INK}" stroke-width="1.6" marker-end="url(#ah)"/>',
         f'<text x="{(X0+X1)/2}" y="{Y0+26}" text-anchor="middle" {F12} fill="{INK}" font-weight="600">temperatura T</text>',
         f'<text x="{X0-8}" y="40" text-anchor="end" {F12} fill="{INK}" font-weight="600">solubilità</text>']
    for (k, col, lbl, ylab) in ((9.0, BLUE, 'P₃', 90), (6.0, GREEN, 'P₂', 150), (3.6, AMBER, 'P₁', 208)):
        pts = []
        for i in range(0, 101, 2):
            t = i / 10
            g = k * math.exp(-0.22 * t) * 1.0
            pts.append(f'{px(t):.1f},{py(g):.1f}')
        s.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="2.4"/>')
        s.append(f'<text x="{px(0)-8:.0f}" y="{ylab}" text-anchor="end" {F12} fill="{col}" font-weight="700">{lbl}</text>')
    s.append(f'<text x="312" y="346" text-anchor="middle" {F12} fill="{INK}">a parità di T la solubilità cresce con la pressione parziale (P₁ &lt; P₂ &lt; P₃);</text>')
    s.append(f'<text x="312" y="362" text-anchor="middle" {F12} fill="{INK}">a parità di P diminuisce al crescere di T (dissoluzione esotermica)</text>')
    return (f'<svg viewBox="0 0 620 376" role="img" aria-label="Solubilità di un gas in funzione della temperatura a tre pressioni">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_osmosi():
    def panel(x0, title, extra, lvl=1):
        s_ = [f'<rect x="{x0}" y="70" width="180" height="180" fill="none" stroke="{INK}" stroke-width="3"/>']
        lw = 26 if lvl == 0 else 26
        s_.append(f'<rect x="{x0+3}" y="{70+150-lw}" width="86" height="{lw}" fill="#d8e8f4"/>')
        rh = 60 if lvl == 1 else 96
        s_.append(f'<rect x="{x0+91}" y="{70+180-40-rh}" width="86" height="{rh}" fill="#d8e8f4"/>')
        s_.append(f'<line x1="{x0+90}" y1="70" x2="{x0+90}" y2="250" stroke="{INK}" stroke-width="3" stroke-dasharray="8 5"/>')
        for x, y in ((x0+30, 216), (x0+60, 226), (x0+45, 206), (x0+70, 214)):
            s_.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{BLUE}"/>')
        for x, y in ((x0+120, 200), (x0+150, 212), (x0+135, 188), (x0+160, 198), (x0+110, 190)):
            s_.append(f'<circle cx="{x}" cy="{y}" r="4" fill="{BLUE}"/>')
            s_.append(f'<circle cx="{x+9}" cy="{y}" r="4" fill="{AMBER}"/>')
        s_.append(f'<text x="{x0+90}" y="56" text-anchor="middle" {F11} fill="{INK}" font-weight="600">{title}</text>')
        s_.append(f'<text x="{x0+46}" y="268" text-anchor="middle" {F10} fill="{INK}">solvente</text>')
        s_.append(f'<text x="{x0+134}" y="268" text-anchor="middle" {F10} fill="{INK}">soluzione</text>')
        s_.append(f'<text x="{x0+90}" y="288" text-anchor="middle" {F10} fill="{INK}">membrana semipermeabile</text>')
        return ''.join(s_) + extra
    s = [panel(20, '(a) inizio', '')]
    s.append(panel(240, '(b) insorge π',
                   f'<line x1="330" y1="250" x2="330" y2="170" stroke="{BLUE}" stroke-width="2.4" marker-end="url(#ah)"/>'
                   f'<text x="338" y="180" {F10} fill="{BLUE}">osmosi</text>'
                   f'<line x1="414" y1="112" x2="414" y2="146" stroke="{RED}" stroke-width="1.6" marker-start="url(#ahr)" marker-end="url(#ahr)"/>'
                   f'<text x="422" y="134" {F11} fill="{RED}" font-weight="700">π</text>'))
    s.append(panel(460, '(c) equilibrio: contropressione',
                   f'<line x1="542" y1="86" x2="542" y2="104" stroke="{RED}" stroke-width="3" marker-end="url(#ahr)"/>'
                   f'<line x1="534" y1="86" x2="590" y2="86" stroke="{INK}" stroke-width="4"/>'
                   f'<text x="566" y="76" text-anchor="middle" {F10} fill="{RED}" font-weight="700">π</text>'))
    s.append(f'<text x="360" y="330" text-anchor="middle" {F12} fill="{INK}" font-weight="600">π V = n RT&#160;&#160;&#160;la pressione osmotica è la contropressione che impedisce l\'osmosi</text>')
    return (f'<svg viewBox="0 0 660 344" role="img" aria-label="Osmosi attraverso membrana semipermeabile e pressione osmotica">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_no_gruppi():
    celle = [('I', '+1'), ('II', '+2'), ('III', '+3'), ('IV', '+4, +2'), ('V', '+5, +3, −3'),
             ('VI', '−2'), ('VII', '−1'), ('0', '0')]
    s = []
    x = 14
    for g, no in celle:
        s.append(f'<rect x="{x}" y="24" width="76" height="84" rx="8" fill="#f6f2ea" stroke="{GRID}" stroke-width="1.6"/>')
        s.append(f'<text x="{x+38}" y="52" text-anchor="middle" {F13} fill="{INK}" font-weight="700">{g}</text>')
        for j, v in enumerate(no.split(', ')):
            s.append(f'<text x="{x+38}" y="{74+j*18}" text-anchor="middle" {F11} fill="{VIOLET}" font-weight="700">{v}</text>')
        x += 84
    s.append(f'<text x="350" y="136" text-anchor="middle" {F11} fill="{INK}">N.O. positivi a sinistra (metalli: cedono e⁻), negativi a destra (non metalli: li acquistano)</text>')
    return f'<svg viewBox="0 0 690 148" role="img" aria-label="Numeri di ossidazione più comuni in funzione del gruppo">' + ''.join(s) + '</svg>'

def svg_famiglie():
    def box(x, y, w, h, html, fill='#f6f2ea', stroke=GRID, fs=12, weight='600'):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.7"/>'
                f'<text x="{x+w/2}" y="{y+h/2+4}" text-anchor="middle" {FONT} font-size="{fs}" fill="{INK}" font-weight="{weight}">{html}</text>')
    s = []
    s.append(box(16, 30, 120, 44, 'METALLO'))
    s.append(box(210, 30, 140, 44, 'ossido basico'))
    s.append(box(430, 30, 150, 44, 'idrossido E⁺(OH)⁻'))
    s.append(box(16, 150, 120, 44, 'NON METALLO'))
    s.append(box(210, 150, 140, 44, 'ossido acido (anidride)'))
    s.append(box(430, 150, 150, 44, 'ossiacido H⁺E⁺O⁻²'))
    s.append(box(650, 90, 130, 52, 'SALE + H₂O', fill='#e8f0e8', stroke=GREEN, weight='700'))
    for y in (52, 172):
        s.append(f'<line x1="136" y1="{y}" x2="206" y2="{y}" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>')
        s.append(f'<text x="171" y="{y-8}" text-anchor="middle" {F10} fill="{INK}">+ O₂</text>')
        s.append(f'<line x1="350" y1="{y}" x2="426" y2="{y}" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>')
        s.append(f'<text x="388" y="{y-8}" text-anchor="middle" {F10} fill="{INK}">+ H₂O</text>')
    s.append(f'<line x1="580" y1="52" x2="646" y2="96" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>')
    s.append(f'<line x1="580" y1="172" x2="646" y2="136" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>')
    s.append(f'<text x="596" y="66" {F10} fill="{INK}">acido+base</text>')
    s.append(f'<text x="350" y="228" text-anchor="middle" {F11} fill="{INK}">due binari paralleli: dal metallo agli idrossidi, dal non metallo agli ossiacidi; l\'incontro dà sale + acqua</text>')
    return (f'<svg viewBox="0 0 796 244" role="img" aria-label="Mappa delle famiglie di composti: dai precursori ai sali">'
            + arrow_defs() + ''.join(s) + '</svg>')

def _struttura_centrale(cx, cy, centro, doppio_ang, r=52):
    """atomo centrale + 3 ossigeni a 90/210/330°, un legame doppio verso doppio_ang; restituisce svg e posizioni O."""
    import math as _m
    pos = {}
    s = ''
    for a in (90, 210, 330):
        x, y = cx + r * _m.cos(_m.radians(a)), cy - r * _m.sin(_m.radians(a))
        pos[a] = (x, y)
        s += _bond(cx, cy, x, y, 2 if a == doppio_ang else 1)
    for a, (x, y) in pos.items():
        s += _atom(x, y, 'O', 14, 12)
    s += _atom(cx, cy, centro, 15, 13)
    return s, pos

def svg_formule_limite():
    s = []
    s.append(f'<text x="360" y="24" text-anchor="middle" {F13} fill="{INK}" font-weight="700">Ione nitrato NO₃⁻</text>')
    s.append(f'<text x="360" y="180" text-anchor="middle" {F13} fill="{INK}" font-weight="700">Ione carbonato CO₃²⁻</text>')
    for k, (cy, centro) in enumerate(((100, 'N'), (256, 'C'))):
        for i, ang in enumerate((90, 210, 330)):
            cx = 130 + i * 230
            frag, pos = _struttura_centrale(cx, cy, centro, ang)
            s.append(frag)
            for a2, (x2, y2) in pos.items():
                if a2 != ang:
                    s.append(f'<text x="{x2:.0f}" y="{y2+22:.0f}" text-anchor="middle" {F10} fill="{RED}">−</text>')
            if i < 2:
                s.append(f'<text x="{cx+115}" y="{cy+5}" text-anchor="middle" {F13} fill="{INK}">↔</text>')
    return f'<svg viewBox="0 0 720 300" role="img" aria-label="Formule limite dello ione nitrato e dello ione carbonato">' + ''.join(s) + '</svg>'

def svg_h2so4():
    s = []
    cx, cy = 300, 170
    su = (cx, cy - 78); sd = (cx, cy + 78); sl = (cx - 88, cy); sr = (cx + 88, cy)
    s.append(_bond(cx, cy, *su, 2)); s.append(_bond(cx, cy, *sr, 2))
    s.append(_bond(cx, cy, *sl)); s.append(_bond(cx, cy, *sd))
    s.append(_atom(*su, 'O', 16)); s.append(_atom(*sr, 'O', 16))
    s.append(_atom(*sl, 'O', 16)); s.append(_atom(*sd, 'O', 16))
    s.append(_atom(cx, cy, 'S', 17, 15))
    hl = (cx - 158, cy + 44); hd = (cx + 52, cy + 148)
    s.append(_bond(sl[0], sl[1], *hl)); s.append(_bond(sd[0], sd[1], *hd))
    s.append(_atom(*hl, 'H', 13, 12)); s.append(_atom(*hd, 'H', 13, 12))
    s.append(_odots(su[0], su[1], 90, 2, 22))
    s.append(_odots(sr[0], sr[1], 0, 2, 22))
    s.append(_odots(sl[0], sl[1], 115, 2, 22))
    s.append(_odots(sd[0], sd[1], 245, 2, 22))
    s.append(f'<text x="470" y="120" {F12} fill="{INK}">elettroni di valenza: 32</text>')
    s.append(f'<text x="470" y="142" {F12} fill="{INK}">(2·1 + 6 + 4·6)</text>')
    s.append(f'<text x="470" y="176" {F12} fill="{BLUE}" font-weight="700">N.O.: H = +1</text>')
    s.append(f'<text x="470" y="196" {F12} fill="{BLUE}" font-weight="700">O = −2&#160;&#160;S = +6</text>')
    s.append(f'<text x="470" y="228" {F11} fill="{INK}">due legami doppi S=O e due</text>')
    s.append(f'<text x="470" y="244" {F11} fill="{INK}">gruppi O–H (funzione acida)</text>')
    return f'<svg viewBox="0 0 640 310" role="img" aria-label="Formula di struttura dell\'acido solforico H2SO4">' + ''.join(s) + '</svg>'

def svg_ccl4():
    s = []
    cx, cy = 300, 160
    pts = [(cx, cy - 78), (cx - 88, cy), (cx + 88, cy), (cx, cy + 78)]
    for x, y in pts:
        s.append(_bond(cx, cy, x, y))
    for x, y in pts:
        s.append(_atom(x, y, 'Cl', 18, 12))
    s.append(_atom(cx, cy, 'C', 17, 15))
    s.append(_odots(pts[0][0], pts[0][1], 90, 3, 24))
    s.append(_odots(pts[1][0], pts[1][1], 180, 3, 24))
    s.append(_odots(pts[2][0], pts[2][1], 0, 3, 24))
    s.append(_odots(pts[3][0], pts[3][1], 270, 3, 24))
    s.append(f'<text x="478" y="128" {F12} fill="{INK}">4·7 + 4 = 32 e⁻</text>')
    s.append(f'<text x="478" y="158" {F12} fill="{BLUE}" font-weight="700">N.O.: C = +4</text>')
    s.append(f'<text x="478" y="178" {F12} fill="{BLUE}" font-weight="700">Cl = −1</text>')
    s.append(f'<text x="478" y="208" {F11} fill="{INK}">tre coppie di non legame</text>')
    s.append(f'<text x="478" y="224" {F11} fill="{INK}">su ciascun cloro (ottetto)</text>')
    return f'<svg viewBox="0 0 620 290" role="img" aria-label="Struttura di Lewis del tetracloruro di carbonio CCl4">' + ''.join(s) + '</svg>'

def svg_co2_strutture():
    s = []
    # (a) respinta
    s.append(_bond(60, 90, 150, 90)); s.append(_bond(150, 90, 240, 90))
    s.append(_atom(60, 90, 'O', 16)); s.append(_atom(150, 90, 'C', 16)); s.append(_atom(240, 90, 'O', 16))
    s.append(_odots(60, 90, 180, 3, 22)); s.append(_odots(240, 90, 0, 3, 22))
    s.append(f'<line x1="40" y1="140" x2="268" y2="46" stroke="{RED}" stroke-width="3"/>')
    s.append(f'<text x="36" y="46" {F13} fill="{RED}" font-weight="700">×</text>')
    s.append(f'<text x="150" y="168" text-anchor="middle" {F11} fill="{RED}">(a) respinta: l\'ottetto del C non è soddisfatto</text>')
    # (b) corretta
    s.append(_bond(430, 90, 520, 90, 2)); s.append(_bond(520, 90, 610, 90, 2))
    s.append(_atom(430, 90, 'O', 16)); s.append(_atom(520, 90, 'C', 16)); s.append(_atom(610, 90, 'O', 16))
    s.append(_odots(430, 90, 135, 2, 22)); s.append(_odots(610, 90, 45, 2, 22))
    s.append(f'<text x="520" y="168" text-anchor="middle" {F11} fill="{GREEN}" font-weight="600">(b) corretta: O=C=O (2 doppi legami)</text>')
    s.append(f'<text x="340" y="212" text-anchor="middle" {F12} fill="{INK}">CO₂: 6·2 + 4 = 16 e⁻;&#160;&#160;N.O.: C = +4, O = −2</text>')
    return f'<svg viewBox="0 0 680 228" role="img" aria-label="Anidride carbonica: struttura a legami semplici respinta e struttura corretta O=C=O">' + ''.join(s) + '</svg>'

def svg_nh3():
    s = []
    nx, ny = 130, 150
    s.append(_bond(nx, ny, 208, 104)); s.append(_bond(nx, ny, 66, 210)); s.append(_bond(nx, ny, 194, 208))
    s.append(_atom(nx, ny, 'N', 17)); s.append(_atom(208, 104, 'H', 14, 12)); s.append(_atom(66, 210, 'H', 14, 12)); s.append(_atom(194, 208, 'H', 14, 12))
    s.append(f'<line x1="{nx-8}" y1="{ny-6}" x2="{nx-52}" y2="{ny-46}" stroke="{INK}" stroke-width="2"/>')
    s.append(f'<circle cx="{nx-58}" cy="{ny-50}" r="2.2" fill="{INK}"/><circle cx="{nx-50}" cy="{ny-58}" r="2.2" fill="{INK}"/>')
    s.append(f'<line x1="248" y1="160" x2="330" y2="160" stroke="{RED}" stroke-width="2.6" marker-end="url(#ahr)"/>')
    px, py = 470, 90
    s.append(f'<line x1="{px}" y1="{py}" x2="{px-96}" y2="{py+120}" stroke="{RED}" stroke-width="2.2"/>')
    s.append(f'<line x1="{px}" y1="{py}" x2="{px+96}" y2="{py+120}" stroke="{RED}" stroke-width="2.2"/>')
    s.append(f'<line x1="{px}" y1="{py}" x2="{px}" y2="{py+140}" stroke="{RED}" stroke-width="2.2"/>')
    s.append(f'<text x="{px}" y="{py-12}" text-anchor="middle" {F12} fill="{RED}" font-weight="700">N</text>')
    for dx, dy in (-96, 120), (96, 120), (0, 140):
        s.append(f'<text x="{px+dx+ (14 if dx else 0)}" y="{py+dy+4}" text-anchor="middle" {F12} fill="{RED}">H</text>')
    s.append(f'<text x="470" y="268" text-anchor="middle" {F11} fill="{INK}">il doppietto = vertice del tetraedro:</text>')
    s.append(f'<text x="470" y="284" text-anchor="middle" {F11} fill="{INK}">geometria piramidale (angoli compressi)</text>')
    s.append(f'<text x="130" y="264" text-anchor="middle" {F11} fill="{INK}">NH₃: 1·3 + 5 = 8 e⁻</text>')
    return (f'<svg viewBox="0 0 620 300" role="img" aria-label="Ammoniaca: struttura con coppia solitaria e geometria piramidale">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_n2_o2():
    s = []
    s.append(_bond(90, 120, 230, 120, 3))
    s.append(_atom(90, 120, 'N', 16)); s.append(_atom(230, 120, 'N', 16))
    s.append(_dots(90, 120, [(180, 2)], 24)); s.append(_dots(230, 120, [(0, 2)], 24))
    s.append(f'<text x="160" y="170" text-anchor="middle" {F12} fill="{INK}">2·5 e⁻ = 10 e⁻</text>')
    s.append(f'<text x="160" y="190" text-anchor="middle" {F11} fill="{INK}">tre elettroni spaiati (Hund): legame triplo</text>')
    s.append(_bond(400, 120, 540, 120, 2))
    s.append(_atom(400, 120, 'O', 16)); s.append(_atom(540, 120, 'O', 16))
    s.append(_dots(400, 120, [(90, 2), (270, 2)], 24)); s.append(_dots(540, 120, [(90, 2), (270, 2)], 24))
    s.append(f'<text x="470" y="170" text-anchor="middle" {F12} fill="{INK}">2·6 e⁻ = 12 e⁻</text>')
    s.append(f'<path d="M 470 186 C 486 210, 510 218, 540 214" fill="none" stroke="{RED}" stroke-width="2" marker-end="url(#ahr)"/>')
    s.append(f'<text x="470" y="246" text-anchor="middle" {F11} fill="{RED}" font-weight="600">la notazione di Lewis ha delle limitazioni:</text>')
    s.append(f'<text x="470" y="262" text-anchor="middle" {F11} fill="{RED}" font-weight="600">O₂ risponde al campo magnetico (e⁻ spaiato: orbitali molecolari)</text>')
    return (f'<svg viewBox="0 0 640 276" role="img" aria-label="N2 con legame triplo e O2 con legame doppio: limiti della notazione di Lewis">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_carbonato():
    s = []
    s.append(f'<text x="380" y="22" text-anchor="middle" {F12} fill="{INK}" font-weight="700">K₂CO₃ → 2 K⁺ + CO₃²⁻&#160;&#160;·&#160;&#160;gli elettroni sono 24 e NON 22 (6·3 + 4 + 2 della carica)</text>')
    # (a) respinta: tre legami singoli
    frag, pos = _struttura_centrale(110, 130, 'C', -1, 46)
    s.append(frag)
    for a, (x, y) in pos.items():
        s.append(_odots(x, y, a, 3, 20))
    s.append(f'<line x1="52" y1="184" x2="168" y2="72" stroke="{RED}" stroke-width="2.6"/>')
    s.append(f'<text x="110" y="212" text-anchor="middle" {F10} fill="{RED}">(a) SBAGLIATO</text>')
    s.append(f'<text x="110" y="226" text-anchor="middle" {F10} fill="{RED}">per l\'effetto sul C</text>')
    # (b) con doppio legame in alto
    frag, pos = _struttura_centrale(300, 130, 'C', 90, 46)
    s.append(frag)
    s.append(_odots(pos[210][0], pos[210][1], 210, 3, 20))
    s.append(_odots(pos[330][0], pos[330][1], 330, 3, 20))
    s.append(_odots(pos[90][0], pos[90][1], 90, 2, 20))
    s.append(f'<text x="300" y="226" text-anchor="middle" {F10} fill="{INK}">(b) un legame doppio:</text>')
    s.append(f'<text x="300" y="240" text-anchor="middle" {F10} fill="{INK}">ottetto per tutti</text>')
    # (c) delocalizzata
    import math as _m
    cx, cy, r = 490, 130, 46
    for a in (90, 210, 330):
        x, y = cx + r * _m.cos(_m.radians(a)), cy - r * _m.sin(_m.radians(a))
        s.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" stroke="{INK}" stroke-width="2"/>')
        s.append(f'<line x1="{cx-6}" y1="{cy+9}" x2="{x-6:.0f}" y2="{y+9:.0f}" stroke="{VIOLET}" stroke-width="1.6" stroke-dasharray="6 4"/>')
        s.append(_atom(x, y, 'O', 14, 12))
    s.append(_atom(cx, cy, 'C', 15, 13))
    s.append(f'<text x="490" y="226" text-anchor="middle" {F10} fill="{VIOLET}">(c) delocalizzata:</text>')
    s.append(f'<text x="490" y="240" text-anchor="middle" {F10} fill="{VIOLET}">doppio legame dappertutto</text>')
    # (d) tre formule limite in colonna
    for k, ang in enumerate((90, 210, 330)):
        cy2 = 68 + k * 62
        frag, pos = _struttura_centrale(648, cy2, 'C', ang, 30)
        s.append(frag)
        s.append(_odots(pos[ang][0], pos[ang][1], ang, 2, 15))
    s.append(f'<text x="648" y="252" text-anchor="middle" {F10} fill="{INK}">(d) 3 formule limite</text>')
    s.append(f'<text x="648" y="266" text-anchor="middle" {F10} fill="{INK}">di risonanza</text>')
    s.append(f'<text x="380" y="286" text-anchor="middle" {F11} fill="{INK}">la distanza C–O misurata è intermedia tra legame singolo e doppio: la struttura reale è l\'ibrido di risonanza</text>')
    return f'<svg viewBox="0 0 760 300" role="img" aria-label="Lo ione carbonato: struttura respinta, struttura con doppio legame, struttura delocalizzata e tre formule limite">' + ''.join(s) + '</svg>'

def svg_azide():
    s = []
    strutture = [('N≡N–N', ['0', '+1', '−2'], 3, 1), ('N=N=N', ['−1', '+1', '−1'], 2, 2), ('N–N≡N', ['−2', '+1', '0'], 1, 3)]
    for i, (formula, cf, n1, n2) in enumerate(strutture):
        x0 = 56 + i * 222
        y = 110
        s.append(_bond(x0, y, x0 + 110, y, n1))
        s.append(_bond(x0 + 110, y, x0 + 220, y, n2))
        s.append(_atom(x0, y, 'N', 15)); s.append(_atom(x0 + 110, y, 'N', 15)); s.append(_atom(x0 + 220, y, 'N', 15))
        s.append(_dots(x0, y, [(180, 2)], 22)); s.append(_dots(x0 + 220, y, [(0, 2)], 22))
        for j, v in enumerate(cf):
            s.append(f'<text x="{x0 + j*110}" y="{y-32}" text-anchor="middle" {F12} fill="{AMBER}" font-weight="700">{v}</text>')
        if i < 2:
            s.append(f'<text x="{x0+166}" y="{y+5}" text-anchor="middle" {F13} fill="{INK}">↔</text>')
    s.append(f'<path d="M 292 150 q 120 34 240 0" fill="none" stroke="{RED}" stroke-width="1.8"/>')
    s.append(f'<text x="412" y="200" text-anchor="middle" {F11} fill="{RED}" font-weight="600">qui la DIFFERENZA DI carica formale</text>')
    s.append(f'<text x="412" y="216" text-anchor="middle" {F11} fill="{RED}" font-weight="600">ci dice che È più corretta</text>')
    s.append(f'<text x="412" y="248" text-anchor="middle" {F12} fill="{INK}">N₃⁻: 3·5 + 1 (carica) = 16 e⁻; cariche formali in giallo sopra gli atomi</text>')
    return f'<svg viewBox="0 0 740 264" role="img" aria-label="Le tre formule di risonanza dello ione azide con le cariche formali">' + ''.join(s) + '</svg>'

def svg_solfato_cf():
    s = []
    # struttura I
    cx, cy = 170, 150
    pts = [(cx, cy - 74, 90), (cx, cy + 74, 270), (cx - 84, cy, 180), (cx + 84, cy, 0)]
    for x, y, a in pts:
        s.append(_bond(cx, cy, x, y))
        s.append(_atom(x, y, 'O', 16))
        s.append(_odots(x, y, a, 3, 22))
    s.append(_atom(cx, cy, 'S', 17, 15))
    for x, y, a in pts:
        dx = 30 if a == 0 else -30 if a == 180 else 0
        dy = -22 if a == 90 else 36 if a == 270 else -12
        s.append(f'<text x="{x+dx}" y="{y+dy}" text-anchor="middle" {F11} fill="{AMBER}" font-weight="700">(−1)</text>')
    s.append(f'<text x="{cx+26}" y="{cy+34}" text-anchor="middle" {F11} fill="{AMBER}" font-weight="700">(+2)</text>')
    s.append(f'<text x="{cx}" y="252" text-anchor="middle" {F11} fill="{INK}">struttura I: CF = +2, −1×4</text>')
    s.append(f'<line x1="340" y1="60" x2="340" y2="240" stroke="{INK}" stroke-width="1.8"/>')
    # struttura II
    cx2 = 520
    up = (cx2, cy - 74); dn = (cx2, cy + 74); lf = (cx2 - 92, cy); rt = (cx2 + 92, cy)
    s.append(_bond(cx2, cy, *up)); s.append(_bond(cx2, cy, *dn))
    s.append(_bond(cx2, cy, *lf, 2)); s.append(_bond(cx2, cy, *rt, 2))
    for x, y in (up, dn, lf, rt):
        s.append(_atom(x, y, 'O', 16))
    s.append(_atom(cx2, cy, 'S', 17, 15))
    s.append(_odots(lf[0], lf[1], 180, 2, 22)); s.append(_odots(rt[0], rt[1], 0, 2, 22))
    s.append(_odots(up[0], up[1], 90, 3, 22)); s.append(_odots(dn[0], dn[1], 270, 3, 22))
    s.append(f'<text x="{cx2}" y="{cy-30}" text-anchor="middle" {F11} fill="{BLUE}" font-weight="700">+6</text>')
    s.append(f'<text x="{cx2}" y="{cy-4}" text-anchor="middle" {F11} fill="{AMBER}" font-weight="700">(0)</text>')
    s.append(f'<text x="{lf[0]}" y="{lf[1]-26}" text-anchor="middle" {F11} fill="{AMBER}" font-weight="700">(0)</text>')
    s.append(f'<text x="{rt[0]}" y="{rt[1]-26}" text-anchor="middle" {F11} fill="{AMBER}" font-weight="700">(0)</text>')
    s.append(f'<text x="{up[0]+34}" y="{up[1]}" {F11} fill="{AMBER}" font-weight="700">(−1)</text>')
    s.append(f'<text x="{dn[0]+34}" y="{dn[1]+4}" {F11} fill="{AMBER}" font-weight="700">(−1)</text>')
    s.append(f'<text x="{cx2}" y="252" text-anchor="middle" {F11} fill="{GREEN}" font-weight="700">struttura II (reale): CF = 0, 0, −1, −1</text>')
    s.append(f'<text x="410" y="284" text-anchor="middle" {F12} fill="{INK}">SO₄²⁻: 6·5 + 2 = 32 e⁻; N.O. S = +6, O = −2 in entrambe — vince chi minimizza le CF (ottetto espanso)</text>')
    return f'<svg viewBox="0 0 820 298" role="img" aria-label="Le due formule di struttura dello ione solfato con le cariche formali">' + ''.join(s) + '</svg>'

def svg_semireazioni():
    def box(x, y, w, h, l1, l2, col):
        return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#f6f2ea" stroke="{col}" stroke-width="1.8"/>'
                f'<text x="{x+w/2}" y="{y+24}" text-anchor="middle" {F13} fill="{INK}" font-weight="700">{l1}</text>'
                f'<text x="{x+w/2}" y="{y+44}" text-anchor="middle" {F11} fill="{col}" font-style="italic">{l2}</text>')
    s = []
    s.append(box(20, 40, 300, 56, '2 Fe³⁺ + 6 e⁻ → 2 Fe', 'si riduce (+3 → 0): ossidante', BLUE))
    s.append(box(440, 40, 300, 56, '3 Zn → 3 Zn²⁺ + 6 e⁻', 'si ossida (0 → +2): riducente', RED))
    s.append(f'<path d="M 440 96 C 380 150, 300 150, 244 100" fill="none" stroke="{INK}" stroke-width="2.2" stroke-dasharray="7 5" marker-end="url(#ah)"/>')
    s.append(f'<text x="342" y="146" text-anchor="middle" {F12} fill="{INK}" font-weight="700">6 e⁻</text>')
    s.append(f'<rect x="150" y="172" width="460" height="44" rx="9" fill="#e8f0e8" stroke="{GREEN}" stroke-width="1.8"/>')
    s.append(f'<text x="380" y="199" text-anchor="middle" {F13} fill="{INK}" font-weight="700">Fe₂O₃ + 3 Zn → 2 Fe + 3 ZnO</text>')
    s.append(f'<text x="380" y="246" text-anchor="middle" {F11} fill="{INK}">il numero di elettroni ceduti è uguale al numero di elettroni acquistati: si pareggia per primo</text>')
    return (f'<svg viewBox="0 0 760 264" role="img" aria-label="Trasferimento di elettroni nella reazione Fe2O3 + 3 Zn">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_redox_flow():
    steps = ['1. assegnare i N.O.; individuare chi si ossida e chi si riduce',
             '2. bilanciare le masse degli elementi redox, poi gli elettroni',
             '3. bilanciare le cariche: H⁺ (acido) oppure OH⁻ (basico)',
             '4. bilanciare le masse con H₂O']
    s = []
    y = 24
    for i, t in enumerate(steps):
        fill = '#e8f0e8' if i == 3 else '#f6f2ea'
        stroke = GREEN if i == 3 else GRID
        s.append(f'<rect x="90" y="{y}" width="440" height="46" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>')
        s.append(f'<text x="310" y="{y+29}" text-anchor="middle" {F13} fill="{INK}">{t}</text>')
        if i < 3:
            s.append(f'<line x1="310" y1="{y+46}" x2="310" y2="{y+68}" stroke="{INK}" stroke-width="2.4" marker-end="url(#ah)"/>')
        y += 70
    return (f'<svg viewBox="0 0 620 {y-70+46+24}" role="img" aria-label="Schema della procedura di bilanciamento delle reazioni redox">'
            + arrow_defs() + ''.join(s) + '</svg>')

def svg_lavagna_redox():
    s = []
    s.append(f'<text x="370" y="34" text-anchor="middle" {F13} fill="{INK}" font-weight="700">MnO₄⁻ + 5 Fe²⁺ + 8 H⁺ → Mn²⁺ + 5 Fe³⁺ + 4 H₂O</text>')
    s.append(f'<path d="M 118 44 q 118 22 236 0" fill="none" stroke="{INK}" stroke-width="1.4"/>')
    s.append(f'<text x="236" y="76" text-anchor="middle" {F12} fill="{RED}" font-weight="700">9 ⊕</text>')
    s.append(f'<path d="M 434 44 q 106 22 212 0" fill="none" stroke="{INK}" stroke-width="1.4"/>')
    s.append(f'<text x="540" y="76" text-anchor="middle" {F12} fill="{RED}" font-weight="700">17 ⊕</text>')
    s.append(f'<text x="436" y="26" text-anchor="middle" {F10} fill="{VIOLET}" font-weight="700">+7</text>')
    s.append(f'<line x1="70" y1="104" x2="70" y2="176" stroke="{INK}" stroke-width="1.6"/>')
    s.append(f'<text x="96" y="122" {F13} fill="{INK}" font-weight="600">Mn⁺⁷ + 5 e⁻ → Mn²⁺</text>')
    s.append(f'<text x="360" y="122" {F11} fill="{RED}" font-weight="700">(RIDUCE) → RED</text>')
    s.append(f'<text x="96" y="156" {F13} fill="{INK}" font-weight="600">Fe²⁺ → Fe³⁺ + 1 e⁻</text>')
    s.append(f'<text x="360" y="156" {F11} fill="{RED}" font-weight="700">(OSSIDA) → OX</text>')
    s.append(f'<line x1="60" y1="208" x2="680" y2="208" stroke="{RED}" stroke-width="1.4"/>')
    s.append(f'<text x="370" y="236" text-anchor="middle" {F12} fill="{RED}" font-weight="600">soluzioni acide → eccesso di (H⁺)&#160;&#160;&#160;soluzioni basiche → eccesso di (OH⁻)</text>')
    s.append(f'<text x="370" y="266" text-anchor="middle" {F11} fill="{INK}">le cariche degli ioni si contano senza gli H⁺ (o OH⁻) aggiunti per bilanciare; l\'acqua chiude O e H</text>')
    return f'<svg viewBox="0 0 740 280" role="img" aria-label="Bilanciamento in ambiente acido di MnO4-/Fe2+: conteggio delle cariche totali e semireazioni">' + ''.join(s) + '</svg>'

def svg_staffe_cr():
    s = []
    s.append(f'<text x="390" y="30" text-anchor="middle" {F12} fill="{INK}" font-weight="700">2 Cr(OH)₄⁻ + 3 Cl₂ + 8 OH⁻ → 2 CrO₄²⁻ + 6 Cl⁻ + 8 H₂O</text>')
    s.append(f'<text x="718" y="56" text-anchor="end" {F11} fill="{VIOLET}" font-weight="700">AMBIENTE BASICO</text>')
    s.append(f'<path d="M 300 44 C 260 118, 480 138, 560 46" fill="none" stroke="{INK}" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.append(f'<text x="404" y="118" text-anchor="middle" {F11} fill="{INK}">OX: −3 e⁻ per atomo × 2</text>')
    s.append(f'<path d="M 176 44 C 150 88, 300 104, 420 48" fill="none" stroke="{INK}" stroke-width="1.8" marker-end="url(#ah)"/>')
    s.append(f'<text x="272" y="84" text-anchor="middle" {F11} fill="{INK}">RED: +2 e⁻ per Cl₂ × 3</text>')
    s.append(f'<text x="390" y="150" text-anchor="middle" {F12} fill="{INK}" font-weight="600">elettroni complessivi: 6 = 6</text>')
    s.append(f'<text x="150" y="190" {F11} fill="{RED}" font-weight="600">non si conta</text>')
    s.append(f'<line x1="212" y1="178" x2="252" y2="44" stroke="{RED}" stroke-width="1.4" marker-end="url(#ahr)"/>')
    s.append(f'<text x="390" y="222" text-anchor="middle" {F11} fill="{INK}">gli OH⁻ aggiunti per bilanciare le cariche non entrano nel conto; l\'acqua si aggiunge per ultima</text>')
    return (f'<svg viewBox="0 0 740 240" role="img" aria-label="Trasferimento elettronico nella reazione in ambiente basico Cr(OH)4-/Cl2">'
            + arrow_defs() + ''.join(s) + '</svg>')

# ---------------------------------------------------------------- figure lezioni 13–14 e diagrammi ex Mermaid
import json
FONT = 'font-family="Inter,system-ui,sans-serif"'
INK, INK2, MUTED = '#3a3833', '#6a6459', '#8f887c'
HAIR, GRIDC = '#ebe5d8', '#d8d1c2'
# serie dei grafici (palette validata: blu, ruggine, verde acqua, viola)
C1, C2, C3, C4, CTX = '#2f62b0', '#c2552b', '#1d8a72', '#7a52c7', '#c4bdb0'
# convenzione cromatica delle figure dello stato solido
AT = {'cation': '#2f9a5a', 'anion': '#7b68d8', 'ferro': '#2d6ab2', 'solf': '#e2a514',
      'ossig': '#d64545', 'silic': '#7d7d8c', 'liti': '#46a5eb', 'carbo': '#45454f',
      'generico': '#5a6e96', 'arancio': '#e0861a'}
ATTR, REPU = '#1d8a72', '#c2552b'

_uid = [0]
def uid(p):
    _uid[0] += 1
    return f'{p}{_uid[0]}'

def esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(x + (y - x) * t):02x}' for x, y in zip(a, b))

def T(x, y, s, size=12, anchor='middle', weight=None, fill=INK, italic=False, raw=False, extra=''):
    w = f' font-weight="{weight}"' if weight else ''
    it = ' font-style="italic"' if italic else ''
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" {FONT} font-size="{size}" '
            f'fill="{fill}"{w}{it}{extra}>{s if raw else esc(s)}</text>')

def SUB(base, sub, size=9):
    """Testo con pedice (già escapato) per T(..., raw=True)."""
    return f'{esc(base)}<tspan baseline-shift="sub" font-size="{size}">{esc(sub)}</tspan>'

def L(x1, y1, x2, y2, color=INK, w=1.6, dash=None, end=None, start=None, op=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    e = f' marker-end="url(#{end})"' if end else ''
    s = f' marker-start="url(#{start})"' if start else ''
    o = f' opacity="{op}"' if op else ''
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" '
            f'stroke-width="{w}" stroke-linecap="round"{d}{e}{s}{o}/>')

def poly(pts, color=INK, w=2, fill='none', dash=None, close=False, extra=''):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    tag = 'polygon' if close else 'polyline'
    p = ' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)
    return (f'<{tag} points="{p}" fill="{fill}" stroke="{color}" stroke-width="{w}" '
            f'stroke-linejoin="round" stroke-linecap="round"{d}{extra}/>')

class Fig:
    def __init__(self, w, h, label):
        self.w, self.h, self.label = w, h, label
        self.defs, self.body, self._mk, self._gr = [], [], {}, {}
        self.attrs = ''

    def mk(self, color, size=7):
        key = (color, size)
        if key not in self._mk:
            i = uid('mk')
            self._mk[key] = i
            self.defs.append(f'<marker id="{i}" viewBox="0 0 10 10" refX="8.6" refY="5" markerWidth="{size}" '
                             f'markerHeight="{size}" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="{color}"/></marker>')
        return self._mk[key]

    def grad(self, color):
        if color not in self._gr:
            i = uid('gr')
            self._gr[color] = i
            self.defs.append(f'<radialGradient id="{i}" cx="36%" cy="32%" r="72%">'
                             f'<stop offset="0%" stop-color="{mix(color, "#ffffff", 0.62)}"/>'
                             f'<stop offset="48%" stop-color="{color}"/>'
                             f'<stop offset="100%" stop-color="{mix(color, "#000000", 0.38)}"/></radialGradient>')
        return self._gr[color]

    def ball(self, x, y, r, color, ring=True):
        st = f' stroke="{mix(color, "#000000", 0.45)}" stroke-width="0.8"' if ring else ''
        return f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="url(#{self.grad(color)})"{st}/>'

    def add(self, *s):
        self.body.extend(s)

    def svg(self):
        lab = self.label.replace('"', '&quot;')
        defs = f'<defs>{"".join(self.defs)}</defs>' if self.defs else ''
        return (f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{lab}"{self.attrs}>'
                + defs + ''.join(self.body) + '</svg>')

# ---------------------------------------------------------------- interpolazione monotona (Fritsch–Carlson)
def monotone(xs, ys):
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [d[0]] + [0.0] * (n - 2) + [d[-1]]
    for i in range(1, n - 1):
        m[i] = 0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2
    for i in range(n - 1):
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        s = a * a + b * b
        if s > 9:
            t = 3 / math.sqrt(s)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        k = max(i for i in range(n - 1) if xs[i] <= x)
        t = (x - xs[k]) / h[k]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[k] + (t3 - 2 * t2 + t) * h[k] * m[k]
                + (-2 * t3 + 3 * t2) * ys[k + 1] + (t3 - t2) * h[k] * m[k + 1])
    return f

def crossing(f, g, a, b, steps=4000):
    """Primo zero di f-g in [a,b] (bisezione dopo campionamento)."""
    prev = f(a) - g(a)
    for k in range(1, steps + 1):
        x = a + (b - a) * k / steps
        cur = f(x) - g(x)
        if prev == 0 or prev * cur < 0:
            lo, hi = x - (b - a) / steps, x
            for _ in range(60):
                mid = (lo + hi) / 2
                if (f(lo) - g(lo)) * (f(mid) - g(mid)) <= 0:
                    hi = mid
                else:
                    lo = mid
            return (lo + hi) / 2
        prev = cur
    return None

# ---------------------------------------------------------------- assi e griglia dei grafici
def axes(fig, X0, X1, Y0, Y1, xt, yt, fx, fy, xlab, ylab, xfmt=str, yfmt=str):
    s = []
    for v in yt:
        y = fy(v)
        s.append(L(X0, y, X1, y, HAIR, 1))
        s.append(T(X0 - 8, y + 4, yfmt(v), 11, 'end', fill=INK2))
    for v in xt:
        x = fx(v)
        s.append(L(x, Y0, x, Y1, HAIR, 1))
        s.append(T(x, Y0 + 18, xfmt(v), 11, fill=INK2))
    s.append(L(X0, Y0, X1 + 12, Y0, INK, 1.4, end=fig.mk(INK, 6)))
    s.append(L(X0, Y0, X0, Y1 - 12, INK, 1.4, end=fig.mk(INK, 6)))
    s.append(T((X0 + X1) / 2, Y0 + 40, xlab, 12, weight=600))
    s.append(T(X0 - 46, (Y0 + Y1) / 2, ylab, 12, weight=600,
               extra=f' transform="rotate(-90 {X0 - 46} {(Y0 + Y1) / 2})"'))
    return s

def curve(f, a, b, fx, fy, color, w=2.2, n=160, dash=None):
    pts = [(fx(a + (b - a) * k / n), fy(f(a + (b - a) * k / n))) for k in range(n + 1)]
    return poly(pts, color, w, dash=dash)

def num_it(v, dec=1):
    s = f'{v:.{dec}f}'.replace('.', ',').replace('-', '−')
    return s[:-2] if s.endswith(',0') else s

# ================================================================ LEZIONE 13
def svg_tensioattivi():
    """Figura 65.4 — (a) molecola anfifilica; (b) micella."""
    f = Fig(780, 336, 'La molecola anfifilica e la micella: teste polari verso l’acqua, code apolari verso il grasso')
    BR, BL, BLS = '#8a5a2b', C1, '#e7eef8'
    f.add(T(185, 26, '(a) molecola anfifilica (a solubilità mista)', 13, weight=700))
    pts = [(42 + 31 * i, 176 if i % 2 == 0 else 150) for i in range(9)]
    f.add(poly(pts, BR, 4))
    f.add(L(pts[-1][0], pts[-1][1], 316, 176, BL, 3))
    f.add(f'<circle cx="342" cy="176" r="26" fill="{BLS}" stroke="{BL}" stroke-width="2.4"/>', T(342, 181, 'OH', 15, weight=700, fill=BL))
    f.add(T(166, 126, 'coda apolare: catena di legami C–H', 12, fill=BR, weight=600))
    f.add(T(342, 228, 'testa polare', 12, fill=BL, weight=600), T(342, 244, '(gruppi ossigenati)', 12, fill=BL))
    f.add(T(185, 300, 'la coda interagisce con i solventi apolari (benzene),', 12, fill=INK2),
          T(185, 316, 'la testa con l’acqua: la molecola si scioglie in entrambi', 12, fill=INK2))
    # (b) micella in acqua
    cx, cy = 532, 166
    f.add(f'<rect x="402" y="40" width="364" height="250" rx="16" fill="#eef4fa" stroke="#d3e1ef"/>')
    f.add(T(584, 26, '(b) micella di tensioattivi', 13, weight=700))
    f.add(f'<circle cx="{cx}" cy="{cy}" r="40" fill="#e9c58c" stroke="#c99a52" stroke-width="1.5"/>')
    f.add(T(cx, cy - 3, 'macchia', 12, weight=600, fill='#6b4a1d'), T(cx, cy + 12, 'di grasso', 12, weight=600, fill='#6b4a1d'))
    for k in range(12):
        a = math.radians(k * 30)
        x1, y1 = cx + 50 * math.cos(a), cy - 50 * math.sin(a)
        x2, y2 = cx + 86 * math.cos(a), cy - 86 * math.sin(a)
        hx, hy = cx + 95 * math.cos(a), cy - 95 * math.sin(a)
        f.add(L(x1, y1, x2, y2, BR, 2.6), f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="9" fill="{BLS}" stroke="{BL}" stroke-width="2"/>')
    m = f.mk(INK, 6)
    f.add(L(660, 92, 626, 109, INK, 1.4, end=m), T(664, 78, 'teste polari', 12, 'start', weight=600, fill=BL), T(664, 93, '(verso l’acqua)', 12, 'start', fill=BL))
    f.add(L(660, 236, 590, 208, INK, 1.4, end=m), T(664, 238, 'code apolari', 12, 'start', weight=600, fill=BR), T(664, 253, '(verso il grasso)', 12, 'start', fill=BR))
    f.add(T(cx, 282, 'acqua (solvente polare)', 12, fill=C1, italic=True))
    f.add(T(584, 318, 'le teste restano in acqua, le code inglobano il grasso apolare', 12, fill=INK2))
    return f.svg()

SOL_DATA = [  # nome, valori a 0/20/40/60/80/100 °C, colore (None = contesto)
    ('KNO₃', [13.3, 31.6, 63.9, 110, 169, 245], C1),
    ('NaNO₃', [73, 88, 104, 124, 148, 180], None),
    ('CaCl₂', [59.5, 74.5, 128, 137, 147, 159], None),
    ('Pb(NO₃)₂', [37.5, 52.2, 65.3, 85, 103, 125], None),
    ('K₂Cr₂O₇', [4.7, 12.3, 26.3, 45.6, 73, 102], None),
    ('NH₄Cl', [29.4, 37.2, 45.8, 55.3, 65.6, 77.3], None),
    ('KCl', [28.0, 34.2, 40.1, 45.8, 51.3, 56.3], C3),
    ('KClO₃', [3.3, 7.3, 13.9, 23.8, 37.6, 56.3], None),
    ('NaCl', [35.7, 36.0, 36.6, 37.3, 38.4, 39.8], C4),
    ('Ce₂(SO₄)₃', [20.1, 13.9, 10.1, 7.5, 5.4, 3.8], C2),
]
KNO3_FINE = ([0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100], [13.3, 20.9, 31.6, 45.8, 63.9, 85.5, 110, 138, 169, 202, 245])
TS = [0, 20, 40, 60, 80, 100]

def svg_solubilita_curve():
    """Figura 67.1 — dieci sali, quattro evidenziati (emphasis), etichette con linee guida."""
    f = Fig(780, 450, 'Curve di solubilità in acqua di dieci sali in funzione della temperatura')
    X0, X1, Y0, Y1 = 78, 600, 386, 30
    fx = lambda t: X0 + t / 100 * (X1 - X0)
    fy = lambda g: Y0 - g / 250 * (Y0 - Y1)
    f.add(*axes(f, X0, X1, Y0, Y1, TS, [0, 50, 100, 150, 200, 250], fx, fy,
                'temperatura (°C)', 'solubilità (g / 100 g H₂O)'))
    funcs = {}
    for name, vals, col in SOL_DATA:
        xs, ys = (KNO3_FINE if name == 'KNO₃' else (TS, vals))
        funcs[name] = monotone(xs, ys)
    for name, vals, col in SOL_DATA:          # prima il contesto, poi le serie evidenziate
        if col is None:
            f.add(curve(funcs[name], 0, 100, fx, fy, CTX, 1.6))
    for name, vals, col in SOL_DATA:
        if col:
            f.add(curve(funcs[name], 0, 100, fx, fy, col, 2.4))
    # incrocio KNO3–KCl (cristallizzazione selettiva)
    tc = crossing(funcs['KNO₃'], funcs['KCl'], 1, 60)
    gc = funcs['KCl'](tc)
    f.add(f'<circle cx="{fx(tc):.1f}" cy="{fy(gc):.1f}" r="5.5" fill="#fff" stroke="{INK}" stroke-width="1.6"/>')
    f.add(L(fx(tc), fy(gc) - 6, fx(tc), fy(178), INK2, 1),
          T(fx(tc), fy(196), 'KNO₃ = KCl', 11, 'middle', weight=600, fill=INK2),
          T(fx(tc), fy(184), 'a ≈ 22–23 °C', 11, 'middle', fill=INK2))
    # etichette a destra con distanziamento minimo
    ends = sorted(((fy(vals[-1]), name, col) for name, vals, col in SOL_DATA), key=lambda e: e[0])
    gap, ys = 15, []
    for y, name, col in ends:
        ys.append(max(y, ys[-1] + gap) if ys else y)
    for k in range(len(ys) - 2, -1, -1):       # ridistribuisce verso l'alto se serve
        if ys[k + 1] - ys[k] < gap:
            ys[k] = ys[k + 1] - gap
    for (y, name, col), yl in zip(ends, ys):
        key = col or CTX
        f.add(L(X1 + 2, y, X1 + 14, yl, key, 1.2))
        f.add(L(X1 + 16, yl, X1 + 30, yl, key, 3 if col else 2))
        f.add(T(X1 + 36, yl + 4, name, 12, 'start', weight=700 if col else None, fill=INK if col else INK2))
    # dati per il livello interattivo (letti dallo script della pagina)
    data = {'T': TS, 'x0': X0, 'x1': X1, 'y0': Y0, 'y1': Y1, 'ymax': 250,
            's': [{'n': n, 'c': c or CTX, 'v': v, 'h': bool(c)} for n, v, c in SOL_DATA]}
    f.attrs = f" data-sol='{json.dumps(data, ensure_ascii=False)}' tabindex=\"0\""
    return f.svg()

def svg_benzene():
    """Figura 67.2 — benzene e ibridazione sp²."""
    f = Fig(660, 330, 'Struttura del benzene e ibridazione sp2 del carbonio')
    cx, cy, R, RH = 205, 165, 92, 152
    Cs = [(cx + R * math.cos(math.radians(30 + 60 * i)), cy - R * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    Hs = [(cx + RH * math.cos(math.radians(30 + 60 * i)), cy - RH * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
    for i in range(6):
        f.add(L(*Cs[i], *Cs[(i + 1) % 6], INK, 3.2), L(*Cs[i], *Hs[i], INK, 3.2))
    f.add(f'<circle cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{C1}" stroke-width="2.2" stroke-dasharray="7 5"/>')
    f.add(T(cx, cy - 3, 'elettroni π', 12, weight=600, fill=C1), T(cx, cy + 13, 'delocalizzati', 12, weight=600, fill=C1))
    for x, y in Cs:
        f.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="16" fill="#e2e2e2" stroke="#4a4a4a" stroke-width="1.6"/>', T(x, y + 4.5, 'C', 13, weight=700))
    for x, y in Hs:
        f.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="12" fill="#f7f7f7" stroke="#7a7a7a" stroke-width="1.2"/>', T(x, y + 4, 'H', 11, weight=600))
    f.add(T(400, 136, 'ibridazione sp²', 14, 'start', weight=700),
          T(400, 162, '3 legami σ planari', 13, 'start'),
          T(400, 186, '+ 1 elettrone π delocalizzato', 13, 'start'),
          T(400, 220, 'molecola planare C₆H₆:', 12, 'start', fill=INK2),
          T(400, 236, 'la stessa geometria della grafite', 12, 'start', fill=INK2))
    return f.svg()

def svg_soluzioni_solide():
    """Figura 67.5 — soluzione solida sostituzionale (a) e interstiziale (b)."""
    f = Fig(800, 364, 'Soluzioni solide sostituzionali (bronzo) e interstiziali (acciaio)')
    d, r = 54, 17
    def lattice(x0, y0):
        s = []
        for i in range(6):
            for j in range(4):
                x, y = x0 + i * d, y0 + (3 - j) * d
                if i < 5: s.append(L(x, y, x + d, y, '#bdb6aa', 1.2))
                if j < 3: s.append(L(x, y, x, y - d, '#bdb6aa', 1.2))
        return s
    def atomA(x, y): return f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ece9e2" stroke="#6f6a61" stroke-width="1.8"/>'
    m = f.mk(INK, 6)
    # (a)
    x0, y0 = 60, 90
    f.add(T(195, 26, '(a) sostituzionale: bronzo (Cu–Sn)', 13, weight=700))
    f.add(*lattice(x0, y0))
    B = {(1, 1), (4, 2), (2, 3), (5, 0)}
    for i in range(6):
        for j in range(4):
            x, y = x0 + i * d, y0 + (3 - j) * d
            f.add(atomA(x, y) if (i, j) not in B else f'<circle cx="{x}" cy="{y}" r="{r}" fill="#3f3d39" stroke="#1d1c1a" stroke-width="1.8"/>')
    bx, by = x0 + 2 * d, y0
    f.add(L(bx + 64, 48, bx + 12, by - 14, INK, 1.3, end=m), T(bx + 70, 50, 'atomo B (stagno), sostituito', 12, 'start', weight=600))
    ax, ay = x0 + 2 * d, y0 + 3 * d
    f.add(L(ax + 40, 296, ax + 6, ay + 16, INK, 1.3, end=m), T(ax + 46, 302, 'atomo A (rame),', 12, 'start', weight=600), T(ax + 46, 317, 'componente principale', 12, 'start', weight=600))
    f.add(T(195, 348, 'stessa dimensione: il reticolo non si deforma', 12, fill=INK2))
    # (b)
    x0 = 470
    f.add(T(605, 26, '(b) interstiziale: acciaio (Fe–C)', 13, weight=700))
    f.add(*lattice(x0, y0))
    for i in range(6):
        for j in range(4):
            f.add(atomA(x0 + i * d, y0 + (3 - j) * d))
    Cpos = [(0, 0), (2, 1), (4, 0), (1, 2), (3, 2), (4, 1)]
    for i, j in Cpos:
        x, y = x0 + (i + 0.5) * d, y0 + (3 - j - 0.5) * d
        f.add(f'<circle cx="{x}" cy="{y}" r="7.5" fill="#8f2d2d" stroke="#3e1414" stroke-width="1.2"/>')
    cx_, cy_ = x0 + 1.5 * d, y0 + 0.5 * d
    f.add(L(x0 + 2.6 * d, 50, cx_ + 6, cy_ - 8, INK, 1.3, end=m), T(x0 + 2.6 * d + 6, 50, 'atomo C, nell’interstizio', 12, 'start', weight=600))
    fx_, fy_ = x0 + 1 * d, y0 + 3 * d
    f.add(L(fx_ + 40, 296, fx_ + 6, fy_ + 16, INK, 1.3, end=m), T(fx_ + 46, 302, 'atomo Fe,', 12, 'start', weight=600), T(fx_ + 46, 317, 'reticolo principale', 12, 'start', weight=600))
    f.add(T(605, 348, 'atomo molto più piccolo: occupa i vuoti del reticolo', 12, fill=INK2))
    return f.svg()

# dati delle curve di tensione di vapore (lezione 13, Figure 7 e 8)
EB_PURE = ([78, 82, 86, 90, 94, 98, 100, 102, 104, 106, 108, 110], [43.6, 50.2, 57.8, 70.1, 81.0, 94.6, 101.3, 108.8, 116.9, 125.4, 134.5, 144.2])
EB_SOL = ([78, 82, 86, 90, 94, 98, 100, 102, 104, 106, 108, 110], [40.1, 46.2, 53.2, 64.5, 74.5, 87.0, 93.2, 100.1, 107.6, 115.4, 123.7, 132.6])
CR_SOL_ICE = ([-15, -12, -10, -8, -6, -5, -4, -3, -2, -1, 0, 2, 4, 6, 8, 10], [0.165, 0.218, 0.260, 0.310, 0.369, 0.402, 0.437, 0.477, 0.517, 0.563, 0.611, 0.706, 0.813, 0.935, 1.072, 1.228])
CR_PURE = ([-15, -12, -10, -8, -6, -4, -2, 0, 2, 5, 8, 10, 12, 15, 18, 20, 25], [0.191, 0.223, 0.286, 0.340, 0.379, 0.434, 0.505, 0.611, 0.706, 0.872, 1.073, 1.228, 1.403, 1.706, 2.064, 2.339, 3.169])
CR_SOL = ([-15, -12, -10, -8, -6, -4, -2, 0, 2, 5, 8, 10, 12, 15, 18, 20, 25], [0.176, 0.205, 0.263, 0.313, 0.349, 0.399, 0.465, 0.562, 0.650, 0.802, 0.987, 1.129, 1.291, 1.569, 1.899, 2.152, 2.915])

def legend(fig, x, y, items):
    s = []
    for k, (lab, col) in enumerate(items):
        yy = y + k * 18
        s.append(L(x, yy - 4, x + 22, yy - 4, col, 2.6))
        s.append(T(x + 30, yy, lab, 12, 'start'))
    return s

def svg_ebullioscopia():
    """Figura 68.1 — innalzamento ebullioscopico."""
    f = Fig(700, 410, 'Innalzamento ebullioscopico: curve della tensione di vapore del solvente puro e della soluzione')
    X0, X1, Y0, Y1 = 84, 650, 340, 30
    fx = lambda t: X0 + (t - 78) / (112 - 78) * (X1 - X0)
    fy = lambda p: Y0 - (p - 40) / (150 - 40) * (Y0 - Y1)
    f.add(*axes(f, X0, X1, Y0, Y1, [80, 85, 90, 95, 100, 105, 110], [40, 60, 80, 100, 120, 140], fx, fy,
                'temperatura (°C)', 'tensione di vapore (kPa)'))
    fp, fs = monotone(*EB_PURE), monotone(*EB_SOL)
    tb = crossing(fs, lambda t: 101.3, 99, 110)
    yA = fy(101.3)
    f.add(L(X0, yA, X1, yA, INK2, 1.4, dash='6 5'))
    f.add(T(X0 + 8, yA + 16, 'P = 1 atm = 101,3 kPa (pressione esterna)', 11, 'start', fill=INK2))
    f.add(curve(fp, 78, 110, fx, fy, C1, 2.4), curve(fs, 78, 110, fx, fy, C2, 2.4))
    for t, col in ((100, C1), (tb, C2)):
        f.add(L(fx(t), yA, fx(t), Y0, col, 1.6, dash='2 4'))
        f.add(f'<circle cx="{fx(t):.1f}" cy="{yA:.1f}" r="5" fill="{col}" stroke="#fff" stroke-width="2"/>')
    ya = fy(55)
    m = f.mk(INK, 6)
    f.add(L(fx(100) + 1, ya, fx(tb) - 1, ya, INK, 1.6, end=m, start=m))
    f.add(T((fx(100) + fx(tb)) / 2, ya + 22, SUB('ΔT', 'eb') + ' &gt; 0', 13, weight=700, raw=True))
    f.add(T(fx(100) - 10, yA - 30, 'ebollizione del', 12, 'end', fill=INK), T(fx(100) - 10, yA - 15, 'solvente puro (100 °C)', 12, 'end', fill=INK))
    f.add(T(fx(tb) + 12, yA + 34, 'ebollizione della', 12, 'start'), T(fx(tb) + 12, yA + 49, f'soluzione (≈ {num_it(tb)} °C)', 12, 'start'))
    f.add(*legend(f, X0 + 18, Y1 + 18, [('solvente puro', C1), ('soluzione', C2)]))
    return f.svg()

CRIO_XA = 0.92                      # frazione molare del solvente (come nella figura della lezione)
def crio_models():
    R, T0 = 8.314, 273.15
    pl = lambda c: 0.6113 * math.exp(45054 / R * (1 / T0 - 1 / (c + T0)))   # liquido (anche sottoraffreddato)
    pi_ = lambda c: 0.6113 * math.exp(51059 / R * (1 / T0 - 1 / (c + T0)))  # ghiaccio
    ps = lambda c: CRIO_XA * pl(c)                                          # soluzione (Raoult)
    return pl, pi_, ps

def svg_crioscopia():
    """Figura 68.2 — abbassamento crioscopico (curve da Clausius–Clapeyron, x_A = 0,92)."""
    f = Fig(700, 410, 'Abbassamento crioscopico: curve della fase solida, del solvente puro e della soluzione')
    X0, X1, Y0, Y1 = 84, 650, 340, 30
    fx = lambda c: X0 + (c + 14) / 18 * (X1 - X0)
    fy = lambda p: Y0 - (p - 0.15) / 0.70 * (Y0 - Y1)
    f.add(*axes(f, X0, X1, Y0, Y1, [-14, -12, -10, -8, -6, -4, -2, 0, 2, 4], [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8], fx, fy,
                'temperatura (°C)', 'tensione di vapore (kPa)', xfmt=lambda v: str(v).replace('-', '−'), yfmt=lambda v: num_it(v)))
    fp, fi, fs = crio_models()
    tc = crossing(fs, fi, -14, -0.5)
    f.add(curve(fi, -14, 1, fx, fy, C3, 2.4), curve(fp, -14, 4, fx, fy, C1, 2.4), curve(fs, -14, 4, fx, fy, C2, 2.4))
    for c, p, col in ((0, fp(0), C1), (tc, fi(tc), C2)):
        f.add(L(fx(c), fy(p), fx(c), Y0, col, 1.6, dash='2 4'))
        f.add(f'<circle cx="{fx(c):.1f}" cy="{fy(p):.1f}" r="5" fill="{col}" stroke="#fff" stroke-width="2"/>')
    ya = fy(0.20)
    m = f.mk(INK, 6)
    f.add(L(fx(tc) + 1, ya, fx(0) - 1, ya, INK, 1.6, end=m, start=m))
    f.add(T((fx(tc) + fx(0)) / 2, ya - 9, SUB('ΔT', 'cr') + ' &gt; 0', 13, weight=700, raw=True))
    f.add(T(fx(-0.6), fy(0.80), 'congelamento del', 12, 'end'), T(fx(-0.6), fy(0.80) + 15, 'solvente puro (0 °C)', 12, 'end'))
    f.add(L(fx(-0.5), fy(0.80) + 20, fx(0) - 3, fy(fp(0)) - 8, INK2, 1))
    f.add(T(fx(tc) - 10, fy(0.50), 'congelamento della', 12, 'end'), T(fx(tc) - 10, fy(0.50) + 15, f'soluzione (≈ {num_it(tc)} °C)', 12, 'end'))
    f.add(L(fx(tc) - 8, fy(0.50) + 20, fx(tc) - 2, fy(fi(tc)) - 8, INK2, 1))
    f.add(*legend(f, X0 + 18, Y1 + 18, [('solvente puro (liquido)', C1), ('soluzione', C2), ('solido (ghiaccio)', C3)]))
    return f.svg()

def svg_osmosi_U():
    """Figura 68.3 — osmosi in un tubo a U con membrana semipermeabile."""
    f = Fig(720, 440, 'Osmosi in un contenitore a U con membrana semipermeabile')
    WL, WR, IL, IR = 170, 410, 250, 330          # pareti esterne e interne
    TOP, BOT = 60, 300
    lvL, lvR = 112, 176                           # livelli finali (sinistra più alta)
    liq = (f'M{WL},{lvL} H{IL} V{BOT} A40,32 0 0 0 {IR},{BOT} V{lvR} H{WR} V{BOT} A120,96 0 0 1 {WL},{BOT} Z')
    f.add(f'<path d="{liq}" fill="#dbe8f5"/>')
    f.add(f'<path d="M{WL},{TOP - 10} V{BOT} A120,96 0 0 0 {WR},{BOT} V{TOP - 10}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    f.add(f'<path d="M{IL},{TOP - 10} V{BOT} A40,32 0 0 0 {IR},{BOT} V{TOP - 10}" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    pid = uid('hatch')
    f.defs.append(f'<pattern id="{pid}" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                  f'<line x1="0" y1="0" x2="0" y2="6" stroke="{INK}" stroke-width="2"/></pattern>')
    f.add(f'<rect x="284" y="333" width="12" height="62" fill="url(#{pid})" stroke="{INK}" stroke-width="1"/>')
    import random
    rnd = random.Random(5)
    small = []
    def inside(x, y):
        if y <= BOT:
            return (WL + 8 < x < IL - 8 and y > lvL + 8) or (IR + 8 < x < WR - 8 and y > lvR + 8)
        out = ((x - 290) / 120) ** 2 + ((y - BOT) / 96) ** 2 < 0.80
        inn = ((x - 290) / 40) ** 2 + ((y - BOT) / 32) ** 2 > 1.6
        return out and inn and abs(x - 290) > 12
    def scatter(n, xa, xb, ya, yb, avoid=()):
        k = 0
        while k < n:
            x, y = rnd.uniform(xa, xb), rnd.uniform(ya, yb)
            if inside(x, y) and all((x - a) ** 2 + (y - b) ** 2 > 196 for a, b in small + list(avoid)):
                small.append((x, y)); k += 1
    big = [(192, 150), (226, 205), (200, 262), (232, 128), (214, 330), (246, 352)]
    scatter(14, 180, 240, lvL + 10, 292, big)
    scatter(9, 340, 400, lvR + 10, 292)
    scatter(5, 190, 278, 312, 376, big)
    scatter(4, 302, 390, 312, 376)
    for x, y in small:
        f.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#222"/>')
    for x, y in big:
        f.add(f'<circle cx="{x}" cy="{y}" r="8" fill="#3f8f45" stroke="#24592a" stroke-width="1"/>')
    m, mr, mb = f.mk(INK, 6), f.mk(C2, 7), f.mk(C1, 7)
    f.add(L(372, 372, 210, 372, C2, 4, end=mr))
    f.add(L(IL - 4, lvR, WL + 4, lvR, INK2, 1.6, dash='6 4'), T(210, lvR + 16, 'livello iniziale', 10, fill=INK2))
    f.add(L(140, lvL + 2, 140, lvR - 2, INK, 1.5, end=m, start=m), T(132, (lvL + lvR) / 2 + 4, 'dislivello', 12, 'end', weight=600))
    f.add(L(210, 34, 210, lvL - 6, C1, 3.4, end=mb), T(224, 54, 'π', 18, 'start', weight=700, fill=C1))
    f.add(T(92, 238, 'soluzione', 12, 'middle', weight=600), T(92, 254, '(solvente + soluto)', 12, 'middle'))
    f.add(T(470, 238, 'solvente puro', 12, 'middle', weight=600))
    f.add(L(300, 380, 420, 404, INK2, 1), T(426, 408, 'membrana semipermeabile', 12, 'start', weight=600))
    f.add(f'<rect x="500" y="56" width="196" height="76" rx="9" fill="#fff" stroke="{GRIDC}"/>')
    f.add(T(514, 76, 'legenda', 11, 'start', weight=700, fill=INK2))
    f.add('<circle cx="522" cy="96" r="3.2" fill="#222"/>', T(536, 100, 'particella di solvente', 12, 'start'))
    f.add('<circle cx="522" cy="118" r="8" fill="#3f8f45" stroke="#24592a" stroke-width="1"/>', T(536, 122, 'particella di soluto', 12, 'start'))
    f.add(T(600, 168, 'freccia rossa: flusso di solvente', 11, 'middle', fill=INK2), T(600, 183, 'attraverso la membrana', 11, 'middle', fill=INK2),
          T(600, 205, 'π: pressione da applicare', 11, 'middle', fill=INK2), T(600, 220, 'per impedire il dislivello', 11, 'middle', fill=INK2))
    return f.svg()

def svg_tonicita():
    """Figura 68.5 — tonicità e forma della cellula."""
    f = Fig(780, 330, 'Tonicità: cellula in soluzione isotonica, ipertonica e ipotonica')
    m, mr, mb = f.mk(INK, 6), f.mk(C2, 7), f.mk(C1, 7)
    panels = [('soluzione isotonica', 'flusso bilanciato:', 'la cellula mantiene la forma', 'π interna = π esterna'),
              ('soluzione ipertonica', 'l’acqua esce:', 'la cellula si comprime', 'π esterna > π interna'),
              ('soluzione ipotonica', 'l’acqua entra:', 'la cellula si gonfia', 'π esterna < π interna')]
    for k, (title, c1, c2, rel) in enumerate(panels):
        x0 = 14 + k * 256
        cx, cy = x0 + 120, 138
        f.add(f'<rect x="{x0}" y="40" width="240" height="196" rx="14" fill="#eef4fa" stroke="#d3e1ef"/>')
        f.add(T(cx, 26, title, 13, weight=700))
        if k == 0:
            f.add(f'<circle cx="{cx}" cy="{cy}" r="52" fill="#f7e7e7" stroke="#8c3b3b" stroke-width="3"/>')
            f.add(L(cx, 52, cx, cy - 60, INK, 2, end=m), L(cx, cy + 58, cx, 228, INK, 2, end=m))
        elif k == 1:
            pts = []
            for i in range(48):
                a = 2 * math.pi * i / 48
                rr = 36 + 5 * math.cos(6 * a) + 2 * math.sin(3 * a)
                pts.append((cx + rr * math.cos(a), cy - rr * math.sin(a)))
            f.add(poly(pts, '#8c3b3b', 3, fill='#f2dede', close=True))
            f.add(L(cx, cy - 46, cx, 54, C2, 3.4, end=mr))
        else:
            f.add(f'<circle cx="{cx}" cy="{cy}" r="66" fill="#fbeeee" stroke="#8c3b3b" stroke-width="3"/>')
            f.add(L(cx, 232, cx, cy + 74, C1, 3.4, end=mb))
        f.add(T(cx, cy + 5, 'cellula', 12, fill='#8c3b3b', weight=600))
        f.add(T(cx, 260, c1, 12, weight=600), T(cx, 276, c2, 12), T(cx, 304, rel, 12, fill=INK2, italic=True))
    return f.svg()

# ================================================================ LEZIONE 14 — stato solido
def P3(x, y, z, ox, oy, S):
    """Proiezione obliqua delle celle cubiche: x a destra, y in alto, z verso l'osservatore
    (in basso a sinistra). Il vertice nascosto è l'origine, come nelle macro TikZ della dispensa."""
    return ox + S * (x - 0.45 * z), oy - S * (y - 0.32 * z)

def depth(x, y, z):
    return 0.45 * x + 0.32 * y + z        # valori grandi = in primo piano

def cell_edges(ox, oy, S, color='#5d584f'):
    V = lambda a: P3(*a, ox, oy, S)
    s = []
    for a, b in (((0, 0, 0), (1, 0, 0)), ((0, 0, 0), (0, 1, 0)), ((0, 0, 0), (0, 0, 1))):
        s.append(L(*V(a), *V(b), color, 1.1, dash='5 4'))
    for a, b in (((1, 0, 0), (1, 1, 0)), ((1, 1, 0), (0, 1, 0)), ((1, 0, 0), (1, 0, 1)), ((1, 0, 1), (0, 0, 1)),
                 ((0, 1, 0), (0, 1, 1)), ((0, 1, 1), (0, 0, 1)), ((1, 1, 0), (1, 1, 1)), ((1, 1, 1), (1, 0, 1)),
                 ((0, 1, 1), (1, 1, 1))):
        s.append(L(*V(a), *V(b), color, 1.3))
    return s

CORNERS = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
FACES = [(0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5), (0.5, 0.5, 1), (0.5, 1, 0.5), (1, 0.5, 0.5)]
EDGES = [(0.5, a, b) for a in (0, 1) for b in (0, 1)] + [(a, 0.5, b) for a in (0, 1) for b in (0, 1)] + [(a, b, 0.5) for a in (0, 1) for b in (0, 1)]

def atoms(fig, items, ox, oy, S):
    """items: lista di ((x,y,z), raggio_px, colore); disegno dal fondo al primo piano."""
    return [fig.ball(*P3(*pos, ox, oy, S), r, col) for pos, r, col in sorted(items, key=lambda it: depth(*it[0]))]

def leader(x1, y1, x2, y2):
    return L(x1, y1, x2, y2, '#8a847a', 1)

def arrowmk(fig, color, w):
    """Marcatore la cui punta resta di ~15 px qualunque sia lo spessore della linea."""
    return fig.mk(color, round(15 / w, 2))

def svg_silice():
    """Figura 71.1 — tetraedro [SiO4], vetro (rete amorfa), quarzo (rete ordinata)."""
    f = Fig(900, 330, 'Il tetraedro di silice e i due ordinamenti: rete amorfa del vetro e rete ordinata del quarzo')
    ex, ey, ez = (0.335, -0.036), (-0.427, 0.884), (0.836, 0.466)
    n = (-0.938, -0.186, 0.281)
    S, cx, cy = 92, 130, 150
    pr = lambda x, y, z: (cx + S * (x * ex[0] + y * ey[0] + z * ez[0]), cy - S * (x * ex[1] + y * ey[1] + z * ez[1]))
    Os = [(-.55, -.55, .55), (-.55, .55, -.55), (.55, .55, .55), (.55, -.55, -.55)]
    for o in Os:
        f.add(L(cx, cy, *pr(*o), '#8b8b95', 4))
    items = [((0, 0, 0), 25, AT['silic'])] + [(o, 17, AT['ossig']) for o in Os]
    for pos, r, col in sorted(items, key=lambda it: -(it[0][0] * n[0] + it[0][1] * n[1] + it[0][2] * n[2])):
        f.add(f.ball(*pr(*pos), r, col))
    f.add(T(cx - 2, cy + 6, 'Si', 13, weight=700, fill='#ffffff'))
    for o, (dx, dy) in zip(Os, ((26, -6), (-28, 2), (26, 10), (26, -2))):
        x, y = pr(*o)
        f.add(T(x + dx, y + dy + 4, 'O', 13, weight=700, fill=AT['ossig']))
    f.add(T(130, 286, '(a) tetraedro di silice [SiO₄]:', 12, weight=700), T(130, 302, 'Si al centro, 4 O a carica negativa', 12))
    S2, ox, oy = 70, 296, 250
    q = lambda x, y: (ox + S2 * x, oy - S2 * y)
    Si = [(0.0, 0.0), (1.5, 0.35), (0.6, 1.3), (2.3, 1.6), (3.1, 0.5), (2.6, 2.6), (1.2, 2.5), (3.6, 1.9), (4.0, 0.8)]
    links = [((0, 0), (0.75, 0.18), (1.5, 0.35)), ((0, 0), (0.3, 0.65), (0.6, 1.3)), ((1.5, 0.35), (1.05, 0.83), (0.6, 1.3)),
             ((1.5, 0.35), (2.3, 0.43), (3.1, 0.5)), ((1.5, 0.35), (1.9, 0.98), (2.3, 1.6)), ((0.6, 1.3), (1.45, 1.45), (2.3, 1.6)),
             ((0.6, 1.3), (0.9, 1.9), (1.2, 2.5)), ((2.3, 1.6), (2.45, 2.1), (2.6, 2.6)), ((2.3, 1.6), (2.7, 1.05), (3.1, 0.5)),
             ((2.3, 1.6), (2.95, 1.75), (3.6, 1.9)), ((3.1, 0.5), (3.55, 0.65), (4.0, 0.8)), ((2.6, 2.6), (1.9, 2.55), (1.2, 2.5)),
             ((2.6, 2.6), (3.1, 2.25), (3.6, 1.9))]
    for a, m_, b in links:
        f.add(poly([q(*a), q(*m_), q(*b)], '#9a9aa4', 2))
    f.add(L(*q(1.5, 0.35), *q(0.6, 1.3), REPU, 2.2, dash='6 4'), L(*q(2.3, 1.6), *q(2.6, 2.6), REPU, 2.2, dash='6 4'))
    for x, y in Si:
        f.add(f.ball(*q(x, y), 11, AT['silic']))
    for a, m_, b in links:
        f.add(f.ball(*q(*m_), 7, AT['ossig']))
    xd1, yd1 = q(0.88, 0.72)
    f.add(T(xd1 - 8, yd1 + 6, SUB('d', '1', 10), 15, 'end', weight=700, fill=REPU, raw=True))
    xd2, yd2 = q(2.45, 2.1)
    f.add(T(xd2 + 26, yd2 + 14, SUB('d', '2', 10), 15, 'start', weight=700, fill=REPU, raw=True))
    f.add(T(436, 286, '(b) vetro: rete amorfa', 12, weight=700), T(436, 302, '(ordine a corto raggio)', 12))
    S3, ox3, oy3 = 70, 636, 250
    r3 = lambda x, y: (ox3 + S3 * x, oy3 - S3 * y)
    for i in range(3):
        for j in range(3):
            if i < 2: f.add(L(*r3(1.3 * i, 1.3 * j), *r3(1.3 * i + 1.3, 1.3 * j), '#9a9aa4', 2))
            if j < 2: f.add(L(*r3(1.3 * i, 1.3 * j), *r3(1.3 * i, 1.3 * j + 1.3), '#9a9aa4', 2))
    f.add(L(*r3(-0.32, 0), *r3(-0.32, 1.3), ATTR, 2.2, dash='6 4'), L(*r3(1.62, 0), *r3(1.62, 1.3), ATTR, 2.2, dash='6 4'))
    for i in range(3):
        for j in range(3):
            f.add(f.ball(*r3(1.3 * i, 1.3 * j), 11, AT['silic']))
    for i in range(3):
        for j in range(3):
            if i < 2: f.add(f.ball(*r3(1.3 * i + 0.65, 1.3 * j), 7, AT['ossig']))
            if j < 2: f.add(f.ball(*r3(1.3 * i, 1.3 * j + 0.65), 7, AT['ossig']))
    xa, ya = r3(-0.32, 0.65); f.add(T(xa - 10, ya + 5, 'd', 15, 'end', weight=700, fill=ATTR, italic=True))
    xb, yb = r3(1.62, 0.65); f.add(T(xb + 10, yb + 5, 'd', 15, 'start', weight=700, fill=ATTR, italic=True))
    f.add(T(727, 286, '(c) quarzo: rete ordinata', 12, weight=700), T(727, 302, '(periodicità a lungo raggio)', 12))
    f.add(f.ball(676, 28, 9, AT['silic']), T(691, 32, 'Si', 12, 'start'), f.ball(736, 28, 6, AT['ossig']), T(748, 32, 'O', 12, 'start'))
    return f.svg()

def svg_reticoli_cubici():
    """Figura 72.1 — celle SC, BCC, FCC."""
    f = Fig(800, 330, 'I tre reticoli cubici: semplice, a corpo centrato, a facce centrate')
    S = 120
    col = AT['generico']
    specs = [('(a) cubico semplice (SC)', 'N = 8·⅛ = 1', [(c, 17, col) for c in CORNERS]),
             ('(b) cubico a corpo centrato (BCC)', 'N = 8·⅛ + 1 = 2', [(c, 14, col) for c in CORNERS] + [((0.5, 0.5, 0.5), 22, col)]),
             ('(c) cubico a facce centrate (FCC)', 'N = 8·⅛ + 6·½ = 4', [(c, 13, col) for c in CORNERS] + [(p, 17, col) for p in FACES])]
    for k, (t1, t2, items) in enumerate(specs):
        cxp = 135 + k * 265
        ox, oy = cxp - 0.275 * S, 196
        f.add(*cell_edges(ox, oy, S))
        f.add(*atoms(f, items, ox, oy, S))
        f.add(T(cxp, 284, t1, 12.5, weight=700), T(cxp, 302, t2, 12.5))
    f.add(T(400, 324, 'gli atomi hanno raggio definito e lasciano vuoti interstiziali; N = atomi che appartengono alla cella', 11.5, fill=INK2))
    return f.svg()

def svg_pirite():
    """Figura 72.2 — pirite FeS2: cella e pesi di condivisione."""
    f = Fig(860, 380, 'Struttura della pirite FeS2 e conteggio degli atomi per cella unitaria')
    S, ox, oy = 150, 118, 232
    u = 0.38
    Ss = [(a, b, c) for a in (u, 1 - u) for b in (u, 1 - u) for c in (u, 1 - u)]
    items = [(c, 13, AT['ferro']) for c in CORNERS] + [(p, 16, AT['ferro']) for p in FACES] + [(s, 10, AT['solf']) for s in Ss]
    f.add(*cell_edges(ox, oy, S))
    f.add(*atoms(f, items, ox, oy, S))
    xf, yf = P3(0, 1, 0, ox, oy, S)
    f.add(leader(xf - 12, yf - 8, xf - 40, yf - 26), T(xf - 44, yf - 28, 'Fe', 14, 'end', weight=700, fill=AT['ferro']))
    xs, ys = P3(1 - u, 1 - u, 1 - u, ox, oy, S)
    f.add(leader(xs + 9, ys - 4, ox + S + 40, oy - 0.62 * S), T(ox + S + 44, oy - 0.62 * S + 5, 'S', 14, 'start', weight=700, fill='#a87700'))
    f.add(T(150, 322, '(a) cella unitaria della pirite:', 12, weight=700), T(150, 338, 'Fe (blu) in posizioni FCC,', 12), T(150, 354, 'S (giallo) negli 8 siti interstiziali', 12))
    g, x0, y0 = 50, 400, 54
    for i in range(3):
        f.add(L(x0 + i * g, y0, x0 + i * g, y0 + 2 * g, '#a59e92', 1.4), L(x0, y0 + i * g, x0 + 2 * g, y0 + i * g, '#a59e92', 1.4))
    f.add(f.ball(x0 + g, y0 + g, 10, AT['ferro']), T(x0 + g + 18, y0 + g - 12, '⅛', 15, 'start', weight=700))
    f.add(T(x0 + g, y0 + 2 * g + 24, 'atomo di vertice: condiviso da 8 celle', 12), T(x0 + g, y0 + 2 * g + 40, '(4 nel piano + 4 fuori dal piano)', 12, fill=INK2))
    x1 = 660
    f.add(f'<rect x="{x1}" y="{y0 + g / 2}" width="{2 * g}" height="{g}" fill="none" stroke="#a59e92" stroke-width="1.4"/>',
          L(x1 + g, y0 + g / 2, x1 + g, y0 + 1.5 * g, '#a59e92', 1.4))
    f.add(f.ball(x1 + g, y0 + g, 10, AT['ferro']), T(x1 + g + 16, y0 + g - 14, '½', 15, 'start', weight=700))
    f.add(T(x1 + g, y0 + 2 * g + 24, 'atomo di faccia: condiviso', 12), T(x1 + g, y0 + 2 * g + 40, 'da 2 celle adiacenti', 12, fill=INK2))
    f.add(f'<rect x="380" y="214" width="460" height="74" rx="10" fill="#f6f2ea" stroke="{GRIDC}"/>')
    f.add(T(610, 240, 'N(Fe) = 8·⅛ + 6·½ = 1 + 3 = 4;    N(S) = 8', 13, weight=600))
    f.add(T(610, 266, 'Fe : S = 4 : 8 = 1 : 2  ⇒  FeS₂', 13, weight=700))
    f.add(T(610, 318, 'alla lavagna: «8(Fe)·1/8 + 6·1/2 = 1 + 3 = 4 (Fe)»', 11.5, fill=INK2, italic=True))
    return f.svg()

def svg_nacl():
    """Figura 73.1 — NaCl: cella con coordinazione 6:6 e piano reticolare."""
    f = Fig(880, 380, 'Struttura del cloruro di sodio NaCl: reticolo cubico con coordinazione ottaedrica 6:6')
    S, ox, oy = 142, 110, 232
    c = (0.5, 0.5, 0.5)
    items = [(q, 14, AT['anion']) for q in CORNERS] + [(q, 18, AT['anion']) for q in FACES] + \
            [(q, 10, AT['cation']) for q in EDGES] + [(c, 12, AT['cation'])]
    f.add(*cell_edges(ox, oy, S))
    # legami di coordinazione dietro al Na+ centrale, poi atomi e legami anteriori
    back = [p for p in FACES if depth(*p) <= depth(*c)]
    front = [p for p in FACES if depth(*p) > depth(*c)]
    for p in back:
        f.add(L(*P3(*c, ox, oy, S), *P3(*p, ox, oy, S), '#55514a', 3))
    f.add(*atoms(f, [it for it in items if depth(*it[0]) <= depth(*c)], ox, oy, S))
    for p in front:
        f.add(L(*P3(*c, ox, oy, S), *P3(*p, ox, oy, S), '#55514a', 3))
    f.add(*atoms(f, [it for it in items if depth(*it[0]) > depth(*c)], ox, oy, S))
    xn, yn = P3(*c, ox, oy, S)
    f.add(leader(xn + 10, yn - 12, ox + S + 34, oy - 0.95 * S), T(ox + S + 38, oy - 0.95 * S + 4, 'Na⁺ centrale', 13, 'start', weight=700, fill='#1f6b3e'))
    xc, yc = P3(0, 1, 0, ox, oy, S)
    f.add(leader(xc - 12, yc - 8, xc - 40, yc - 26), T(xc - 44, yc - 28, 'Cl⁻', 14, 'end', weight=700, fill='#4b3aa6'))
    f.add(T(150, 330, '(a) cella unitaria: il Na⁺ centrale è circondato', 12, weight=700), T(150, 346, 'da 6 Cl⁻ lungo ±x, ±y, ±z (NC = 6)', 12))
    g, x0, y0 = 54, 448, 74
    for i in range(7):
        for j in range(4):
            if i < 6: f.add(L(x0 + i * g, y0 + j * g, x0 + (i + 1) * g, y0 + j * g, '#d2cbbd', 1.2))
            if j < 3: f.add(L(x0 + i * g, y0 + j * g, x0 + i * g, y0 + (j + 1) * g, '#d2cbbd', 1.2))
    ci, cj = 3, 1
    for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        f.add(L(x0 + ci * g, y0 + cj * g, x0 + (ci + di) * g, y0 + (cj + dj) * g, INK, 1.6, dash='4 3'))
    for i in range(7):
        for j in range(4):
            na = (i + j) % 2 == 1
            f.add(f.ball(x0 + i * g, y0 + j * g, 13 if na else 18, AT['cation'] if na else AT['anion']))
    f.add(f'<circle cx="{x0 + ci * g}" cy="{y0 + cj * g}" r="{g * 0.62:.1f}" fill="none" stroke="{INK}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    f.add(f.ball(478, 300, 10, AT['cation']), T(494, 304, 'Na⁺', 12, 'start'), f.ball(546, 300, 13, AT['anion']), T(565, 304, 'Cl⁻', 12, 'start'))
    f.add(T(610, 330, '(b) piano reticolare: alternanza 1:1 lungo ogni direzione', 12, weight=700),
          T(610, 346, '(nel piano ogni ione ha 4 primi vicini; nello spazio NC = 6)', 12, fill=INK2))
    return f.svg()

def svg_rapporto_raggi():
    """Figura 73.2 — criterio del rapporto dei raggi (tangenza esatta)."""
    f = Fig(820, 330, 'Criterio del rapporto dei raggi: numero di coordinazione 3, 4 e 6')
    R = 40
    cases = [(130, 2 / math.sqrt(3) - 1, (90, 210, 330), '(a) catione molto più piccolo', 'r₊/r₋ ≪ 1  ⇒  NC = 3'),
             (380, math.sqrt(2) - 1, (45, 135, 225, 315), '(b) raggi più confrontabili', 'r₊/r₋ < 1  ⇒  NC = 4 (es. ZnS)'),
             (655, 1.0, (0, 60, 120, 180, 240, 300), '(c) raggi sostanzialmente uguali', 'r₊/r₋ ≈ 1  ⇒  NC = 6')]
    for cx, ratio, angs, t1, t2 in cases:
        cy, r = 140, R * ratio
        for a in angs:
            f.add(f.ball(cx + (R + r) * math.cos(math.radians(a)), cy - (R + r) * math.sin(math.radians(a)), R, AT['anion']))
        f.add(f.ball(cx, cy, r, AT['cation']))
        f.add(T(cx, 284, t1, 12.5, weight=700), T(cx, 302, t2, 12.5))
    f.add(f.ball(28, 26, 8, AT['cation']), T(42, 30, 'catione', 12, 'start'), f.ball(118, 26, 10, AT['anion']), T(134, 30, 'anione', 12, 'start'))
    return f.svg()

def svg_li2o():
    """Figura 73.3 — Li2O: O2- in FCC, Li+ negli otto siti interstiziali."""
    f = Fig(780, 380, 'Ossido di litio Li2O: anioni ossigeno in posizioni FCC e cationi litio nei siti interstiziali')
    S, ox, oy = 152, 120, 236
    lis = [(a, b, c) for a in (0.25, 0.75) for b in (0.25, 0.75) for c in (0.25, 0.75)]
    li0 = (0.75, 0.25, 0.75)                 # Li+ nell'ottante anteriore in basso a destra
    tet = ((1, 0, 1), (0.5, 0.5, 1), (0.5, 0, 0.5), (1, 0.5, 0.5))
    items = [(q, 14, AT['ossig']) for q in CORNERS] + [(q, 18, AT['ossig']) for q in FACES] + [(q, 10, AT['liti']) for q in lis]
    f.add(*cell_edges(ox, oy, S))
    f.add(*atoms(f, items, ox, oy, S))
    for q in tet:
        f.add(L(*P3(*li0, ox, oy, S), *P3(*q, ox, oy, S), INK, 1.8, dash='5 3'))
    f.add(f.ball(*P3(*li0, ox, oy, S), 10, AT['liti']))
    xo, yo = P3(0, 1, 0, ox, oy, S)
    f.add(leader(xo - 12, yo - 8, xo - 40, yo - 26), T(xo - 44, yo - 28, 'O²⁻', 14, 'end', weight=700, fill='#a32d2d'))
    xl, yl = P3(*li0, ox, oy, S)
    f.add(leader(xl + 9, yl + 7, xl + 112, yl + 60), T(xl + 116, yl + 66, 'Li⁺', 14, 'start', weight=700, fill='#1f75b5'))
    f.add(T(430, 112, 'NC(Li⁺) = 4: ogni Li⁺ coordina 4 O²⁻', 13, 'start', weight=600),
          T(430, 132, '(tetraedro tratteggiato)', 12, 'start', fill=INK2),
          T(430, 164, 'NC(O²⁻) = 8', 13, 'start', weight=600))
    f.add(f'<rect x="420" y="200" width="330" height="62" rx="10" fill="#f6f2ea" stroke="{GRIDC}"/>')
    f.add(T(585, 224, 'N(O) = 8·⅛ + 6·½ = 4;   N(Li) = 8', 13, weight=600), T(585, 248, 'Li : O = 2 : 1  ⇒  Li₂O', 13, weight=700))
    f.add(T(390, 350, 'cella cubica: O²⁻ ai vertici e alle facce (FCC), un Li⁺ in ciascun ottante del cubo', 12, fill=INK2))
    return f.svg()

def svg_madelung_nacl():
    """Figura 74.1 — intorni di uno ione Cl- nel piano xy del reticolo NaCl."""
    f = Fig(880, 470, 'Intorni di uno ione cloruro nel reticolo NaCl: attrazioni e repulsioni con i vicini successivi')
    cx, cy, d = 250, 232, 82
    rC, rN, rc = 24, 16, 19
    mA, mR = arrowmk(f, ATTR, 3), arrowmk(f, REPU, 3)
    f.add(L(cx, cy, cx + d, cy, '#7a756c', 1.4, dash='5 4'), L(cx, cy, cx + d, cy - d, '#7a756c', 1.4, dash='5 4'), L(cx, cy, cx + 2 * d, cy, '#7a756c', 1.4, dash='5 4'))
    nas = [(d, 0), (-d, 0), (0, d), (0, -d)]
    cls = [(d, d), (-d, d), (d, -d), (-d, -d), (2 * d, 0), (-2 * d, 0), (0, 2 * d), (0, -2 * d)]
    f.add(f.ball(cx, cy, rC, AT['anion']))
    for x, y in nas:
        f.add(f.ball(cx + x, cy + y, rN, AT['cation']))
    for x, y in cls:
        f.add(f.ball(cx + x, cy + y, rc, AT['anion']))
    for x, y in nas:
        ux, uy = x / d, y / d
        f.add(L(cx + ux * (d - rN - 3), cy + uy * (d - rN - 3), cx + ux * (rC + 5), cy + uy * (rC + 5), ATTR, 3, end=mA))
    for x, y in cls:
        ln = math.hypot(x, y); ux, uy = x / ln, y / ln
        f.add(L(cx + ux * (ln + rc + 4), cy + uy * (ln + rc + 4), cx + ux * (ln + rc + 30), cy + uy * (ln + rc + 30), REPU, 3, end=mR))
    f.add(T(cx + d / 2, cy + 20, 'd', 15, weight=700, italic=True),
          T(cx + d / 2 + 14, cy - d / 2 + 14, '√2 d', 15, 'start', weight=700, italic=True),
          T(cx + 1.5 * d, cy - 10, '2d', 15, weight=700, italic=True))
    f.add(T(cx - 28, cy + 40, 'Cl⁻', 13, 'end', weight=700, fill='#4b3aa6'))
    f.add(leader(cx + d + 10, cy + 13, cx + d + 30, cy + 44), T(cx + d + 32, cy + 56, 'Na⁺', 13, 'start', weight=700, fill='#1f6b3e'))
    f.add(f'<rect x="14" y="14" width="204" height="58" rx="9" fill="#fff" stroke="{GRIDC}"/>')
    f.add(L(26, 34, 58, 34, ATTR, 3, end=mA), T(66, 38, 'attrazione (segni opposti)', 12, 'start'))
    f.add(L(26, 56, 58, 56, REPU, 3, end=mR), T(66, 60, 'repulsione (stesso segno)', 12, 'start'))
    x0, y = 520, 92
    blocks = [('primi vicini:', ['6 Na⁺ a distanza d — attrattivi'], ATTR),
              ('secondi vicini:', ['12 Cl⁻ a √2 d — repulsivi', '(lungo la diagonale delle facce)'], REPU),
              ('terzi vicini (fuori dal piano):', ['8 Na⁺ a √3 d — attrattivi'], ATTR),
              ('quarti vicini:', ['6 Cl⁻ a 2d — repulsivi'], REPU)]
    for head, lines, col in blocks:
        f.add(f'<rect x="{x0 - 14}" y="{y - 11}" width="5" height="{16 + 16 * len(lines)}" rx="2" fill="{col}"/>')
        f.add(T(x0, y, head, 12.5, 'start', weight=700))
        for k, ln in enumerate(lines):
            f.add(T(x0, y + 17 * (k + 1), ln, 12.5, 'start', fill=INK if k == 0 else INK2))
        y += 17 * (len(lines) + 1) + 14
    f.add(T(x0 - 14, y + 4, 'sezione sul piano xy: 4 + 4 + 4 ioni visibili;', 12, 'start', fill=INK2),
          T(x0 - 14, y + 20, 'nello spazio: 6, 12, 8 e 6', 12, 'start', fill=INK2))
    f.add(f'<rect x="{x0 - 14}" y="{y + 40}" width="352" height="74" rx="10" fill="#f6f2ea" stroke="{GRIDC}"/>')
    f.add(T(x0 + 162, y + 60, 'serie di Madelung (primi termini):', 12, fill=INK2),
          T(x0 + 162, y + 81, 'α = 6 − 12/√2 + 8/√3 − 6/2 + 24/√5 − …', 13.5, weight=700),
          T(x0 + 162, y + 103, 'α(NaCl) ≈ 1,748', 14, weight=700))
    return f.svg()

def svg_born_haber():
    """Figura 74.2 — ciclo di Born–Haber per NaCl(s) da Na(g) e Cl(g) (livelli in scala)."""
    f = Fig(860, 440, 'Ciclo di Born-Haber per la formazione di NaCl solido da sodio e cloro gassosi')
    k = 0.28
    y0 = 52 + 496 * k
    lev = {'ion': y0 - 496 * k, 'ioni': y0 - 147 * k, 'zero': y0, 'sol': y0 + 640 * k}
    mI = f.mk(INK, 6)
    mR, mA, mB = arrowmk(f, REPU, 3.2), arrowmk(f, ATTR, 3.2), arrowmk(f, C1, 6)
    f.add(L(70, lev['sol'] + 30, 70, 24, INK, 1.6, end=mI), T(44, (lev['sol'] + 24) / 2, 'Energia', 13, weight=700, extra=f' transform="rotate(-90 44 {(lev["sol"] + 24) / 2})"'))
    for key in lev:
        f.add(L(84, lev[key], 820, lev[key], '#8f897e', 2))
    f.add(T(96, lev['ion'] - 8, 'Na⁺(g) + e⁻ + Cl(g)', 13, 'start', weight=600),
          T(96, lev['ioni'] - 8, 'Na⁺(g) + Cl⁻(g)', 13, 'start', weight=600),
          T(96, lev['zero'] - 8, 'Na(g) + Cl(g)', 13, 'start', weight=600),
          T(96, lev['zero'] + 18, '(livello di riferimento, E = 0)', 12, 'start', fill=INK2),
          T(96, lev['sol'] - 8, 'NaCl(s): reticolo cristallino (NC = 6)', 13, 'start', weight=600))
    f.add(L(300, lev['zero'] - 2, 300, lev['ion'] + 4, REPU, 3.2, end=mR))
    f.add(T(312, lev['ion'] + 42, '+' + SUB('E′', 'ion') + ': energia di', 12.5, 'start', raw=True), T(312, lev['ion'] + 58, 'ionizzazione del sodio', 12.5, 'start'))
    f.add(L(500, lev['ion'] + 2, 500, lev['ioni'] - 4, ATTR, 3.2, end=mA))
    f.add(T(512, lev['ion'] + 20, SUB('E¹', 'AE') + ' &lt; 0: affinità elettronica', 12.5, 'start', raw=True), T(512, lev['ion'] + 36, 'del cloro (energia rilasciata)', 12.5, 'start'))
    f.add(L(700, lev['ioni'] + 2, 700, lev['sol'] - 4, C1, 6, end=mB))
    yl = (lev['zero'] + lev['sol']) / 2
    f.add(T(684, yl - 10, SUB('E', 'ret') + ' &lt; 0: condensazione', 12.5, 'end', raw=True), T(684, yl + 6, 'nel reticolo (energia', 12.5, 'end'), T(684, yl + 22, 'reticolare, v. Figura 74.1)', 12.5, 'end'))
    f.add(T(452, lev['sol'] + 34, 'il livello più basso è quello del solido: il reticolo cristallino è energeticamente', 12, fill=INK2),
          T(452, lev['sol'] + 50, 'favorito rispetto a molecole discrete Na⁺Cl⁻; ' + SUB('E', 'ret') + ' separa gli ioni gassosi dal solido', 12, fill=INK2, raw=True))
    return f.svg()

def svg_fragilita():
    """Figura 75.1 — scorrimento di un piano reticolare: attrazione → repulsione → frattura."""
    f = Fig(860, 560, 'Meccanismo microscopico della fragilità dei solidi ionici: lo scorrimento porta a contatto ioni dello stesso segno')
    g, r = 52, 15
    mA, mR, mI = arrowmk(f, ATTR, 2.2), arrowmk(f, REPU, 2.2), f.mk(INK, 7)
    def rows(x0, ybase, shift):
        s = []
        for j in range(4):
            for i in range(7):
                ii = i + (shift if j >= 2 else 0)
                if ii > 6:
                    continue
                cat = (i + j) % 2 == 1
                s.append(f.ball(x0 + ii * g, ybase - j * g, r if cat else r + 3, AT['cation'] if cat else AT['anion']))
        return s
    x0, yb = 70, 230
    yp = yb - 1.5 * g
    f.add(L(x0 - 30, yp, x0 + 6 * g + 30, yp, '#77716a', 1.6, dash='7 5'), T(x0 + 6 * g + 40, yp + 4, 'piano di scorrimento', 12, 'start', fill=INK2))
    f.add(*rows(x0, yb, 0))
    for i in range(7):
        x = x0 + i * g
        f.add(L(x, yp + 15, x, yp + 4, ATTR, 2.2, end=mA), L(x, yp - 15, x, yp - 4, ATTR, 2.2, end=mA))
    f.add(L(x0 + 10, yb - 3 * g - 40, x0 + 150, yb - 3 * g - 40, INK, 2.6, end=mI), T(x0 + 80, yb - 3 * g - 50, 'sforzo di taglio', 12, weight=600))
    f.add(f.ball(660, 60, 10, AT['cation']), T(676, 64, 'Na⁺ (catione)', 12, 'start'), f.ball(660, 86, 13, AT['anion']), T(676, 90, 'Cl⁻ (anione)', 12, 'start'))
    f.add(T(400, 262, '(a) prima dello scorrimento: ioni di segno opposto affacciati lungo il piano ⇒ attrazione', 12.5, weight=700))
    yb2 = 500
    yp2 = yb2 - 1.5 * g
    f.add(L(x0 - 30, yp2, x0 + 6 * g + 20, yp2, '#77716a', 1.6, dash='7 5'))
    f.add(*rows(x0, yb2, 1))
    for i in range(1, 7):
        x = x0 + i * g
        f.add(L(x, yp2 + 5, x, yp2 + 17, REPU, 2.2, end=mR), L(x, yp2 - 5, x, yp2 - 17, REPU, 2.2, end=mR))
    zz = [(x0 + 6.35 * g + k * 7, yp2 + (5 if k % 2 else -5)) for k in range(12)]
    f.add(poly(zz, REPU, 2.6), T(zz[-1][0] + 10, yp2 - 2, 'frattura', 12.5, 'start', weight=700, fill=REPU), T(zz[-1][0] + 10, yp2 + 14, 'fragile', 12.5, 'start', weight=700, fill=REPU))
    f.add(L(x0 + 60, yb2 - 3 * g - 40, x0 + 170, yb2 - 3 * g - 40, INK, 2.6, end=mI), T(x0 + 115, yb2 - 3 * g - 50, 'slittamento di una posizione', 12, weight=600))
    f.add(T(400, 532, '(b) dopo lo scorrimento: ioni dello stesso segno affacciati ⇒ repulsione ⇒ rottura improvvisa', 12.5, weight=700))
    f.add(T(700, 330, 'nei metalli gli elettroni liberi', 12, fill=INK2), T(700, 346, 'fanno da cuscinetto e compensano', 12, fill=INK2),
          T(700, 362, 'le repulsioni: lo slittamento è', 12, fill=INK2), T(700, 378, 'possibile senza frattura (plastico)', 12, fill=INK2))
    return f.svg()

def hexagon(cx, cy, R, rot=90):
    return [(cx + R * math.cos(math.radians(rot + 60 * k)), cy - R * math.sin(math.radians(rot + 60 * k))) for k in range(6)]

def svg_diamante_grafite():
    """Figura 76.1 — diamante (sp3) e grafite (sp2)."""
    f = Fig(880, 390, 'Le due forme del carbonio: diamante con ibridazione sp3 e grafite con ibridazione sp2')
    S, ox, oy = 150, 118, 236
    inter = [(0.25, 0.25, 0.25), (0.75, 0.75, 0.25), (0.75, 0.25, 0.75), (0.25, 0.75, 0.75)]
    nb = {(0.75, 0.25, 0.75): ((1, 0, 1), (0.5, 0, 0.5), (1, 0.5, 0.5), (0.5, 0.5, 1)),
          (0.25, 0.75, 0.75): ((0, 1, 1), (0.5, 1, 0.5), (0, 0.5, 0.5), (0.5, 0.5, 1))}
    items = [(q, 12, AT['carbo']) for q in CORNERS] + [(q, 15, AT['carbo']) for q in FACES] + [(q, 15, AT['carbo']) for q in inter]
    f.add(*cell_edges(ox, oy, S))
    bonds = [(a, b) for a, bs in nb.items() for b in bs]
    # ordina atomi e legami insieme per profondità (legame = media degli estremi)
    objs = [(depth(*pos), 'a', (pos, r, col)) for pos, r, col in items] + \
           [((depth(*a) + depth(*b)) / 2 - 0.01, 'b', (a, b)) for a, b in bonds]
    for _, kind, o in sorted(objs, key=lambda z: z[0]):
        if kind == 'a':
            f.add(f.ball(*P3(*o[0], ox, oy, S), o[1], o[2]))
        else:
            f.add(L(*P3(*o[0], ox, oy, S), *P3(*o[1], ox, oy, S), '#6b6b75', 4))
    xc, yc = P3(0, 1, 0, ox, oy, S)
    f.add(leader(xc - 12, yc - 8, xc - 40, yc - 26), T(xc - 44, yc - 28, 'C', 14, 'end', weight=700))
    f.add(T(160, 342, '(a) diamante: C in posizioni FCC + 4 siti interstiziali;', 12, weight=700), T(160, 358, 'ibridazione sp³, NC = 4 (tetraedrica)', 12))
    R, sc = 0.32 * 70, 70
    ox2, oy2 = 470, 262
    centers = lambda dx, dy: [(ox2 + dx + sc * (0.554 * i + 0.277 * (j % 2)), oy2 - dy - sc * 0.48 * j) for i in range(4) for j in range(4)]
    for cxh, cyh in centers(0.28 * sc, 0.55 * sc):
        f.add(poly(hexagon(cxh, cyh, R), '#b7b7c0', 1.4, close=True))
    fx0, fy0 = ox2 + sc * (0.554 * 3) + R * math.cos(math.radians(30)), oy2 - R * math.sin(math.radians(30))
    for dy in (0, sc * 0.96):
        f.add(L(fx0, fy0 - dy, fx0 + 0.28 * sc, fy0 - dy - 0.55 * sc, '#77716a', 1.3, dash='4 3'))
    for cxh, cyh in centers(0, 0):
        f.add(poly(hexagon(cxh, cyh, R), AT['carbo'], 2.4, close=True))
    hx, hy = ox2 + sc * 0.277, oy2 - sc * 0.48
    hexo = hexagon(hx, hy, R)
    f.add(poly(hexo, AT['arancio'], 3.2, close=True))
    for x, y in hexo:
        f.add(f.ball(x, y, 4.5, AT['arancio']))
    mv = arrowmk(f, REPU, 2)
    xv, yv = fx0 + 14, fy0 - 0.48 * sc
    f.add(L(xv, yv, xv + 0.28 * sc, yv - 0.55 * sc, REPU, 2, end=mv, start=mv))
    f.add(T(xv + 0.28 * sc + 8, yv - 0.3 * sc, 'van der Waals', 12, 'start', weight=600, fill=REPU), T(xv + 0.28 * sc + 8, yv - 0.3 * sc + 15, '(tra i piani)', 12, 'start', fill=REPU))
    mi = f.mk(INK, 7)
    f.add(L(ox2 - 10, oy2 + 40, ox2 + sc * 1.6, oy2 + 40, INK, 2.4, end=mi), T(ox2 + sc * 0.78, oy2 + 60, 'slittamento dei piani', 12, weight=600))
    f.add(leader(hx - R - 2, hy - 4, ox2 - 20, oy2 - sc * 2.0), T(ox2 - 22, oy2 - sc * 2.0 - 36, 'elettroni π delocalizzati', 12, 'start', weight=600, fill='#9a5a0a'),
          T(ox2 - 22, oy2 - sc * 2.0 - 20, '(1 per atomo: sull’anello e su tutto il piano)', 12, 'start', fill='#9a5a0a'))
    f.add(T(660, 342, '(b) grafite: piani esagonali sp² sfalsati;', 12, weight=700), T(660, 358, 'covalente nel piano, debole (van der Waals) tra i piani', 12))
    return f.svg()

def c60_edges():
    """Vertici e spigoli del C60 (icosaedro troncato), ruotato con un pentagono verso l'osservatore."""
    ph = (1 + 5 ** 0.5) / 2
    base = [(0, 1, 3 * ph), (1, 2 + ph, 2 * ph), (ph, 2, ph ** 3)]
    V = set()
    for a, b, c in base:
        for sa in (1, -1):
            for sb in (1, -1):
                for sc_ in (1, -1):
                    v = (a * sa, b * sb, c * sc_)
                    for k in range(3):
                        V.add(tuple(round(x, 9) for x in (v[k % 3], v[(k + 1) % 3], v[(k + 2) % 3])))
    V = list(V)
    E = [(i, j) for i in range(len(V)) for j in range(i + 1, len(V)) if abs(math.dist(V[i], V[j]) - 2) < 1e-6]
    ax = (0, 1, ph); nrm = math.sqrt(sum(c * c for c in ax)); ax = tuple(c / nrm for c in ax)
    z = (0, 0, 1)
    v = (ax[1] * z[2] - ax[2] * z[1], ax[2] * z[0] - ax[0] * z[2], ax[0] * z[1] - ax[1] * z[0])
    s = math.sqrt(sum(c * c for c in v)); cth = sum(a * b for a, b in zip(ax, z))
    k = tuple(c / s for c in v)
    def rot(p):
        kxp = (k[1] * p[2] - k[2] * p[1], k[2] * p[0] - k[0] * p[2], k[0] * p[1] - k[1] * p[0])
        kdp = sum(a * b for a, b in zip(k, p))
        return tuple(p[i] * cth + kxp[i] * s + k[i] * kdp * (1 - cth) for i in range(3))
    return [rot(p) for p in V], E

def svg_nanocarbonio():
    """Figura 76.2 — grafene, fullerene C60 (proiezione reale dell'icosaedro troncato), nanotubo."""
    f = Fig(900, 380, 'Le nanostrutture del carbonio sp2: grafene, fullerene C60 e nanotubo')
    R, sc, ox, oy = 0.30 * 66, 66, 40, 250
    for i in range(5):
        for j in range(4):
            f.add(poly(hexagon(ox + sc * (0.52 * i + 0.26 * (j % 2)), oy - sc * 0.45 * j, R), AT['carbo'], 2.2, close=True))
    hx, hy = ox + sc * 1.04, oy - sc * 0.90
    hexo = hexagon(hx, hy, R)
    f.add(poly(hexo, AT['arancio'], 3, close=True))
    for x, y in hexo:
        f.add(f.ball(x, y, 4, AT['arancio']))
    f.add(T(122, 106, 'spessore atomico (~1 Å),', 12, fill=INK2), T(122, 122, 'altissima conducibilità nel piano', 12, fill=INK2))
    f.add(T(122, 300, '(a) grafene: singolo piano', 12, weight=700), T(122, 316, 'di esagoni di C (sp²)', 12))
    W, E = c60_edges()
    cx, cy, Rb = 440, 168, 100
    rmax = max(math.hypot(p[0], p[1]) for p in W)
    pr = lambda p: (cx + Rb * p[0] / rmax, cy - Rb * p[1] / rmax)
    f.add(f'<circle cx="{cx}" cy="{cy}" r="{Rb + 6}" fill="#f4f2ee" stroke="{AT["carbo"]}" stroke-width="2.4"/>')
    for i, j in E:
        if W[i][2] + W[j][2] < 0:
            f.add(L(*pr(W[i]), *pr(W[j]), '#d3cfd6', 1.2))
    for i, j in E:
        if W[i][2] + W[j][2] >= 0:
            f.add(L(*pr(W[i]), *pr(W[j]), AT['carbo'], 2.2))
    for i in sorted(range(len(W)), key=lambda i: -W[i][2])[:5]:
        f.add(f.ball(*pr(W[i]), 4.5, AT['arancio']))
    f.add(T(cx, cy + Rb + 30, 'C₆₀', 14, weight=700))
    f.add(T(cx, 318, '(b) fullerene: esagoni + pentagoni', 12, weight=700), T(cx, 334, '(pallone da calcio; C sp²)', 12),
          T(cx, 356, '60 atomi di C; facile funzionalizzazione', 12, fill=INK2))
    cx3, top3, bot3, rx, ry = 690, 70, 250, 62, 18
    cid = uid('clip')
    f.defs.append(f'<clipPath id="{cid}"><path d="M{cx3 - rx},{top3} V{bot3} A{rx},{ry} 0 0 0 {cx3 + rx},{bot3} V{top3} Z"/></clipPath>')
    R3, sc3 = 0.28 * 66, 66
    hexes = [poly(hexagon(cx3 - rx + sc3 * (0.485 * i + 0.242 * (j % 2)), bot3 + 20 - sc3 * 0.42 * j, R3), AT['carbo'], 1.8, close=True)
             for i in range(-2, 4) for j in range(0, 8)]
    f.add(f'<g clip-path="url(#{cid})">' + ''.join(hexes) + '</g>')
    f.add(L(cx3 - rx, top3, cx3 - rx, bot3, AT['carbo'], 3), L(cx3 + rx, top3, cx3 + rx, bot3, AT['carbo'], 3))
    f.add(f'<ellipse cx="{cx3}" cy="{top3}" rx="{rx}" ry="{ry}" fill="#f4f2ee" stroke="{AT["carbo"]}" stroke-width="3"/>')
    f.add(f'<path d="M{cx3 - rx},{bot3} A{rx},{ry} 0 0 0 {cx3 + rx},{bot3}" fill="none" stroke="{AT["carbo"]}" stroke-width="3"/>')
    md, mb = f.mk(INK, 6), arrowmk(f, C1, 3.4)
    f.add(L(cx3 - rx + 6, top3 - 32, cx3 + rx - 6, top3 - 32, INK, 1.6, end=md, start=md), T(cx3, top3 - 42, 'diametro ≈ 1 nm', 12, weight=600))
    f.add(L(cx3 + rx + 26, bot3 - 30, cx3 + rx + 26, top3 + 30, C1, 3.4, end=mb))
    f.add(T(cx3 + rx + 40, 136, 'lungo l’asse:', 12, 'start', weight=600, fill=C1), T(cx3 + rx + 40, 152, 'conducibilità e', 12, 'start', fill=C1),
          T(cx3 + rx + 40, 168, 'resistenza', 12, 'start', fill=C1), T(cx3 + rx + 40, 184, 'meccanica', 12, 'start', fill=C1))
    f.add(T(cx3 + 30, 300, '(c) nanotubo: foglio di grafene', 12, weight=700), T(cx3 + 30, 316, 'arrotolato in cilindro cavo', 12))
    return f.svg()

# ================================================================ diagrammi già presenti (ex Mermaid)
SOFT = {'blue': ('#eef2f7', '#3b5b92'), 'leaf': ('#f6f2ea', '#bfb6a3'), 'amber': ('#f8f0e2', '#a86f2d'), 'green': ('#eef4ee', '#4a7c59')}

def node(cx, y, w, lines, style='leaf', lh=16, pad=10, shape='rect'):
    """Riquadro con testo centrato; la prima riga in grassetto. Restituisce (svg, y_basso)."""
    fill, stroke = SOFT[style]
    h = pad * 2 + lh * len(lines) - 4
    if shape == 'rect':
        s = f'<rect x="{cx - w / 2:.1f}" y="{y:.1f}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{stroke}" stroke-width="1.6"/>'
    else:                                    # nodo decisionale (esagono)
        k = 14
        pts = [(cx - w / 2, y + h / 2), (cx - w / 2 + k, y), (cx + w / 2 - k, y), (cx + w / 2, y + h / 2), (cx + w / 2 - k, y + h), (cx - w / 2 + k, y + h)]
        s = poly(pts, stroke, 1.6, fill=fill, close=True)
    for i, ln in enumerate(lines):
        s += T(cx, y + pad + 11 + i * lh, ln, 12.5 if i == 0 else 11.5, weight=700 if i == 0 else None, fill=INK if i == 0 else INK2)
    return s, y + h

def elbow(x1, y1, x2, y2, mk, ymid=None):
    ym = ymid if ymid is not None else (y1 + y2) / 2
    return (f'<path d="M{x1:.1f},{y1:.1f} V{ym:.1f} H{x2:.1f} V{y2 - 1:.1f}" fill="none" stroke="#8a8f98" '
            f'stroke-width="1.6" marker-end="url(#{mk})"/>')

def svg_classificazione_materia():
    """Figura 1.1 — albero di classificazione della materia."""
    f = Fig(1012, 350, 'Albero di classificazione della materia')
    mk = f.mk('#8a8f98', 6)
    X = {'ELA': 70, 'ELM': 210, 'COM': 350, 'COI': 490, 'MO': 616, 'ME': 772, 'DC': 932}
    X['EL'] = (X['ELA'] + X['ELM']) / 2; X['CO'] = (X['COM'] + X['COI']) / 2
    X['SP'] = (X['EL'] + X['CO']) / 2; X['MI'] = X['ME']; X['M'] = (X['SP'] + X['MI']) / 2
    Y = {'M': 14, 'SP': 92, 'MI': 92, 'EL': 172, 'CO': 172, 'MO': 172, 'ME': 172, 'DC': 172, 'ELA': 262, 'ELM': 262, 'COM': 262, 'COI': 262}
    spec = {'M': (150, ['Materia'], 'blue'), 'SP': (160, ['Sostanze pure'], 'blue'), 'MI': (150, ['Miscele'], 'blue'),
            'EL': (130, ['Elementi'], 'blue'), 'CO': (130, ['Composti'], 'blue'),
            'ELA': (130, ['Elementi atomici', 'gas nobili, metalli'], 'leaf'), 'ELM': (130, ['Elementi molecolari', 'N₂, O₂, S₈, P₄'], 'leaf'),
            'COM': (130, ['Composti molecolari', 'H₂O, CO₂, CH₄'], 'leaf'), 'COI': (130, ['Composti ionici', 'NaCl: reticolo', 'cristallino'], 'leaf'),
            'MO': (146, ['Miscele omogenee', '= soluzioni: aria,', 'leghe, zucchero', 'in acqua'], 'leaf'),
            'ME': (146, ['Miscele eterogenee', 'sabbia, granito,', 'olio e acqua'], 'leaf'),
            'DC': (152, ['Dispersioni colloidali', 'nebbia, fumo,', 'emulsioni, gelatina'], 'leaf')}
    bottom = {}
    for k, (w, lines, st) in spec.items():
        s, yb = node(X[k], Y[k], w, lines, st)
        f.add(s); bottom[k] = yb
    for p, cs in (('M', ('SP', 'MI')), ('SP', ('EL', 'CO')), ('EL', ('ELA', 'ELM')), ('CO', ('COM', 'COI')), ('MI', ('MO', 'ME', 'DC'))):
        for c in cs:
            f.body.insert(0, elbow(X[p], bottom[p], X[c], Y[c], mk))
    return f.svg()

def svg_stati_passaggi():
    """Figura 29.1 — i tre stati e i passaggi di stato."""
    f = Fig(860, 230, 'I tre stati della materia e i passaggi di stato')
    boxes = [(130, ['SOLIDO', 'interazioni ≫ E cinetica', 'forma e volume propri']),
             (430, ['LIQUIDO', 'interazioni ≈ E cinetica', 'volume proprio,', 'forma del recipiente']),
             (730, ['GAS', 'interazioni ≈ 0', 'né forma né volume propri'])]
    for cx, lines in boxes:
        s, yb = node(cx, 40, 200, lines, 'blue')
        f.add(s)
    mR, mB = f.mk(C2, 7), f.mk(C1, 7)
    for xa, xb, up, down in ((232, 328, 'T (fusione)', 'P (solidificazione)'), (532, 628, 'T (evaporazione)', 'P (condensazione)')):
        f.add(L(xa + 4, 78, xb - 6, 78, C2, 2.2, end=mR), T((xa + xb) / 2, 68, up, 11.5, weight=600))
        f.add(L(xb - 4, 112, xa + 6, 112, C1, 2.2, end=mB), T((xa + xb) / 2, 132, down, 11.5, weight=600))
    f.add(T(430, 186, '→  l’energia cinetica (temperatura) spinge verso il gas', 12, fill=C2),
          T(430, 206, '←  le forze intermolecolari (e la pressione) spingono verso il solido', 12, fill=C1))
    return f.svg()

def svg_tipi_interazione():
    """Figura 52.1 — albero dei tipi di interazione."""
    f = Fig(940, 250, 'Albero dei tipi di interazione: forti tra atomi, deboli tra molecole')
    mk = f.mk('#8a8f98', 6)
    X = {'F1': 90, 'F2': 266, 'F3': 442, 'D1': 640, 'D2': 830}
    X['F'] = X['F2']; X['D'] = (X['D1'] + X['D2']) / 2; X['T'] = (X['F'] + X['D']) / 2
    spec = {'T': (200, ['TIPI DI INTERAZIONE'], 'blue', 14), 'F': (190, ['FORTI — tra atomi'], 'blue', 98), 'D': (200, ['DEBOLI — tra molecole'], 'blue', 98),
            'F1': (164, ['Legame covalente', 'polare od omopolare'], 'leaf', 178), 'F2': (164, ['Legame metallico'], 'leaf', 178),
            'F3': (164, ['Legame ionico'], 'leaf', 178), 'D1': (196, ['Forze di van der Waals', 'London, dipolo-dipolo,', 'ione-molecola'], 'leaf', 178),
            'D2': (164, ['Legame a idrogeno'], 'leaf', 178)}
    bottom = {}
    for k, (w, lines, st, y) in spec.items():
        s, yb = node(X[k], y, w, lines, st)
        f.add(s); bottom[k] = (y, yb)
    for p, cs in (('T', ('F', 'D')), ('F', ('F1', 'F2', 'F3')), ('D', ('D1', 'D2'))):
        for c in cs:
            f.body.insert(0, elbow(X[p], bottom[p][1], X[c], bottom[c][0], mk))
    f.add(T((X['T'] + X['F']) / 2 - 6, 70, 'condivisione di carica', 11.5, 'middle', fill=INK2, italic=True))
    return f.svg()

def svg_decisionale():
    """Figura 60.1 — diagramma decisionale delle interazioni intermolecolari."""
    f = Fig(1000, 440, 'Diagramma decisionale delle interazioni intermolecolari')
    mk = f.mk('#8a8f98', 6)
    X = {'D': 110, 'E': 330, 'G': 545, 'I': 640, 'L': 880}
    X['H'] = (X['I'] + X['L']) / 2; X['C'] = (X['D'] + X['E']) / 2; X['F'] = (X['G'] + X['H']) / 2
    X['B'] = (X['C'] + X['F']) / 2; X['A'] = X['B']
    spec = {'A': (210, ['Specie che interagiscono'], 'blue', 'rect', 10),
            'B': (210, ['Sono coinvolti ioni?'], 'amber', 'hex', 76),
            'C': (216, ['Ioni + molecole polari?'], 'amber', 'hex', 162),
            'F': (190, ['Molecole polari?'], 'amber', 'hex', 162),
            'D': (204, ['Forze ione–dipolo', 'es. KBr in H₂O — ~15 kJ/mol'], 'green', 'rect', 256),
            'E': (176, ['Legame ionico', 'es. NaCl, NH₄NO₃'], 'green', 'rect', 256),
            'G': (176, ['Solo forze di London', 'es. Ar(l), I₂(s)'], 'green', 'rect', 256),
            'H': (196, ['H legato a N, O o F?'], 'amber', 'hex', 256),
            'I': (236, ['Forze dipolo–dipolo', 'es. H₂S, CH₃Cl — vdW 2–10 kJ/mol'], 'green', 'rect', 350),
            'L': (228, ['Legame a idrogeno', 'es. H₂O, NH₃, HF — 5–25 kJ/mol'], 'green', 'rect', 350)}
    ybox = {}
    for k, (w, lines, st, shape, y) in spec.items():
        s, yb = node(X[k], y, w, lines, st, shape=shape)
        f.add(s); ybox[k] = (y, yb)
    edges = [('A', 'B', ''), ('B', 'C', 'sì'), ('B', 'F', 'no'), ('C', 'D', 'sì'), ('C', 'E', 'no'),
             ('F', 'G', 'no'), ('F', 'H', 'sì'), ('H', 'I', 'no'), ('H', 'L', 'sì')]
    for p, c, lab in edges:
        y1, y2 = ybox[p][1], ybox[c][0]
        ym = (y1 + y2) / 2
        f.body.insert(0, elbow(X[p], y1, X[c], y2, mk, ym))
        if lab:
            f.add(T(X[c] + (10 if X[c] >= X[p] else -10), ym - 5, lab, 11.5, 'start' if X[c] >= X[p] else 'end', weight=700, fill='#a86f2d'))
    f.add(T(500, 428, 'energie tipiche: van der Waals 2–10 kJ/mol · legami a idrogeno 5–25 kJ/mol · ione–dipolo ~15 kJ/mol', 12, fill=INK2))
    return f.svg()

# ---------------------------------------------------------------- markdown → html
def render_table(rows, cls='table-wrap reveal'):
    def cells(r):
        return [c.strip() for c in r.strip().strip('|').split('|')]
    header = cells(rows[0])
    body_rows = [cells(r) for r in rows[1:] if not re.match(r'^\|[\s:\-|]+\|$', r)]
    th = ''.join(f'<th scope="col">{inline_md(c)}</th>' for c in header)
    trs = ''.join('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in r) + '</tr>' for r in body_rows)
    return f'<div class="{cls}"><table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

BOX_RULES = [
    (r'definizione', 'def', 'Definizione'),
    (r'controesempio', 'counterex', 'Controesempio'),
    (r'esempio', 'ex', 'Esempio'),
    (r'esercizio|testo', 'exercise', 'Esercizio'),
    (r'teorema|proposizione|lemma|corollario', 'thm', 'Teorema'),
    (r'legge|principio|regola|modello|postulato', 'thm', 'Legge'),
    (r'attenzione|avvertenza|errore', 'warn', 'Attenzione'),
    (r'osservazione', 'obs', 'Osservazione'),
    (r'consiglio', 'tip', 'Consiglio del docente'),
    (r'nota|promemoria', 'note', 'Nota'),
]

ICONS = {
 'def': '<path d="M3 2.2 8 1l5 1.2v11L8 12 3 13.2z"/><line x1="8" y1="1" x2="8" y2="12"/>',
 'thm': '<path d="M2.5 13V4M13.5 13V4M2 4h12M2 13h12M4.8 4V2.6h6.4V4"/>',
 'ex': '<path d="M6 2h4M6.5 2v4L3 12.2a1 1 0 0 0 .9 1.4h6.2a1 1 0 0 0 .9-1.4L7.5 6V2"/><path d="M4.8 9.4h6.4"/>',
 'counterex': '<circle cx="8" cy="8" r="5.6"/><line x1="4" y1="12" x2="12" y2="4"/>',
 'obs': '<path d="M1.6 8S4 3.6 8 3.6 14.4 8 14.4 8 12 12.4 8 12.4 1.6 8 1.6 8z"/><circle cx="8" cy="8" r="2"/>',
 'warn': '<path d="M8 2 14.6 13.4H1.4z"/><line x1="8" y1="6.4" x2="8" y2="9.4"/><circle cx="8" cy="11.3" r="0.7" fill="currentColor"/>',
 'tip': '<path d="M8 1.6a4.6 4.6 0 0 0-2.6 8.4c.6.5 1 1.2 1 2h3.2c0-.8.4-1.5 1-2A4.6 4.6 0 0 0 8 1.6z"/><line x1="6.6" y1="14" x2="9.4" y2="14"/>',
 'exercise': '<path d="M3 13.2 2.6 10.6 10.6 2.6l2 2-8 8z"/><line x1="9.6" y1="3.6" x2="11.6" y2="5.6"/>',
 'note': '<circle cx="8" cy="8" r="6"/><line x1="8" y1="7" x2="8" y2="11"/><circle cx="8" cy="5" r="0.8" fill="currentColor"/>',
}

def icon(kind):
    return (f'<svg class="bicon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS.get(kind, ICONS["note"])}</svg>')

def classify_quote(first):
    m = re.match(r'\*\*(.+?)\*\*', first)
    if not m:
        return 'note', 'Nota', None
    bold = m.group(1)
    low = bold.lower()
    for pat, kind, chip in BOX_RULES:
        mk = re.match(pat, low)
        if mk:
            title = bold
            kw = mk.group(0)
            if title.lower().startswith(kw):
                title = title[len(kw):].lstrip(' —-.:')
            return kind, chip, (title or None)
    return 'note', 'Nota', bold

def render_block(lines):
    """lines: lista di stringhe già senza '> '. Ritorna html interno del box."""
    out, buf, mathbuf = [], [], []
    def flush():
        nonlocal buf
        if buf:
            out.append('<p>' + inline_md(' '.join(buf)) + '</p>')
            buf = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            flush(); i += 1; continue
        if ln.startswith('$$'):
            flush()
            if ln.count('$$') >= 2:
                out.append(f'<div class="mathdisp">{ln}</div>')
                i += 1; continue
            mathbuf = [ln]
            i += 1
            while i < len(lines) and lines[i].count('$$') == 0:
                mathbuf.append(lines[i]); i += 1
            if i < len(lines):
                mathbuf.append(lines[i]); i += 1
            out.append('<div class="mathdisp">$$' + esc_inner_math('\n'.join(mathbuf)[2:-2]) + '$$</div>')
            continue
        if ln.startswith('- '):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith('- '):
                items.append(f'<li>{inline_md(lines[i][2:])}</li>'); i += 1
            out.append('<ul>' + ''.join(items) + '</ul>')
            continue
        if re.match(r'\d+\. ', ln):
            flush()
            items = []
            while i < len(lines) and re.match(r'\d+\. ', lines[i]):
                items.append(f'<li>{inline_md(re.sub(r"^\d+\. ", "", lines[i]))}</li>'); i += 1
            out.append('<ol>' + ''.join(items) + '</ol>')
            continue
        if ln.startswith('|'):
            flush()
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            out.append(render_table(rows, 'table-wrap'))
            continue
        buf.append(ln); i += 1
    flush()
    return '\n'.join(out)

def esc_inner_math(s):
    return s  # il testo è già escaped a monte; le entità sono decodificate da MathJax

_fig_counter = [0]
def unique_markers(svg):
    """Rende unici gli id dei marker frecia (ah/ahr/ahg) per ogni SVG."""
    _fig_counter[0] += 1
    n = _fig_counter[0]
    for mid in ('ah', 'ahr', 'ahg'):
        svg = svg.replace(f'id="{mid}"', f'id="{mid}{n}"')
        svg = svg.replace(f'url(#{mid})', f'url(#{mid}{n})')
    return svg

def convert(md):
    lines = md.split('\n')
    out = []
    toc = []           # (level, id, text)
    i = 0
    n = len(lines)
    current_part = None

    def heading_register(level, id_, text):
        nonlocal current_part
        if current_part is None and level >= 2:
            toc.append({'lvl': 1, 'id': 'intro', 'text': 'Introduzione — Copertina e sommario', 'children': []})
            current_part = toc[-1]
        if level == 1:
            toc.append({'lvl': 1, 'id': id_, 'text': text, 'children': []})
            current_part = toc[-1]
        elif level == 2:
            current_part['children'].append({'lvl': 2, 'id': id_, 'text': text, 'children': []})
        else:
            if current_part and current_part['children']:
                current_part['children'][-1]['children'].append({'lvl': 3, 'id': id_, 'text': text})
            elif current_part:
                current_part['children'].append({'lvl': 3, 'id': id_, 'text': text, 'children': []})

    in_svolgimento = False
    sol_buf = []
    first_part = True

    def close_sol():
        nonlocal in_svolgimento, sol_buf
        if in_svolgimento:
            body = '\n'.join(b for b in sol_buf if b)
            out.append('<details class="sol reveal"><summary>Svolgimento</summary>'
                       + body + '</details>')
            in_svolgimento = False; sol_buf = []

    def emit(htmlchunk):
        if in_svolgimento:
            sol_buf.append(htmlchunk)
        else:
            out.append(htmlchunk)

    while i < n:
        line = lines[i]

        # ---- blocchi di codice
        if line.startswith('```'):
            lang = line[3:].strip()
            body = []
            i += 1
            while i < n and not lines[i].startswith('```'):
                body.append(lines[i]); i += 1
            i += 1  # skip closing
            close_sol()
            src = '\n'.join(body)
            svg = None
            if lang == 'latex':
                # --- figure lezioni 13–14 (controllate per prime: alcune contengono parole chiave delle regole successive)
                if 'molecola anfifilica e la Micella' in src: svg = svg_tensioattivi()
                elif 'dieci sali' in src: svg = svg_solubilita_curve()
                elif 'Struttura del benzene' in src: svg = svg_benzene()
                elif 'Soluzioni solide sostituzionali e interstiziali' in src: svg = svg_soluzioni_solide()
                elif 'Innalzamento ebullioscopico' in src: svg = svg_ebullioscopia()
                elif 'Abbassamento crioscopico' in src: svg = svg_crioscopia()
                elif 'Osmosi in un contenitore a U' in src: svg = svg_osmosi_U()
                elif "Tonicita' e forma della cellula" in src: svg = svg_tonicita()
                elif 'tetraedro di silice e i due ordinamenti' in src: svg = svg_silice()
                elif 'I tre reticoli cubici' in src: svg = svg_reticoli_cubici()
                elif 'pirite FeS2 e conteggio' in src: svg = svg_pirite()
                elif 'cloruro di sodio NaCl e coordinazione' in src: svg = svg_nacl()
                elif 'rapporto dei raggi e numero di coordinazione' in src: svg = svg_rapporto_raggi()
                elif 'Ossido di litio Li2O' in src: svg = svg_li2o()
                elif 'Intorni di uno ione Cl-' in src: svg = svg_madelung_nacl()
                elif 'Ciclo di Born-Haber' in src: svg = svg_born_haber()
                elif "fragilita' dei solidi ionici" in src: svg = svg_fragilita()
                elif 'due forme del carbonio' in src: svg = svg_diamante_grafite()
                elif 'nanostrutture del carbonio sp2' in src: svg = svg_nanocarbonio()
                elif 'Isoterme' in src: svg = svg_isoterme()
                elif 'energia potenziale in funzione della distanza internucleare' in src: svg = svg_morse()
                elif 'Bilancio energetico' in src: svg = svg_bilancio()
                elif 'sei casi' in src: svg = svg_sei_casi()
                elif 'Maxwell' in src: svg = svg_maxwell()
                elif 'stati della materia e i passaggi' in src: svg = svg_stati()
                elif 'pressione di vapore' in src: svg = svg_vapore()
                elif 'campo magnetico' in src: svg = svg_radiazioni()
                elif 'Schema a due stati' in src: svg = svg_due_stati()
                elif 'unico recipiente (legge di Dalton)' in src: svg = svg_miscela_dalton()
                elif 'Miscela di due gas a parit' in src: svg = svg_graham_miscela()
                elif 'mediante effusione' in src: svg = svg_effusione()
                elif 'Gas a contatto con un liquido' in src: svg = svg_henry()
                elif 'combinazione minima alla scala' in src: svg = svg_combinazione()
                elif 'composizione percentuale alla formula molecolare' in src: svg = svg_formula_flow()
                # --- figure lezioni 10–12 ---
                elif 'risultante vettoriale dei dipoli' in src: svg = svg_dipoli()
                elif 'a corto raggio nello stato liquido' in src: svg = svg_corto_raggio()
                elif 'piani della grafite' in src: svg = svg_grafite()
                elif 'fase massiva e molecola in superficie' in src: svg = svg_bulk_superficie()
                elif 'a due temperature e soglia' in src: svg = svg_evap_distribuzione()
                elif 'Equilibrio dinamico liquido-vapore' in src: svg = svg_equilibrio_dinamico()
                elif 'angolo di contatto' in src: svg = svg_bagnabilita()
                elif 'Menisco concavo' in src: svg = svg_menisco()
                elif 'tre tubi di diametro decrescente' in src: svg = svg_capillarita()
                elif 'meccanica della viscosit' in src: svg = svg_viscosita()
                elif 'P1 < P2 < P3' in src: svg = svg_solubilita_pressioni()
                elif 'membrana semipermeabile' in src and 'Osmosi' in src: svg = svg_osmosi()
                elif 'in funzione del gruppo' in src: svg = svg_no_gruppi()
                elif 'dai precursori ai sali' in src: svg = svg_famiglie()
                elif 'acido solforico H2SO4' in src: svg = svg_h2so4()
                elif 'tetracloruro di carbonio CCl4' in src: svg = svg_ccl4()
                elif 'Anidride carbonica CO2' in src: svg = svg_co2_strutture()
                elif 'Ammoniaca NH3' in src: svg = svg_nh3()
                elif 'N2 (legame triplo' in src: svg = svg_n2_o2()
                elif 'carbonato CO3(2-) dal sale' in src or 'ione carbonato CO3(2-): struttura' in src: svg = svg_carbonato()
                elif 'limite dello ione nitrato' in src: svg = svg_formule_limite()
                elif 'ione azide' in src: svg = svg_azide()
                elif 'ione solfato SO4' in src: svg = svg_solfato_cf()
                elif 'elettroni nella reazione Fe2O3' in src: svg = svg_semireazioni()
                elif 'procedura di bilanciamento delle reazioni redox' in src: svg = svg_redox_flow()
                elif 'cariche totali (9 e 17)' in src: svg = svg_lavagna_redox()
                elif 'elettronico nella reazione in ambiente basico' in src or 'elettronico nella reazione Cr' in src: svg = svg_staffe_cr()
            elif lang == 'mermaid':
                if 'M[Materia]' in src: svg = svg_classificazione_materia()
                elif 'S["SOLIDO' in src: svg = svg_stati_passaggi()
                elif 'T[TIPI DI INTERAZIONE]' in src: svg = svg_tipi_interazione()
                elif 'A[Specie che interagiscono]' in src: svg = svg_decisionale()
            else:
                if '7s' in src and '2p' in src and '1s' in src and 'mermaid' not in lang: svg = svg_madelung()
                elif 'n = 3' in src and 'n = 1' in src: svg = svg_livelli()
                elif 'AUMENTA' in src: svg = svg_trends()
            if svg:
                emit(f'<figure class="figure reveal">{unique_markers(svg)}</figure>')
            else:
                if lang in ('latex', 'mermaid'):
                    print(f'ATTENZIONE: figura {lang} senza SVG corrispondente:', src.strip().split(chr(10))[0][:80])
                emit(f'<figure class="figure ascii-fig reveal"><pre class="ascii">{esc(src)}</pre></figure>')
            continue

        # ---- titoli
        m = re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            close_sol()
            lvl = len(m.group(1)); text = m.group(2).strip()
            if lvl == 1 and text.startswith('CHIMICA'):
                i += 1; continue
            if lvl >= 2 and (text.startswith('Corso di Chimica Generale')
                             or text.startswith('Università degli Studi')):
                i += 1; continue
            id_ = slug(re.sub(r'\*\*', '', text))
            heading_register(lvl, id_, text)
            if lvl == 1:
                if first_part:
                    emit(f'<section class="parte" id="{id_}">')
                    first_part = False
                else:
                    emit(f'</section><section class="parte" id="{id_}">')
                emit(f'<header class="parte-head"><div class="parte-kicker">Dispensa</div><h1>{inline_md(text)}</h1></header>')
            elif lvl == 2:
                emit(f'<h2 id="{id_}" class="reveal-h">{inline_md(text)}</h2>')
            else:
                emit(f'<h3 id="{id_}" class="reveal-h">{inline_md(text)}</h3>')
            i += 1; continue

        if line.strip() == '---':
            i += 1; continue

        # ---- blockquote → box
        if line.startswith('>'):
            close_sol()
            qlines = []
            while i < n and lines[i].startswith('>'):
                qlines.append(lines[i][1:].lstrip()); i += 1
            first = qlines[0] if qlines else ''
            kind, chip, title = classify_quote(first)
            rest = qlines[1:]
            m = re.match(r'\*\*(.+?)\*\*\s*(.*)$', first)
            first_rest = m.group(2) if m else first
            inner = []
            if first_rest.strip():
                inner.append('<p>' + inline_md(first_rest) + '</p>')
            inner.append(render_block(rest))
            tblock = (f'<div class="box-title">{icon(kind)}<span class="chip">{chip}</span>'
                      + (f'<span class="btitle">{inline_md(title)}</span>' if title else '') + '</div>')
            emit(f'<div class="box box-{kind} reveal">{tblock}{"".join(inner)}</div>')
            continue

        # ---- tabella
        if line.startswith('|'):
            rows = []
            while i < n and lines[i].startswith('|'):
                rows.append(lines[i]); i += 1
            emit(render_table(rows, 'table-wrap' if in_svolgimento else 'table-wrap reveal'))
            continue

        # ---- math display a blocco
        if line.startswith('$$'):
            if line.count('$$') >= 2:
                emit(f'<div class="mathdisp">{inline_md(line)}</div>')
                i += 1; continue
            mlines = [line]; i += 1
            while i < n and not lines[i].rstrip().endswith('$$'):
                mlines.append(lines[i]); i += 1
            if i < n:
                mlines.append(lines[i]); i += 1
            emit('<div class="mathdisp">' + '\n'.join(mlines) + '</div>')
            continue

        # ---- liste
        if re.match(r'^\s*- ', line):
            items, sub = [], []
            while i < n and (re.match(r'^\s*- ', lines[i]) or re.match(r'^\s{2,}\w', lines[i])):
                if re.match(r'^\s*- ', lines[i]):
                    items.append(re.sub(r'^\s*- ', '', lines[i])); i += 1
                else:
                    items[-1] += ' ' + lines[i].strip(); i += 1
            lis = ''.join(f'<li>{inline_md(t)}</li>' for t in items)
            emit(f'<ul class="reveal">{lis}</ul>')
            continue
        if re.match(r'^\s*\d+\. ', line):
            items = []
            while i < n and re.match(r'^\s*\d+\. ', lines[i]):
                t = re.sub(r'^\s*\d+\. ', '', lines[i]); i += 1
                while i < n and re.match(r'^\s{2,}\S', lines[i]) and not re.match(r'^\s*[-\d]', lines[i]):
                    t += ' ' + lines[i].strip(); i += 1
                items.append(t)
            lis = ''.join(f'<li>{inline_md(t)}</li>' for t in items)
            emit(f'<ol class="reveal">{lis}</ol>')
            continue

        # ---- riga vuota
        if not line.strip():
            close_sol_if_soft()
            i += 1; continue

        # ---- paragrafo (accumula fino a riga vuota o blocco)
        para = [line]; i += 1
        while i < n and lines[i].strip() and not re.match(r'^(#|\||>|```|\$\$|- |\d+\. )', lines[i]):
            para.append(lines[i]); i += 1
        ptext = ' '.join(para)
        stripped = ptext.strip()

        mS = re.match(r'\*\*Svolgimento[^*]*\*\*\s*(.*)$', stripped)
        if mS:
            close_sol()
            in_svolgimento = True
            sol_buf = ['<p>' + inline_md(mS.group(1)) + '</p>' if mS.group(1) else '']
            continue

        # paragrafi notevoli
        cls = None
        if re.match(r'\*\*(Esempio|Controesempio)', stripped): cls = 'p-ex'
        elif re.match(r'\*\*(Osservazione|Nota)[^*]*[:.]?\*\*', stripped): cls = 'p-obs'
        elif re.match(r'\*\*(Attenzione|Avvertenza)', stripped): cls = 'p-warn'
        elif re.match(r'^\*(Figura|Spiegazione|Lettura)', stripped): cls = 'caption'
        elif re.match(r'^\*\(', stripped): cls = 'caption'
        elif stripped.startswith('**Da ricordare') or stripped.startswith('**Da notare'): cls = 'p-obs'
        if cls == 'caption':
            close_sol()
            out.append(f'<p class="caption reveal">{inline_md(stripped)}</p>')
            continue
        if in_svolgimento:
            sol_buf.append(f'<p class="{cls}">{inline_md(stripped)}</p>' if cls else f'<p>{inline_md(stripped)}</p>')
            continue
        emit(f'<p class="{cls} reveal-p">{inline_md(stripped)}</p>' if cls else f'<p class="reveal-p">{inline_md(stripped)}</p>')
        continue

    close_sol()
    if not first_part:
        out.append('</section>')
    # collega i riferimenti «Parte N» del sommario alle sezioni
    content = '\n'.join(out)
    for part in toc:
        m = re.match(r'PARTE ([IVX]+)', part['text'])
        if m:
            roman = m.group(1)
            content = content.replace(f'<strong>Parte {roman} —',
                                      f'<a class="partlink" href="#{part["id"]}"><strong>Parte {roman} —', 1)
    # chiudi i link del sommario: aggiunge </a> dopo il </strong> del partlink aperto
    content = re.sub(r'(<a class="partlink" href="#[^"]+"><strong>Parte [IVX]+ — [^<]*</strong>)',
                     r'\1</a>', content)
    return content, toc

def close_sol_if_soft():
    pass  # le soluzioni restano aperte tra paragrafi; chiuse da close_sol()

# ---------------------------------------------------------------- TOC html
ROMANS = ['I','II','III','IV','V','VI','VII','VIII','IX','X','XI','XII']
def build_toc(toc):
    html_toc = ['<nav id="toc" aria-label="Indice della dispensa">']
    html_toc.append('<div class="toc-filter"><input id="tocFilter" type="search" placeholder="Filtra indice…" aria-label="Filtra indice"></div>')
    html_toc.append('<a class="toc-home" href="#top">copertina</a>')
    for pi, part in enumerate(toc):
        pid = part['id']
        label = re.sub(r'\*\*', '', part['text'])
        html_toc.append(f'<details class="toc-group" data-part="{pid}"><summary><span class="tg-title">{label}</span>'
                        '<span class="chev">▾</span></summary><div class="toc-children">')
        for ch in part['children']:
            html_toc.append(f'<a href="#{ch["id"]}" data-target="{ch["id"]}" class="toc-h2">{ch["text"]}</a>')
            for sub in ch.get('children', []):
                html_toc.append(f'<a href="#{sub["id"]}" data-target="{sub["id"]}" class="toc-h3">{sub["text"]}</a>')
        html_toc.append('</div></details>')
    html_toc.append('</nav>')
    return ''.join(html_toc)

# ---------------------------------------------------------------- template
def page(content, toclinks, counts):
    tpl = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chimica_template.html'), encoding='utf-8').read()
    return (tpl.replace('__CONTENT__', content)
               .replace('__TOC__', toclinks)
               .replace('__NPARTI__', str(counts['parti']))
               .replace('__NSEC__', str(counts['sec']))
               .replace('__NFIG__', str(counts['fig']))
               .replace('__NES__', str(counts['box'])))

# ---------------------------------------------------------------- main
md = open(SRC, encoding='utf-8').read()
body, toc = convert(md)
toc_html = build_toc(toc)
counts = {
    'parti': len(toc),
    'sec': sum(1 for p in toc for c in p['children']),
    'fig': body.count('<figure'),
    'box': body.count('class="box box-'),
}
html = page(body, toc_html, counts)
open(OUT, 'w', encoding='utf-8').write(html)
print('OK:', OUT, len(html), 'bytes;', counts)
