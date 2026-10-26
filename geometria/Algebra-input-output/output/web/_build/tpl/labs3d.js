/* Laboratori nello spazio: piccolo motore 3D (proiezione ortogonale, SVG) e scene interattive. */
(function () {
  'use strict';
  const GAL = window.GAL = window.GAL || {};
  const labs = GAL.labs = GAL.labs || {};
  const NS = 'http://www.w3.org/2000/svg';
  const h = (...a) => GAL.h(...a);
  const K = (tex) => (GAL.tex ? GAL.tex(tex) : tex);
  const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const N = () => GAL.num;

  /* ------------------------------------------------------------ algebra */
  const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const mul = (a, k) => [a[0] * k, a[1] * k, a[2] * k];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  const norm = (a) => Math.hypot(a[0], a[1], a[2]);
  const unit = (a) => { const n = norm(a) || 1; return mul(a, 1 / n); };
  const lin = (...terms) => terms.reduce((acc, [k, v]) => add(acc, mul(v, k)), [0, 0, 0]);
  const V3 = { add, sub, mul, dot, cross, norm, unit, lin };
  GAL.v3 = V3;

  /* ------------------------------------------------------------ scena */
  class Scene3D {
    constructor(parent, o) {
      this.o = Object.assign({ range: 4, box: null, az: 0.5, el: 0.38, W: 560, H: 420, axes: true, ticks: false, ground: false, labels: ['x', 'y', 'z'], zoom: 1, center: [0, 0, 0] }, o);
      this.box = this.o.box || this.o.range;
      this.az = this.o.az; this.el = this.o.el;
      this.W = this.o.W; this.H = this.o.H;
      this.wrap = h('div', { class: 'lab-plot c3d' + (this.o.cls ? ' ' + this.o.cls : '') });
      this.wrap.style.aspectRatio = `${this.W} / ${this.H}`;
      this.svg = document.createElementNS(NS, 'svg');
      this.svg.setAttribute('viewBox', `0 0 ${this.W} ${this.H}`);
      this.svg.setAttribute('role', 'img');
      this.svg.setAttribute('aria-label', this.o.aria || 'Scena tridimensionale: trascina per ruotare');
      this.g = document.createElementNS(NS, 'g');
      this.svg.append(this.g);
      this.ov = h('div', { style: 'position:absolute;inset:0;pointer-events:none' });
      this.wrap.append(this.svg, this.ov);
      if (this.o.hint !== false) this.wrap.append(h('span', { class: 'c3d-hint', text: 'trascina per ruotare' }));
      parent.append(this.wrap);
      this.labels = new Map();
      this.drawFn = null;
      this.bind();
    }
    get scale() { return this.o.zoom * Math.min(this.W, this.H) / (2.25 * this.o.range); }
    basis() {
      const ca = Math.cos(this.az), sa = Math.sin(this.az), ce = Math.cos(this.el), se = Math.sin(this.el);
      this.r = [-sa, ca, 0];
      this.u = [-se * ca, -se * sa, ce];
      this.d = [ce * ca, ce * sa, se];
    }
    P(p) {
      const k = this.scale, q = sub(p, this.o.center);
      return [this.W / 2 + k * dot(q, this.r), this.H / 2 - k * dot(q, this.u), dot(q, this.d)];
    }
    bind() {
      let drag = null;
      this.svg.addEventListener('pointerdown', (e) => {
        drag = { x: e.clientX, y: e.clientY, az: this.az, el: this.el, id: e.pointerId };
        this.svg.setPointerCapture(e.pointerId);
        this.dragging = true;
        if (this.onUser) this.onUser();
      });
      this.svg.addEventListener('pointermove', (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        const rect = this.svg.getBoundingClientRect();
        const f = 2.6 / Math.max(240, rect.width);
        this.az = drag.az - (e.clientX - drag.x) * f;
        this.el = Math.max(-1.45, Math.min(1.45, drag.el + (e.clientY - drag.y) * f));
        this.render();
      });
      const up = (e) => { if (drag && e.pointerId === drag.id) { drag = null; this.dragging = false; } };
      this.svg.addEventListener('pointerup', up);
      this.svg.addEventListener('pointercancel', up);
      this.svg.setAttribute('tabindex', '0');
      this.svg.addEventListener('keydown', (e) => {
        const st = 0.08;
        if (e.key === 'ArrowLeft') this.az += st; else if (e.key === 'ArrowRight') this.az -= st;
        else if (e.key === 'ArrowUp') this.el = Math.min(1.45, this.el + st); else if (e.key === 'ArrowDown') this.el = Math.max(-1.45, this.el - st);
        else return;
        e.preventDefault();
        this.render();
      });
    }
    setDraw(f) { this.drawFn = f; this.render(); }
    render() {
      this.basis();
      this.items = [];
      this.used = new Set();
      if (this.o.ground) this.groundGrid();
      if (this.o.axes) this.axes();
      if (this.drawFn) this.drawFn(this);
      this.items.sort((a, b) => a.z - b.z);
      const frag = document.createDocumentFragment();
      for (const it of this.items) frag.append(it.el);
      this.g.replaceChildren(frag);
      for (const [k, d] of this.labels) if (!this.used.has(k)) { d.remove(); this.labels.delete(k); }
    }
    css(st) {
      const c = [];
      c.push('stroke:' + (st.color || 'var(--ink-2)'));
      c.push('stroke-width:' + (st.w || 2));
      c.push('fill:' + (st.fill || 'none'));
      if (st.fop != null) c.push('fill-opacity:' + st.fop);
      if (st.op != null) c.push('opacity:' + st.op);
      if (st.dash) c.push('stroke-dasharray:' + st.dash);
      c.push('stroke-linecap:round;stroke-linejoin:round');
      return c.join(';');
    }
    push(el, z) { this.items.push({ el, z }); }
    seg(a, b, st) {
      st = st || {};
      const A = this.P(a), B = this.P(b);
      const l = document.createElementNS(NS, 'line');
      l.setAttribute('x1', A[0]); l.setAttribute('y1', A[1]); l.setAttribute('x2', B[0]); l.setAttribute('y2', B[1]);
      l.setAttribute('style', this.css(st));
      this.push(l, (A[2] + B[2]) / 2 + (st.zb || 0));
    }
    arrow(a, b, st) {
      st = Object.assign({ color: 'var(--c-blue)', w: 2.8 }, st);
      const A = this.P(a), B = this.P(b);
      const len = Math.hypot(B[0] - A[0], B[1] - A[1]);
      const g = document.createElementNS(NS, 'g');
      if (len > 0.5) {
        const L = Math.min(13, len * 0.5), w = 5.2;
        const ux = (B[0] - A[0]) / len, uy = (B[1] - A[1]) / len;
        const bx = B[0] - ux * L, by = B[1] - uy * L;
        const l = document.createElementNS(NS, 'line');
        l.setAttribute('x1', A[0]); l.setAttribute('y1', A[1]); l.setAttribute('x2', B[0] - ux * L * 0.6); l.setAttribute('y2', B[1] - uy * L * 0.6);
        l.setAttribute('style', this.css(st));
        const hd = document.createElementNS(NS, 'path');
        hd.setAttribute('d', `M${B[0]},${B[1]} L${bx - uy * w},${by + ux * w} L${bx + uy * w},${by - ux * w} Z`);
        hd.setAttribute('style', `fill:${st.color};stroke:${st.color};stroke-width:1;stroke-linejoin:round${st.op != null ? ';opacity:' + st.op : ''}`);
        g.append(l, hd);
      }
      this.push(g, (A[2] + B[2]) / 2 + (st.zb || 0.05));
    }
    poly(pts, st) {
      st = Object.assign({ fill: 'var(--c-blue)', fop: 0.14, color: 'var(--c-blue)', w: 1 }, st);
      const P = pts.map((p) => this.P(p));
      const pg = document.createElementNS(NS, 'polygon');
      pg.setAttribute('points', P.map((q) => q[0] + ',' + q[1]).join(' '));
      pg.setAttribute('style', this.css(st));
      this.push(pg, P.reduce((s, q) => s + q[2], 0) / P.length + (st.zb != null ? st.zb : -0.6));
    }
    point(p, st) {
      st = Object.assign({ color: 'var(--ink)', r: 4 }, st);
      const P = this.P(p);
      const c = document.createElementNS(NS, 'circle');
      c.setAttribute('cx', P[0]); c.setAttribute('cy', P[1]); c.setAttribute('r', st.r);
      c.setAttribute('style', `fill:${st.color};stroke:var(--plot-bg);stroke-width:1.5`);
      this.push(c, P[2] + 0.2);
    }
    label(key, tex, p, opt) {
      opt = opt || {};
      let d = this.labels.get(key);
      if (!d) { d = h('div', { class: 'pl-tex' }); this.ov.append(d); this.labels.set(key, d); }
      if (d._tex !== tex) { d.innerHTML = K(tex); d._tex = tex; }
      const P = this.P(p);
      d.style.left = (100 * (P[0] + (opt.dx || 0)) / this.W) + '%';
      d.style.top = (100 * (P[1] + (opt.dy || 0)) / this.H) + '%';
      d.style.color = opt.color || '';
      d.classList.toggle('sm', !!opt.small);
      this.used.add(key);
    }
    // etichetta oltre la punta di un vettore
    tip(key, tex, a, b, color, dist) {
      const A = this.P(a), B = this.P(b);
      const l = Math.hypot(B[0] - A[0], B[1] - A[1]) || 1;
      const dd = dist || 16;
      this.label(key, tex, b, { dx: (B[0] - A[0]) / l * dd, dy: (B[1] - A[1]) / l * dd, color });
    }
    axes() {
      const R = this.o.axisLen || this.box;
      const L = this.o.labels;
      const E = [[1, 0, 0], [0, 1, 0], [0, 0, 1]];
      E.forEach((e, i) => {
        this.seg(mul(e, -R), [0, 0, 0], { color: 'var(--plot-axis)', w: 1, dash: '3 4', op: 0.6, zb: -0.3 });
        this.arrow([0, 0, 0], mul(e, R), { color: 'var(--plot-axis)', w: 1.3, op: 0.85, zb: -0.3 });
        if (L) this.label('ax' + i, L[i], mul(e, R * 1.08), { color: 'var(--ink-3)', small: true });
      });
    }
    groundGrid() {
      const R = this.box, st = this.o.gridStep || 1;
      for (let x = -R; x <= R + 1e-9; x += st) {
        this.seg([x, -R, 0], [x, R, 0], { color: 'var(--plot-grid)', w: 1, zb: -2 });
        this.seg([-R, x, 0], [R, x, 0], { color: 'var(--plot-grid)', w: 1, zb: -2 });
      }
    }
    // piano n·p = d ritagliato nel cubo [-B,B]^3
    plane(n, d, st) {
      const B = this.box;
      const V = [];
      for (const x of [-B, B]) for (const y of [-B, B]) for (const z of [-B, B]) V.push([x, y, z]);
      const E = [];
      for (let i = 0; i < 8; i++) for (let j = i + 1; j < 8; j++) {
        const diff = sub(V[i], V[j]).filter((q) => Math.abs(q) > 1e-9).length;
        if (diff === 1) E.push([V[i], V[j]]);
      }
      const pts = [];
      for (const [a, b] of E) {
        const fa = dot(n, a) - d, fb = dot(n, b) - d;
        if ((fa <= 0 && fb >= 0) || (fa >= 0 && fb <= 0)) {
          if (Math.abs(fa - fb) < 1e-12) continue;
          const t = fa / (fa - fb);
          const p = add(a, mul(sub(b, a), t));
          if (!pts.some((q) => norm(sub(q, p)) < 1e-6)) pts.push(p);
        }
      }
      if (pts.length < 3) return null;
      const c = mul(pts.reduce((s, p) => add(s, p), [0, 0, 0]), 1 / pts.length);
      const e1 = unit(sub(pts[0], c)), e2 = cross(unit(n), e1);
      pts.sort((p, q) => Math.atan2(dot(sub(p, c), e2), dot(sub(p, c), e1)) - Math.atan2(dot(sub(q, c), e2), dot(sub(q, c), e1)));
      this.poly(pts, st);
      return pts;
    }
    // retta p0 + t v ritagliata nel cubo
    clipLine(p0, v) {
      const B = this.box;
      let t0 = -Infinity, t1 = Infinity;
      for (let i = 0; i < 3; i++) {
        if (Math.abs(v[i]) < 1e-12) { if (Math.abs(p0[i]) > B) return null; continue; }
        let a = (-B - p0[i]) / v[i], b = (B - p0[i]) / v[i];
        if (a > b) [a, b] = [b, a];
        t0 = Math.max(t0, a); t1 = Math.min(t1, b);
      }
      if (t0 > t1) return null;
      return [add(p0, mul(v, t0)), add(p0, mul(v, t1))];
    }
    line(p0, v, st) {
      const c = this.clipLine(p0, v);
      if (c) this.seg(c[0], c[1], st);
      return c;
    }
    // piccolo arco (angolo retto) fra due direzioni in un punto
    rightAngle(p, a, b, size) {
      const s = size || 0.32;
      const ua = mul(unit(a), s), ub = mul(unit(b), s);
      this.seg(add(p, ua), add(add(p, ua), ub), { color: 'var(--c-orange)', w: 1.5 });
      this.seg(add(add(p, ua), ub), add(p, ub), { color: 'var(--c-orange)', w: 1.5 });
    }
  }
  GAL.Scene3D = Scene3D;

  const ui = () => GAL.ui;
  const T = (tex) => K(tex);
  const tn = (x, d) => N().tn(x, d);
  const vt = (v, d) => `(${tn(v[0], d)},\\ ${tn(v[1], d)},\\ ${tn(v[2], d)})`;
  function lay(m) { return GAL.layout(m); }
  // combinazione lineare con i segni giusti: [[coef, 'tex'], ...]
  function combo(terms) {
    let out = '';
    terms.forEach(([c, t], i) => {
      const r = N().rnd(c, 2);
      if (Math.abs(r) < 1e-9) return;
      const a = Math.abs(r), sgn = r < 0 ? '-' : (out ? '+' : '');
      out += `${sgn}${a === 1 ? '' : tn(a, 2) + '\\,'}${t}`;
      void i;
    });
    return out || '\\underline{0}';
  }

  /* ------------------------------------------------------------ intestazione: base i, j, k */
  GAL.heroArt = function (box) {
    if (!box) return;
    const S = new Scene3D(box, { range: 1.55, box: 1.9, axisLen: 1.75, W: 420, H: 420, az: 0.62, el: 0.36, labels: ['x', 'y', 'z'], hint: false, aria: 'La base i, j, k e un vettore v: trascina per ruotare' });
    S.wrap.classList.add('hero-3d');
    const v = [1.15, 1.3, 1.0];
    S.setDraw((s) => {
      const vx = [v[0], 0, 0], vy = [0, v[1], 0], vxy = [v[0], v[1], 0];
      s.poly([[0, 0, 0], vx, vxy, vy], { fill: 'var(--c-blue)', fop: 0.06, color: 'none', w: 0, zb: -3 });
      [[vx, vxy], [vy, vxy], [vxy, v], [[0, 0, v[2]], v]].forEach(([a, b]) => s.seg(a, b, { color: 'var(--c-gray)', dash: '4 4', w: 1.2 }));
      s.arrow([0, 0, 0], [1, 0, 0], { color: 'var(--c-blue)', w: 3.2 });
      s.arrow([0, 0, 0], [0, 1, 0], { color: 'var(--c-teal)', w: 3.2 });
      s.arrow([0, 0, 0], [0, 0, 1], { color: 'var(--c-violet)', w: 3.2 });
      s.arrow([0, 0, 0], v, { color: 'var(--c-red)', w: 3.4 });
      s.tip('i', '\\underline{i}', [0, 0, 0], [1, 0, 0], 'var(--c-blue)', 15);
      s.tip('j', '\\underline{j}', [0, 0, 0], [0, 1, 0], 'var(--c-teal)', 15);
      s.tip('k', '\\underline{k}', [0, 0, 0], [0, 0, 1], 'var(--c-violet)', 15);
      s.tip('v', '\\underline{v}', [0, 0, 0], v, 'var(--c-red)', 16);
      s.point([0, 0, 0], { color: 'var(--ink)', r: 3 });
    });
    if (reduce()) return;
    let raf = 0, visible = true, t0 = performance.now(), base = S.az, user = false;
    S.onUser = () => { user = true; };
    const loop = (now) => {
      if (!visible || user) { raf = 0; return; }
      S.az = base + 0.35 * Math.sin((now - t0) / 4200);
      S.render();
      raf = requestAnimationFrame(loop);
    };
    if ('IntersectionObserver' in window) {
      new IntersectionObserver((e) => {
        visible = e[0].isIntersecting;
        if (visible && !raf && !user) raf = requestAnimationFrame(loop);
      }).observe(box);
    }
    raf = requestAnimationFrame(loop);
  };

  /* ============================================================ CAPITOLO 7: teorema delle basi */
  labs['v-basi3d'] = function (m) {
    const { slider, readout } = ui();
    const v1 = [2, 0.3, 0], v2 = [0.5, 2, 0], v3 = [0.6, 0.4, 1.8];
    let l = [0.8, 0.7, 0.9];
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 2.7, box: 3.4, az: 0.55, el: 0.33, center: [0.4, 0.4, 0.5] });
    const info = readout();
    function draw(s) {
      const w1 = lin([l[0], v1], [l[1], v2]), w2 = mul(v3, l[2]), P = add(w1, w2);
      const c = 1.6;
      s.poly([lin([-c, v1], [-c, v2]), lin([c, v1], [-c, v2]), lin([c, v1], [c, v2]), lin([-c, v1], [c, v2])], { fill: 'var(--c-blue)', fop: 0.08, color: 'var(--c-blue)', w: 0.8, op: 0.8 });
      s.label('pi', '\\pi', lin([c * 0.92, v1], [-c * 0.85, v2]), { color: 'var(--c-blue)' });
      s.line([0, 0, 0], v3, { color: 'var(--c-violet)', dash: '4 5', w: 1.2, op: 0.7 });
      // costruzione nel piano: parallelogramma di λ1v1, λ2v2
      const a = mul(v1, l[0]), b = mul(v2, l[1]);
      s.seg(a, w1, { color: 'var(--c-gray)', dash: '4 4', w: 1.2 });
      s.seg(b, w1, { color: 'var(--c-gray)', dash: '4 4', w: 1.2 });
      // parallelogramma OQPR
      s.seg(w1, P, { color: 'var(--c-orange)', dash: '5 4', w: 1.6 });
      s.seg(w2, P, { color: 'var(--c-orange)', dash: '5 4', w: 1.6 });
      s.arrow([0, 0, 0], v1, { color: 'var(--c-blue)', w: 2.4 });
      s.arrow([0, 0, 0], v2, { color: 'var(--c-teal)', w: 2.4 });
      s.arrow([0, 0, 0], v3, { color: 'var(--c-violet)', w: 2.4 });
      s.arrow([0, 0, 0], w1, { color: 'var(--c-gray)', w: 2, op: 0.9 });
      s.arrow([0, 0, 0], w2, { color: 'var(--c-gray)', w: 2, op: 0.9 });
      s.arrow([0, 0, 0], P, { color: 'var(--c-red)', w: 3.2 });
      s.tip('v1', '\\underline{v}_1', [0, 0, 0], v1, 'var(--c-blue)');
      s.tip('v2', '\\underline{v}_2', [0, 0, 0], v2, 'var(--c-teal)');
      s.tip('v3', '\\underline{v}_3', [0, 0, 0], v3, 'var(--c-violet)');
      s.tip('v', '\\underline{v}', [0, 0, 0], P, 'var(--c-red)');
      s.label('O', 'O', [0, 0, 0], { dx: -10, dy: 12 });
      s.label('Q', 'Q', w1, { dx: 12, dy: 10, color: 'var(--ink-2)' });
      s.label('R', 'R', w2, { dx: -12, dy: -8, color: 'var(--ink-2)' });
      s.point(w1, { r: 3.5, color: 'var(--ink-2)' }); s.point(w2, { r: 3.5, color: 'var(--ink-2)' }); s.point(P, { r: 3.5, color: 'var(--c-red)' });
      info.set([
        ['', T(`\\underline{v} = ${combo([[l[0], '\\underline{v}_1'], [l[1], '\\underline{v}_2'], [l[2], '\\underline{v}_3']])}`)],
        ['nel piano π', T(`\\underline{w}_1 = [(O,Q)] = \\lambda_1\\underline{v}_1+\\lambda_2\\underline{v}_2`)],
        ['sulla retta di v₃', T(`\\underline{w}_2 = [(O,R)] = \\lambda_3\\underline{v}_3`)],
      ]);
    }
    const sl = [0, 1, 2].map((k) => slider({ label: `$\\lambda_${k + 1}$`, min: -1.5, max: 1.5, step: 0.05, value: l[k], onInput: (x) => { l[k] = x; S.render(); } }));
    L.side.append(...sl, info, GAL.note('La parallela per $P$ a $\\underline{v}_3$ incontra il piano $\\pi$ in $Q$; $OQPR$ (tratteggio arancione) è un parallelogramma anche se sta nello spazio. Muovendo i cursori cambia $\\underline{v}$, mai la base.'));
    S.setDraw(draw);
  };

  /* ============================================================ CAPITOLO 9 */
  labs['pv-vettoriale'] = function (m) {
    const { slider, readout, check } = ui();
    let th = 1.15, lv = 1.5, tilt = 0, flip = false;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 2.0, box: 2.8, az: 0.5, el: 0.55, center: [0.4, 0.4, 0.6] });
    const info = readout();
    function draw(s) {
      const c = Math.cos(tilt), sn = Math.sin(tilt);
      const rot = (p) => [p[0], p[1] * c - p[2] * sn, p[1] * sn + p[2] * c];
      const u = rot([1.6, 0, 0]), v = rot([lv * Math.cos(th), lv * Math.sin(th), 0]);
      const a = flip ? v : u, b = flip ? u : v;
      const w = cross(a, b);
      s.poly([[0, 0, 0], u, add(u, v), v], { fill: 'var(--c-blue)', fop: 0.13, color: 'var(--c-blue)', w: 1 });
      // freccia della mano destra: arco da a verso b attorno alla normale
      const n = unit(w);
      if (norm(w) > 1e-6) {
        const e1 = unit(a), e2 = unit(sub(b, mul(e1, dot(b, e1))));
        const ang = Math.acos(Math.max(-1, Math.min(1, dot(unit(a), unit(b)))));
        const pts = [];
        for (let k = 0; k <= 24; k++) { const t = ang * k / 24; pts.push(add(mul(e1, 0.7 * Math.cos(t)), mul(e2, 0.7 * Math.sin(t)))); }
        for (let k = 0; k + 1 < pts.length; k++) s.seg(pts[k], pts[k + 1], { color: 'var(--c-orange)', w: 2 });
        s.arrow(pts[pts.length - 3], pts[pts.length - 1], { color: 'var(--c-orange)', w: 2 });
        s.rightAngle([0, 0, 0], a, n, 0.28);
      }
      s.arrow([0, 0, 0], u, { color: 'var(--c-blue)', w: 2.8 });
      s.arrow([0, 0, 0], v, { color: 'var(--c-teal)', w: 2.8 });
      s.arrow([0, 0, 0], w, { color: 'var(--c-red)', w: 3.2 });
      s.tip('u', '\\underline{u}', [0, 0, 0], u, 'var(--c-blue)');
      s.tip('v', '\\underline{v}', [0, 0, 0], v, 'var(--c-teal)');
      s.tip('w', flip ? '\\underline{v}\\wedge\\underline{u}' : '\\underline{u}\\wedge\\underline{v}', [0, 0, 0], w, 'var(--c-red)', 22);
      const area = norm(w);
      info.set([
        ['u', T(`\\underline{u} = ${vt(u, 2)}`)], ['v', T(`\\underline{v} = ${vt(v, 2)}`)],
        [flip ? 'v∧u' : 'u∧v', T(`${flip ? '\\underline{v}\\wedge\\underline{u}' : '\\underline{u}\\wedge\\underline{v}'} = ${vt(w, 2)}`)],
        ['modulo', T(`|\\underline{u}||\\underline{v}||\\sin\\theta| = 1{,}6\\cdot${tn(lv, 2)}\\cdot${tn(Math.abs(Math.sin(th)), 3)} = ${tn(area, 3)}`)],
        ['', area < 1e-6 ? '<span class="badge no">vettori paralleli: prodotto vettoriale nullo</span>' : '<span class="badge neu">area del parallelogramma = ' + N().fx(area, 2) + '</span>'],
      ]);
    }
    L.side.append(
      slider({ label: '$\\theta$', min: 0, max: 3.14, step: 0.01, value: th, onInput: (x) => { th = x; S.render(); }, format: (x) => N().fx(x * 180 / Math.PI, 0) + '°' }),
      slider({ label: '$|\\underline{v}|$', min: 0, max: 3, step: 0.05, value: lv, onInput: (x) => { lv = x; S.render(); } }),
      slider({ label: 'inclinazione', min: -1.5, max: 1.5, step: 0.02, value: tilt, onInput: (x) => { tilt = x; S.render(); }, format: (x) => N().fx(x * 180 / Math.PI, 0) + '°' }),
      check('scambia l’ordine: $\\underline{v}\\wedge\\underline{u}$', flip, (x) => { flip = x; S.render(); }),
      info, GAL.note('L’arco arancione va dal primo al secondo fattore: visto dalla punta di $\\underline{u}\\wedge\\underline{v}$ la rotazione è antioraria (regola della mano destra). Scambiando i fattori il verso si inverte.'));
    S.setDraw(draw);
  };

  labs['pv-misto'] = function (m) {
    const { slider, readout, seg } = ui();
    const u = [1.6, 0, 0], v = [0.6, 1.5, 0];
    let t = [0.5, 0.4, 1.3];
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 2.2, box: 2.6, az: 0.55, el: 0.3, center: [0.7, 0.7, 0.5] });
    const info = readout();
    let sls;
    function draw(s) {
      const O = [0, 0, 0];
      const V = [O, u, add(u, v), v].map((p) => p);
      const Tp = V.map((p) => add(p, t));
      const vol = dot(cross(u, v), t);
      const col = Math.abs(vol) < 1e-6 ? 'var(--c-gray)' : vol > 0 ? 'var(--c-blue)' : 'var(--c-red)';
      const faces = [[V[0], V[1], V[2], V[3]], [Tp[0], Tp[1], Tp[2], Tp[3]], [V[0], V[1], Tp[1], Tp[0]], [V[1], V[2], Tp[2], Tp[1]], [V[2], V[3], Tp[3], Tp[2]], [V[3], V[0], Tp[0], Tp[3]]];
      faces.forEach((f, i) => s.poly(f, { fill: col, fop: i === 0 ? 0.16 : 0.07, color: col, w: 0.9, op: 0.85 }));
      const n = cross(u, v);
      s.arrow(O, mul(unit(n), 2.2), { color: 'var(--c-red)', w: 1.6, dash: '5 4', op: 0.8 });
      s.label('n', '\\underline{u}\\wedge\\underline{v}', mul(unit(n), 2.35), { color: 'var(--c-red)', small: true });
      s.seg(t, [t[0], t[1], 0], { color: 'var(--c-gray)', dash: '3 4', w: 1.2 });
      s.arrow(O, u, { color: 'var(--c-blue)', w: 2.8 });
      s.arrow(O, v, { color: 'var(--c-teal)', w: 2.8 });
      s.arrow(O, t, { color: 'var(--c-violet)', w: 2.8 });
      s.tip('u', '\\underline{u}', O, u, 'var(--c-blue)');
      s.tip('v', '\\underline{v}', O, v, 'var(--c-teal)');
      s.tip('t', '\\underline{t}', O, t, 'var(--c-violet)');
      info.set([
        ['', T(`\\underline{u}\\wedge\\underline{v}\\cdot\\underline{t} = \\det\\begin{pmatrix} 1{,}6 & 0 & 0 \\\\ ${tn(v[0])} & ${tn(v[1])} & 0 \\\\ ${tn(t[0])} & ${tn(t[1])} & ${tn(t[2])}\\end{pmatrix} = ${tn(vol, 3)}`)],
        ['volume', T(`|\\underline{u}\\wedge\\underline{v}\\cdot\\underline{t}| = ${tn(Math.abs(vol), 3)}`)],
        ['', Math.abs(vol) < 1e-6 ? '<span class="badge no">prodotto misto nullo: vettori complanari (dipendenti)</span>' : vol > 0 ? '<span class="badge ok">prodotto misto positivo: terna positiva</span>' : '<span class="badge no">prodotto misto negativo: terna negativa</span>'],
      ]);
    }
    sls = [0, 1, 2].map((k) => slider({ label: `$t_${['x', 'y', 'z'][k]}$`, min: -2, max: 2, step: 0.05, value: t[k], onInput: (x) => { t[k] = x; S.render(); } }));
    const pre = seg([['pos', 'positiva'], ['neg', 'negativa'], ['cop', 'complanari']], 'pos', (x) => {
      t = x === 'pos' ? [0.5, 0.4, 1.3] : x === 'neg' ? [0.5, 0.4, -1.3] : [1.1, 1.2, 0];
      sls.forEach((sl, k) => sl.setValue(t[k]));
      S.render();
    }, 'Configurazione');
    L.side.append(pre, ...sls, info, GAL.note('Con $\\underline{u}$, $\\underline{v}$ nel piano $xy$ il volume è area di base per altezza: conta solo la quota $t_z$, cioè la componente di $\\underline{t}$ lungo $\\underline{u}\\wedge\\underline{v}$.'));
    S.setDraw(draw);
  };

  /* ============================================================ CAPITOLO 10: base ortonormale positiva */
  labs['base-on'] = function (m) {
    const { readout, btn } = ui();
    const v = [1, 1, 0], w = [1, 0, 1];
    let step = 0;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 1.25, box: 1.6, az: 0.75, el: 0.35, center: [0.3, 0.1, 0.25] });
    const info = readout();
    const u1 = unit(v);
    const pr = mul(v, dot(v, w) / dot(v, v));
    const t2 = sub(w, pr);
    const u2 = unit(t2);
    const u3 = cross(u1, u2);
    function draw(s) {
      const O = [0, 0, 0];
      s.arrow(O, v, { color: 'var(--c-blue)', w: 2, op: step >= 1 ? 0.35 : 1 });
      s.arrow(O, w, { color: 'var(--c-teal)', w: 2, op: step >= 2 ? 0.35 : 1 });
      s.tip('v', '\\underline{v}', O, v, 'var(--c-blue)');
      s.tip('w', '\\underline{w}', O, w, 'var(--c-teal)');
      if (step >= 1) { s.arrow(O, u1, { color: 'var(--c-red)', w: 3.2 }); s.tip('u1', '\\underline{u}_1', O, u1, 'var(--c-red)', 18); }
      if (step >= 2) {
        s.arrow(O, pr, { color: 'var(--c-gray)', w: 2, dash: '5 4' });
        s.seg(pr, w, { color: 'var(--c-gray)', dash: '3 4', w: 1.4 });
        s.arrow(O, t2, { color: 'var(--c-violet)', w: 2, op: 0.6 });
        s.arrow(O, u2, { color: 'var(--c-red)', w: 3.2 });
        s.tip('u2', '\\underline{u}_2', O, u2, 'var(--c-red)', 18);
        s.rightAngle(O, u1, u2, 0.18);
      }
      if (step >= 3) {
        s.arrow(O, u3, { color: 'var(--c-red)', w: 3.2 });
        s.tip('u3', '\\underline{u}_3', O, u3, 'var(--c-red)', 18);
        s.rightAngle(O, u1, u3, 0.18); s.rightAngle(O, u2, u3, 0.18);
      }
      const rows = [['dati', T('\\underline{v}=(1,1,0),\\ \\ \\underline{w}=(1,0,1)')]];
      if (step >= 1) rows.push(['passo 1', T('\\underline{u}_1=\\frac{\\underline{v}}{|\\underline{v}|}=\\tfrac{1}{\\sqrt2}(1,1,0)')]);
      if (step >= 2) rows.push(['passo 2', T('\\underline{t}_2=\\underline{w}-\\frac{\\underline{v}\\cdot\\underline{w}}{|\\underline{v}|^2}\\underline{v}=\\left(\\tfrac12,-\\tfrac12,1\\right),\\ \\underline{u}_2=\\tfrac{1}{\\sqrt6}(1,-1,2)')]);
      if (step >= 3) rows.push(['passo 3', T('\\underline{u}_3=\\underline{u}_1\\wedge\\underline{u}_2=\\tfrac1{\\sqrt3}(1,-1,-1)')]);
      if (step >= 3) rows.push(['', '<span class="badge ok">moduli 1, prodotti scalari nulli, terna positiva</span>']);
      info.set(rows);
    }
    const nx = btn('Passo successivo', 'play', () => { step = (step + 1) % 4; nx.setLabel(step === 3 ? 'Ricomincia' : 'Passo successivo', step === 3 ? 'reset' : 'play'); S.render(); }, 'pri');
    L.side.append(h('div', { class: 'lab-ctl' }, nx), info, GAL.note('Sono i numeri dell’Esempio 10.9: il secondo vettore si ottiene togliendo a $\\underline{w}$ la sua proiezione su $\\underline{v}$ (tratteggio grigio), il terzo con il prodotto vettoriale.'));
    S.setDraw(draw);
  };

  /* ============================================================ CAPITOLO 11: retta e piano */
  labs['r-retta'] = function (m) {
    const { slider, readout, check } = ui();
    const P0 = [1, 3, 5], P1 = [2, 2, 3], v = sub(P1, P0);
    let t = 0.6, other = false;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 4.2, box: 7, az: 0.55, el: 0.3, ground: true, gridStep: 2, center: [1.5, 2.5, 3] });
    const info = readout();
    function draw(s) {
      s.line(P0, v, { color: 'var(--c-blue)', w: 2.2 });
      const Pt = add(P0, mul(v, t));
      s.seg(Pt, [Pt[0], Pt[1], 0], { color: 'var(--c-gray)', dash: '3 4', w: 1 });
      s.arrow(P0, Pt, { color: 'var(--c-red)', w: 3 });
      s.arrow(P0, P1, { color: 'var(--c-teal)', w: 2.4, op: 0.8 });
      s.point(P0, { color: 'var(--c-blue)', r: 4.5 });
      s.point(P1, { color: 'var(--c-teal)', r: 4 });
      s.point(Pt, { color: 'var(--c-red)', r: 5 });
      s.label('P0', 'P_0', P0, { dx: -16, dy: -10, color: 'var(--c-blue)' });
      s.label('P1', 'P_1', P1, { dx: 16, dy: -8, color: 'var(--c-teal)' });
      s.label('Pt', 'P(t)', Pt, { dx: 22, dy: 10, color: 'var(--c-red)' });
      s.label('r', 'r', add(P0, mul(v, -2.2)), { dx: 12, color: 'var(--c-blue)' });
      if (other) {
        const Q0 = add(P0, mul(v, -3));
        s.point(Q0, { color: 'var(--c-violet)', r: 4.5 });
        s.arrow(Q0, add(Q0, mul(v, 2)), { color: 'var(--c-violet)', w: 2.4 });
        s.label('Q0', "P_0'", Q0, { dx: -18, dy: 0, color: 'var(--c-violet)' });
      }
      const rows = [
        ['retta', T('r:\\ \\begin{cases} x = 1+t \\\\ y = 3-t \\\\ z = 5-2t\\end{cases}')],
        ['punto', T(`P(${tn(t, 2)}) = ${vt(Pt, 2)}`)],
        ['', Math.abs(t) < 1e-9 ? 'per ' + K('t=0') + ' si ottiene ' + K('P_0') : Math.abs(t - 1) < 1e-9 ? 'per ' + K('t=1') + ' si ottiene ' + K('P_1') : (t < 0 ? K('t<0') + ': si va nel verso opposto a ' + K('\\underline{v}') : K('t>0') + ': si va nel verso di ' + K('\\underline{v}'))],
      ];
      if (other) rows.push(['stessa retta', T("P_0' = (-2,6,11),\\ \\ 2\\underline{v} = (2,-2,-4)")]);
      info.set(rows);
    }
    L.side.append(
      slider({ label: '$t$', min: -3, max: 3, step: 0.05, value: t, onInput: (x) => { t = x; S.render(); } }),
      check('mostra un’altra parametrizzazione', other, (x) => { other = x; S.render(); }),
      info, GAL.note('Dati dell’Esempio 11.6: $P_0=(1,3,5)$, $P_1=(2,2,3)$, $\\underline{v}=(1,-1,-2)$. Lo stesso insieme di punti si descrive con un qualsiasi punto della retta e un qualsiasi vettore parallelo non nullo.'));
    S.setDraw(draw);
  };

  labs['r-piano'] = function (m) {
    const { slider, readout } = ui();
    const P0 = [1, 2, 3], v1 = [-2, 0, -2], v2 = [0, -1, 2];
    let tt = 0.5, ss = 0.8;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 3.6, box: 5.5, az: 0.95, el: 0.28, center: [0.5, 1.6, 2.6] });
    const info = readout();
    const M = cross(v1, v2);   // (−2, 4, 2)
    const d = dot(M, P0);
    function draw(s) {
      s.plane(M, d, { fill: 'var(--c-blue)', fop: 0.1, color: 'var(--c-blue)', w: 0.8, op: 0.9 });
      const A = add(P0, mul(v1, tt)), B = add(P0, mul(v2, ss)), P = add(A, mul(v2, ss));
      s.seg(A, P, { color: 'var(--c-gray)', dash: '4 4', w: 1.3 });
      s.seg(B, P, { color: 'var(--c-gray)', dash: '4 4', w: 1.3 });
      s.arrow(P0, add(P0, v1), { color: 'var(--c-blue)', w: 2.6 });
      s.arrow(P0, add(P0, v2), { color: 'var(--c-teal)', w: 2.6 });
      s.arrow(P0, P, { color: 'var(--c-violet)', w: 2.2 });
      s.arrow(P0, add(P0, mul(unit(M), 2.2)), { color: 'var(--c-red)', w: 3 });
      s.rightAngle(P0, v1, M, 0.4);
      s.point(P0, { color: 'var(--ink)', r: 4 });
      s.point(P, { color: 'var(--c-violet)', r: 4.5 });
      s.label('P0', 'P_0', P0, { dx: -14, dy: 12 });
      s.label('P', 'P', P, { dx: 12, dy: -10, color: 'var(--c-violet)' });
      s.tip('v1', '\\underline{v}_1', P0, add(P0, v1), 'var(--c-blue)');
      s.tip('v2', '\\underline{v}_2', P0, add(P0, v2), 'var(--c-teal)');
      s.tip('M', '\\underline{M}', P0, add(P0, mul(unit(M), 2.2)), 'var(--c-red)');
      const PP = sub(P, P0);
      info.set([
        ['parametrica', T('\\pi:\\ \\begin{cases} x = 1-2t \\\\ y = 2-s \\\\ z = 3-2t+2s\\end{cases}')],
        ['normale', T('\\underline{M} = \\underline{v}_1\\wedge\\underline{v}_2 = (-2,4,2)')],
        ['cartesiana', T('-2x+4y+2z-12=0\\ \\iff\\ x-2y-z+6=0')],
        ['verifica', T(`(P-P_0)\\cdot\\underline{M} = ${vt(PP, 2)}\\cdot(-2,4,2) = ${tn(dot(PP, M), 2)}`)],
      ]);
    }
    L.side.append(
      slider({ label: '$t$', min: -2, max: 2, step: 0.05, value: tt, onInput: (x) => { tt = x; S.render(); } }),
      slider({ label: '$s$', min: -2, max: 2, step: 0.05, value: ss, onInput: (x) => { ss = x; S.render(); } }),
      info, GAL.note('Dati dell’Esempio 11.24. Qualunque punto $P$ del piano dà $(P-P_0)\\cdot\\underline{M}=0$: è l’equazione cartesiana (Teorema 11.9).'));
    S.setDraw(draw);
  };

  /* ============================================================ CAPITOLO 12 */
  labs['r-complanari'] = function (m) {
    const { slider, readout, btn } = ui();
    const P0 = [1, 0, 1], v = [-1, 2, 2], w = [-1, 1, -1];
    let hh = 2;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 3.1, box: 3.6, az: 2.05, el: 0.24, center: [0.4, 0.5, 0.2] });
    const info = readout();
    const n = cross(v, w);
    let sl;
    function draw(s) {
      const P1 = [0, hh, -1];
      const det = dot(sub(P0, P1), cross(v, w));    // = 3h − 2 (con P0 − P1)
      s.plane(n, dot(n, P0), { fill: 'var(--c-blue)', fop: 0.08, color: 'var(--c-blue)', w: 0.7, op: 0.8 });
      s.line(P0, v, { color: 'var(--c-blue)', w: 2.6 });
      s.line(P1, w, { color: 'var(--c-violet)', w: 2.6 });
      // distanza di P1 dal piano α
      const dd = (dot(n, P1) - dot(n, P0)) / dot(n, n);
      const F = sub(P1, mul(n, dd));
      if (Math.abs(det) > 1e-6) s.seg(P1, F, { color: 'var(--c-red)', dash: '4 3', w: 1.6 });
      s.point(P0, { color: 'var(--c-blue)', r: 4.5 });
      s.point(P1, { color: 'var(--c-violet)', r: 4.5 });
      s.label('P0', 'P_0', P0, { dx: -14, dy: -10, color: 'var(--c-blue)' });
      s.label('P1', 'P_1', P1, { dx: 14, dy: -10, color: 'var(--c-violet)' });
      s.label('r', 'r', add(P0, mul(v, 1.3)), { dx: 12, color: 'var(--c-blue)' });
      s.label('r1', "r'", add(P1, mul(w, -1.6)), { dx: 12, color: 'var(--c-violet)' });
      s.label('al', '\\alpha', add(P0, add(mul(v, -1.1), mul(w, 1.4))), { color: 'var(--c-blue)' });
      const rows = [
        ['determinante', T(`\\det\\begin{pmatrix}1&-h&2\\\\-1&2&2\\\\-1&1&-1\\end{pmatrix} = 3h-2 = ${tn(3 * hh - 2, 2)}`)],
      ];
      if (Math.abs(3 * hh - 2) < 0.011) {
        rows.push(['', '<span class="badge ok">complanari e non parallele: incidenti</span>']);
        rows.push(['punto comune', T('\\left(\\tfrac43,-\\tfrac23,\\tfrac13\\right)')]);
        s.point([4 / 3, -2 / 3, 1 / 3], { color: 'var(--c-red)', r: 6 });
      } else rows.push(['', '<span class="badge no">sghembe: ' + K('P_1') + ' non sta sul piano ausiliario ' + K('\\alpha') + '</span>']);
      info.set(rows);
      void det;
    }
    sl = slider({ label: '$h$', min: -2, max: 3, step: 0.01, value: hh, onInput: (x) => { hh = x; S.render(); } });
    L.side.append(sl, h('div', { class: 'lab-ctl' }, btn('Porta h a 2/3', null, () => { hh = 2 / 3; sl.setValue(0.67); S.render(); })), info,
      GAL.note('Il piano $\\alpha$ contiene $r$ ed è parallelo a $r\'$. Il tratto rosso misura quanto $P_1$ dista da $\\alpha$: le rette sono complanari esattamente quando si annulla.'));
    S.setDraw(draw);
  };

  labs['r-tre-piani'] = function (m) {
    const { seg, readout, slider } = ui();
    const CONF = {
      uno: { planes: [[[1, 1, 1], 3], [[1, -1, 0], 0], [[1, 0, 2], 3]], label: 'Esempio 12.7' },
      fascio: { planes: [[[1, 1, 0], 1], [[1, 0, -1], 0], [[0, 1, 1], 1]], label: 'Esempio 12.8, k = 1' },
      prisma: { planes: [[[1, 1, 0], 1], [[1, 0, -1], 0], [[0, 1, 1], 2.5]], label: 'Esempio 12.8, k ≠ 1' },
      par: { planes: [[[0, 0, 1], -1.5], [[0, 0, 1], 0.2], [[1, 0, 1], 0.5]], label: 'due piani paralleli' },
    };
    let key = 'uno', k = 2.5;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 2.5, box: 2.4, az: 0.65, el: 0.32, center: [0.5, 0.5, 0.6] });
    const info = readout();
    const colors = ['var(--c-blue)', 'var(--c-teal)', 'var(--c-violet)'];
    const kRow = slider({ label: '$k$', min: -1, max: 3, step: 0.05, value: k, onInput: (x) => { k = x; S.render(); } });
    function det3(A) { return A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0]) + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]); }
    function draw(s) {
      let P = CONF[key].planes.map((p) => [p[0].slice(), p[1]]);
      kRow.style.display = key === 'prisma' || key === 'fascio' ? '' : 'none';
      if (key === 'prisma' || key === 'fascio') P[2][1] = k;
      P.forEach(([n, d], i) => s.plane(n, d, { fill: colors[i], fop: 0.13, color: colors[i], w: 0.9, op: 0.9 }));
      // rette di intersezione a due a due
      for (let i = 0; i < 3; i++) for (let j = i + 1; j < 3; j++) {
        const [n1, d1] = P[i], [n2, d2] = P[j];
        const dir = cross(n1, n2);
        if (norm(dir) < 1e-9) continue;
        // un punto: risolve n1·p=d1, n2·p=d2 con p = a n1 + b n2
        const a11 = dot(n1, n1), a12 = dot(n1, n2), a22 = dot(n2, n2), D = a11 * a22 - a12 * a12;
        const a = (d1 * a22 - d2 * a12) / D, b = (d2 * a11 - d1 * a12) / D;
        s.line(add(mul(n1, a), mul(n2, b)), dir, { color: 'var(--ink-2)', w: 2 });
      }
      const A = P.map((p) => p[0]);
      const dt = det3(A);
      const rows = [['', CONF[key].label]];
      rows.push(['det delle normali', T(`\\det = ${N().tn(dt, 3)}`)]);
      if (Math.abs(dt) > 1e-9) {
        // soluzione con Cramer
        const b = P.map((p) => p[1]);
        const sol = [0, 1, 2].map((c) => det3(A.map((r, i) => r.map((x, j) => (j === c ? b[i] : x)))) / dt);
        s.point(sol, { color: 'var(--c-red)', r: 6 });
        rows.push(['', '<span class="badge ok">un solo punto comune: il sistema ha una sola soluzione</span>']);
        rows.push(['punto', T(vt(sol, 2))]);
      } else {
        const par = A.some((x, i) => A.some((y, j) => j > i && norm(cross(x, y)) < 1e-9));
        let common = false;
        if (!par) {
          const [n1, d1] = P[0], [n2, d2] = P[1];
          const a11 = dot(n1, n1), a12 = dot(n1, n2), a22 = dot(n2, n2), D = a11 * a22 - a12 * a12;
          const p = add(mul(n1, (d1 * a22 - d2 * a12) / D), mul(n2, (d2 * a11 - d1 * a12) / D));
          common = Math.abs(dot(P[2][0], p) - P[2][1]) < 0.03;
        }
        rows.push(['', common ? '<span class="badge ok">una retta comune: infinite soluzioni</span>' : '<span class="badge no">nessun punto comune: il sistema non ha soluzioni</span>']);
        if (par) rows.push(['', 'due normali sono parallele: due piani sono paralleli']);
        else rows.push(['', 'normali complanari: le tre rette di intersezione sono parallele' + (common ? ' e coincidono' : '')]);
      }
      info.set(rows);
    }
    L.side.append(seg([['uno', 'un punto'], ['fascio', 'una retta'], ['prisma', 'prisma'], ['par', 'paralleli']], key, (x) => {
      key = x;
      k = x === 'fascio' ? 1 : x === 'prisma' ? 2.5 : k;
      kRow.setValue(k);
      S.render();
    }, 'Configurazione'), kRow, info, GAL.note('Nell’Esempio 12.8 il terzo piano è $y+z-k=0$: per $k=1$ contiene la retta comune agli altri due, per ogni altro $k$ i tre piani formano un «prisma» senza punti comuni.'));
    S.setDraw(draw);
  };

  labs['r-fascio'] = function (m) {
    const { slider, readout, btn } = ui();
    const n1 = [1, -2, 3], d1 = -1, n2 = [2, -1, 4], d2 = -3;   // x−2y+3z+1=0, 2x−y+4z+3=0
    let phi = 0.6, anim = null;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 3.2, box: 3.2, az: 0.4, el: 0.25 });
    const info = readout();
    const dir = cross(n1, n2);
    const a11 = dot(n1, n1), a12 = dot(n1, n2), a22 = dot(n2, n2), D = a11 * a22 - a12 * a12;
    const p0 = add(mul(n1, (d1 * a22 - d2 * a12) / D), mul(n2, (d2 * a11 - d1 * a12) / D));
    let sl;
    function draw(s) {
      const lam = Math.cos(phi), mu = Math.sin(phi);
      const n = add(mul(n1, lam), mul(n2, mu)), d = lam * d1 + mu * d2;
      s.plane(n1, d1, { fill: 'var(--c-gray)', fop: 0.05, color: 'var(--c-gray)', w: 0.6, op: 0.7 });
      s.plane(n2, d2, { fill: 'var(--c-gray)', fop: 0.05, color: 'var(--c-gray)', w: 0.6, op: 0.7 });
      s.plane(n, d, { fill: 'var(--c-violet)', fop: 0.2, color: 'var(--c-violet)', w: 1.2 });
      s.line(p0, dir, { color: 'var(--c-red)', w: 3.2 });
      s.label('r', 'r', add(p0, mul(unit(dir), 2.6)), { dx: 12, color: 'var(--c-red)' });
      const c = (x) => N().tn(x, 2);
      const A = n1[0] * lam + n2[0] * mu, B = n1[1] * lam + n2[1] * mu, C = n1[2] * lam + n2[2] * mu, Dd = 1 * lam + 3 * mu;
      info.set([
        ['', T('\\lambda(x-2y+3z+1)+\\mu(2x-y+4z+3)=0')],
        ['', T(`\\lambda = ${c(lam)},\\ \\ \\mu = ${c(mu)}`)],
        ['piano', T(`${c(A)}x ${B < 0 ? '' : '+'}${c(B)}y ${C < 0 ? '' : '+'}${c(C)}z ${Dd < 0 ? '' : '+'}${c(Dd)} = 0`)],
        ['', Math.abs(lam) < 0.01 ? '<span class="badge neu">λ = 0: è il secondo piano, perso scrivendo λ = 1 (Osservazione 12.2)</span>' : ''],
      ]);
    }
    sl = slider({ label: 'parametro', min: 0, max: 3.14, step: 0.01, value: phi, onInput: (x) => { phi = x; S.render(); }, format: (x) => '(λ, μ) = (' + N().fx(Math.cos(x), 2) + '; ' + N().fx(Math.sin(x), 2) + ')' });
    sl.style.gridTemplateColumns = 'auto minmax(0,1fr)';
    sl.querySelector('output').style.gridColumn = '1 / -1';
    sl.querySelector('output').style.textAlign = 'left';
    const go = btn('Anima', 'play', () => {
      if (anim) anim.stop();
      const from = phi;
      anim = GAL.animate(4000, (t) => { phi = (from + Math.PI * t) % Math.PI; sl.setValue(N().rnd(phi, 2)); S.render(); });
    });
    L.side.append(sl, h('div', { class: 'lab-ctl' }, go), info, GAL.note('La retta $r$ è quella dell’Esempio 12.10. Ogni coppia $(\\lambda,\\mu)\\neq(0,0)$ dà un piano che contiene $r$; coppie proporzionali danno lo stesso piano, quindi basta un parametro (qui un angolo).'));
    S.setDraw(draw);
  };

  labs['r-sghembe'] = function (m) {
    const { slider, readout, btn } = ui();
    const P0 = [1, -1, 2], v1 = [1, 1, 1], Q0 = [0, -1, 1], v2 = [2, 1, -2];
    let t = 0.6, sv = -0.8;
    const L = lay(m);
    const S = new Scene3D(L.main, { range: 2.8, box: 3.4, az: 1.15, el: 0.32, center: [0.4, -0.6, 1.1] });
    const info = readout();
    const n = cross(v1, v2);
    const dmin = Math.abs(dot(sub(Q0, P0), n)) / norm(n);
    const Ps = add(P0, mul(v1, -9 / 13)), Qs = add(Q0, mul(v2, -1 / 13));
    let st, ss;
    function draw(s) {
      // piano per r ortogonale a v1∧v2 (secondo metodo)
      s.plane(n, dot(n, P0), { fill: 'var(--c-blue)', fop: 0.06, color: 'var(--c-blue)', w: 0.6, op: 0.6 });
      s.line(P0, v1, { color: 'var(--c-blue)', w: 2.6 });
      s.line(Q0, v2, { color: 'var(--c-violet)', w: 2.6 });
      s.seg(Ps, Qs, { color: 'var(--c-red)', w: 2, dash: '5 4' });
      s.rightAngle(Ps, v1, sub(Qs, Ps), 0.25);
      const P = add(P0, mul(v1, t)), Q = add(Q0, mul(v2, sv));
      s.seg(P, Q, { color: 'var(--c-orange)', w: 2.6 });
      s.point(P, { color: 'var(--c-blue)', r: 5 });
      s.point(Q, { color: 'var(--c-violet)', r: 5 });
      s.label('P', 'P', P, { dx: -12, dy: -10, color: 'var(--c-blue)' });
      s.label('Q', 'Q', Q, { dx: 12, dy: -10, color: 'var(--c-violet)' });
      s.label('r', 'r', add(P0, mul(v1, 1.4)), { dx: 12, color: 'var(--c-blue)' });
      s.label('s', 's', add(Q0, mul(v2, 1.1)), { dx: 12, color: 'var(--c-violet)' });
      const d = norm(sub(Q, P));
      info.set([
        ['d(P, Q)', T(`|Q-P| = ${N().tn(d, 3)}`)],
        ['d(r, s)', T(`\\frac{|(Q_0-P_0)\\cdot(\\underline{v}_1\\wedge\\underline{v}_2)|}{|\\underline{v}_1\\wedge\\underline{v}_2|} = \\frac{4}{\\sqrt{26}} = \\frac{2\\sqrt{26}}{13}\\approx ${N().tn(dmin, 3)}`)],
        ['', Math.abs(d - dmin) < 0.004 ? '<span class="badge ok">minimo raggiunto: PQ è la perpendicolare comune</span>' : `<span class="badge neu">eccesso rispetto al minimo: ${N().fx(d - dmin, 3)}</span>`],
      ]);
    }
    st = slider({ label: '$t$', min: -2.5, max: 1.5, step: 0.01, value: t, onInput: (x) => { t = x; S.render(); } });
    ss = slider({ label: '$s$', min: -1.5, max: 1.2, step: 0.01, value: sv, onInput: (x) => { sv = x; S.render(); } });
    L.side.append(st, ss, h('div', { class: 'lab-ctl' }, btn('Vai al minimo', null, () => { t = -9 / 13; sv = -1 / 13; st.setValue(N().rnd(t, 2)); ss.setValue(N().rnd(sv, 2)); S.render(); })), info,
      GAL.note('Rette dell’Esempio 12.18. Il tratteggio rosso è la perpendicolare comune ($t=-\\frac9{13}$, $s=-\\frac1{13}$); il piano azzurro contiene $r$ ed è parallelo a $s$ (secondo metodo).'));
    S.setDraw(draw);
  };
})();
