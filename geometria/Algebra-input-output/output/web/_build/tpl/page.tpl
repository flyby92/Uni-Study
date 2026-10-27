<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{{TITLE}}</title>
<meta name="description" content="{{SUBTITLE}}">
<meta name="color-scheme" content="light dark">
<script>
(function(){try{var t=JSON.parse(localStorage.getItem('gal:theme'));if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t);}catch(e){}document.documentElement.classList.add('js');})();
</script>
<style>{{FONTS}}</style>
<style>{{KATEX_CSS}}</style>
<style>{{CSS}}</style>
<noscript><style>.m,.dm{visibility:visible!important}</style></noscript>
</head>
<body>
<svg class="sprite" aria-hidden="true" focusable="false">
<symbol id="i-chev" viewBox="0 0 24 24"><path d="M9 6l6 6-6 6" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5" fill="none" stroke="currentColor" stroke-width="2"/><path d="M16 16l4.5 4.5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></symbol>
<symbol id="i-auto" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 4a8 8 0 0 1 0 16z" fill="currentColor"/></symbol>
<symbol id="i-pin" viewBox="0 0 24 24"><path d="M14.5 3.5l6 6-2.6 1.1-3.6 3.6.6 4.3-1.5 1.5-4-4L4.5 20.9l-1.4-1.4 4.9-4.9-4-4L5.5 9.1l4.3.6 3.6-3.6z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></symbol>
<symbol id="i-eye" viewBox="0 0 24 24"><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" stroke-width="1.9"/></symbol>
<symbol id="i-alert" viewBox="0 0 24 24"><path d="M12 3.5l9.5 16.5h-19z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><path d="M12 10v4.5M12 17.3v.2" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></symbol>
<symbol id="i-info" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="M12 11v6M12 7.6v.2" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round"/></symbol>
<symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-flask" viewBox="0 0 24 24"><path d="M9.5 3.5h5M10.5 3.5v5.2L5 18.2A1.6 1.6 0 0 0 6.4 20.5h11.2a1.6 1.6 0 0 0 1.4-2.3l-5.5-9.5V3.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round"/><path d="M7.6 14.5h8.8" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></symbol>
<symbol id="i-list" viewBox="0 0 24 24"><path d="M9 7h11M9 12h11M9 17h11" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/><circle cx="4.8" cy="7" r="1.3" fill="currentColor"/><circle cx="4.8" cy="12" r="1.3" fill="currentColor"/><circle cx="4.8" cy="17" r="1.3" fill="currentColor"/></symbol>
<symbol id="i-target" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.5" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="12" cy="12" r="1.3" fill="currentColor"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24"><path d="M4 5.5A2 2 0 0 1 6 3.5h13.5v14H6a2 2 0 0 0-2 2zM4 19.5a2 2 0 0 0 2 2h13.5v-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/></symbol>
<symbol id="i-pen" viewBox="0 0 24 24"><path d="M4 20l1-4.5L16 4.5l3.5 3.5-11 11z" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round"/><path d="M13.5 7l3.5 3.5" fill="none" stroke="currentColor" stroke-width="1.9"/></symbol>
<symbol id="i-play" viewBox="0 0 24 24"><path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/></symbol>
<symbol id="i-pause" viewBox="0 0 24 24"><path d="M7.5 5.5h3v13h-3zM13.5 5.5h3v13h-3z" fill="currentColor"/></symbol>
<symbol id="i-reset" viewBox="0 0 24 24"><path d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3M4.5 4.5v4h4" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-kbd" viewBox="0 0 24 24"><rect x="2.5" y="6" width="19" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M6 10h.01M9.5 10h.01M13 10h.01M16.5 10h.01M7.5 14h9" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></symbol>
<symbol id="i-sigma" viewBox="0 0 24 24"><path d="M18 5H6.5l6 7-6 7H18" fill="none" stroke="currentColor" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-up" viewBox="0 0 24 24"><path d="M12 19V5M5.5 11.5L12 5l6.5 6.5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></symbol>
<symbol id="i-axes" viewBox="0 0 32 32"><path d="M9 23V5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M9 23h18" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M9 23l-5.5 5.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/><path d="M9 3.2l-3 4.2h6zM28.8 23l-4.2-3v6z" fill="currentColor"/><path d="M9 23l11-11" fill="none" stroke="var(--brand-v, #b3261e)" stroke-width="2.6" stroke-linecap="round"/><path d="M22.4 9.6l-1.1 5.2-4.1-4.1z" fill="var(--brand-v, #b3261e)"/></symbol>
</svg>

