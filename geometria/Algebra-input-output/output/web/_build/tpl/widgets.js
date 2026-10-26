/* Laboratori interattivi 2D e strumenti comuni (piano SVG, controlli, letture con KaTeX). */
(function () {
  'use strict';
  const GAL = window.GAL = window.GAL || {};
  const labs = GAL.labs = GAL.labs || {};
  const NS = 'http://www.w3.org/2000/svg';
  const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------ DOM */
  function h(tag, attrs, ...kids) {
    const el = document.createElement(tag);
    if (attrs) for (const k in attrs) {
      const v = attrs[k];
      if (v == null || v === false) continue;
      if (k === 'class') el.className = v;
      else if (k === 'html') el.innerHTML = v;
      else if (k === 'text') el.textContent = v;
      else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v === true ? '' : v);
    }
    for (const c of kids.flat()) if (c != null) el.append(c);
    return el;
  }
  function s(tag, attrs) {
    const el = document.createElementNS(NS, tag);
    if (attrs) for (const k in attrs) if (attrs[k] != null) el.setAttribute(k, attrs[k]);
    return el;
  }
  const K = (tex, d) => GAL.tex ? GAL.tex(tex, d) : tex;
  GAL.h = h; GAL.s = s;

  /* ------------------------------------------------------------ numeri */
  const EPS = 1e-9;
  function rnd(x, d) { const p = Math.pow(10, d == null ? 2 : d); return Math.round(x * p) / p; }
  // numero in TeX con virgola decimale italiana
  function tn(x, d) {
    let r = rnd(x, d == null ? 2 : d);
    if (Math.abs(r) < EPS) r = 0;
    const neg = r < 0;
    const str = Math.abs(r).toString().replace('.', '{,}');
    return (neg ? '-' : '') + str;
  }
  // numero in testo semplice
  function fx(x, d) { return tn(x, d).replace('{,}', ',').replace('-', '−'); }
  function gcd(a, b) { a = Math.abs(a); b = Math.abs(b); while (b) { [a, b] = [b, a % b]; } return a || 1; }
  // frazione semplice (denominatore piccolo) se esiste
  function frac(x, maxDen) {
    maxDen = maxDen || 12;
    for (let q = 1; q <= maxDen; q++) {
      const p = Math.round(x * q);
      if (Math.abs(p / q - x) < 1e-7) {
        const g = gcd(p, q);
        return [p / g, q / g];
      }
    }
    return null;
  }
  function tfrac(x, d) {
    const f = frac(x, 16);
    if (!f) return tn(x, d);
    const [p, q] = f;
    if (q === 1) return String(p);
    return (p < 0 ? '-' : '') + `\\tfrac{${Math.abs(p)}}{${q}}`;
  }
  // angolo come multiplo di π (se «bello») in TeX
  function piTex(theta) {
    const f = frac(theta / Math.PI, 24);
    if (!f) return null;
    const [p, q] = f;
    if (p === 0) return '0';
    const sgn = p < 0 ? '-' : '';
    const a = Math.abs(p);
    const num = a === 1 ? '\\pi' : a + '\\pi';
    return q === 1 ? sgn + num : `${sgn}\\tfrac{${num}}{${q}}`;
  }
  function angTex(theta) {
    const p = piTex(theta);
    return p !== null ? p : tn(theta, 3);
  }
  // radice «bella»: √n o intero
  function sqrtTex(x2) {
    const r = Math.sqrt(x2);
    if (Math.abs(r - Math.round(r)) < 1e-7) return String(Math.round(r));
    const n = Math.round(x2);
    if (Math.abs(n - x2) < 1e-7) {
      let a = 1, b = n;
      for (let k = Math.floor(Math.sqrt(n)); k > 1; k--) if (n % (k * k) === 0) { a = k; b = n / (k * k); break; }
      return (a > 1 ? a : '') + `\\sqrt{${b}}`;
    }
    return tn(r, 3);
  }
  // numero complesso a+bi in TeX
  function cTex(a, b, d) {
    const A = Math.abs(a) < 5e-4 ? 0 : a, B = Math.abs(b) < 5e-4 ? 0 : b;
    const bs = Math.abs(rnd(B, d == null ? 2 : d));
    const bpart = bs === 1 ? 'i' : tn(Math.abs(B), d) + 'i';
    if (A === 0 && B === 0) return '0';
    if (B === 0) return tn(A, d);
    if (A === 0) return (B < 0 ? '-' : '') + bpart;
    return tn(A, d) + (B < 0 ? '-' : '+') + bpart;
  }
  const NUM = { rnd, tn, fx, frac, tfrac, piTex, angTex, sqrtTex, cTex, gcd };
  GAL.num = NUM;

  /* ------------------------------------------------------------ controlli */
  function slider(o) {
    const id = 'r' + Math.random().toString(36).slice(2, 8);
    const out = h('output', { for: id });
    const inp = h('input', { type: 'range', id, min: o.min, max: o.max, step: o.step || 1, value: o.value, 'aria-label': o.aria || '' });
    const fmt = o.format || ((v) => fx(v, 2));
    const set = (v) => { out.innerHTML = ''; const f = fmt(Number(v)); if (typeof f === 'string' && f.startsWith('$')) out.innerHTML = K(f.slice(1, -1)); else out.textContent = f; };
    inp.addEventListener('input', () => { set(inp.value); o.onInput(Number(inp.value)); });
    set(o.value);
    const lab = h('label', { for: id, html: o.label.startsWith('$') ? K(o.label.slice(1, -1)) : o.label });
    const row = h('div', { class: 'lab-row' }, lab, inp, out);
    row.input = inp;
    row.setValue = (v) => { inp.value = v; set(v); };
    return row;
  }
  function seg(options, value, onChange, aria) {
    const box = h('div', { class: 'seg', role: 'group', 'aria-label': aria || '' });
    const btns = options.map(([val, label]) => {
      const b = h('button', { type: 'button', 'aria-pressed': val === value ? 'true' : 'false' });
      if (label.startsWith('$')) b.innerHTML = K(label.slice(1, -1)); else b.innerHTML = label.replace(/\$(.+?)\$/g, (m, t) => K(t));
      b.addEventListener('click', () => { set(val); onChange(val); });
      return [val, b];
    });
    function set(v) { btns.forEach(([val, b]) => b.setAttribute('aria-pressed', val === v ? 'true' : 'false')); }
    btns.forEach(([, b]) => box.append(b));
    box.set = set;
    return box;
  }
  function btn(label, icon, onClick, cls) {
    const b = h('button', { type: 'button', class: 'lbtn' + (cls ? ' ' + cls : '') });
    if (icon) b.innerHTML = `<svg class="ic" aria-hidden="true"><use href="#i-${icon}"/></svg>`;
    const lab = h('span', { html: label.replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c])).replace(/\$(.+?)\$/g, (mm, t) => K(t)) });
    b.append(lab);
    b.addEventListener('click', onClick);
    b.setLabel = (t, ic) => { b.innerHTML = ic ? `<svg class="ic" aria-hidden="true"><use href="#i-${ic}"/></svg>` : ''; b.append(document.createTextNode(t)); };
    return b;
  }
  function check(label, value, onChange) {
    const inp = h('input', { type: 'checkbox' });
    inp.checked = !!value;
    inp.addEventListener('change', () => onChange(inp.checked));
    const l = h('label', { class: 'chk' }, inp, h('span', { html: label.replace(/\$(.+?)\$/g, (m, t) => K(t)) }));
    l.input = inp;
    return l;
  }
  function readout() {
    const box = h('div', { class: 'readout', 'aria-live': 'polite' });
    box.set = (rows) => {
      box.innerHTML = rows.filter((r) => r && (typeof r === 'string' || r[1])).map((r) => {
        if (typeof r === 'string') return `<div class="r-row full"><span class="r-v">${r}</span></div>`;
        const [k, v] = r;
        if (!k) return `<div class="r-row full"><span class="r-v">${v}</span></div>`;
        const kk = k.replace(/\$(.+?)\$/g, (mm, t) => K(t));
        return `<div class="r-row"><span class="r-k">${kk}</span><span class="r-v">${v}</span></div>`;
      }).join('');
    };
    return box;
  }
  const T = (tex) => K(tex);
  GAL.ui = { slider, seg, btn, check, readout, h, s, T };

  /* ------------------------------------------------------------ piano cartesiano SVG */
  class Plot {
    constructor(parent, o) {
      this.o = Object.assign({ xmin: -5, xmax: 5, ymin: -4, ymax: 4, W: 560, grid: 1, axes: true, ticks: true, snap: 0.5, axisLabels: null, pad: 0 }, o);
      const { xmin, xmax, ymin, ymax, W } = this.o;
      this.k = W / (xmax - xmin);
      this.W = W;
      this.H = Math.round(this.k * (ymax - ymin));
      this.wrap = h('div', { class: 'lab-plot' });
      this.svg = s('svg', { viewBox: `0 0 ${this.W} ${this.H}`, role: 'img', 'aria-label': o.aria || 'Grafico interattivo' });
      this.gGrid = s('g'); this.gMain = s('g'); this.gTop = s('g'); this.gHandles = s('g');
      this.svg.append(this.gGrid, this.gMain, this.gTop, this.gHandles);
      this.ov = h('div', { style: 'position:absolute;inset:0;pointer-events:none' });
      this.wrap.append(this.svg, this.ov);
      parent.append(this.wrap);
      this.labels = new Map();
      this.used = new Set();
      this.handles = [];
      this.drawGrid();
      this.bindPointer();
    }
    X(x) { return (x - this.o.xmin) * this.k; }
    Y(y) { return (this.o.ymax - y) * this.k; }
    fromPx(px, py) { return [px / this.k + this.o.xmin, this.o.ymax - py / this.k]; }
    drawGrid() {
      const g = this.gGrid, o = this.o;
      g.innerHTML = '';
      if (o.grid) {
        for (let x = Math.ceil(o.xmin / o.grid) * o.grid; x <= o.xmax + EPS; x += o.grid) g.append(s('line', { x1: this.X(x), y1: 0, x2: this.X(x), y2: this.H, class: 'pl-grid' }));
        for (let y = Math.ceil(o.ymin / o.grid) * o.grid; y <= o.ymax + EPS; y += o.grid) g.append(s('line', { x1: 0, y1: this.Y(y), x2: this.W, y2: this.Y(y), class: 'pl-grid' }));
      }
      if (o.axes) {
        const ax = (x1, y1, x2, y2) => {
          g.append(s('line', { x1, y1, x2, y2, class: 'pl-axis' }));
          const a = Math.atan2(y2 - y1, x2 - x1), L = 9, w = 4.5;
          g.append(s('path', { d: `M${x2},${y2} L${x2 - L * Math.cos(a) + w * Math.sin(a)},${y2 - L * Math.sin(a) - w * Math.cos(a)} L${x2 - L * Math.cos(a) - w * Math.sin(a)},${y2 - L * Math.sin(a) + w * Math.cos(a)} Z`, style: 'fill:var(--plot-axis)' }));
        };
        if (o.ymin < 0 && o.ymax > 0) ax(2, this.Y(0), this.W - 2, this.Y(0));
        if (o.xmin < 0 && o.xmax > 0) ax(this.X(0), this.H - 2, this.X(0), 2);
        if (o.ticks) {
          const step = o.tickStep || o.grid || 1;
          for (let x = Math.ceil(o.xmin / step) * step; x <= o.xmax - step / 2; x += step) {
            if (Math.abs(x) < EPS) continue;
            const t = s('text', { x: this.X(x), y: this.Y(0) + 15, class: 'pl-tick', 'text-anchor': 'middle' });
            t.textContent = fx(x, 1);
            g.append(t);
          }
          for (let y = Math.ceil(o.ymin / step) * step; y <= o.ymax - step / 2; y += step) {
            if (Math.abs(y) < EPS) continue;
            const t = s('text', { x: this.X(0) - 6, y: this.Y(y) + 4, class: 'pl-tick', 'text-anchor': 'end' });
            t.textContent = fx(y, 1);
            g.append(t);
          }
        }
        if (o.axisLabels) {
          this.fixedLabel(o.axisLabels[0], o.xmax, 0, { dx: -10, dy: -14, cls: 'muted' });
          this.fixedLabel(o.axisLabels[1], 0, o.ymax, { dx: 18, dy: 8, cls: 'muted' });
        }
      }
    }
    fixedLabel(tex, x, y, opt) {
      const d = h('div', { class: 'pl-tex' + (opt && opt.cls ? ' ' + opt.cls : ''), html: K(tex) });
      this.place(d, x, y, opt);
      this.ov.append(d);
      return d;
    }
    place(d, x, y, opt) {
      opt = opt || {};
      const px = this.X(x) + (opt.dx || 0), py = this.Y(y) + (opt.dy || 0);
      d.style.left = (100 * px / this.W) + '%';
      d.style.top = (100 * py / this.H) + '%';
    }
    // inizio di un nuovo fotogramma
    begin() { this.gMain.innerHTML = ''; this.gTop.innerHTML = ''; this.used = new Set(); }
    end() { for (const [k, d] of this.labels) if (!this.used.has(k)) { d.remove(); this.labels.delete(k); } }
    label(key, tex, x, y, opt) {
      opt = opt || {};
      let d = this.labels.get(key);
      if (!d) { d = h('div', { class: 'pl-tex' }); this.ov.append(d); this.labels.set(key, d); }
      if (d._tex !== tex) { d.innerHTML = K(tex); d._tex = tex; }
      d.style.color = opt.color || '';
      d.classList.toggle('sm', !!opt.small);
      this.place(d, x, y, opt);
      this.used.add(key);
      return d;
    }
    // etichetta vicino alla punta di un vettore, spostata lungo la direzione
    tipLabel(key, tex, x0, y0, x1, y1, color, dist) {
      const a = Math.atan2(this.Y(y1) - this.Y(y0), this.X(x1) - this.X(x0));
      const dd = dist || 16;
      return this.label(key, tex, x1, y1, { dx: Math.cos(a) * dd, dy: Math.sin(a) * dd, color });
    }
    line(x1, y1, x2, y2, st, top) {
      const l = s('line', { x1: this.X(x1), y1: this.Y(y1), x2: this.X(x2), y2: this.Y(y2) });
      this.style(l, Object.assign({ fill: 'none' }, st));
      (top ? this.gTop : this.gMain).append(l);
      return l;
    }
    style(el, st) {
      st = st || {};
      const css = [];
      if (st.color) css.push('stroke:' + st.color);
      if (st.fill) css.push('fill:' + st.fill);
      if (st.op != null) css.push('opacity:' + st.op);
      if (st.fop != null) css.push('fill-opacity:' + st.fop);
      css.push('stroke-width:' + (st.w || 2));
      if (st.dash) css.push('stroke-dasharray:' + st.dash);
      css.push('stroke-linecap:round;stroke-linejoin:round');
      el.setAttribute('style', css.join(';'));
    }
    arrow(x1, y1, x2, y2, st, top) {
      st = Object.assign({ color: 'var(--c-blue)', w: 2.6 }, st);
      const X1 = this.X(x1), Y1 = this.Y(y1), X2 = this.X(x2), Y2 = this.Y(y2);
      const len = Math.hypot(X2 - X1, Y2 - Y1);
      const g = s('g');
      if (len < 1) { (top ? this.gTop : this.gMain).append(g); return g; }
      const L = Math.min(st.head || 13, len * 0.45), w = (st.head || 13) * 0.42;
      const ux = (X2 - X1) / len, uy = (Y2 - Y1) / len;
      const bx = X2 - ux * L, by = Y2 - uy * L;
      const ln = s('line', { x1: X1, y1: Y1, x2: X2 - ux * L * 0.6, y2: Y2 - uy * L * 0.6 });
      this.style(ln, { color: st.color, w: st.w, dash: st.dash, op: st.op });
      const hd = s('path', { d: `M${X2},${Y2} L${bx - uy * w},${by + ux * w} L${bx + uy * w},${by - ux * w} Z` });
      hd.setAttribute('style', `fill:${st.color};stroke:${st.color};stroke-width:1;stroke-linejoin:round${st.op != null ? ';opacity:' + st.op : ''}`);
      g.append(ln, hd);
      (top ? this.gTop : this.gMain).append(g);
      return g;
    }
    poly(pts, st, top) {
      const p = s('polygon', { points: pts.map(([x, y]) => this.X(x) + ',' + this.Y(y)).join(' ') });
      this.style(p, Object.assign({ fill: 'none', w: 1.5 }, st));
      (top ? this.gTop : this.gMain).append(p);
      return p;
    }
    path(d, st, top) {
      const p = s('path', { d });
      this.style(p, Object.assign({ fill: 'none' }, st));
      (top ? this.gTop : this.gMain).append(p);
      return p;
    }
    polyline(pts, st, top) {
      const p = s('polyline', { points: pts.map(([x, y]) => this.X(x) + ',' + this.Y(y)).join(' ') });
      this.style(p, Object.assign({ fill: 'none' }, st));
      (top ? this.gTop : this.gMain).append(p);
      return p;
    }
    circle(cx, cy, r, st, top) {
      const c = s('circle', { cx: this.X(cx), cy: this.Y(cy), r: r * this.k });
      this.style(c, Object.assign({ fill: 'none', w: 1.5 }, st));
      (top ? this.gTop : this.gMain).append(c);
      return c;
    }
    dot(x, y, st, top) {
      st = Object.assign({ color: 'var(--c-blue)', r: 4.5 }, st);
      const c = s('circle', { cx: this.X(x), cy: this.Y(y), r: st.r });
      c.setAttribute('style', `fill:${st.fill || st.color};stroke:${st.ring || 'var(--plot-bg)'};stroke-width:${st.rw == null ? 1.5 : st.rw}`);
      (top ? this.gTop : this.gMain).append(c);
      return c;
    }
    // arco di angolo (in coordinate del mondo), da a0 ad a1 (radianti, antiorario se a1>a0)
    arc(cx, cy, r, a0, a1, st, arrowEnd) {
      const n = Math.max(8, Math.ceil(Math.abs(a1 - a0) / 0.05));
      const pts = [];
      for (let i = 0; i <= n; i++) { const a = a0 + (a1 - a0) * i / n; pts.push([cx + r * Math.cos(a), cy + r * Math.sin(a)]); }
      const p = this.polyline(pts, Object.assign({ w: 1.6 }, st));
      if (arrowEnd && Math.abs(a1 - a0) > 0.15) {
        const a = a1, dir = Math.sign(a1 - a0);
        const tx = -Math.sin(a) * dir, ty = Math.cos(a) * dir;
        const ex = cx + r * Math.cos(a), ey = cy + r * Math.sin(a);
        const X2 = this.X(ex), Y2 = this.Y(ey);
        const ux = tx, uy = -ty, L = 8, w = 4;
        const bx = X2 - ux * L, by = Y2 - uy * L;
        const hd = s('path', { d: `M${X2},${Y2} L${bx - uy * w},${by + ux * w} L${bx + uy * w},${by - ux * w} Z` });
        hd.setAttribute('style', `fill:${(st && st.color) || 'var(--ink-2)'}`);
        this.gMain.append(hd);
      }
      return p;
    }
    // quadratino dell'angolo retto in P fra le direzioni u e v (unitarie, mondo)
    rightAngle(px, py, ux, uy, vx, vy, size) {
      const r = (size || 12) / this.k;
      const a = [px + ux * r, py + uy * r], b = [px + (ux + vx) * r, py + (uy + vy) * r], c = [px + vx * r, py + vy * r];
      this.polyline([a, b, c], { color: 'var(--c-orange)', w: 1.5 });
    }
    // maniglia trascinabile
    handle(o) {
      const g = s('g', { class: 'pl-handle', tabindex: 0, role: 'slider', 'aria-label': o.aria || 'punto trascinabile' });
      const hit = s('circle', { r: 18, class: 'hit' });
      const dot = s('circle', { r: o.r || 7, class: 'dot' });
      dot.setAttribute('style', `fill:${o.color || 'var(--c-blue)'}`);
      g.append(hit, dot);
      this.gHandles.append(g);
      const hd = { g, x: o.x, y: o.y, o };
      hd.set = (x, y) => {
        hd.x = x; hd.y = y;
        g.setAttribute('transform', `translate(${this.X(x)},${this.Y(y)})`);
        g.setAttribute('aria-valuetext', `(${fx(x, 2)}; ${fx(y, 2)})`);
      };
      hd.set(o.x, o.y);
      g.addEventListener('pointerdown', (e) => {
        e.preventDefault();
        this.drag = { hd, id: e.pointerId };
        g.classList.add('drag');
        this.svg.setPointerCapture(e.pointerId);
      });
      g.addEventListener('keydown', (e) => {
        const st = this.o.snap || 0.1;
        let dx = 0, dy = 0;
        if (e.key === 'ArrowLeft') dx = -st; else if (e.key === 'ArrowRight') dx = st;
        else if (e.key === 'ArrowUp') dy = st; else if (e.key === 'ArrowDown') dy = -st; else return;
        e.preventDefault();
        this.moveHandle(hd, hd.x + dx, hd.y + dy);
      });
      this.handles.push(hd);
      return hd;
    }
    moveHandle(hd, x, y, free) {
      const o = this.o, m = 0.0;
      const st = hd.o.snap != null ? hd.o.snap : o.snap;
      if (st && !free) { x = Math.round(x / st) * st; y = Math.round(y / st) * st; }
      x = Math.max(o.xmin + m, Math.min(o.xmax - m, x));
      y = Math.max(o.ymin + m, Math.min(o.ymax - m, y));
      if (hd.o.constrain) [x, y] = hd.o.constrain(x, y);
      if (Math.abs(x - hd.x) < EPS && Math.abs(y - hd.y) < EPS) return;
      hd.set(x, y);
      if (hd.o.onDrag) hd.o.onDrag(x, y);
    }
    bindPointer() {
      const pt = this.svg.createSVGPoint();
      const toWorld = (e) => {
        pt.x = e.clientX; pt.y = e.clientY;
        const m = this.svg.getScreenCTM();
        if (!m) return [0, 0];
        const p = pt.matrixTransform(m.inverse());
        return this.fromPx(p.x, p.y);
      };
      this.svg.addEventListener('pointermove', (e) => {
        if (!this.drag || e.pointerId !== this.drag.id) return;
        const [x, y] = toWorld(e);
        this.moveHandle(this.drag.hd, x, y, e.shiftKey);
      });
      const up = (e) => {
        if (!this.drag || e.pointerId !== this.drag.id) return;
        this.drag.hd.g.classList.remove('drag');
        if (this.drag.hd.o.onEnd) this.drag.hd.o.onEnd();
        this.drag = null;
      };
      this.svg.addEventListener('pointerup', up);
      this.svg.addEventListener('pointercancel', up);
    }
  }
  GAL.Plot = Plot;

  /* ------------------------------------------------------------ animazione */
  function animate(dur, step, done) {
    if (reduce()) { step(1); if (done) done(); return { stop() {} }; }
    let raf = 0, stopped = false;
    const t0 = performance.now();
    const f = (now) => {
      if (stopped) return;
      const t = Math.min(1, (now - t0) / dur);
      step(t);
      if (t < 1) raf = requestAnimationFrame(f); else if (done) done();
    };
    raf = requestAnimationFrame(f);
    return { stop() { stopped = true; cancelAnimationFrame(raf); } };
  }
  const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  GAL.animate = animate; GAL.ease = ease;

  // disposizione standard: grafico a sinistra, controlli e letture a destra
  function layout(m, solo) {
    const grid = h('div', { class: 'lab-grid' + (solo ? ' solo' : '') });
    const main = h('div', { style: 'min-width:0' });
    const side = h('div', { class: 'lab-side' });
    grid.append(main, side);
    m.append(grid);
    return { grid, main, side };
  }
  GAL.layout = layout;
  function note(html) { return h('p', { class: 'lab-note', html: html.replace(/\$(.+?)\$/g, (mm, t) => K(t)) }); }
  GAL.note = note;

  /* ============================================================ CAPITOLO 1 */
  labs['zp-classi'] = function (m) {
    let p = 4, hover = null;
    const L = layout(m, true);
    const strip = h('div', { class: 'zp-strip', role: 'list' });
    const classes = h('div', { class: 'zp-classes' });
    const info = readout();
    const N0 = -12, N1 = 23;
    function draw() {
      strip.innerHTML = '';
      for (let n = N0; n <= N1; n++) {
        const r = ((n % p) + p) % p;
        const cell = h('button', { type: 'button', class: 'zp-n' + (hover !== null && r !== hover ? ' dim' : '') + (hover === r ? ' on' : ''), role: 'listitem', 'aria-label': `${n}, classe ${r}` });
        cell.style.setProperty('--h', `${(r * 360 / p + 210) % 360}`);
        cell.innerHTML = `<b>${n < 0 ? '−' + (-n) : n}</b><span>[${r}]</span>`;
        cell.addEventListener('pointerenter', () => { hover = r; show(n); draw(); });
        cell.addEventListener('focus', () => { hover = r; show(n); draw(); });
        cell.addEventListener('click', () => { hover = r; show(n); draw(); });
        strip.append(cell);
      }
      classes.innerHTML = '';
      for (let r = 0; r < p; r++) {
        const el = [];
        for (let n = N0; n <= N1; n++) if (((n % p) + p) % p === r) el.push(n);
        const ex = el.filter((n) => Math.abs(n) <= 3 * p).slice(0, 6);
        const row = h('div', { class: 'zp-c' + (hover !== null && r !== hover ? ' dim' : '') });
        row.style.setProperty('--h', `${(r * 360 / p + 210) % 360}`);
        row.innerHTML = K(`[${r}] = \\{\\dots,\\ ${ex.join(',\\ ')},\\ \\dots\\}`);
        classes.append(row);
      }
    }
    function show(n) {
      const r = ((n % p) + p) % p;
      const q = (n - r) / p;
      info.set([
        ['divisione per p', T(`${n} = ${p}\\cdot(${q}) + ${r}`)],
        ['classe', T(`[${n}] = [${r}]`)],
        ['nella stessa classe', T(`${n - p},\\ ${n + p},\\ ${n + 2 * p},\\ \\dots`)],
      ]);
    }
    const sl = slider({ label: '$p$', min: 2, max: 13, value: p, onInput: (v) => { p = v; hover = null; info.set([note('Passa sopra (o tocca) un numero.').outerHTML]); draw(); } , format: (v) => String(v) });
    L.main.append(strip, classes);
    L.side.append(h('div', { class: 'lab-ctl' }, sl), info);
    sl.style.maxWidth = '22rem';
    info.set([note('Passa sopra (o tocca) un numero: si illumina la sua classe di resto. Due interi sono equivalenti se hanno lo stesso resto nella divisione per $p$; con $p=13$, ad esempio, $18\\simeq 31$.').outerHTML]);
    draw();
  };

  labs['induzione'] = function (m) {
    const N = 12;
    let base = true, passo = true, rotto = false, anim = null;
    const L = layout(m, true);
    const W = 640, H = 170;
    const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Tessere del domino che rappresentano p(0), p(1), …' });
    const wrap = h('div', { class: 'lab-plot' }, svg);
    const tiles = [];
    const gap = W / (N + 1);
    for (let k = 0; k < N; k++) {
      const x = gap * (k + 0.8), y = 130;
      const g = s('g', { class: 'dom' });
      const r = s('rect', { x: -9, y: -86, width: 18, height: 86, rx: 3 });
      const t = s('text', { x: 0, y: 22, 'text-anchor': 'middle', class: 'dom-t' });
      t.textContent = `p(${k})`;
      g.append(r);
      const holder = s('g', { transform: `translate(${x},${y})` });
      holder.append(g, t);
      svg.append(holder);
      tiles.push(g);
    }
    svg.prepend(s('line', { x1: 10, y1: 130, x2: W - 10, y2: 130, class: 'pl-axis' }));
    const msg = h('div', { class: 'readout' });
    function reset() {
      if (anim) anim.forEach(clearTimeout);
      anim = [];
      tiles.forEach((g) => { g.style.transition = 'none'; g.style.transform = 'rotate(0deg)'; g.classList.remove('down', 'stop'); });
      msg.innerHTML = K('p(0),\\ p(1),\\ p(2),\\ \\dots') + ' in piedi: premi «Avvia».';
    }
    function run() {
      reset();
      requestAnimationFrame(() => {
        if (!base) {
          msg.innerHTML = 'Senza la <b>base</b> nessuna tessera cade: il passo induttivo da solo non dimostra niente.';
          tiles[0].classList.add('stop');
          return;
        }
        let k = 0;
        const fall = () => {
          const g = tiles[k];
          g.style.transition = reduce() ? 'none' : 'transform .38s cubic-bezier(.5,0,.8,.4)';
          g.style.transform = 'rotate(52deg)';
          g.classList.add('down');
          const brokenHere = rotto && k === 5;
          if (k + 1 < N && passo && !brokenHere) { k++; anim.push(setTimeout(fall, reduce() ? 0 : 230)); }
          else {
            anim.push(setTimeout(() => {
              if (k + 1 >= N) msg.innerHTML = 'Base + passo induttivo: cadono <b>tutte</b> le tessere, cioè ' + K('p(n)') + ' vale per ogni ' + K('n\\in\\mathbb{N}') + '.';
              else if (!passo) msg.innerHTML = 'Senza il <b>passo induttivo</b> cade solo ' + K('p(0)') + ': la base da sola non basta.';
              else { msg.innerHTML = 'Il passo «da ' + K('n=5') + ' a ' + K('n=6') + '» fallisce: la catena si interrompe e ' + K('p(6)') + ' resta non dimostrata.'; tiles[6].classList.add('stop'); }
            }, 300));
          }
        };
        fall();
      });
    }
    const ctl = h('div', { class: 'lab-ctl' },
      check('Base: $p(0)$ vera', base, (v) => { base = v; reset(); }),
      check('Passo: $p(n)\\Rightarrow p(n+1)$', passo, (v) => { passo = v; reset(); }),
      check('Il passo fallisce da $5$ a $6$', rotto, (v) => { rotto = v; reset(); }),
      btn('Avvia', 'play', run, 'pri'),
      btn('Rimetti in piedi', 'reset', reset));
    L.main.append(wrap);
    L.side.append(ctl, msg);
    reset();
  };

  /* ============================================================ CAPITOLO 2 */
  labs['zp-tabella'] = function (m) {
    let p = 5, sel = null;
    const L = layout(m);
    const tbl = h('div', { class: 'zp-tab' });
    const info = readout();
    const isPrime = (n) => { if (n < 2) return false; for (let k = 2; k * k <= n; k++) if (n % k === 0) return false; return true; };
    function draw() {
      tbl.innerHTML = '';
      tbl.style.setProperty('--n', p + 1);
      tbl.append(h('div', { class: 'zt h corner', html: K('\\cdot') }));
      for (let b = 0; b < p; b++) tbl.append(h('div', { class: 'zt h' + (sel !== null ? '' : ''), text: `[${b}]` }));
      for (let a = 0; a < p; a++) {
        const rh = h('button', { type: 'button', class: 'zt h rowh' + (sel === a ? ' on' : ''), text: `[${a}]`, 'aria-label': `riga di [${a}]` });
        rh.addEventListener('click', () => { sel = sel === a ? null : a; draw(); });
        tbl.append(rh);
        for (let b = 0; b < p; b++) {
          const v = (a * b) % p;
          let cls = 'zt';
          if (v === 1) cls += ' one';
          if (v === 0 && a !== 0 && b !== 0) cls += ' zd';
          if (sel === a) cls += ' sel';
          if (sel !== null && sel !== a) cls += ' dim';
          tbl.append(h('div', { class: cls, text: String(v) }));
        }
      }
      const prime = isPrime(p);
      const rows = [];
      rows.push(['p', prime ? `<span class="badge ok">${p} è primo: ℤ<sub>${p}</sub> è un campo</span>` : `<span class="badge no">${p} non è primo: ℤ<sub>${p}</sub> non è un campo</span>`]);
      const inv = [];
      for (let a = 1; a < p; a++) { let found = null; for (let b = 1; b < p; b++) if ((a * b) % p === 1) found = b; inv.push(found === null ? `[${a}]^{-1}\\ \\text{no}` : `[${a}]^{-1}=[${found}]`); }
      rows.push(['inversi', '<span class="inv-chips">' + inv.map((x) => '<span>' + T(x) + '</span>').join('') + '</span>']);
      if (!prime) {
        for (let r = 2; r < p; r++) if (p % r === 0) { rows.push(['divisori dello zero', T(`[${r}]\\cdot[${p / r}]=[${p}]=[0]`)]); break; }
      }
      if (sel !== null) {
        let f = null;
        for (let b = 1; b < p; b++) if ((sel * b) % p === 1) f = b;
        rows.push(['riga selezionata', sel === 0 ? T('[0]\\ \\text{non ha inverso}') : f === null ? T(`[${sel}]\\ \\text{non ha inverso}`) : T(`[${sel}]\\cdot[${f}]=[1]`)]);
      }
      info.set(rows);
    }
    const sl = slider({ label: '$p$', min: 2, max: 13, value: p, onInput: (v) => { p = v; sel = null; draw(); }, format: (v) => String(v) });
    L.main.append(h('div', { style: 'overflow-x:auto' }, tbl));
    L.side.append(sl, info, note('Celle verdi: prodotto $[1]$ (coppie di inversi). Celle rosse: prodotto $[0]$ con fattori non nulli. Clicca un\'etichetta di riga per evidenziarla.'));
    draw();
  };

  /* ============================================================ CAPITOLO 3: numeri complessi */
  function complexPlot(parent, r) {
    return new Plot(parent, { xmin: -r[0], xmax: r[0], ymin: -r[1], ymax: r[1], W: 560, grid: r[2] || 1, tickStep: 1, snap: r[3] || 0.5, axisLabels: ['\\operatorname{Re}', '\\operatorname{Im}'] });
  }
  const arg = (a, b) => Math.atan2(b, a);  // in (−π, π]
  function polarTex(rho2, th) {
    return `${sqrtTex(rho2)}\\,e^{i\\,${angTex(th)}}`;
  }

  labs['c-piano'] = function (m) {
    let a = 3, b = 2, showConj = true, showInv = false;
    const L = layout(m);
    const P = complexPlot(L.main, [5, 3.5, 1, 0.5]);
    const info = readout();
    function draw() {
      P.begin();
      P.circle(0, 0, 1, { color: 'var(--c-gray)', dash: '3 4', w: 1.2 });
      P.line(a, 0, a, b, { color: 'var(--c-gray)', dash: '4 4', w: 1.3 });
      P.line(0, b, a, b, { color: 'var(--c-gray)', dash: '4 4', w: 1.3 });
      const r2 = a * a + b * b;
      if (showConj) {
        P.arrow(0, 0, a, -b, { color: 'var(--c-teal)', w: 2.2 });
        P.line(a, b, a, -b, { color: 'var(--c-teal)', dash: '2 5', w: 1.2 });
        P.tipLabel('cj', '\\overline{z}', 0, 0, a, -b, 'var(--c-teal)');
      }
      if (showInv && r2 > 1e-9) {
        P.arrow(0, 0, a / r2, -b / r2, { color: 'var(--c-violet)', w: 2.2 });
        P.tipLabel('inv', 'z^{-1}', 0, 0, a / r2, -b / r2, 'var(--c-violet)');
      }
      P.arrow(0, 0, a, b, { color: 'var(--c-blue)', w: 2.8 });
      P.tipLabel('z', 'z', 0, 0, a, b, 'var(--c-blue)', 20);
      P.label('a', 'a', a, 0, { dx: 10, dy: b >= 0 ? 30 : -14, small: true });
      P.label('b', 'b', 0, b, { dx: a >= 0 ? -32 : 14, dy: -10, small: true });
      P.end();
      const th = arg(a, b);
      const rows = [
        ['forma algebrica', T(`z = ${cTex(a, b)}`)],
        ['modulo', T(`|z| = \\sqrt{${tn(a * a, 2)}+${tn(b * b, 2)}} = ${sqrtTex(r2)}`)],
      ];
      if (r2 > 1e-9) {
        rows.push(['argomento principale', T(`\\operatorname{Arg} z = ${angTex(th)}` + (piTex(th) === null ? '' : '') + `\\ (\\approx ${tn(th * 180 / Math.PI, 1)}^\\circ)`)]);
        rows.push(['coniugato', T(`\\overline{z} = ${cTex(a, -b)}`)]);
        rows.push(['identità (3.4)', T(`z\\,\\overline{z} = |z|^2 = ${tn(r2, 2)}`)]);
        rows.push(['inverso', T(`z^{-1} = \\dfrac{\\overline{z}}{|z|^2} = ${cTex(a / r2, -b / r2, 3)}`)]);
      } else rows.push(['', 'Per $z=0$ l’argomento non è definito e non esiste l’inverso.'.replace(/\$(.+?)\$/g, (mm, t) => K(t))]);
      info.set(rows);
    }
    P.handle({ x: a, y: b, color: 'var(--c-blue)', aria: 'punto z', onDrag: (x, y) => { a = x; b = y; draw(); } });
    L.side.append(h('div', { class: 'lab-ctl' },
      check('coniugato $\\overline{z}$', showConj, (v) => { showConj = v; draw(); }),
      check('inverso $z^{-1}$', showInv, (v) => { showInv = v; draw(); })), info,
    note('Il coniugato è il simmetrico rispetto all’asse reale; l’inverso ha modulo $1/|z|$ e argomento opposto (la circonferenza tratteggiata ha raggio 1). Tieni premuto Maiusc per muovere $z$ senza agganciarlo alla griglia.'));
    draw();
  };

  labs['c-arg'] = function (m) {
    let a = -2, b = -1;
    const L = layout(m);
    const P = complexPlot(L.main, [3.5, 3, 1, 0.5]);
    const info = readout();
    const cases = h('div', { class: 'readout cases' });
    function draw() {
      P.begin();
      const th = arg(a, b);
      // quadrante evidenziato
      const qx = a >= 0 ? [0, 3.5] : [-3.5, 0], qy = b >= 0 ? [0, 3] : [-3, 0];
      P.poly([[qx[0], qy[0]], [qx[1], qy[0]], [qx[1], qy[1]], [qx[0], qy[1]]], { fill: 'var(--accent)', fop: 0.05, color: 'none', w: 0 });
      if (Math.abs(a) > 1e-9) {
        // stessa tangente: il punto simmetrico
        P.line(-a * 3, -b * 3, a * 3, b * 3, { color: 'var(--c-gray)', dash: '3 5', w: 1.1 });
        P.dot(-a, -b, { color: 'var(--c-gray)', r: 3.5 });
        P.label('sim', '-z', -a, -b, { dx: 14, dy: -12, small: true, color: 'var(--ink-3)' });
      }
      if (a * a + b * b > 1e-9) {
        P.arc(0, 0, 0.75, 0, th, { color: 'var(--c-red)', w: 2 }, true);
        P.label('th', '\\operatorname{Arg} z', 0.95 * Math.cos(th / 2) * 1.35, 0.95 * Math.sin(th / 2) * 1.35, { color: 'var(--c-red)', small: true });
      }
      P.arrow(0, 0, a, b, { color: 'var(--c-blue)', w: 2.8 });
      P.tipLabel('z', 'z', 0, 0, a, b, 'var(--c-blue)', 18);
      P.end();
      const rows = [['z', T(`z = ${cTex(a, b)}`)]];
      let which = -1;
      if (a > 1e-9) which = 0; else if (a < -1e-9) which = b >= 0 ? 1 : 4; else if (b > 0) which = 2; else if (b < 0) which = 3;
      if (which === 0 || which === 1 || which === 4) rows.push(['arctan(b/a)', T(`\\arctan\\dfrac{${tn(b, 2)}}{${tn(a, 2)}} = ${angTex(Math.atan(b / a))}`)]);
      if (which >= 0) rows.push(['Arg z', `<span class="big">${T(`\\operatorname{Arg} z = ${angTex(th)}\\ \\ (${tn(th * 180 / Math.PI, 1)}^\\circ)`)}</span>`]);
      else rows.push(['', 'Per ' + K('z=0') + ' l’argomento non è definito.']);
      info.set(rows);
      const C = [
        ['a>0', '\\theta=\\arctan\\frac ba'],
        ['a<0,\\ b\\ge0', '\\theta=\\arctan\\frac ba+\\pi'],
        ['a=0,\\ b>0', '\\theta=\\frac\\pi2'],
        ['a=0,\\ b<0', '\\theta=-\\frac\\pi2'],
        ['a<0,\\ b<0', '\\theta=\\arctan\\frac ba+\\pi', 'argomento principale: $\\arctan\\frac ba-\\pi$'],
      ];
      cases.innerHTML = '<div class="r-k" style="margin-bottom:.3rem">Quale caso della (3.9)?</div>' + C.map(([c, f, extra], i) => `<div class="case${i === which ? ' on' : ''}">${K(c)}<span>${K(f)}${extra ? '<small>' + extra.replace(/\$(.+?)\$/g, (mm, t) => K(t)) + '</small>' : ''}</span></div>`).join('');
    }
    P.handle({ x: a, y: b, color: 'var(--c-blue)', aria: 'punto z', onDrag: (x, y) => { a = x; b = y; draw(); } });
    L.side.append(info, cases, note('La retta tratteggiata unisce $z$ e $-z$: hanno la stessa tangente dell’argomento, ma argomenti che differiscono di $\\pi$. Per questo l’arcotangente da sola non basta.'));
    draw();
  };

  labs['c-prodotto'] = function (m) {
    let z1 = [Math.SQRT2, Math.SQRT2], z2 = [1.5, 1.5 * Math.sqrt(3)], mode = 'prod', anim = null, at = null;
    const L = layout(m);
    const P = complexPlot(L.main, [6.5, 6.5, 1, 0.5]);
    const info = readout();
    const H1 = P.handle({ x: z1[0], y: z1[1], color: 'var(--c-blue)', aria: 'punto z1', snap: 0.25, onDrag: (x, y) => { z1 = [x, y]; at = null; draw(); } });
    const H2 = P.handle({ x: z2[0], y: z2[1], color: 'var(--c-teal)', aria: 'punto z2', snap: 0.25, onDrag: (x, y) => { z2 = [x, y]; at = null; draw(); } });
    function mul(p, q) { return [p[0] * q[0] - p[1] * q[1], p[0] * q[1] + p[1] * q[0]]; }
    function draw() {
      P.begin();
      const [a1, b1] = z1, [a2, b2] = z2;
      const r1 = Math.hypot(a1, b1), r2 = Math.hypot(a2, b2), t1 = arg(a1, b1), t2 = arg(a2, b2);
      if (mode === 'sum') {
        const sx = a1 + a2, sy = b1 + b2;
        P.poly([[0, 0], [a1, b1], [sx, sy], [a2, b2]], { fill: 'var(--c-blue)', fop: 0.06, color: 'none', w: 0 });
        P.line(a1, b1, sx, sy, { color: 'var(--c-teal)', dash: '5 5', w: 1.4 });
        P.line(a2, b2, sx, sy, { color: 'var(--c-blue)', dash: '5 5', w: 1.4 });
        P.arrow(0, 0, sx, sy, { color: 'var(--c-red)', w: 3 });
        P.tipLabel('s', 'z_1+z_2', 0, 0, sx, sy, 'var(--c-red)', 26);
        info.set([
          ['z₁', T(`z_1 = ${cTex(a1, b1)}`)], ['z₂', T(`z_2 = ${cTex(a2, b2)}`)],
          ['somma', `<span class="big">${T(`z_1+z_2 = ${cTex(sx, sy)}`)}</span>`],
          ['', 'Si sommano parti reali e parti immaginarie: è la regola del parallelogramma.'],
        ]);
      } else {
        const p = mul(z1, z2), rp = r1 * r2;
        P.circle(0, 0, rp, { color: 'var(--c-red)', dash: '2 5', w: 1, op: 0.6 });
        if (r1 > 1e-6) P.arc(0, 0, 0.9, 0, t1, { color: 'var(--c-blue)', w: 1.8 }, true);
        if (r2 > 1e-6) P.arc(0, 0, 1.25, 0, t2, { color: 'var(--c-teal)', w: 1.8 }, true);
        if (rp > 1e-6) P.arc(0, 0, 1.6, t1, t1 + t2, { color: 'var(--c-red)', w: 1.8 }, true);
        if (at) {
          // spirale z1·exp(t log z2)
          const pts = [];
          for (let k = 0; k <= 60 * at.t; k++) {
            const t = k / 60;
            const rr = r1 * Math.pow(r2, t), aa = t1 + t2 * t;
            pts.push([rr * Math.cos(aa), rr * Math.sin(aa)]);
          }
          P.polyline(pts, { color: 'var(--c-red)', w: 2, dash: '1 4' });
          const rr = r1 * Math.pow(r2, at.t), aa = t1 + t2 * at.t;
          P.arrow(0, 0, rr * Math.cos(aa), rr * Math.sin(aa), { color: 'var(--c-red)', w: 2.6, op: 0.9 });
        } else {
          P.arrow(0, 0, p[0], p[1], { color: 'var(--c-red)', w: 3 });
          P.tipLabel('p', 'z_1z_2', 0, 0, p[0], p[1], 'var(--c-red)', 22);
        }
        info.set([
          ['z₁', T(`z_1 = ${polarTex(r1 * r1, t1)}`)], ['z₂', T(`z_2 = ${polarTex(r2 * r2, t2)}`)],
          ['moduli', T(`|z_1z_2| = |z_1|\\,|z_2| = ${tn(rp, 3)}`)],
          ['argomenti', T(`\\arg z_1+\\arg z_2 = ${angTex(t1)} + ${angTex(t2)} = ${angTex(t1 + t2)}`)],
          ['prodotto', `<span class="big">${T(`z_1z_2 = ${cTex(p[0], p[1])}`)}</span>`],
        ]);
      }
      P.arrow(0, 0, a1, b1, { color: 'var(--c-blue)', w: 2.6 });
      P.arrow(0, 0, a2, b2, { color: 'var(--c-teal)', w: 2.6 });
      P.tipLabel('z1', 'z_1', 0, 0, a1, b1, 'var(--c-blue)', 18);
      P.tipLabel('z2', 'z_2', 0, 0, a2, b2, 'var(--c-teal)', 18);
      P.end();
    }
    const sg = seg([['sum', 'Somma'], ['prod', 'Prodotto']], mode, (v) => { mode = v; at = null; draw(); }, 'Operazione');
    const go = btn('Anima', 'play', () => {
      if (mode !== 'prod') { mode = 'prod'; sg.set('prod'); }
      if (anim) anim.stop();
      at = { t: 0 };
      anim = animate(1800, (t) => { at.t = ease(t); draw(); }, () => { at = null; draw(); });
    });
    const ex = btn('Esempio 3.9', 'reset', () => { z1 = [Math.SQRT2, Math.SQRT2]; z2 = [1.5, 1.5 * Math.sqrt(3)]; H1.set(...z1); H2.set(...z2); at = null; draw(); });
    L.side.append(h('div', { class: 'lab-ctl' }, sg, go, ex), info,
      note('Nel prodotto i moduli si moltiplicano e gli argomenti si sommano: moltiplicare per $z_2$ ruota di $\\arg z_2$ e dilata di $|z_2|$ (la spirale dell’animazione combina i due movimenti).'));
    draw();
  };

  labs['c-demoivre'] = function (m) {
    let z = [1.1 * Math.cos(Math.PI / 6), 1.1 * Math.sin(Math.PI / 6)], n = 6;
    const L = layout(m);
    const P = complexPlot(L.main, [3, 3, 0.5, 0.05]);
    const info = readout();
    function draw() {
      P.begin();
      const r = Math.hypot(z[0], z[1]), th = arg(z[0], z[1]);
      P.circle(0, 0, 1, { color: 'var(--c-gray)', dash: '3 4', w: 1.1 });
      const pts = [];
      for (let k = 0; k <= 60 * n; k++) {
        const t = k / 60;
        const rr = Math.pow(r, t);
        if (rr > 6) break;
        pts.push([rr * Math.cos(th * t), rr * Math.sin(th * t)]);
      }
      P.polyline(pts, { color: 'var(--c-violet)', w: 1.4, dash: '2 4' });
      for (let k = 0; k <= n; k++) {
        const rr = Math.pow(r, k);
        if (rr > 6) break;
        const x = rr * Math.cos(k * th), y = rr * Math.sin(k * th);
        P.line(0, 0, x, y, { color: 'var(--c-violet)', w: 1, op: 0.35 });
        P.dot(x, y, { color: k === n ? 'var(--c-red)' : 'var(--c-violet)', r: k === n ? 5.5 : 4 });
        if (k > 0 && k <= 8) P.label('k' + k, `z^{${k}}`, x, y, { dx: 13 * Math.cos(k * th), dy: -13 * Math.sin(k * th), small: true, color: k === n ? 'var(--c-red)' : 'var(--c-violet)' });
      }
      P.arrow(0, 0, z[0], z[1], { color: 'var(--c-blue)', w: 2.4 });
      P.end();
      const zn = [Math.pow(r, n) * Math.cos(n * th), Math.pow(r, n) * Math.sin(n * th)];
      info.set([
        ['z', T(`z = ${tn(r, 2)}\\,e^{i\\,${angTex(th)}}`)],
        ['De Moivre', T(`z^{${n}} = ${tn(r, 2)}^{${n}}\\,e^{i\\,${n}\\cdot${angTex(th)}}`)],
        ['', T(`= ${tn(Math.pow(r, n), 3)}\\,e^{i\\,${angTex(n * th)}} = ${cTex(zn[0], zn[1], 3)}`)],
      ]);
    }
    P.handle({ x: z[0], y: z[1], color: 'var(--c-blue)', aria: 'punto z', snap: 0.05, onDrag: (x, y) => { z = [x, y]; draw(); } });
    const sl = slider({ label: '$n$', min: 1, max: 12, value: n, onInput: (v) => { n = v; draw(); }, format: (v) => String(v) });
    L.side.append(sl, info, note('Se $|z|=1$ le potenze restano sulla circonferenza unitaria; se $|z|>1$ si allontanano a spirale, se $|z|<1$ si avvicinano all’origine.'));
    draw();
  };

  labs['c-eulero'] = function (m) {
    let th = 2, N = 4;
    const L = layout(m);
    const P = complexPlot(L.main, [3, 3, 0.5, 0.05]);
    const info = readout();
    const fact = (k) => { let f = 1; for (let i = 2; i <= k; i++) f *= i; return f; };
    function draw() {
      P.begin();
      P.circle(0, 0, 1, { color: 'var(--c-gray)', w: 1.3 });
      let x = 0, y = 0;
      const ex = Math.cos(th), ey = Math.sin(th);
      for (let k = 0; k <= N; k++) {
        const mag = Math.pow(Math.abs(th), k) / fact(k);
        const sgn = th < 0 && k % 2 === 1 ? -1 : 1;
        // i^k ruota di 90° a ogni termine
        const dirs = [[1, 0], [0, 1], [-1, 0], [0, -1]];
        const [dx, dy] = dirs[k % 4];
        const nx = x + sgn * mag * dx, ny = y + sgn * mag * dy;
        P.arrow(x, y, nx, ny, { color: k % 2 === 0 ? 'var(--c-blue)' : 'var(--c-teal)', w: 2.2, head: 10 });
        x = nx; y = ny;
      }
      P.dot(ex, ey, { color: 'var(--c-red)', r: 6 });
      P.label('e', 'e^{i\\theta}', ex, ey, { dx: 22 * Math.cos(th), dy: -22 * Math.sin(th), color: 'var(--c-red)' });
      P.dot(x, y, { color: 'var(--ink)', r: 4 });
      P.arc(0, 0, 0.35, 0, th, { color: 'var(--c-red)', w: 1.5 }, true);
      P.end();
      info.set([
        ['θ', T(`\\theta = ${tn(th, 2)}`)],
        ['somma parziale', T(`S_{${N}} = \\sum_{k=0}^{${N}} \\frac{(i\\theta)^k}{k!} = ${cTex(x, y, 3)}`)],
        ['valore esatto', T(`e^{i\\theta} = \\cos\\theta + i\\sin\\theta = ${cTex(ex, ey, 3)}`)],
        ['distanza', T(`|S_{${N}} - e^{i\\theta}| = ${tn(Math.hypot(x - ex, y - ey), 4)}`)],
      ]);
    }
    L.side.append(
      slider({ label: '$\\theta$', min: -6.28, max: 6.28, step: 0.01, value: th, onInput: (v) => { th = v; draw(); } }),
      slider({ label: 'termini', min: 0, max: 20, value: N, onInput: (v) => { N = v; draw(); }, format: (v) => String(v + 1) }),
      info, note('Ogni termine della serie è ruotato di $90^\\circ$ rispetto al precedente (le potenze di $i$ si ripetono con periodo 4) e diventa sempre più piccolo: la spezzata si avvolge attorno a $e^{i\\theta}$. Curiosità dal corso di Analisi: non è in programma, ma aiuta a «vedere» la formula di Eulero.'));
    draw();
  };

  labs['c-radici'] = function (m) {
    let a = [1, 1], n = 3;
    const L = layout(m);
    const P = complexPlot(L.main, [2.5, 2.5, 0.5, 0.25]);
    const info = readout();
    const HA = P.handle({ x: a[0], y: a[1], color: 'var(--c-red)', aria: 'punto a', snap: 0.25, onDrag: (x, y) => { a = [x, y]; draw(); } });
    function draw() {
      P.begin();
      const r0 = Math.hypot(a[0], a[1]), t0 = arg(a[0], a[1]);
      if (r0 < 1e-9) { P.end(); info.set([['', 'Per ' + K('a=0') + ' l’unica soluzione è ' + K('z=0') + '.']]); return; }
      const R = Math.pow(r0, 1 / n);
      P.circle(0, 0, R, { color: 'var(--c-blue)', w: 1.3, dash: '4 4' });
      P.circle(0, 0, 1, { color: 'var(--c-gray)', w: 1, dash: '2 5' });
      const pts = [];
      for (let k = 0; k < n; k++) { const t = (t0 + 2 * k * Math.PI) / n; pts.push([R * Math.cos(t), R * Math.sin(t)]); }
      P.poly(pts, { fill: 'var(--c-blue)', fop: 0.07, color: 'var(--c-blue)', w: 1.4 });
      P.arc(0, 0, 0.45, 0, t0, { color: 'var(--c-red)', w: 1.6 }, true);
      if (Math.abs(t0) > 1e-6) P.arc(0, 0, 0.3, 0, t0 / n, { color: 'var(--c-blue)', w: 1.6 }, true);
      pts.forEach(([x, y], k) => {
        P.line(0, 0, x, y, { color: 'var(--c-blue)', w: 1, op: 0.5 });
        P.dot(x, y, { color: k === 0 ? 'var(--c-blue)' : 'var(--c-teal)', r: 5 });
        const t = (t0 + 2 * k * Math.PI) / n;
        P.label('z' + k, `z_{${k}}`, x, y, { dx: 16 * Math.cos(t), dy: -16 * Math.sin(t), small: true, color: 'var(--ink)' });
      });
      P.arrow(0, 0, a[0], a[1], { color: 'var(--c-red)', w: 2.2 });
      P.end();
      const list = [];
      for (let k = 0; k < Math.min(n, 4); k++) list.push(`z_{${k}} = ${tn(R, 3)}\\,e^{i\\,${angTex((t0 + 2 * k * Math.PI) / n)}}`);
      info.set([
        ['a', T(`a = ${cTex(a[0], a[1])} = ${sqrtTex(r0 * r0)}\\,e^{i\\,${angTex(t0)}}`)],
        ['raggio', T(`\\sqrt[${n}]{|a|} = ${tn(R, 3)}`)],
        ['radici', T('\\begin{gathered}' + list.join('\\\\') + '\\end{gathered}')],
        n > 4 ? ['', '… e le altre si ottengono ruotando di ' + K(`\\tfrac{2\\pi}{${n}}`) + '.'] : ['passo', T(`\\text{rotazione di }\\tfrac{2\\pi}{${n}}`)],
      ]);
    }
    L.side.append(
      slider({ label: '$n$', min: 2, max: 9, value: n, onInput: (v) => { n = v; draw(); }, format: (v) => String(v) }),
      h('div', { class: 'lab-ctl' },
        btn('Radici dell’unità (a = 1)', null, () => { a = [1, 0]; HA.set(1, 0); draw(); }),
        btn('Esempio 3.15 (a = 1 + i)', null, () => { a = [1, 1]; n = 3; HA.set(1, 1); L.side.querySelector('input[type=range]').value = 3; L.side.querySelector('output').textContent = '3'; draw(); })),
      info, note('La prima radice ha argomento $\\theta_0/n$ (arco blu), le altre si ottengono dividendo la circonferenza in $n$ parti uguali a partire da $z_0$.'));
    draw();
  };

  /* ============================================================ CAPITOLO 4: matrici */
  function mxEl(M, opt) {
    opt = opt || {};
    const el = h('div', { class: 'mx' + (opt.click ? ' click' : '') });
    el.style.gridTemplateColumns = `repeat(${M[0].length}, auto)`;
    M.forEach((row, i) => row.forEach((v, j) => {
      const c = h('span', { text: typeof v === 'number' ? fx(v, 3) : v });
      c.dataset.i = i; c.dataset.j = j;
      if (opt.click) c.addEventListener('click', () => opt.click(i, j));
      el.append(c);
    }));
    el.cell = (i, j) => el.children[i * M[0].length + j];
    return el;
  }
  GAL.mxEl = mxEl;
  function thou(x) { return String(Math.round(x)).replace(/\B(?=(\d{3})+(?!\d))/g, '\u2009'); }
  function matmul(A, B) { return A.map((r) => B[0].map((_, j) => r.reduce((s2, a, k) => s2 + a * B[k][j], 0))); }

  labs['m-prodotto'] = function (m) {
    const PRE = {
      '4.8': [[[3, 1], [-1, 2], [0, 3]], [[1, 2], [-1, 3]]],
      '4.9': [[[1, 2, 3], [1, 0, 1]], [[1, 0, 2], [1, 1, 1], [0, -2, 3]]],
      '4.11': [[[1, 3], [0, 2]], [[1, 1], [-1, 1]]],
    };
    let key = '4.8', A, B, C, sel = [0, 0], anim = null, swap = false;
    const L = layout(m, true);
    const row = h('div', { class: 'mx-row' });
    const calc = h('div', { class: 'readout', style: 'text-align:center' });
    function load() {
      [A, B] = PRE[key];
      if (swap) [A, B] = [B, A];
      C = matmul(A, B);
      sel = [0, 0];
      draw();
    }
    function draw() {
      row.innerHTML = '';
      const eA = mxEl(A), eB = mxEl(B), eC = mxEl(C, { click: (i, j) => { stop(); sel = [i, j]; draw(); } });
      const [i, j] = sel;
      A[i].forEach((_, k) => eA.cell(i, k).classList.add('hl'));
      B.forEach((_, k) => eB.cell(k, j).classList.add('hl'));
      eC.cell(i, j).classList.add('hl2');
      const cap = (el, t) => h('div', {}, el, h('div', { class: 'mx-cap', html: K(t) }));
      row.append(cap(eA, `A\\in M(${A.length}\\times${A[0].length})`), h('span', { html: K('\\cdot') }), cap(eB, `B\\in M(${B.length}\\times${B[0].length})`), h('span', { html: K('=') }), cap(eC, `AB\\in M(${C.length}\\times${C[0].length})`));
      const terms = A[i].map((a, k) => `${a < 0 ? `(${a})` : a}\\cdot${B[k][j] < 0 ? `(${B[k][j]})` : B[k][j]}`).join(' + ');
      calc.innerHTML = K(`(AB)_{${i + 1}${j + 1}} = \\sum_{h=1}^{${A[0].length}} a_{${i + 1}h}\\,b_{h${j + 1}} = ${terms} = ${C[i][j]}`);
    }
    function stop() { if (anim) { clearInterval(anim); anim = null; play.setLabel('Anima', 'play'); } }
    const play = btn('Anima', 'play', () => {
      if (anim) { stop(); return; }
      play.setLabel('Pausa', 'pause');
      let k = sel[0] * C[0].length + sel[1];
      anim = setInterval(() => { k = (k + 1) % (C.length * C[0].length); sel = [Math.floor(k / C[0].length), k % C[0].length]; draw(); }, reduce() ? 1400 : 1100);
    });
    const sg = seg([['4.8', 'Esempio 4.8'], ['4.9', 'Esempio 4.9'], ['4.11', 'Esempio 4.11']], key, (v) => { stop(); key = v; swap = false; swapB.style.display = v === '4.11' ? '' : 'none'; load(); }, 'Esempio');
    const swapB = btn('Scambia: BA', null, () => { stop(); swap = !swap; swapB.setLabel(swap ? 'Torna ad AB' : 'Scambia: BA'); load(); });
    swapB.style.display = 'none';
    L.main.append(h('div', { class: 'lab-ctl', style: 'margin-bottom:.8rem' }, sg, play, swapB), row, h('div', { style: 'height:.8rem' }), calc,
      note('Il numero di colonne di $A$ deve essere uguale al numero di righe di $B$: $(m\\times n)\\cdot(n\\times p)=(m\\times p)$. Nell’Esempio 4.11 il pulsante «Scambia» mostra che in generale $AB\\neq BA$.'));
    load();
  };

  labs['m-trasf'] = function (m) {
    const PRE = [
      ['I', 'Identità', [1, 0, 0, 1]],
      ['D', 'Dilatazione $2I_2$', [2, 0, 0, 2]],
      ['R4', 'Rotazione di $-\\pi/4$', [Math.SQRT1_2, Math.SQRT1_2, -Math.SQRT1_2, Math.SQRT1_2]],
      ['R2', 'Rotazione di $-\\pi/2$', [0, 1, -1, 0]],
      ['S', 'Simmetria $-I_2$', [-1, 0, 0, -1]],
      ['T', 'Taglio', [1, 1, 0, 1]],
      ['Y', 'Simmetria assiale', [-1, 0, 0, 1]],
      ['P', 'Schiacciamento', [1, 2, 0.5, 1]],
    ];
    let M = [2, 1, 0, 1.5], shown = M.slice(), anim = null;
    const L = layout(m);
    const P = new Plot(L.main, { xmin: -4.5, xmax: 4.5, ymin: -3.5, ymax: 3.5, W: 560, grid: 1, snap: 0, ticks: false });
    const info = readout();
    // la lettera F (asimmetrica): mostra orientazione e riflessioni
    const F = [[0.2, 0.15], [0.45, 0.15], [0.45, 0.55], [0.75, 0.55], [0.75, 0.75], [0.45, 0.75], [0.45, 0.9], [0.85, 0.9], [0.85, 1.1], [0.2, 1.1]];
    function draw() {
      const [a, b, c, d] = shown;   // matrice [[a,b],[c,d]]
      const T2 = (x, y) => [a * x + b * y, c * x + d * y];
      P.begin();
      for (let k = -6; k <= 6; k++) {
        const p1 = T2(k, -6), p2 = T2(k, 6), q1 = T2(-6, k), q2 = T2(6, k);
        P.line(p1[0], p1[1], p2[0], p2[1], { color: 'var(--c-blue)', w: 0.8, op: 0.28 });
        P.line(q1[0], q1[1], q2[0], q2[1], { color: 'var(--c-blue)', w: 0.8, op: 0.28 });
      }
      const det = a * d - b * c;
      const sq = [[0, 0], [1, 0], [1, 1], [0, 1]].map(([x, y]) => T2(x, y));
      P.poly([[0, 0], [1, 0], [1, 1], [0, 1]], { color: 'var(--c-gray)', dash: '3 4', w: 1 });
      P.poly(sq, { fill: det >= 0 ? 'var(--c-blue)' : 'var(--c-red)', fop: 0.16, color: det >= 0 ? 'var(--c-blue)' : 'var(--c-red)', w: 1.4 });
      P.poly(F.map(([x, y]) => T2(x, y)), { fill: 'var(--c-violet)', fop: 0.55, color: 'var(--c-violet)', w: 1 });
      P.arrow(0, 0, a, c, { color: 'var(--c-red)', w: 2.8 });
      P.arrow(0, 0, b, d, { color: 'var(--c-teal)', w: 2.8 });
      P.tipLabel('v1', 'AV_1', 0, 0, a, c, 'var(--c-red)', 24);
      P.tipLabel('v2', 'AV_2', 0, 0, b, d, 'var(--c-teal)', 24);
      P.end();
      info.set([
        ['matrice', T(`A = \\begin{pmatrix} ${tn(a, 2)} & ${tn(b, 2)} \\\\ ${tn(c, 2)} & ${tn(d, 2)} \\end{pmatrix}`)],
        ['colonne', T(`AV_1 = (${tn(a, 2)}, ${tn(c, 2)}),\\ \\ AV_2 = (${tn(b, 2)}, ${tn(d, 2)})`)],
        ['determinante', T(`\\det A = ad-bc = ${tn(det, 3)}`)],
        ['', Math.abs(det) < 1e-9 ? '<span class="badge no">det = 0: il piano viene schiacciato su una retta (o un punto), A non è invertibile</span>'
          : det > 0 ? '<span class="badge ok">det &gt; 0: l’orientazione si conserva</span>' : '<span class="badge no">det &lt; 0: l’orientazione si inverte (la F si specchia)</span>'],
      ]);
    }
    const sliders = ['a', 'b', 'c', 'd'].map((n2, k) => slider({ label: `$${n2}$`, min: -3, max: 3, step: 0.05, value: M[k], onInput: (v) => { stopAnim(); M[k] = v; shown = M.slice(); draw(); } }));
    function setM(v, animated) {
      stopAnim();
      const from = shown.slice();
      M = v.slice();
      sliders.forEach((sl, k) => sl.setValue(rnd(M[k], 2)));
      if (!animated) { shown = M.slice(); draw(); return; }
      anim = animate(900, (t) => { const e = ease(t); shown = from.map((x, k) => x + (M[k] - x) * e); draw(); });
    }
    function stopAnim() { if (anim) { anim.stop(); anim = null; } }
    const pre = h('div', { class: 'lab-ctl' });
    PRE.forEach(([id, lab, v]) => pre.append(btn(lab, null, () => setM(v, true))));
    const fromI = btn('Anima da I', 'play', () => { const target = M.slice(); shown = [1, 0, 0, 1]; draw(); setTimeout(() => setM(target, true), 250); });
    L.side.append(h('div', { class: 'lab-ctl' }, fromI), ...sliders, info);
    L.main.append(pre);
    draw();
  };

  labs['m-markov'] = function (m) {
    const A = [[0.9, 0.7], [0.1, 0.3]];
    let n = 3, anim = null;
    const L = layout(m);
    const W = 560, H = 300;
    const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, role: 'img', 'aria-label': 'Occupati e disoccupati anno per anno' });
    const wrap = h('div', { class: 'lab-plot' }, svg);
    L.main.append(wrap);
    const info = readout();
    const X = [[80000, 20000]];
    for (let k = 1; k <= 15; k++) { const [x, y] = X[k - 1]; X.push([A[0][0] * x + A[0][1] * y, A[1][0] * x + A[1][1] * y]); }
    function draw() {
      svg.innerHTML = '';
      const left = 52, right = 14, top = 16, bottom = 34;
      const bw = (W - left - right) / 16;
      const Y = (v) => top + (H - top - bottom) * (1 - v / 100000);
      for (let v = 0; v <= 100000; v += 20000) {
        svg.append(s('line', { x1: left, x2: W - right, y1: Y(v), y2: Y(v), class: 'pl-grid' }));
        const t = s('text', { x: left - 6, y: Y(v) + 4, 'text-anchor': 'end', class: 'pl-tick' });
        t.textContent = v === 0 ? '0' : (v / 1000) + ' mila';
        svg.append(t);
      }
      for (let k = 0; k <= 15; k++) {
        const [x, y] = X[k];
        const x0 = left + k * bw + bw * 0.15, w = bw * 0.7;
        const on = k <= n;
        const r1 = s('rect', { x: x0, y: Y(x), width: w, height: Y(0) - Y(x), rx: 2 });
        r1.setAttribute('style', `fill:var(--c-blue);opacity:${on ? (k === n ? 1 : 0.55) : 0.12}`);
        const r2 = s('rect', { x: x0, y: Y(x + y), width: w, height: Y(x) - Y(x + y), rx: 2 });
        r2.setAttribute('style', `fill:var(--c-orange);opacity:${on ? (k === n ? 1 : 0.55) : 0.12}`);
        svg.append(r1, r2);
        const t = s('text', { x: x0 + w / 2, y: H - 14, 'text-anchor': 'middle', class: 'pl-tick' });
        t.textContent = k;
        svg.append(t);
      }
      const yl = s('line', { x1: left, x2: W - right, y1: Y(87500), y2: Y(87500) });
      yl.setAttribute('style', 'stroke:var(--c-red);stroke-dasharray:5 5;stroke-width:1.3');
      svg.append(yl);
      const lt = s('text', { x: W - right - 4, y: Y(87500) - 6, 'text-anchor': 'end', class: 'pl-tick' });
      lt.textContent = '87 500';
      svg.append(lt);
      const ax = s('text', { x: left + (W - left - right) / 2, y: H - 1, 'text-anchor': 'middle', class: 'pl-tick' });
      ax.textContent = 'anni';
      svg.append(ax);
      const [x, y] = X[n];
      let An = [[1, 0], [0, 1]];
      for (let k = 0; k < n; k++) An = matmul(A, An);
      info.set([
        ['anno', T(`n = ${n}`)],
        ['matrice', T(`A^{${n}} = \\begin{pmatrix} ${tn(An[0][0], 3)} & ${tn(An[0][1], 3)} \\\\ ${tn(An[1][0], 3)} & ${tn(An[1][1], 3)}\\end{pmatrix}`)],
        ['occupati', `<span style="color:var(--c-blue);font-weight:700">${thou(x)}</span>`],
        ['disoccupati', `<span style="color:var(--c-orange);font-weight:700">${thou(y)}</span>`],
      ]);
    }
    const sl = slider({ label: '$n$', min: 0, max: 15, value: n, onInput: (v) => { n = v; draw(); }, format: (v) => String(v) });
    const go = btn('Anima', 'play', () => {
      if (anim) clearInterval(anim);
      n = 0; sl.setValue(0); draw();
      anim = setInterval(() => { n++; sl.setValue(n); draw(); if (n >= 15) { clearInterval(anim); anim = null; } }, reduce() ? 300 : 450);
    });
    L.side.append(sl, h('div', { class: 'lab-ctl' }, go), info,
      note('$X_n = A^nX_0$ con $X_0 = (80\\,000,\\ 20\\,000)$: per $n=3$ si ritrovano i $87\\,440$ occupati del testo. La linea rossa a $87\\,500$ è il valore a cui la successione si avvicina: il vettore $(87\\,500,\\ 12\\,500)$ non cambia applicando $A$.'));
    draw();
  };

  /* ============================================================ CAPITOLO 5: determinante */
  function det2(a, b, c, d) { return a * d - b * c; }
  function det3(M) { return M[0][0] * det2(M[1][1], M[1][2], M[2][1], M[2][2]) - M[0][1] * det2(M[1][0], M[1][2], M[2][0], M[2][2]) + M[0][2] * det2(M[1][0], M[1][1], M[2][0], M[2][1]); }
  function minor(M, i, j) { return M.filter((_, r) => r !== i).map((row) => row.filter((_, c) => c !== j)); }
  GAL.det3 = det3;

  labs['det-laplace'] = function (m) {
    const PRE = {
      '5.3': [[1, 2, 1], [3, 0, -1], [2, 5, -3]],
      '5.4': [[2, 1, 3], [0, 2, 0], [1, 1, -1]],
      '5.5': [[2, 1, 0], [2, 1, 1], [3, 0, 1]],
      '5.6': [[1, 2, 3], [4, 5, 6], [8, 8, 9]],
    };
    let key = '5.3', M = PRE[key], line = ['r', 0];
    const L = layout(m, true);
    const top = h('div', { class: 'lab-ctl', style: 'margin-bottom:.7rem' });
    const body = h('div', { class: 'lap' });
    const res = h('div', { class: 'readout', style: 'margin-top:.7rem' });
    function draw() {
      body.innerHTML = '';
      const [kind, idx] = line;
      const mat = mxEl(M);
      for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) {
        const c = mat.cell(i, j);
        const sign = (i + j) % 2 === 0 ? '+' : '−';
        c.setAttribute('data-sign', sign);
        if ((kind === 'r' && i === idx) || (kind === 'c' && j === idx)) c.classList.add('hl');
      }
      const left = h('div', { class: 'lap-m' }, mat, h('div', { class: 'mx-cap', html: 'segni ' + K('(-1)^{i+j}') + ' in apice' }));
      const terms = h('div', { class: 'lap-t' });
      let total = 0, computed = 0;
      for (let k = 0; k < 3; k++) {
        const i = kind === 'r' ? idx : k, j = kind === 'c' ? idx : k;
        const a = M[i][j], sg = (i + j) % 2 === 0 ? 1 : -1;
        const mi = minor(M, i, j), dm = det2(mi[0][0], mi[0][1], mi[1][0], mi[1][1]);
        const term = sg * a * dm;
        total += term;
        const row = h('div', { class: 'lap-r' + (a === 0 ? ' zero' : '') });
        const small = mxEl(M);
        for (let r = 0; r < 3; r++) for (let c = 0; c < 3; c++) if (r === i || c === j) small.cell(r, c).classList.add('cross');
        small.cell(i, j).classList.remove('cross');
        small.cell(i, j).classList.add('hl2');
        small.classList.add('mini');
        if (a !== 0) computed++;
        row.append(small, h('div', {
          class: 'lap-x', html: a === 0
            ? K(`(-1)^{${i + 1}+${j + 1}}\\cdot 0\\cdot(\\dots) = 0`) + '<span class="lab-note"> elemento nullo: il minore non si calcola</span>'
            : K(`(-1)^{${i + 1}+${j + 1}}\\cdot ${a < 0 ? `(${a})` : a}\\cdot\\det\\begin{pmatrix}${mi[0][0]}&${mi[0][1]}\\\\${mi[1][0]}&${mi[1][1]}\\end{pmatrix} = ${sg < 0 ? '-' : '+'}${a < 0 ? `(${a})` : a}\\cdot(${dm}) = ${term}`)
        }));
        terms.append(row);
      }
      body.append(left, terms);
      res.innerHTML = K(`\\det A = ${Math.round(total)}`) + ` &nbsp; <span class="badge neu">${computed} ${computed === 1 ? 'determinante 2×2 calcolato' : 'determinanti 2×2 calcolati'}</span> &nbsp; <span class="lab-note">Prova un’altra riga o colonna: il risultato non cambia.</span>`;
    }
    const sgE = seg(Object.keys(PRE).map((k2) => [k2, 'Esempio ' + k2]), key, (v) => { key = v; M = PRE[v]; draw(); }, 'Matrice');
    const opts = [];
    for (let k = 0; k < 3; k++) opts.push(['r' + k, `riga ${k + 1}`]);
    for (let k = 0; k < 3; k++) opts.push(['c' + k, `colonna ${k + 1}`]);
    const sgL = seg(opts, 'r0', (v) => { line = [v[0], Number(v[1])]; draw(); }, 'Sviluppa lungo');
    top.append(sgE, sgL);
    L.main.append(top, body, res);
    draw();
  };

  labs['det-area'] = function (m) {
    let u = [3, 1], v = [1, 2];
    const L = layout(m);
    const P = new Plot(L.main, { xmin: -4, xmax: 5, ymin: -3, ymax: 4, W: 560, grid: 1, snap: 0.5 });
    const info = readout();
    function draw() {
      P.begin();
      const det = u[0] * v[1] - v[0] * u[1];
      const col = det >= 0 ? 'var(--c-blue)' : 'var(--c-red)';
      P.poly([[0, 0], u, [u[0] + v[0], u[1] + v[1]], v], { fill: col, fop: 0.16, color: col, w: 1.2 });
      const a0 = Math.atan2(u[1], u[0]);
      let a1 = Math.atan2(v[1], v[0]);
      let d = a1 - a0;
      while (d > Math.PI) d -= 2 * Math.PI;
      while (d < -Math.PI) d += 2 * Math.PI;
      if (Math.abs(det) > 1e-9) P.arc(0, 0, 0.8, a0, a0 + d, { color: 'var(--c-orange)', w: 1.8 }, true);
      P.arrow(0, 0, u[0], u[1], { color: 'var(--c-blue)', w: 2.8 });
      P.arrow(0, 0, v[0], v[1], { color: 'var(--c-teal)', w: 2.8 });
      P.tipLabel('u', 'u', 0, 0, u[0], u[1], 'var(--c-blue)', 18);
      P.tipLabel('v', 'v', 0, 0, v[0], v[1], 'var(--c-teal)', 18);
      P.end();
      info.set([
        ['matrice', T(`A = \\begin{pmatrix} ${tn(u[0])} & ${tn(v[0])} \\\\ ${tn(u[1])} & ${tn(v[1])}\\end{pmatrix}`)],
        ['determinante', T(`\\det A = ${tn(u[0])}\\cdot${tn(v[1])} - ${tn(v[0])}\\cdot${tn(u[1])} = ${tn(det)}`)],
        ['area', T(`\\text{area} = |\\det A| = ${tn(Math.abs(det))}`)],
        ['', Math.abs(det) < 1e-9 ? '<span class="badge no">colonne parallele: area nulla, A non invertibile</span>'
          : det > 0 ? '<span class="badge ok">da u a v si ruota in senso antiorario: det &gt; 0</span>' : '<span class="badge no">da u a v si ruota in senso orario: det &lt; 0</span>'],
      ]);
    }
    P.handle({ x: u[0], y: u[1], color: 'var(--c-blue)', aria: 'colonna u', onDrag: (x, y) => { u = [x, y]; draw(); } });
    P.handle({ x: v[0], y: v[1], color: 'var(--c-teal)', aria: 'colonna v', onDrag: (x, y) => { v = [x, y]; draw(); } });
    L.side.append(info, note('Con $u=(3,1)$ e $v=(1,2)$ (la matrice della Figura 5.3) l’area è $|3\\cdot2-1\\cdot1|=5$. Porta $v$ sulla retta di $u$: il parallelogramma degenera e il determinante si annulla.'));
    draw();
  };

  /* ============================================================ CAPITOLO 6: vettori liberi */
  labs['v-liberi'] = function (m) {
    let v = [2, 1], Pp = [-2, -1.5];
    const L = layout(m);
    const PL = new Plot(L.main, { xmin: -5, xmax: 5, ymin: -3.5, ymax: 3.5, W: 560, grid: 1, axes: false, snap: 0.5 });
    const info = readout();
    const base = [0.5, 1.5];
    let HT;
    function draw() {
      PL.begin();
      for (let x = -4.5; x <= 4; x += 2.5) for (let y = -3; y <= 3; y += 2) {
        if (Math.hypot(x - Pp[0], y - Pp[1]) < 0.6 || Math.hypot(x - base[0], y - base[1]) < 0.6) continue;
        PL.arrow(x, y, x + v[0], y + v[1], { color: 'var(--c-blue)', w: 1.6, op: 0.35, head: 10 });
      }
      PL.arrow(base[0], base[1], base[0] + v[0], base[1] + v[1], { color: 'var(--c-blue)', w: 2.8 });
      PL.label('vb', '\\underline{v}', base[0] + v[0] / 2, base[1] + v[1] / 2, { dx: -14 * Math.sign(v[1] || 1), dy: -14 * Math.sign(v[0] || 1), color: 'var(--c-blue)' });
      PL.arrow(Pp[0], Pp[1], Pp[0] + v[0], Pp[1] + v[1], { color: 'var(--c-red)', w: 3 });
      PL.dot(Pp[0], Pp[1], { color: 'var(--c-red)', r: 3 });
      PL.label('P', 'P', Pp[0], Pp[1], { dx: -12, dy: 12, color: 'var(--c-red)' });
      PL.label('Q', 'Q', Pp[0] + v[0], Pp[1] + v[1], { dx: 12, dy: -12, color: 'var(--c-red)' });
      PL.end();
      const mod = Math.hypot(v[0], v[1]);
      info.set([
        ['', 'Tutte le frecce disegnate sono <b>rappresentanti</b> dello stesso ' + K('\\underline{v}') + ': stessa direzione, stesso verso, stesso modulo.'],
        ['modulo', T(`|\\underline{v}| = ${sqrtTex(v[0] * v[0] + v[1] * v[1])}` + (Math.abs(mod - rnd(mod, 0)) > 1e-6 ? `\\approx ${tn(mod, 2)}` : ''))],
        ['', 'L’unico rappresentante applicato in ' + K('P') + ' è ' + K('(P,Q)') + ' (Proposizione 6.1).'],
      ]);
    }
    HT = PL.handle({ x: base[0] + v[0], y: base[1] + v[1], color: 'var(--c-blue)', aria: 'punta del vettore', onDrag: (x, y) => { v = [x - base[0], y - base[1]]; draw(); } });
    PL.handle({ x: Pp[0], y: Pp[1], color: 'var(--c-red)', aria: 'punto P', onDrag: (x, y) => { Pp = [x, y]; draw(); } });
    L.side.append(info, note('Il vettore libero non ha un punto di applicazione: disegnarlo significa scegliere uno dei suoi rappresentanti. Spostando $P$ cambia il rappresentante, non il vettore.'));
    draw();
    void HT;
  };

  labs['v-somma'] = function (m) {
    let v = [3, 0.5], w = [1.5, 2.5], mode = 'tri', lam = 1.5;
    const L = layout(m);
    const PL = new Plot(L.main, { xmin: -4.5, xmax: 5.5, ymin: -3.5, ymax: 4, W: 560, grid: 1, axes: false, snap: 0.5 });
    const info = readout();
    const O = [-2.5, -2];
    const lamRow = slider({ label: '$\\lambda$', min: -3, max: 3, step: 0.1, value: lam, onInput: (x) => { lam = x; draw(); } });
    function draw() {
      PL.begin();
      const Q = [O[0] + v[0], O[1] + v[1]], R = [Q[0] + w[0], Q[1] + w[1]], S = [O[0] + w[0], O[1] + w[1]];
      lamRow.style.display = mode === 'lam' ? '' : 'none';
      if (mode === 'tri') {
        PL.arrow(O[0], O[1], Q[0], Q[1], { color: 'var(--c-blue)', w: 2.8 });
        PL.arrow(Q[0], Q[1], R[0], R[1], { color: 'var(--c-teal)', w: 2.8 });
        PL.arrow(O[0], O[1], R[0], R[1], { color: 'var(--c-red)', w: 3 });
        PL.label('P', 'P', O[0], O[1], { dx: -12, dy: 10 }); PL.label('Q', 'Q', Q[0], Q[1], { dx: 12, dy: 12 }); PL.label('R', 'R', R[0], R[1], { dx: 10, dy: -12 });
        PL.label('lv', '\\underline{v}', (O[0] + Q[0]) / 2, (O[1] + Q[1]) / 2, { dy: 16, color: 'var(--c-blue)' });
        PL.label('lw', '\\underline{w}', (Q[0] + R[0]) / 2, (Q[1] + R[1]) / 2, { dx: 16, color: 'var(--c-teal)' });
        PL.label('ls', '\\underline{v}+\\underline{w}', (O[0] + R[0]) / 2, (O[1] + R[1]) / 2, { dx: -30, dy: -12, color: 'var(--c-red)' });
        info.set([['', '<b>Regola del triangolo.</b> Si applica ' + K('\\underline{v}') + ' in ' + K('P') + ', poi ' + K('\\underline{w}') + ' nel punto di arrivo ' + K('Q') + ': la somma va dalla partenza ' + K('P') + ' all’arrivo ' + K('R') + '.']]);
      } else if (mode === 'par') {
        PL.poly([O, Q, R, S], { fill: 'var(--c-blue)', fop: 0.05, color: 'none', w: 0 });
        PL.line(Q[0], Q[1], R[0], R[1], { color: 'var(--c-teal)', dash: '5 5', w: 1.4 });
        PL.line(S[0], S[1], R[0], R[1], { color: 'var(--c-blue)', dash: '5 5', w: 1.4 });
        PL.arrow(O[0], O[1], Q[0], Q[1], { color: 'var(--c-blue)', w: 2.8 });
        PL.arrow(O[0], O[1], S[0], S[1], { color: 'var(--c-teal)', w: 2.8 });
        PL.arrow(O[0], O[1], R[0], R[1], { color: 'var(--c-red)', w: 3 });
        PL.label('lv', '\\underline{v}', Q[0], Q[1], { dx: 14, dy: 12, color: 'var(--c-blue)' });
        PL.label('lw', '\\underline{w}', S[0], S[1], { dx: -14, dy: -10, color: 'var(--c-teal)' });
        PL.label('ls', '\\underline{v}+\\underline{w}=\\underline{w}+\\underline{v}', R[0], R[1], { dx: 12, dy: -16, color: 'var(--c-red)' });
        info.set([['', '<b>Regola del parallelogramma.</b> Applicati nello stesso punto, ' + K('\\underline{v}') + ' e ' + K('\\underline{w}') + ' sono lati consecutivi; la diagonale è la somma. I due cammini (prima ' + K('\\underline{v}') + ' o prima ' + K('\\underline{w}') + ') arrivano nello stesso punto: la somma è commutativa.']]);
      } else if (mode === 'diff') {
        PL.poly([O, Q, R, S], { fill: 'var(--c-blue)', fop: 0.04, color: 'var(--c-gray)', dash: '3 5', w: 1 });
        PL.arrow(O[0], O[1], Q[0], Q[1], { color: 'var(--c-blue)', w: 2.8 });
        PL.arrow(O[0], O[1], S[0], S[1], { color: 'var(--c-teal)', w: 2.8 });
        PL.arrow(S[0], S[1], Q[0], Q[1], { color: 'var(--c-violet)', w: 3 });
        PL.arrow(O[0], O[1], R[0], R[1], { color: 'var(--c-red)', w: 1.8, op: 0.45 });
        PL.label('lv', '\\underline{v}', Q[0], Q[1], { dx: 14, dy: 12, color: 'var(--c-blue)' });
        PL.label('lw', '\\underline{w}', S[0], S[1], { dx: -14, dy: -10, color: 'var(--c-teal)' });
        PL.label('ld', '\\underline{v}-\\underline{w}', (S[0] + Q[0]) / 2, (S[1] + Q[1]) / 2, { dx: 18, dy: -14, color: 'var(--c-violet)' });
        info.set([['', '<b>Differenza.</b> L’altra diagonale, orientata dal secondo estremo di ' + K('\\underline{w}') + ' al secondo estremo di ' + K('\\underline{v}') + ', rappresenta ' + K('\\underline{v}-\\underline{w}') + ' (Figura 6.5).']]);
      } else {
        const Lm = [O[0] + lam * v[0], O[1] + lam * v[1]];
        PL.line(O[0] - 3 * v[0], O[1] - 3 * v[1], O[0] + 3 * v[0], O[1] + 3 * v[1], { color: 'var(--c-gray)', dash: '3 5', w: 1 });
        PL.arrow(O[0], O[1], Q[0], Q[1], { color: 'var(--c-blue)', w: 2.2, op: 0.55 });
        PL.arrow(O[0], O[1], Lm[0], Lm[1], { color: 'var(--c-red)', w: 3 });
        PL.label('lv', '\\underline{v}', Q[0], Q[1], { dx: 0, dy: 18, color: 'var(--c-blue)' });
        PL.label('ll', '\\lambda\\underline{v}', Lm[0], Lm[1], { dx: 0, dy: -18, color: 'var(--c-red)' });
        info.set([
          ['', T(`\\lambda = ${tn(lam, 1)}`) + ': ' + (Math.abs(lam) < 1e-9 ? 'si ottiene il vettore nullo' : lam > 0 ? 'stessa direzione e stesso verso di ' + K('\\underline{v}') : 'stessa direzione, verso opposto')],
          ['modulo', T(`|\\lambda\\underline{v}| = |\\lambda|\\,|\\underline{v}| = ${tn(Math.abs(lam), 1)}\\cdot${tn(Math.hypot(v[0], v[1]), 2)} = ${tn(Math.abs(lam) * Math.hypot(v[0], v[1]), 2)}`)],
        ]);
      }
      PL.end();
      HW.g.style.display = mode === 'lam' ? 'none' : '';
      HV.set(O[0] + v[0], O[1] + v[1]);
      HW.set(mode === 'tri' ? Q[0] + w[0] : O[0] + w[0], mode === 'tri' ? Q[1] + w[1] : O[1] + w[1]);
    }
    const HV = PL.handle({ x: O[0] + v[0], y: O[1] + v[1], color: 'var(--c-blue)', aria: 'punta di v', onDrag: (x, y) => { v = [x - O[0], y - O[1]]; draw(); } });
    const HW = PL.handle({
      x: O[0] + v[0] + w[0], y: O[1] + v[1] + w[1], color: 'var(--c-teal)', aria: 'punta di w', onDrag: (x, y) => {
        if (mode === 'tri') w = [x - (O[0] + v[0]), y - (O[1] + v[1])]; else w = [x - O[0], y - O[1]];
        draw();
      }
    });
    L.side.append(seg([['tri', 'Triangolo'], ['par', 'Parallelogramma'], ['diff', 'Differenza'], ['lam', 'Multiplo $\\lambda\\underline{v}$']], mode, (x) => { mode = x; draw(); }, 'Costruzione'), lamRow, info);
    draw();
  };

  /* ============================================================ CAPITOLO 7: combinazioni lineari */
  labs['v-comb'] = function (m) {
    let v1 = [2, 0.5], v2 = [0.5, 1.5], t = [3, 3];
    const L = layout(m);
    const PL = new Plot(L.main, { xmin: -4.5, xmax: 5.5, ymin: -3.5, ymax: 4.5, W: 560, grid: 0, axes: false, snap: 0.5 });
    const info = readout();
    function draw() {
      PL.begin();
      const det = v1[0] * v2[1] - v1[1] * v2[0];
      if (Math.abs(det) > 1e-6) {
        for (let k = -8; k <= 8; k++) {
          PL.line(k * v1[0] - 9 * v2[0], k * v1[1] - 9 * v2[1], k * v1[0] + 9 * v2[0], k * v1[1] + 9 * v2[1], { color: 'var(--c-teal)', w: 0.9, op: 0.3 });
          PL.line(k * v2[0] - 9 * v1[0], k * v2[1] - 9 * v1[1], k * v2[0] + 9 * v1[0], k * v2[1] + 9 * v1[1], { color: 'var(--c-blue)', w: 0.9, op: 0.3 });
        }
        const l1 = (t[0] * v2[1] - t[1] * v2[0]) / det, l2 = (v1[0] * t[1] - v1[1] * t[0]) / det;
        const A = [l1 * v1[0], l1 * v1[1]], B = [l2 * v2[0], l2 * v2[1]];
        PL.line(A[0], A[1], t[0], t[1], { color: 'var(--c-gray)', dash: '5 5', w: 1.4 });
        PL.line(B[0], B[1], t[0], t[1], { color: 'var(--c-gray)', dash: '5 5', w: 1.4 });
        PL.arrow(0, 0, A[0], A[1], { color: 'var(--c-blue)', w: 2, op: 0.65, dash: '6 4' });
        PL.arrow(0, 0, B[0], B[1], { color: 'var(--c-teal)', w: 2, op: 0.65, dash: '6 4' });
        PL.label('A', '\\lambda_1\\underline{v}_1', A[0], A[1], { dx: 10, dy: 16, small: true, color: 'var(--c-blue)' });
        PL.label('B', '\\lambda_2\\underline{v}_2', B[0], B[1], { dx: -26, dy: -4, small: true, color: 'var(--c-teal)' });
        info.set([
          ['coefficienti', T(`\\lambda_1 = ${tfrac(l1, 2)},\\quad \\lambda_2 = ${tfrac(l2, 2)}`)],
          ['scomposizione', T(`\\underline{t} = ${tfrac(l1, 2)}\\,\\underline{v}_1 ${l2 < 0 ? '' : '+'} ${tfrac(l2, 2)}\\,\\underline{v}_2`)],
          ['', '<span class="badge ok">' + K('\\underline{v}_1,\\underline{v}_2') + ' indipendenti: ogni vettore del piano si scrive in modo unico</span>'],
        ]);
      } else {
        const len = Math.hypot(v1[0], v1[1]) || Math.hypot(v2[0], v2[1]) || 1;
        const d = Math.hypot(v1[0], v1[1]) > 1e-9 ? v1 : v2;
        PL.line(-9 * d[0] / len, -9 * d[1] / len, 9 * d[0] / len, 9 * d[1] / len, { color: 'var(--c-red)', w: 2, op: 0.5 });
        const onLine = Math.abs(t[0] * d[1] - t[1] * d[0]) < 1e-6;
        info.set([
          ['', '<span class="badge no">' + K('\\underline{v}_1\\parallel\\underline{v}_2') + ': sono dipendenti</span>'],
          ['', 'Le combinazioni ' + K('\\lambda_1\\underline{v}_1+\\lambda_2\\underline{v}_2') + ' riempiono solo la retta rossa: ' + (onLine ? K('\\underline{t}') + ' ci sta (in infiniti modi).' : K('\\underline{t}') + ' non si può ottenere.')],
        ]);
      }
      PL.arrow(0, 0, v1[0], v1[1], { color: 'var(--c-blue)', w: 2.8 });
      PL.arrow(0, 0, v2[0], v2[1], { color: 'var(--c-teal)', w: 2.8 });
      PL.arrow(0, 0, t[0], t[1], { color: 'var(--c-red)', w: 3 });
      PL.tipLabel('v1', '\\underline{v}_1', 0, 0, v1[0], v1[1], 'var(--c-blue)', 20);
      PL.tipLabel('v2', '\\underline{v}_2', 0, 0, v2[0], v2[1], 'var(--c-teal)', 20);
      PL.tipLabel('t', '\\underline{t}', 0, 0, t[0], t[1], 'var(--c-red)', 18);
      PL.dot(0, 0, { color: 'var(--ink)', r: 3 });
      PL.end();
    }
    PL.handle({ x: v1[0], y: v1[1], color: 'var(--c-blue)', aria: 'punta di v1', onDrag: (x, y) => { v1 = [x, y]; draw(); } });
    PL.handle({ x: v2[0], y: v2[1], color: 'var(--c-teal)', aria: 'punta di v2', onDrag: (x, y) => { v2 = [x, y]; draw(); } });
    PL.handle({ x: t[0], y: t[1], color: 'var(--c-red)', aria: 'punta di t', onDrag: (x, y) => { t = [x, y]; draw(); } });
    L.side.append(info, note('È la Costruzione 7.3: le parallele per la punta di $\\underline{t}$ a $\\underline{v}_2$ e a $\\underline{v}_1$ individuano i due addendi. La perpendicolarità non conta: il reticolo può essere obliquo quanto si vuole (Osservazione 7.2).'));
    draw();
  };

  /* ============================================================ CAPITOLO 8: prodotto scalare */
  labs['ps-parametro'] = function (m) {
    let hh = 1;
    const L = layout(m);
    const PL = new Plot(L.main, { xmin: -7, xmax: 7, ymin: -4, ymax: 7, W: 560, grid: 1, axes: false, snap: 0 });
    const info = readout();
    // |v1| = 2, |v2| = 3, angolo π/3
    const v1 = [2, 0], v2 = [3 * Math.cos(Math.PI / 3), 3 * Math.sin(Math.PI / 3)];
    const w1 = [-v1[0] + 2 * v2[0], -v1[1] + 2 * v2[1]];
    const slh = slider({ label: '$h$', min: -3, max: 3, step: 0.01, value: hh, onInput: (x) => { hh = x; draw(); } });
    function draw() {
      PL.begin();
      const w2 = [3 * v1[0] + hh * v2[0], 3 * v1[1] + hh * v2[1]];
      const dot = w1[0] * w2[0] + w1[1] * w2[1];
      PL.line(3 * v1[0] - 3 * v2[0], 3 * v1[1] - 3 * v2[1], 3 * v1[0] + 3 * v2[0], 3 * v1[1] + 3 * v2[1], { color: 'var(--c-gray)', dash: '3 5', w: 1 });
      PL.arrow(0, 0, v1[0], v1[1], { color: 'var(--c-blue)', w: 2.2, op: 0.7 });
      PL.arrow(0, 0, v2[0], v2[1], { color: 'var(--c-teal)', w: 2.2, op: 0.7 });
      PL.arc(0, 0, 0.7, 0, Math.PI / 3, { color: 'var(--ink-3)', w: 1.2 });
      PL.label('a', '\\tfrac\\pi3', 1.1, 0.55, { small: true, color: 'var(--ink-3)' });
      PL.arrow(0, 0, w1[0], w1[1], { color: 'var(--c-red)', w: 3 });
      PL.arrow(0, 0, w2[0], w2[1], { color: Math.abs(dot) < 0.06 ? 'var(--c-green)' : 'var(--c-violet)', w: 3 });
      if (Math.abs(dot) < 0.06) {
        const n1 = Math.hypot(...w1), n2 = Math.hypot(...w2);
        PL.rightAngle(0, 0, w1[0] / n1, w1[1] / n1, w2[0] / n2, w2[1] / n2, 16);
      }
      PL.tipLabel('v1', '\\underline{v}_1', 0, 0, v1[0], v1[1], 'var(--c-blue)', 16);
      PL.tipLabel('v2', '\\underline{v}_2', 0, 0, v2[0], v2[1], 'var(--c-teal)', 18);
      PL.tipLabel('w1', '\\underline{w}_1', 0, 0, w1[0], w1[1], 'var(--c-red)', 18);
      PL.tipLabel('w2', '\\underline{w}_2', 0, 0, w2[0], w2[1], Math.abs(dot) < 0.06 ? 'var(--c-green)' : 'var(--c-violet)', 18);
      PL.end();
      const ang = Math.acos(Math.max(-1, Math.min(1, dot / (Math.hypot(...w1) * Math.hypot(...w2) || 1))));
      info.set([
        ['dati', T('|\\underline{v}_1|=2,\\ |\\underline{v}_2|=3,\\ \\widehat{\\underline{v}_1\\underline{v}_2}=\\tfrac\\pi3')],
        ['', T(`\\underline{w}_1\\cdot\\underline{w}_2 = 15h+6 = 15\\cdot(${tn(hh, 2)})+6 = ${tn(15 * hh + 6, 2)}`)],
        ['angolo', T(`\\widehat{\\underline{w}_1\\underline{w}_2} \\approx ${tn(ang * 180 / Math.PI, 1)}^\\circ`)],
        ['', Math.abs(dot) < 0.06 ? '<span class="badge ok">perpendicolari: h = −2/5</span>' : `<span class="badge neu">${dot > 0 ? 'angolo acuto: prodotto positivo' : 'angolo ottuso: prodotto negativo'}</span>`],
      ]);
    }
    L.side.append(slh, h('div', { class: 'lab-ctl' }, btn('Porta h a −2/5', null, () => { hh = -0.4; slh.setValue(-0.4); draw(); })), info,
      note('Al variare di $h$ la punta di $\\underline{w}_2$ scorre sulla retta tratteggiata: una sola posizione è perpendicolare a $\\underline{w}_1$, e il prodotto scalare cambia segno proprio lì.'));
    draw();
  };

  labs['ps-proiezione'] = function (m) {
    let v = [3, 1], w = [1.5, 2.5];
    const L = layout(m);
    const PL = new Plot(L.main, { xmin: -4.5, xmax: 4.5, ymin: -3.2, ymax: 3.8, W: 560, grid: 1, snap: 0.5 });
    const info = readout();
    function draw() {
      PL.begin();
      const vv = v[0] * v[0] + v[1] * v[1];
      const d = v[0] * w[0] + v[1] * w[1];
      const nv = Math.sqrt(vv), nw = Math.hypot(w[0], w[1]);
      if (nv > 1e-9) {
        PL.line(-6 * v[0] / nv, -6 * v[1] / nv, 6 * v[0] / nv, 6 * v[1] / nv, { color: 'var(--c-gray)', dash: '3 5', w: 1 });
        const p = [d / vv * v[0], d / vv * v[1]];
        PL.line(w[0], w[1], p[0], p[1], { color: 'var(--c-gray)', dash: '5 4', w: 1.4 });
        PL.arrow(p[0], p[1], w[0], w[1], { color: 'var(--c-violet)', w: 2, op: 0.75 });
        PL.arrow(0, 0, p[0], p[1], { color: 'var(--c-red)', w: 3.2 });
        if (nw > 1e-9 && Math.hypot(w[0] - p[0], w[1] - p[1]) > 1e-6) {
          const tx = (w[0] - p[0]), ty = (w[1] - p[1]), tl = Math.hypot(tx, ty);
          const sg = d >= 0 ? 1 : -1;
          PL.rightAngle(p[0], p[1], -sg * v[0] / nv, -sg * v[1] / nv, tx / tl, ty / tl, 11);
        }
        PL.label('p', '\\underline{t}_1', p[0], p[1], { dx: 0, dy: 18, small: true, color: 'var(--c-red)' });
        PL.label('t2', '\\underline{t}_2', (p[0] + w[0]) / 2, (p[1] + w[1]) / 2, { dx: 14, dy: 0, small: true, color: 'var(--c-violet)' });
        if (nw > 1e-9) {
          const a0 = Math.atan2(v[1], v[0]); let a1 = Math.atan2(w[1], w[0]); let dd = a1 - a0;
          while (dd > Math.PI) dd -= 2 * Math.PI; while (dd < -Math.PI) dd += 2 * Math.PI;
          PL.arc(0, 0, 0.6, a0, a0 + dd, { color: 'var(--c-orange)', w: 1.8 });
        }
      }
      PL.arrow(0, 0, v[0], v[1], { color: 'var(--c-blue)', w: 2.8 });
      PL.arrow(0, 0, w[0], w[1], { color: 'var(--c-teal)', w: 2.8 });
      PL.tipLabel('v', '\\underline{v}', 0, 0, v[0], v[1], 'var(--c-blue)', 18);
      PL.tipLabel('w', '\\underline{w}', 0, 0, w[0], w[1], 'var(--c-teal)', 18);
      PL.end();
      if (nv < 1e-9) { info.set([['', 'Con ' + K('\\underline{v}=\\underline{0}') + ' la proiezione non è definita.']]); return; }
      const cos = nw > 1e-9 ? d / (nv * nw) : 0;
      const ang = Math.acos(Math.max(-1, Math.min(1, cos)));
      info.set([
        ['prodotto scalare', T(`\\underline{v}\\cdot\\underline{w} = ${tn(v[0])}\\cdot${tn(w[0])}+${tn(v[1])}\\cdot${tn(w[1])} = ${tn(d)}`)],
        ['angolo', T(`\\widehat{\\underline{v}\\underline{w}} \\approx ${tn(ang * 180 / Math.PI, 1)}^\\circ,\\ \\ \\cos = ${tn(cos, 3)}`)],
        ['componente orientata', T(`\\dfrac{\\underline{v}\\cdot\\underline{w}}{|\\underline{v}|} = ${tn(d / nv, 3)}`)],
        ['proiezione', T(`\\underline{t}_1=\\operatorname{proj}_{\\underline{v}}\\underline{w} = \\dfrac{${tn(d)}}{${tn(vv)}}\\,\\underline{v} = (${tn(d / vv * v[0], 3)},\\ ${tn(d / vv * v[1], 3)})`)],
        ['', Math.abs(d) < 1e-9 ? '<span class="badge ok">perpendicolari: prodotto nullo, proiezione nulla</span>' : d > 0 ? '<span class="badge neu">angolo acuto: la proiezione ha il verso di v</span>' : '<span class="badge no">angolo ottuso: la proiezione ha verso opposto a v</span>'],
      ]);
    }
    PL.handle({ x: v[0], y: v[1], color: 'var(--c-blue)', aria: 'punta di v', onDrag: (x, y) => { v = [x, y]; draw(); } });
    PL.handle({ x: w[0], y: w[1], color: 'var(--c-teal)', aria: 'punta di w', onDrag: (x, y) => { w = [x, y]; draw(); } });
    L.side.append(info, note('Il vettore $\\underline{t}_2=\\underline{w}-\\operatorname{proj}_{\\underline{v}}\\underline{w}$ è perpendicolare a $\\underline{v}$ (Proposizione 8.5): è il secondo cateto del triangolo rettangolo con ipotenusa $\\underline{w}$. Qui le componenti sono in una base ortonormale, quindi $\\underline{v}\\cdot\\underline{w}$ si calcola come in (10.4).'));
    draw();
  };
})();
