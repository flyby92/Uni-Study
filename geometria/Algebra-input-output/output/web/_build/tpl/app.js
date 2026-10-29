/* Geometria e Algebra Lineare — logica della pagina (indice, scroll-spy, formule, ricerca, preferenze). */
(function () {
  'use strict';
  const GAL = window.GAL = window.GAL || {};
  const root = document.documentElement;
  const doc = document.getElementById('doc');
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const store = {
    get(k, d) { try { const v = localStorage.getItem('gal:' + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem('gal:' + k, JSON.stringify(v)); } catch (e) { /* archiviazione non disponibile */ } }
  };
  GAL.store = store;
  const mqReduce = matchMedia('(prefers-reduced-motion: reduce)');
  const mqNarrow = matchMedia('(max-width: 1080px)');
  const smooth = () => (mqReduce.matches ? 'auto' : 'smooth');
  const topbar = $('#topbar');
  const topOffset = () => (topbar ? topbar.offsetHeight : 54) + 18;
  const listeners = {};
  GAL.on = (ev, f) => { (listeners[ev] = listeners[ev] || []).push(f); };
  GAL.emit = (ev, x) => { (listeners[ev] || []).forEach((f) => { try { f(x); } catch (e) { console.error(e); } }); };

  /* ------------------------------------------------------------------ formule (KaTeX) */
  const KOPT = { throwOnError: false, output: 'html', strict: 'ignore' };
  function renderMath(el) {
    if (el.dataset.k) return;
    const tex = el.textContent;
    try {
      katex.render(tex, el, Object.assign({ displayMode: el.classList.contains('dm') }, KOPT));
    } catch (e) {
      el.textContent = tex;
      el.classList.add('m-err');
    }
    el.dataset.tex = tex;
    el.dataset.k = '1';
    if (el.classList.contains('dm')) queueFit(el);
  }
  GAL.renderMath = renderMath;

  /* formule in display più larghe della colonna: a capo sui \qquad di primo livello, poi scala */
  function splitTop(tex) {
    const parts = [];
    let depth = 0, env = 0, lr = 0, last = 0;
    for (let i = 0; i < tex.length; i++) {
      const c = tex[i];
      if (c === '\\') {
        const rest = tex.slice(i + 1, i + 8);
        const word = (rest.match(/^[a-zA-Z]+/) || [''])[0];
        if (word === 'begin') env++;
        else if (word === 'end') env--;
        else if (word === 'left') lr++;
        else if (word === 'right') lr--;
        else if (word === 'qquad' && depth === 0 && env === 0 && lr === 0) {
          parts.push(tex.slice(last, i));
          last = i + 6;
        }
        i += Math.max(1, word.length);
        continue;
      }
      if (c === '{') depth++;
      else if (c === '}') depth--;
    }
    parts.push(tex.slice(last));
    const out = [];
    for (const p of parts.map((x) => x.trim()).filter(Boolean)) {
      if (out.length && (p.length < 8 || /^\\blacksquare/.test(p))) out[out.length - 1] += '\\qquad ' + p;
      else out.push(p);
    }
    return out;
  }
  const fitQ = new Set();
  let fitRaf = 0;
  function queueFit(el) {
    fitQ.add(el);
    if (!fitRaf) fitRaf = requestAnimationFrame(runFit);
  }
  function runFit() {
    fitRaf = 0;
    const els = Array.from(fitQ).filter((el) => el.isConnected && el.offsetParent !== null);
    fitQ.clear();
    const meas = els.map((el) => {
      let sw = el.scrollWidth;
      const tag = el.querySelector('.tag');
      if (tag) {
        // con l'etichetta (n.m) a destra la formula, centrata, non deve sovrapporsi: serve spazio per due etichette
        let bw = 0;
        el.querySelectorAll('.katex-html > .base').forEach((b) => { bw += b.getBoundingClientRect().width; });
        sw = Math.max(sw, bw + 2 * tag.getBoundingClientRect().width + 12);
      }
      return { el, cw: el.clientWidth, sw };
    });
    let again = false;
    for (const m of meas) {
      const el = m.el;
      if (!m.cw || m.sw <= m.cw + 1) continue;
      const tex = el.dataset.tex || '';
      if (!el.dataset.split && !/\\tag/.test(tex)) {
        const parts = splitTop(tex);
        el.dataset.split = '1';
        if (parts.length > 1) {
          try {
            katex.render('\\begin{gathered}' + parts.join('\\\\[0.35em]') + '\\end{gathered}', el, Object.assign({ displayMode: true }, KOPT));
            fitQ.add(el);
            again = true;
            continue;
          } catch (e) { /* resta su una riga */ }
        }
      }
      const cur = parseFloat(el.style.fontSize) || 1;
      const sc = Math.max(0.68, (m.cw / m.sw) * cur * 0.985);
      el.style.fontSize = sc.toFixed(3) + 'em';
      el.dataset.fit = '1';
    }
    if (again && !fitRaf) fitRaf = requestAnimationFrame(runFit);
  }
  let refitT = 0;
  window.addEventListener('resize', () => {
    clearTimeout(refitT);
    refitT = setTimeout(() => {
      document.querySelectorAll('.dm[data-k]').forEach((el) => { el.style.fontSize = ''; queueFit(el); });
    }, 250);
  });
  GAL.renderIn = (r) => { r.querySelectorAll('.m:not([data-k]), .dm:not([data-k])').forEach(renderMath); };
  GAL.tex = (tex, display) => katex.renderToString(tex, Object.assign({ displayMode: !!display }, KOPT));

  const mathEls = $$('.m, .dm', doc);
  function renderRange(a, b) {
    for (let i = Math.max(0, a), n = Math.min(mathEls.length, b); i < n; i++) renderMath(mathEls[i]);
  }
  function indexAfter(node) {
    let lo = 0, hi = mathEls.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      const el = mathEls[mid];
      const pos = node.compareDocumentPosition(el);
      if (el === node || (pos & Node.DOCUMENT_POSITION_FOLLOWING) || (pos & Node.DOCUMENT_POSITION_CONTAINED_BY)) hi = mid;
      else lo = mid + 1;
    }
    return lo;
  }
  let mio = null;
  if ('IntersectionObserver' in window) {
    mio = new IntersectionObserver((ents) => {
      for (const e of ents) if (e.isIntersecting) { renderMath(e.target); mio.unobserve(e.target); }
    }, { rootMargin: '1600px 0px' });
  }
  let bgIdx = 0;
  const idle = window.requestIdleCallback ? (f) => requestIdleCallback(f, { timeout: 80 }) : (f) => setTimeout(f, 20);
  function bgStep() {
    const t0 = performance.now();
    while (bgIdx < mathEls.length) {
      renderMath(mathEls[bgIdx++]);
      if ((bgIdx & 7) === 0 && performance.now() - t0 > 10) break;
    }
    if (bgIdx < mathEls.length) idle(bgStep);
    else {
      if (mio) mio.disconnect();
      root.classList.add('math-ready');
      scheduleMeasure();
      GAL.emit('mathready');
    }
  }

  /* ------------------------------------------------------------------ indice ad albero */
  const nav = $('#sideNav');
  const items = $$('.t-i', nav);
  const liById = new Map(items.map((li) => [li.dataset.id, li]));
  function setOpen(li, open, manual) {
    if (!li || !li.hasAttribute('data-has')) return;
    // una Parte e un capitolo aperti alla volta: aprendo una voce si chiudono le voci
    // dello stesso livello (mai gli antenati)
    if (open && (li.classList.contains('t-part') || li.classList.contains('t-chapter'))) {
      const kind = li.classList.contains('t-part') ? 't-part' : 't-chapter';
      for (const other of items) {
        if (other !== li && !other.contains(li) && other.classList.contains(kind) && other.classList.contains('open')) {
          other.classList.remove('open');
          const ob = other.querySelector(':scope > .t-row > .t-tog');
          if (ob) ob.setAttribute('aria-expanded', 'false');
          other.dataset.manual = '0';
        }
      }
    }
    li.classList.toggle('open', open);
    const b = li.querySelector(':scope > .t-row > .t-tog');
    if (b) b.setAttribute('aria-expanded', open ? 'true' : 'false');
    if (manual) li.dataset.manual = open ? '1' : '0';
  }
  let navTouched = 0;
  ['wheel', 'touchmove', 'pointerdown'].forEach((ev) => nav.addEventListener(ev, () => { navTouched = Date.now(); }, { passive: true }));
  nav.addEventListener('click', (e) => {
    const tog = e.target.closest('.t-tog');
    if (tog) {
      e.preventDefault();
      const li = tog.closest('.t-i');
      setOpen(li, !li.classList.contains('open'), true);
      return;
    }
    const a = e.target.closest('.t-a');
    if (a) {
      e.preventDefault();
      const li = a.closest('.t-i');
      if (li.hasAttribute('data-has')) setOpen(li, true, true);
      navigate(li.dataset.id);
      if (mqNarrow.matches) closeSide();
    }
  });
  nav.addEventListener('keydown', (e) => {
    const a = e.target.closest('.t-a');
    if (!a) return;
    const li = a.closest('.t-i');
    const visible = $$('.t-a', nav).filter((x) => x.offsetParent !== null && !x.closest('.t-i:not(.open) > .t-kids'));
    const k = visible.indexOf(a);
    if (e.key === 'ArrowDown' && k < visible.length - 1) { e.preventDefault(); visible[k + 1].focus(); }
    else if (e.key === 'ArrowUp' && k > 0) { e.preventDefault(); visible[k - 1].focus(); }
    else if (e.key === 'ArrowRight' && li.hasAttribute('data-has')) { e.preventDefault(); setOpen(li, true, true); }
    else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      if (li.classList.contains('open') && li.hasAttribute('data-has')) setOpen(li, false, true);
      else { const p = li.parentElement.closest('.t-i'); if (p) p.querySelector(':scope > .t-row > .t-a').focus(); }
    }
  });

  /* ------------------------------------------------------------------ navigazione */
  let spyLock = null, spyLockT = 0;
  function flash(el) {
    el.classList.remove('flash');
    void el.offsetWidth;
    el.classList.add('flash');
    setTimeout(() => el.classList.remove('flash'), 1700);
  }
  function openCollapsedAround(el) {
    let c = el.closest('.closed');
    while (c) {
      setCollapsed(c, false);
      c = c.parentElement && c.parentElement.closest('.closed');
    }
  }
  function navigate(id, opts) {
    opts = opts || {};
    const el = document.getElementById(id);
    if (!el) return;
    const i = indexAfter(el);
    renderRange(i - 120, i + 320);
    openCollapsedAround(el);
    const y = el.getBoundingClientRect().top + window.scrollY - topOffset();
    window.scrollTo({ top: Math.max(0, y), behavior: opts.instant ? 'auto' : smooth() });
    if (!opts.noHistory) {
      try { history.pushState(null, '', '#' + id); } catch (e) { /* ignorato */ }
    }
    if (liById.has(id)) { spyLock = id; spyLockT = Date.now(); setActive(id); }
    if (opts.flash !== false && !el.matches('h2, h3, .hero')) flash(el);
    GAL.emit('navigate', id);
  }
  GAL.navigate = navigate;
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || a.closest('#sideNav') || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey) return;
    const id = decodeURIComponent(a.getAttribute('href').slice(1));
    if (!id || !document.getElementById(id)) return;
    e.preventDefault();
    hidePop();
    if (a.closest('.side') && mqNarrow.matches) closeSide();
    navigate(id);
  });
  window.addEventListener('popstate', () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && document.getElementById(id)) navigate(id, { noHistory: true });
  });

  /* ------------------------------------------------------------------ scroll-spy */
  let spy = [];
  let chapters = [];
  let activeId = null, activeChain = [], autoOpened = [];
  function measure() {
    const y0 = window.scrollY;
    spy = [];
    for (const li of items) {
      const el = document.getElementById(li.dataset.id);
      if (el) spy.push({ id: li.dataset.id, li, top: el.getBoundingClientRect().top + y0 });
    }
    spy.sort((a, b) => a.top - b.top);
    chapters = $$('.chap', doc).map((c) => {
      const r = c.getBoundingClientRect();
      return { el: c, top: r.top + y0, bottom: r.bottom + y0 };
    });
  }
  let measureT = 0;
  function scheduleMeasure() {
    clearTimeout(measureT);
    measureT = setTimeout(() => { measure(); onScroll(); }, 140);
  }
  GAL.scheduleMeasure = scheduleMeasure;
  function crumbHtml(li) {
    const a = li.querySelector(':scope > .t-row > .t-a');
    const id = li.dataset.id;
    const n = a.querySelector('.t-n:not(.t-ic)');
    const tx = a.querySelector('.t-tx');
    const isPart = li.classList.contains('t-part');
    const cls = isPart || li.classList.contains('t-chapter') || li.classList.contains('t-intro') ? 'c-chap' : 'c-sec';
    const pre = n && !isPart ? n.textContent + (li.classList.contains('t-chapter') ? '. ' : ' ') : '';
    const body = tx ? tx.innerHTML : '';
    return `<a class="${cls}" href="#${id}">${pre}${body}</a>`;
  }
  const crumbs = $('#crumbs');
  function setActive(id) {
    if (id === activeId) return;
    activeChain.forEach((li) => li.classList.remove('active', 'trail'));
    activeId = id;
    const li = liById.get(id);
    if (!li) { activeChain = []; crumbs.innerHTML = ''; return; }
    const chain = [];
    for (let x = li; x; x = x.parentElement.closest('.t-i')) chain.push(x);
    chain[0].classList.add('active');
    chain.slice(1).forEach((x) => x.classList.add('trail'));
    const toOpen = chain.slice(1);
    if (li.hasAttribute('data-has')) toOpen.unshift(li);
    for (const x of toOpen) {
      if (!x.classList.contains('open')) { setOpen(x, true); x.dataset.auto = '1'; }
    }
    for (const x of autoOpened) {
      if (!toOpen.includes(x) && x.dataset.auto && x.dataset.manual !== '1') { setOpen(x, false); delete x.dataset.auto; }
    }
    autoOpened = toOpen.filter((x) => x.dataset.auto);
    activeChain = chain;
    crumbs.innerHTML = chain.slice().reverse().map(crumbHtml).join('<span class="sep" aria-hidden="true">›</span>');
    setTimeout(() => keepVisible(chain[0]), 340);
    store.set('pos', id);
  }
  function keepVisible(li) {
    if (Date.now() - navTouched < 2000 || li !== activeChain[0]) return;
    const row = li.querySelector(':scope > .t-row');
    const nr = nav.getBoundingClientRect();
    const rr = row.getBoundingClientRect();
    if (rr.top < nr.top + 48 || rr.bottom > nr.bottom - 48) {
      nav.scrollTo({ top: nav.scrollTop + (rr.top - nr.top) - nr.height * 0.32, behavior: smooth() });
    }
  }
  const progFill = $('#progFill');
  const courseFill = $('#courseFill');
  function onScroll() {
    const y = window.scrollY + topOffset() + 6;
    if (spyLock && Date.now() - spyLockT < 1200) {
      // durante lo scorrimento verso un link resta evidenziata la destinazione
    } else {
      spyLock = null;
      let lo = 0, hi = spy.length - 1, best = -1;
      while (lo <= hi) {
        const mid = (lo + hi) >> 1;
        if (spy[mid].top <= y) { best = mid; lo = mid + 1; } else hi = mid - 1;
      }
      setActive(best >= 0 ? spy[best].id : null);
    }
    // avanzamento nel capitolo corrente
    const vh = window.innerHeight;
    const yy = window.scrollY + vh * 0.35;
    let p = 0;
    for (const c of chapters) {
      if (yy >= c.top && yy < c.bottom) { p = (window.scrollY + vh - c.top) / Math.max(1, c.bottom - c.top); break; }
    }
    progFill.style.width = (Math.max(0, Math.min(1, p)) * 100).toFixed(2) + '%';
    // avanzamento nell'intero corso (dal primo all'ultimo capitolo)
    let cp = 0;
    if (chapters.length) {
      const start = chapters[0].top, end = chapters[chapters.length - 1].bottom;
      cp = (yy - start) / Math.max(1, end - start);
    }
    courseFill.style.width = (Math.max(0, Math.min(1, cp)) * 100).toFixed(2) + '%';
  }
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) { ticking = true; requestAnimationFrame(() => { ticking = false; onScroll(); }); }
  }, { passive: true });
  window.addEventListener('resize', scheduleMeasure);
  if ('ResizeObserver' in window) new ResizeObserver(scheduleMeasure).observe(doc);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(scheduleMeasure);

  /* ------------------------------------------------------------------ barra laterale (schermi stretti) */
  const side = $('#side'), scrim = $('#scrim'), menuBtn = $('#menuBtn');
  function openSide() {
    document.body.classList.add('side-open');
    scrim.hidden = false;
    menuBtn.setAttribute('aria-expanded', 'true');
    const a = side.querySelector('.t-i.active > .t-row > .t-a') || side.querySelector('.t-a');
    setTimeout(() => { if (a) { keepVisible(activeChain[0] || a.closest('.t-i')); a.focus({ preventScroll: true }); } }, 320);
  }
  function closeSide() {
    document.body.classList.remove('side-open');
    scrim.hidden = true;
    menuBtn.setAttribute('aria-expanded', 'false');
  }
  menuBtn.addEventListener('click', openSide);
  $('#sideClose').addEventListener('click', closeSide);
  scrim.addEventListener('click', closeSide);

  /* ------------------------------------------------------------------ soluzioni e dimostrazioni */
  function setCollapsed(box, closed) {
    box.classList.toggle('closed', closed);
    const t = box.querySelector(':scope > .sol-tog, :scope > .prf-tog');
    if (t) t.setAttribute('aria-expanded', closed ? 'false' : 'true');
    if (!closed) GAL.renderIn(box);
    scheduleMeasure();
  }
  doc.addEventListener('click', (e) => {
    const t = e.target.closest('.sol-tog, .prf-tog');
    if (!t) return;
    const box = t.parentElement;
    setCollapsed(box, !box.classList.contains('closed'));
  });

  /* ------------------------------------------------------------------ tema */
  const themeBtn = $('#themeBtn');
  const THEMES = { auto: ['#i-auto', 'automatico'], light: ['#i-sun', 'chiaro'], dark: ['#i-moon', 'scuro'] };
  let theme = store.get('theme', 'auto');
  if (!THEMES[theme]) theme = 'auto';
  function applyTheme(announce) {
    if (theme === 'auto') root.removeAttribute('data-theme'); else root.setAttribute('data-theme', theme);
    themeBtn.querySelector('use').setAttribute('href', THEMES[theme][0]);
    themeBtn.setAttribute('aria-label', 'Tema: ' + THEMES[theme][1] + ' (cambia)');
    themeBtn.title = 'Tema: ' + THEMES[theme][1];
    if (announce) toast('Tema ' + THEMES[theme][1]);
    GAL.emit('theme');
  }
  function cycleTheme() {
    theme = theme === 'auto' ? 'light' : theme === 'light' ? 'dark' : 'auto';
    store.set('theme', theme);
    applyTheme(true);
  }
  themeBtn.addEventListener('click', cycleTheme);
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => GAL.emit('theme'));
  applyTheme(false);
  /* ------------------------------------------------------------------ messaggi */
  const toastEl = $('#toast');
  let toastT = 0;
  function toast(msg, action, ms) {
    toastEl.innerHTML = '';
    const s = document.createElement('span');
    if (msg instanceof Node) s.append(msg); else s.textContent = msg;
    toastEl.append(s);
    if (action) {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = action.label;
      b.addEventListener('click', () => { toastEl.hidden = true; action.run(); });
      toastEl.append(b);
    }
    toastEl.hidden = false;
    clearTimeout(toastT);
    toastT = setTimeout(() => { toastEl.hidden = true; }, ms || 2600);
  }
  GAL.toast = toast;

  /* ------------------------------------------------------------------ ricerca */
  const ovlSearch = $('#search'), input = $('#searchInput'), results = $('#searchResults');
  let sdata = null, sfilter = '', ssel = -1, sitems = [];
  const FOLD = { 'à': 'a', 'á': 'a', 'â': 'a', 'ä': 'a', 'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e', 'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
    'ò': 'o', 'ó': 'o', 'ô': 'o', 'ö': 'o', 'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u', 'ç': 'c', 'ñ': 'n', '’': "'" };
  const fold = (s) => { s = s.toLowerCase(); let o = ''; for (const ch of s) o += FOLD[ch] || ch; return o; };
  const escH = (s) => s.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const KINDS = { h: 'Sezione', e: 'Enunciato', n: 'Nota', q: 'Domanda', f: 'Figura', l: 'Laboratorio', p: 'Testo' };
  const ORDER = ['h', 'e', 'l', 'n', 'q', 'f', 'p'];
  const GROUP = { h: 'Sezioni', e: 'Definizioni, teoremi, esempi ed esercizi', l: 'Laboratori interattivi', n: 'Note e osservazioni', q: "Domande d'esame", f: 'Figure', p: 'Nel testo' };
  function loadSearch() {
    if (sdata) return;
    try { sdata = JSON.parse($('#searchData').textContent); } catch (e) { sdata = []; }
    sdata.forEach((d, i) => { d.i = i; d.ft = fold(d.t || ''); d.fx = fold(d.x || ''); });
  }
  function openSearch() {
    loadSearch();
    hidePop();
    ovlSearch.hidden = false;
    input.focus();
    input.select();
    runSearch();
  }
  function closeSearch() { ovlSearch.hidden = true; }
  function snippet(d, terms) {
    const x = d.x || '';
    const fx = d.fx;
    let at = -1;
    for (const t of terms) { const k = fx.indexOf(t); if (k >= 0 && (at < 0 || k < at)) at = k; }
    let a = Math.max(0, at - 60), b = Math.min(x.length, a + 190);
    if (at < 0) { a = 0; b = Math.min(x.length, 170); }
    let s = x.slice(a, b);
    let fs2 = fx.slice(a, b);
    let out = '', i = 0;
    const marks = [];
    for (const t of terms) { let k = fs2.indexOf(t); while (k >= 0) { marks.push([k, k + t.length]); k = fs2.indexOf(t, k + t.length); } }
    marks.sort((p, q) => p[0] - q[0]);
    for (const [m0, m1] of marks) { if (m0 < i) continue; out += escH(s.slice(i, m0)) + '<mark>' + escH(s.slice(m0, m1)) + '</mark>'; i = m1; }
    out += escH(s.slice(i));
    return (a > 0 ? '… ' : '') + out + (b < x.length ? ' …' : '');
  }
  function markTitle(t, terms) {
    const ft = fold(t);
    const marks = [];
    for (const term of terms) { let k = ft.indexOf(term); while (k >= 0) { marks.push([k, k + term.length]); k = ft.indexOf(term, k + term.length); } }
    marks.sort((p, q) => p[0] - q[0]);
    let out = '', i = 0;
    for (const [a, b] of marks) { if (a < i) continue; out += escH(t.slice(i, a)) + '<mark>' + escH(t.slice(a, b)) + '</mark>'; i = b; }
    return out + escH(t.slice(i));
  }
  function runSearch() {
    const q = fold(input.value.trim());
    const terms = q.split(/\s+/).filter(Boolean);
    results.innerHTML = '';
    sitems = [];
    ssel = -1;
    if (!terms.length) {
      results.innerHTML = '<div class="srch-empty">Scrivi una parola o un concetto. Prova con: ' +
        ['base ortonormale', 'De Moivre', 'rette sghembe', 'Sarrus', 'fascio di piani', 'argomento principale']
          .map((s) => `<button type="button" class="srch-sug" data-s="${s}">${s}</button>`).join(', ') + '.</div>';
      return;
    }
    const hits = [];
    for (const d of sdata) {
      if (sfilter && d.k !== sfilter && !(sfilter === 'n' && d.k === 'n')) continue;
      const hay = d.ft + ' ' + d.fx;
      if (!terms.every((t) => hay.includes(t))) continue;
      let sc = { h: 100, e: 70, l: 55, n: 45, q: 40, f: 35, p: 10 }[d.k] || 0;
      for (const t of terms) if (d.ft.includes(t)) sc += 40;
      if (d.ft.startsWith(terms[0])) sc += 15;
      hits.push([sc, d]);
    }
    hits.sort((a, b) => b[0] - a[0] || a[1].i - b[1].i);
    if (!hits.length) { results.innerHTML = '<div class="srch-empty">Nessun risultato. Controlla l’ortografia o usa meno parole.</div>'; return; }
    const groups = {};
    for (const [, d] of hits) (groups[d.k] = groups[d.k] || []).push(d);
    const frag = document.createDocumentFragment();
    for (const k of ORDER) {
      const g = groups[k];
      if (!g) continue;
      const lim = k === 'p' ? 30 : 15;
      const head = document.createElement('div');
      head.className = 'srch-g';
      head.textContent = `${GROUP[k]} · ${g.length}`;
      frag.append(head);
      g.slice(0, lim).sort((a, b) => a.i - b.i).forEach((d) => {
        const b = document.createElement('button');
        b.type = 'button';
        b.className = 'srch-i';
        b.setAttribute('role', 'option');
        b.dataset.a = d.a;
        const title = d.t ? markTitle(d.t, terms) : '';
        const kind = d.k === 'e' ? (d.t || '').split(' ')[0] : KINDS[d.k];
        const ek = d.k === 'e' ? ' e-' + kind.toLowerCase() : '';
        b.innerHTML = `<span class="srch-it"><span class="srch-ik k-${d.k}${ek}">${escH(kind)}</span><span class="srch-tt">${title}</span></span>` +
          (d.k !== 'h' || !d.t ? `<span class="srch-ix">${snippet(d, terms)}</span>` : '') +
          (d.p ? `<span class="srch-ip">${escH(d.p)}</span>` : '');
        frag.append(b);
        sitems.push(b);
      });
    }
    results.append(frag);
    select(0);
  }
  function select(i) {
    if (!sitems.length) return;
    if (ssel >= 0 && sitems[ssel]) sitems[ssel].setAttribute('aria-selected', 'false');
    ssel = (i + sitems.length) % sitems.length;
    const b = sitems[ssel];
    b.setAttribute('aria-selected', 'true');
    b.scrollIntoView({ block: 'nearest' });
  }
  input.addEventListener('input', runSearch);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); select(ssel + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); select(ssel - 1); }
    else if (e.key === 'Enter') { e.preventDefault(); if (sitems[ssel]) sitems[ssel].click(); }
  });
  results.addEventListener('click', (e) => {
    const sug = e.target.closest('.srch-sug');
    if (sug) { input.value = sug.dataset.s; runSearch(); input.focus(); return; }
    const b = e.target.closest('.srch-i');
    if (!b) return;
    closeSearch();
    navigate(b.dataset.a, { flash: true });
  });
  $('#searchFilters').addEventListener('click', (e) => {
    const b = e.target.closest('button');
    if (!b) return;
    sfilter = b.dataset.f;
    $$('#searchFilters button').forEach((x) => x.setAttribute('aria-pressed', x === b ? 'true' : 'false'));
    runSearch();
    input.focus();
  });
  $('#searchBtn').addEventListener('click', openSearch);
  $('#sideSearch').addEventListener('click', () => { if (mqNarrow.matches) closeSide(); openSearch(); });
  $('#searchClose').addEventListener('click', closeSearch);
  ovlSearch.addEventListener('click', (e) => { if (e.target === ovlSearch) closeSearch(); });

  /* ------------------------------------------------------------------ anteprime dei riferimenti */
  const pop = $('#pop');
  let popT = 0, popFor = null;
  const canHover = matchMedia('(hover: hover) and (pointer: fine)');
  function hidePop() { clearTimeout(popT); pop.hidden = true; popFor = null; }
  function showPop(a) {
    const id = decodeURIComponent(a.getAttribute('href').slice(1));
    const t = document.getElementById(id);
    if (!t || t.closest('.lab')) return;
    let node;
    if (t.matches('h3, h4, h5, h2')) {
      node = document.createElement('div');
      let s = t, k = 0;
      while (s && k < 3) {
        if (k > 0 && s.matches('h2, h3, h4, h5, .lab, .part')) break;
        GAL.renderIn(s);
        node.append(s.cloneNode(true));
        s = s.nextElementSibling;
        k++;
      }
    } else {
      GAL.renderIn(t);
      node = t.cloneNode(true);
    }
    node.querySelectorAll('[id]').forEach((x) => x.removeAttribute('id'));
    node.removeAttribute && node.removeAttribute('id');
    node.querySelectorAll('.closed').forEach((x) => x.classList.remove('closed'));
    pop.innerHTML = '';
    pop.append(node);
    const go = document.createElement('a');
    go.className = 'pop-go';
    go.href = '#' + id;
    go.textContent = 'Vai al punto della dispensa →';
    pop.append(go);
    pop.hidden = false;
    const r = a.getBoundingClientRect();
    const pw = pop.offsetWidth, ph = pop.offsetHeight;
    let x = Math.min(window.innerWidth - pw - 12, Math.max(12, r.left + r.width / 2 - pw / 2));
    let y = r.bottom + 10;
    if (y + ph > window.innerHeight - 12) y = Math.max(12, r.top - ph - 10);
    pop.style.left = x + 'px';
    pop.style.top = y + 'px';
    popFor = a;
  }
  doc.addEventListener('pointerover', (e) => {
    const a = e.target.closest('a.xr');
    if (!a || !canHover.matches) return;
    clearTimeout(popT);
    if (popFor === a) return;
    popT = setTimeout(() => showPop(a), 320);
  });
  doc.addEventListener('pointerout', (e) => {
    const a = e.target.closest('a.xr');
    if (!a) return;
    clearTimeout(popT);
    popT = setTimeout(hidePop, 260);
  });
  GAL.preview = showPop;
  pop.addEventListener('pointerenter', () => clearTimeout(popT));
  pop.addEventListener('pointerleave', () => { popT = setTimeout(hidePop, 220); });
  window.addEventListener('scroll', () => { if (!pop.hidden) hidePop(); }, { passive: true });

  /* ------------------------------------------------------------------ figure ingrandite */
  const lbx = $('#lightbox');
  doc.addEventListener('click', (e) => {
    const b = e.target.closest('.fig-zoom');
    if (!b || b.closest('.pop')) return;
    const img = b.querySelector('img');
    $('#lbxImg').src = img.src;
    $('#lbxImg').alt = img.alt;
    const cap = b.parentElement.querySelector('figcaption');
    $('#lbxCap').innerHTML = cap ? cap.innerHTML : '';
    lbx.hidden = false;
    $('#lbxClose').focus();
  });
  $('#lbxClose').addEventListener('click', () => { lbx.hidden = true; });
  lbx.addEventListener('click', (e) => { if (e.target === lbx || e.target.closest('.lbx-img')) lbx.hidden = true; });

  /* ------------------------------------------------------------------ formulario */
  const frm = $('#formulario');
  let frmBuilt = false;
  function buildForm() {
    if (frmBuilt) return;
    frmBuilt = true;
    let data = [];
    try { data = JSON.parse($('#keyData').textContent); } catch (e) { data = []; }
    const body = $('#formBody');
    const sel = $('#formChap');
    const frag = document.createDocumentFragment();
    let last = null;
    let sec = null;
    for (const d of data) {
      if (d.c !== last) {
        last = d.c;
        sec = document.createElement('section');
        sec.className = 'frm-c';
        sec.dataset.c = d.c;
        const h = document.createElement('h3');
        h.textContent = d.c;
        sec.append(h);
        frag.append(sec);
        const o = document.createElement('option');
        o.value = d.c;
        o.textContent = d.c;
        sel.append(o);
      }
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'frm-i';
      b.dataset.a = d.a;
      const lab = [d.e, d.g ? '(' + d.g + ')' : ''].filter(Boolean).join(' · ');
      b.innerHTML = `<span class="frm-l"><b>${escH(lab || 'Formula')}</b><span class="frm-s">${escH(d.s)}</span></span><span class="frm-f"></span>`;
      const f = b.querySelector('.frm-f');
      try { f.innerHTML = GAL.tex(d.x.replace(/\\tag\{[^}]*\}/g, '').replace(/[.,;:]\s*$/, ''), true); } catch (e) { f.textContent = d.x; }
      sec.append(b);
    }
    body.append(frag);
  }
  function openForm() { buildForm(); frm.hidden = false; $('#formClose').focus(); }
  function closeForm() { frm.hidden = true; }
  $('#formBtn').addEventListener('click', openForm);
  $('#formClose').addEventListener('click', closeForm);
  frm.addEventListener('click', (e) => {
    if (e.target === frm) { closeForm(); return; }
    const it = e.target.closest('.frm-i');
    if (it) { closeForm(); navigate(it.dataset.a); }
  });
  $('#formChap').addEventListener('change', (e) => {
    const v = e.target.value;
    $$('.frm-c', frm).forEach((x) => { x.hidden = !!v && x.dataset.c !== v; });
    $('#formBody').scrollTop = 0;
  });

  /* ------------------------------------------------------------------ scorciatoie */
  const help = $('#help');
  $('#helpBtn').addEventListener('click', () => { help.hidden = false; $('#helpClose').focus(); });
  $('#helpClose').addEventListener('click', () => { help.hidden = true; });
  help.addEventListener('click', (e) => { if (e.target === help) help.hidden = true; });
  function sectionStep(dir) {
    const heads = spy.filter((s) => /t-(section|riepilogo|chapter|intro|indice)/.test(s.li.className));
    const y = window.scrollY + topOffset() + 8;
    let k = heads.findIndex((s) => s.top > y + 4);
    if (k < 0) k = heads.length;
    const target = dir > 0 ? heads[k] : heads[Math.max(0, k - 2)];
    if (target) navigate(target.id);
  }
  document.addEventListener('keydown', (e) => {
    const tag = (e.target && e.target.tagName) || '';
    const typing = /INPUT|TEXTAREA|SELECT/.test(tag) || (e.target && e.target.isContentEditable);
    if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) { e.preventDefault(); openSearch(); return; }
    if (e.key === 'Escape') {
      if (!ovlSearch.hidden) closeSearch();
      else if (!frm.hidden) closeForm();
      else if (!lbx.hidden) lbx.hidden = true;
      else if (!help.hidden) help.hidden = true;
      else if (!pop.hidden) hidePop();
      else if (document.body.classList.contains('side-open')) closeSide();
      return;
    }
    if (typing || e.ctrlKey || e.metaKey || e.altKey) return;
    if (!ovlSearch.hidden || !help.hidden || !lbx.hidden || !frm.hidden) return;
    const k = e.key;
    if (k === '/') { e.preventDefault(); openSearch(); }
    else if (k === 'n' || k === 'N') sectionStep(1);
    else if (k === 'p' || k === 'P') sectionStep(-1);
    else if (k === 't' || k === 'T') cycleTheme();
    else if (k === 'f' || k === 'F') openForm();
    else if (k === '?') { help.hidden = false; $('#helpClose').focus(); }
  });

  /* ------------------------------------------------------------------ copia: formule in LaTeX */
  document.addEventListener('copy', (e) => {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return;
    const range = sel.getRangeAt(0).cloneRange();
    const up = (n) => (n.nodeType === 1 ? n : n.parentElement);
    const sm = up(range.startContainer) && up(range.startContainer).closest('[data-tex]');
    const em = up(range.endContainer) && up(range.endContainer).closest('[data-tex]');
    if (sm) range.setStartBefore(sm);
    if (em) range.setEndAfter(em);
    const frag = range.cloneContents();
    if (!frag.querySelector('[data-tex]')) return;
    frag.querySelectorAll('[data-tex]').forEach((m) => {
      const d = m.classList.contains('dm');
      m.replaceWith(document.createTextNode(d ? '\n$$' + m.dataset.tex + '$$\n' : '$' + m.dataset.tex + '$'));
    });
    frag.querySelectorAll('[data-x], svg, .lab').forEach((x) => x.remove());
    const box = document.createElement('div');
    box.style.cssText = 'position:fixed;left:-9999px;top:0;white-space:pre-wrap';
    box.append(frag);
    document.body.append(box);
    const text = box.innerText;
    box.remove();
    e.clipboardData.setData('text/plain', text);
    e.preventDefault();
  });

  /* ------------------------------------------------------------------ laboratori e diagrammi (al bisogno) */
  function mountLab(sec) {
    const id = sec.dataset.lab;
    const f = GAL.labs && GAL.labs[id];
    const m = sec.querySelector('.lab-m');
    GAL.renderIn(sec);
    if (!f) { m.innerHTML = '<p class="lab-note">Laboratorio non disponibile.</p>'; return; }
    try { f(m, sec); } catch (err) {
      console.error('laboratorio', id, err);
      m.innerHTML = '<p class="lab-note">Non è stato possibile avviare questo laboratorio.</p>';
    }
    scheduleMeasure();
  }
  const dgms = $$('.dgm-c', doc);
  function layoutDgm(el) {
    if (!GAL.diagram) return;
    GAL.renderIn(el.closest('.dgm'));
    try { GAL.diagram(el); } catch (err) { console.error('diagramma', err); }
  }
  if ('IntersectionObserver' in window) {
    const lio = new IntersectionObserver((ents) => {
      for (const e of ents) if (e.isIntersecting) { lio.unobserve(e.target); mountLab(e.target); }
    }, { rootMargin: '700px 0px' });
    $$('.lab', doc).forEach((l) => lio.observe(l));
    const dio = new IntersectionObserver((ents) => {
      for (const e of ents) if (e.isIntersecting) { dio.unobserve(e.target); layoutDgm(e.target); e.target.dataset.done = '1'; }
    }, { rootMargin: '900px 0px' });
    dgms.forEach((d) => dio.observe(d));
  } else {
    $$('.lab', doc).forEach(mountLab);
    dgms.forEach(layoutDgm);
  }
  let dgmT = 0;
  window.addEventListener('resize', () => {
    clearTimeout(dgmT);
    dgmT = setTimeout(() => dgms.filter((d) => d.dataset.done).forEach(layoutDgm), 200);
  });
  GAL.on('mathready', () => dgms.filter((d) => d.dataset.done).forEach(layoutDgm));
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => dgms.filter((d) => d.dataset.done).forEach(layoutDgm));

  /* ------------------------------------------------------------------ avvio */
  const savedPos = store.get('pos', null);
  root.classList.add('init');
  setTimeout(() => root.classList.remove('init'), 700);
  $$('.side .m').forEach(renderMath);
  let start = null;
  const hashId = decodeURIComponent(location.hash.slice(1));
  if (hashId) start = document.getElementById(hashId);
  const i0 = start ? indexAfter(start) : 0;
  renderRange(i0 - 120, i0 + 320);
  if (mio) mathEls.forEach((el) => { if (!el.dataset.k) mio.observe(el); });
  measure();
  if (start) {
    openCollapsedAround(start);
    requestAnimationFrame(() => {
      const y = start.getBoundingClientRect().top + window.scrollY - topOffset();
      window.scrollTo({ top: Math.max(0, y), behavior: 'auto' });
      onScroll();
    });
  } else onScroll();
  idle(bgStep);
  if (GAL.heroArt) { try { GAL.heroArt($('#heroArt')); } catch (e) { console.error(e); } }

  // riprendi la lettura
  const pos = savedPos;
  if (!hashId && pos && liById.has(pos) && document.getElementById(pos)) {
    const li = liById.get(pos);
    const a = li.querySelector(':scope > .t-row > .t-a');
    const n = a.querySelector('.t-n:not(.t-ic)');
    const tx = a.querySelector('.t-tx');
    const label = (n ? n.textContent + ' ' : '') + (tx ? tx.textContent : a.textContent);
    if (spy.length && pos !== spy[0].id) {
      const rb = $('#resumeBtn');
      rb.querySelector('span').textContent = 'Riprendi: ' + label;
      rb.hidden = false;
      rb.addEventListener('click', () => navigate(pos));
      const s = document.createElement('span');
      s.textContent = 'Eri arrivato a «' + label + '».';
      toast(s, { label: 'Riprendi', run: () => navigate(pos) }, 9000);
    }
  }
})();