<a class="skip" href="#doc">Vai al contenuto</a>

<aside class="side" id="side" aria-label="Indice della dispensa">
  <div class="side-h">
    <a class="brand" href="#top" data-nav>
      <svg class="brand-ic" aria-hidden="true"><use href="#i-axes"/></svg>
      <span class="brand-tx"><span class="brand-t">{{TITLE}}</span><span class="brand-s">Dispensa del corso</span></span>
    </a>
    <button class="side-x icbtn" id="sideClose" type="button" aria-label="Chiudi l’indice"><svg class="ic" aria-hidden="true"><use href="#i-x"/></svg></button>
  </div>
  <button class="side-search" id="sideSearch" type="button">
    <svg class="ic" aria-hidden="true"><use href="#i-search"/></svg><span>Cerca nella dispensa…</span><kbd>Ctrl K</kbd>
  </button>
  <nav class="side-nav" id="sideNav" aria-label="Capitoli e sezioni">{{TREE}}</nav>
  <div class="side-f">
    <button class="side-help" id="helpBtn" type="button"><svg class="ic" aria-hidden="true"><use href="#i-kbd"/></svg>Scorciatoie da tastiera</button>
  </div>
</aside>
<div class="scrim" id="scrim" hidden></div>

<div class="main" id="main">
  <header class="top" id="topbar">
    <button class="icbtn tb-menu" id="menuBtn" type="button" aria-label="Apri l’indice" aria-controls="side" aria-expanded="false"><svg class="ic" aria-hidden="true"><use href="#i-menu"/></svg></button>
    <nav class="crumbs" id="crumbs" aria-label="Sei qui"></nav>
    <div class="tb-act">
      <button class="tb-btn" id="formBtn" type="button" aria-label="Formulario (F)"><svg class="ic" aria-hidden="true"><use href="#i-sigma"/></svg><span class="tb-l">Formulario</span></button>
      <button class="tb-btn" id="searchBtn" type="button" aria-label="Cerca (Ctrl K)"><svg class="ic" aria-hidden="true"><use href="#i-search"/></svg><span class="tb-l">Cerca</span></button>
      <button class="tb-btn tb-sq" id="themeBtn" type="button" aria-label="Tema"><svg class="ic" aria-hidden="true"><use href="#i-auto"/></svg></button>
    </div>
    <div class="prog" aria-hidden="true"><span id="courseFill" class="course"></span><span id="progFill"></span></div>
  </header>

  <main class="doc" id="doc">
    <header class="hero" id="top">
      <div class="hero-tx">
        <h1 class="hero-t">{{TITLE}}</h1>
        <p class="hero-s">{{SUBTITLE}}</p>
        <ul class="hero-stats" data-x>{{STATS}}</ul>
        <div class="hero-cta" data-x>
          <a class="btn btn-pri" href="#introduzione-il-corso-e-il-suo-metodo" data-nav><svg class="ic" aria-hidden="true"><use href="#i-book"/></svg>Inizia a studiare</a>
          <button class="btn" id="resumeBtn" type="button" hidden><svg class="ic" aria-hidden="true"><use href="#i-play"/></svg><span>Riprendi</span></button>
        </div>
      </div>
      <div class="hero-art" data-x aria-hidden="true"><div id="heroArt"></div><span class="hero-art-k">la base <i>i</i>, <i>j</i>, <i>k</i> e un vettore <i>v</i> · trascina per ruotare</span></div>
    </header>
{{BODY}}
    <footer class="doc-end" data-x>
      <p>Fine della dispensa ({{CHAPS}}).</p>
      <a class="btn" href="#top" data-nav><svg class="ic" aria-hidden="true"><use href="#i-up"/></svg>Torna all’inizio</a>
    </footer>
  </main>
</div>

