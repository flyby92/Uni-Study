# Generatore del sito `geometria.html`

Il sito `../geometria.html` (file unico, funziona offline) si **rigenera** dalla dispensa
`../../Dispensa-Definitiva/dispensa_definitiva.md`. Non modificare l'HTML a mano: aggiornare la
dispensa (o questi sorgenti) e rilanciare.

```
python3 build.py                 # scrive ../geometria.html ed esegue i controlli
python3 build.py --out /tmp/x.html   # prova altrove
python3 build.py --no-check      # salta i controlli
```

Solo libreria standard di Python. Nessun accesso alla rete in fase di build.

## Pezzi

- `mdparse.py` — parser Markdown su misura (paragrafi su una riga, `$$…$$` su riga propria,
  liste annidate con righe di continuazione, tabelle, citazioni `>`, blocchi ```mermaid, immagini).
- `build.py` — raggruppa i blocchi in ambienti e produce l'HTML:
  - riquadri da `**Definizione N.M (titolo).**` (e Teorema, Proposizione, Corollario, Lemma,
    Esempio, Esercizio, Osservazione, Costruzione, Procedimento, Principio di induzione);
    estensione del riquadro: regole in `absorb_env`, eccezioni in `ENV_EXTRA`;
  - `*Dimostrazione…*` / `*Spiegazione.*` → dimostrazione comprimibile fino a `\blacksquare`;
  - `*Soluzione.*` dentro Esempio/Esercizio → soluzione comprimibile (modalità esercitazione);
  - `> **📌 Nota del professore…**`, `> **Osservazione N.M**`, `> **Attenzione.**` → riquadri;
  - immagine + `*Figura N.M — …*` → figura con didascalia (SVG incorporato);
  - riferimenti automatici: «Teorema 9.4», «Figura 3.1», «(3.2)», «§3.11», «Capitolo 7»;
  - diagrammi Mermaid → JSON disegnato in pagina da `tpl/diagrams.js`; etichette con formule in
    `DIAGRAM_LABELS` (stesse parole, simboli in TeX);
  - laboratori interattivi: elenco `LABS` (àncora = id di un riquadro/figura, oppure `p:` + inizio
    di un paragrafo) → il codice è in `tpl/widgets.js` (2D) e `tpl/labs3d.js` (3D), registrato in
    `GAL.labs['id']`;
  - indice di ricerca e albero della barra laterale (id dei titoli = gli stessi dell'Indice).
  - formule chiave: ogni formula display con `\boxed{…}` diventa un riquadro «Formula chiave» (classe
    `dm key`) e una voce del **Formulario** (pulsante Σ nella barra in alto, tasto `F`; dati JSON in
    `#keyData`, finestra disegnata da `tpl/app.js`). Le formule del Capitolo 20 (quaderno) sono escluse.
- `checks.py` — controlli di fedeltà: tutte le formule identiche e nello stesso ordine, testo
  identico parola per parola, figure, id unici, link interni con bersaglio, HTML ben annidato.
- `tpl/` — `page.tpl` (scheletro), `style.css`, `app.js` (indice, scroll-spy, ricerca, preferenze,
  formule), `diagrams.js`, `widgets.js`, `labs3d.js`.
- `vendor/katex-0.16.47/dist` — KaTeX (incorporato; le formule si rendono nel browser, prima
  quelle visibili). `fonts/` — Source Serif 4 e Libre Franklin (woff2, sottoinsieme latin).

## Sorgenti della dispensa

`Dispensa-Definitiva/dispensa_definitiva.md` è assemblata da `Dispensa-Definitiva/.build/capitoli/*.md`
(un file per capitolo, Parti incluse; `20_quaderno.md` è il quaderno di esercizi) con
`python3 .build/assemble.py`, che rigenera anche l'Indice. Le figure si rigenerano con
`.build/fig_parte1.py` … `fig_parte6.py` (libreria `figlib.py`).

## Dopo nuove lezioni

1. aggiornare la dispensa (mantenere le convenzioni sopra: numerazione «N.M», didascalie
   `*Figura N.M — …*`, figure in `Dispensa-Definitiva/figure/`);
2. `python3 build.py` e controllare che stampi `CONTROLLI SUPERATI`;
3. se un diagramma Mermaid nuovo contiene simboli (ℝ, 𝕂, v₁…), aggiungere la sua etichetta in
   `DIAGRAM_LABELS`; se serve un laboratorio nuovo, aggiungerlo a `LABS` e a `tpl/*.js`.

## Prove visive

`firefox --headless --no-remote --profile <cartella-vuota> --window-size=1440,900 --screenshot out.png file.html`
(non usare il profilo predefinito). Limiti noti della cattura: con un'àncora `#…` nell'URL gli
elementi fissi escono dall'inquadratura; oltre ~8000 px di altezza compaiono artefatti. Per le
parti profonde conviene una copia di prova che tenga solo il capitolo da esaminare.