<div class="ovl" id="search" hidden>
  <div class="srch" role="dialog" aria-modal="true" aria-label="Cerca nella dispensa">
    <div class="srch-h">
      <svg class="ic" aria-hidden="true"><use href="#i-search"/></svg>
      <input id="searchInput" type="search" placeholder="Cerca un concetto, una definizione, un teorema…" autocomplete="off" spellcheck="false" aria-label="Testo da cercare">
      <button class="icbtn" id="searchClose" type="button" aria-label="Chiudi la ricerca"><svg class="ic" aria-hidden="true"><use href="#i-x"/></svg></button>
    </div>
    <div class="srch-f" id="searchFilters" role="group" aria-label="Filtra per tipo">
      <button type="button" data-f="" aria-pressed="true">Tutto</button>
      <button type="button" data-f="h" aria-pressed="false">Sezioni</button>
      <button type="button" data-f="e" aria-pressed="false">Definizioni, teoremi, esempi</button>
      <button type="button" data-f="n" aria-pressed="false">Note del professore</button>
      <button type="button" data-f="q" aria-pressed="false">Domande d’esame</button>
    </div>
    <div class="srch-r" id="searchResults" role="listbox" aria-label="Risultati"></div>
    <div class="srch-k"><span><kbd>↑</kbd><kbd>↓</kbd> scegli</span><span><kbd>Invio</kbd> apri</span><span><kbd>Esc</kbd> chiudi</span></div>
  </div>
</div>

<div class="ovl lbx" id="lightbox" hidden>
  <figure class="lbx-f" role="dialog" aria-modal="true" aria-label="Figura ingrandita">
    <button class="icbtn lbx-x" id="lbxClose" type="button" aria-label="Chiudi"><svg class="ic" aria-hidden="true"><use href="#i-x"/></svg></button>
    <div class="lbx-img"><img id="lbxImg" alt=""></div>
    <figcaption id="lbxCap"></figcaption>
  </figure>
</div>

<div class="ovl" id="formulario" hidden>
  <div class="frm" role="dialog" aria-modal="true" aria-labelledby="formT">
    <div class="frm-h">
      <svg class="ic" aria-hidden="true"><use href="#i-sigma"/></svg>
      <h2 id="formT">Formulario</h2>
      <select id="formChap" aria-label="Mostra un solo capitolo"><option value="">Tutti i capitoli</option></select>
      <button class="icbtn" id="formClose" type="button" aria-label="Chiudi il formulario"><svg class="ic" aria-hidden="true"><use href="#i-x"/></svg></button>
    </div>
    <p class="frm-n">Le formule chiave della dispensa, capitolo per capitolo. Fai clic su una formula per raggiungerla nel testo.</p>
    <div class="frm-b" id="formBody"></div>
  </div>
</div>

<div class="ovl" id="help" hidden>
  <div class="hlp" role="dialog" aria-modal="true" aria-labelledby="helpT">
    <div class="hlp-h"><h2 id="helpT">Scorciatoie da tastiera</h2><button class="icbtn" id="helpClose" type="button" aria-label="Chiudi"><svg class="ic" aria-hidden="true"><use href="#i-x"/></svg></button></div>
    <dl class="hlp-l">
      <dt><kbd>/</kbd> o <kbd>Ctrl</kbd>+<kbd>K</kbd></dt><dd>Cerca nella dispensa</dd>
      <dt><kbd>N</kbd> / <kbd>P</kbd></dt><dd>Sezione successiva / precedente</dd>
      <dt><kbd>F</kbd></dt><dd>Apre il formulario (le formule chiave, capitolo per capitolo)</dd>
      <dt><kbd>T</kbd></dt><dd>Cambia tema (automatico, chiaro, scuro)</dd>
      <dt><kbd>Esc</kbd></dt><dd>Chiude finestre e indice</dd>
    </dl>
    <p class="hlp-n">Passando sopra un riferimento (ad esempio «Teorema 9.4» o «(3.2)») compare un’anteprima. Copiando del testo, le formule vengono copiate in LaTeX.</p>
  </div>
</div>

<div class="pop" id="pop" hidden></div>
<div class="toast" id="toast" role="status" aria-live="polite" hidden></div>

<script type="application/json" id="searchData">{{SEARCH}}</script>
<script type="application/json" id="keyData">{{FORMULE}}</script>
<script>{{KATEX_JS}}</script>
<script>{{APP_JS}}</script>
</body>
</html>
