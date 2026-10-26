/* Diagrammi di flusso ricostruiti dai blocchi Mermaid della dispensa:
   disposizione a livelli (Sugiyama semplificato), archi su canali liberi, etichette HTML con formule. */
(function () {
  'use strict';
  const GAL = window.GAL = window.GAL || {};
  const SVGNS = 'http://www.w3.org/2000/svg';

  /* ---------------------------------------------------------------- disposizione */
  function layout(g, dir, sizes, opt) {
    const horiz = dir === 'LR';
    const ids = g.nodes.map((n) => n.id);
    // cicli (coppie andata/ritorno): DFS nell'ordine di definizione
    const state = new Map(), rev = new Set();
    const adj = new Map(ids.map((id) => [id, []]));
    g.edges.forEach((e, k) => adj.get(e.from).push([e.to, k]));
    const dfs = (v) => {
      state.set(v, 1);
      for (const [w, k] of adj.get(v)) {
        if (state.get(w) === 1) rev.add(k);
        else if (!state.get(w)) dfs(w);
      }
      state.set(v, 2);
    };
    ids.forEach((id) => { if (!state.get(id)) dfs(id); });
    const E = g.edges.map((e, k) => (rev.has(k) ? { a: e.to, b: e.from, k, rev: true } : { a: e.from, b: e.to, k, rev: false }));
    // livelli (cammino più lungo)
    const indeg = new Map(ids.map((id) => [id, 0]));
    E.forEach((e) => indeg.set(e.b, indeg.get(e.b) + 1));
    const rank = new Map();
    const q = ids.filter((id) => indeg.get(id) === 0);
    q.forEach((id) => rank.set(id, 0));
    while (q.length) {
      const v = q.shift();
      E.filter((e) => e.a === v).forEach((e) => {
        rank.set(e.b, Math.max(rank.get(e.b) || 0, rank.get(v) + 1));
        indeg.set(e.b, indeg.get(e.b) - 1);
        if (indeg.get(e.b) === 0) q.push(e.b);
      });
    }
    ids.forEach((id) => { if (!rank.has(id)) rank.set(id, 0); });
    const along = (s) => (horiz ? s.w : s.h);
    const across = (s) => (horiz ? s.h : s.w);
    // nodi fittizi: gli archi lunghi passano per un canale; quello con l'etichetta ne riserva lo spazio
    const V = new Map();
    ids.forEach((id) => V.set(id, Object.assign({ id, rank: rank.get(id), dummy: false }, sizes.get(id))));
    const chains = [];
    E.forEach((e) => {
      const ra = rank.get(e.a), rb = rank.get(e.b);
      const chain = [e.a];
      const span = rb - ra;
      const lab = g.edges[e.k].lsize;
      const labAt = ra + Math.max(1, Math.ceil(span / 2)) - (span % 2 === 0 ? 0 : 0);
      for (let r = ra + 1; r < rb; r++) {
        const did = `__d${e.k}_${r}`;
        const carries = lab && r === Math.min(rb - 1, Math.max(ra + 1, labAt));
        V.set(did, { id: did, rank: r, dummy: true, edge: e.k, w: carries ? lab.w : 6, h: carries ? lab.h : 6, carries });
        chain.push(did);
      }
      chain.push(e.b);
      chains[e.k] = chain;
    });
    const maxR = Math.max(...Array.from(V.values()).map((v) => v.rank));
    const ranks = Array.from({ length: maxR + 1 }, () => []);
    const seen = new Set();
    const put = (id) => { if (!seen.has(id)) { seen.add(id); ranks[V.get(id).rank].push(id); } };
    ids.forEach(put);
    chains.forEach((c) => c.forEach(put));
    const up = new Map(), down = new Map();
    V.forEach((v, id) => { up.set(id, []); down.set(id, []); });
    chains.forEach((c) => { for (let i = 0; i + 1 < c.length; i++) { down.get(c[i]).push(c[i + 1]); up.get(c[i + 1]).push(c[i]); } });
    // pesi per l'allineamento: le coppie andata/ritorno tirano molto di più (archi paralleli e diritti)
    const pairCount = new Map();
    g.edges.forEach((e) => { const kk = [e.from, e.to].sort().join('|'); pairCount.set(kk, (pairCount.get(kk) || 0) + 1); });
    const wOf = (a, b) => (pairCount.get([a, b].sort().join('|')) > 1 ? 4 : 1);
    const groupOf = new Map();
    (g.groups || []).forEach((gr, gi) => gr.nodes.forEach((id) => groupOf.set(id, gi)));
    // ordine nei livelli: baricentri, poi i gruppi restano compatti
    for (let it = 0; it < 16; it++) {
      const pos = new Map();
      ranks.forEach((r) => r.forEach((id, i) => pos.set(id, i)));
      const goDown = it % 2 === 0;
      const order = goDown ? ranks.map((_, i) => i) : ranks.map((_, i) => ranks.length - 1 - i);
      for (const r of order) {
        const bc = new Map();
        ranks[r].forEach((id, i) => {
          const nb = (goDown ? up : down).get(id);
          bc.set(id, nb.length ? nb.reduce((s, x) => s + pos.get(x), 0) / nb.length : i);
        });
        if (groupOf.size) {
          // media per gruppo: i nodi dello stesso gruppo restano adiacenti
          const gm = new Map();
          ranks[r].forEach((id) => { if (groupOf.has(id)) { const k = groupOf.get(id); const a = gm.get(k) || [0, 0]; gm.set(k, [a[0] + bc.get(id), a[1] + 1]); } });
          ranks[r].forEach((id) => { if (groupOf.has(id)) { const a = gm.get(groupOf.get(id)); bc.set(id, a[0] / a[1] + bc.get(id) * 1e-3); } });
        }
        ranks[r].sort((x, y) => bc.get(x) - bc.get(y));
        ranks[r].forEach((id, i) => pos.set(id, i));
      }
    }
    // coordinate lungo i livelli
    const mainPos = [], band = [];
    let m = 0;
    for (let r = 0; r <= maxR; r++) {
      const ext = Math.max(...ranks[r].map((id) => along(V.get(id))), 8);
      mainPos[r] = m + ext / 2;
      band[r] = [m, m + ext];
      m += ext + opt.gapMain;
    }
    // coordinate trasversali
    const gap = (a, b) => {
      const A = V.get(a), B = V.get(b);
      let s = (across(A) + across(B)) / 2;
      if (A.dummy && B.dummy && !A.carries && !B.carries) s += opt.gapCross * 0.45;
      else if (A.dummy || B.dummy) s += opt.gapCross * 0.75;
      else s += opt.gapCross;
      const ga = groupOf.get(a), gb = groupOf.get(b);
      if (ga !== gb && (ga !== undefined || gb !== undefined)) s += opt.groupGap;
      return s;
    };
    const cross = new Map();
    ranks.forEach((r) => { let c = 0; r.forEach((id, i) => { if (i) c += gap(r[i - 1], id); cross.set(id, c); }); });
    const width = (r) => (r.length ? cross.get(r[r.length - 1]) - cross.get(r[0]) : 0);
    const maxW = Math.max(...ranks.map(width));
    ranks.forEach((r) => { const off = (maxW - width(r)) / 2; r.forEach((id) => cross.set(id, cross.get(id) + off)); });
    for (let it = 0; it < 40; it++) {
      const sweep = it % 2 === 0 ? ranks : ranks.slice().reverse();
      sweep.forEach((r) => {
        const want = r.map((id) => {
          const nb = up.get(id).concat(down.get(id));
          if (!nb.length) return cross.get(id);
          let sw = 0, sx = 0;
          nb.forEach((x) => { const w = wOf(id, x); sw += w; sx += w * cross.get(x); });
          return sx / sw;
        });
        const L = want.slice(), R = want.slice();
        for (let i = 1; i < r.length; i++) L[i] = Math.max(L[i], L[i - 1] + gap(r[i - 1], r[i]));
        for (let i = r.length - 2; i >= 0; i--) R[i] = Math.min(R[i], R[i + 1] - gap(r[i], r[i + 1]));
        r.forEach((id, i) => cross.set(id, (L[i] + R[i]) / 2));
        for (let i = 1; i < r.length; i++) {
          const need = cross.get(r[i - 1]) + gap(r[i - 1], r[i]);
          if (cross.get(r[i]) < need) cross.set(r[i], need);
        }
      });
    }
    const pos = new Map();
    V.forEach((v, id) => {
      const mm = mainPos[v.rank], cc = cross.get(id);
      pos.set(id, horiz ? { x: mm, y: cc } : { x: cc, y: mm });
    });
    return { V, pos, chains, E, horiz, band, rank };
  }

  /* ---------------------------------------------------------------- disegno */
  function build(box, g) {
    box.innerHTML = '';
    const inner = document.createElement('div');
    inner.className = 'dgm-in';
    box.append(inner);
    const nodeEl = new Map();
    g.nodes.forEach((n) => {
      const el = document.createElement('div');
      el.className = 'dgm-node' + (n.shape === 'diamond' ? ' diamond' : '');
      const l = document.createElement('div');
      l.className = 'dgm-l';
      l.innerHTML = n.html;
      el.append(l);
      inner.append(el);
      nodeEl.set(n.id, el);
    });
    g.edges.forEach((e) => {
      e._el = null;
      if (e.html) {
        const el = document.createElement('div');
        el.className = 'dgm-el';
        el.innerHTML = e.html;
        inner.append(el);
        e._el = el;
      }
    });
    if (GAL.renderIn) GAL.renderIn(inner);
    return { inner, nodeEl };
  }

  function draw(box, g, dir, measureOnly) {
    const { inner, nodeEl } = build(box, g);
    const sizes = new Map();
    nodeEl.forEach((el, id) => { const r = el.getBoundingClientRect(); sizes.set(id, { w: Math.ceil(r.width), h: Math.ceil(r.height) }); });
    const twinKey = (e) => [e.from, e.to].sort().join('|');
    const twins = new Map();
    g.edges.forEach((e) => twins.set(twinKey(e), (twins.get(twinKey(e)) || 0) + 1));
    g.edges.forEach((e) => {
      e.twin = twins.get(twinKey(e)) > 1;
      if (e._el) { const r = e._el.getBoundingClientRect(); e.lsize = { w: Math.ceil(r.width), h: Math.ceil(r.height) }; } else e.lsize = null;
    });
    const fsz = parseFloat(getComputedStyle(inner).fontSize) || 16;
    const horiz = dir === 'LR';
    // spazio fra livelli per le etichette degli archi diretti (senza nodi fittizi)
    let labMain = 0;
    g.edges.forEach((e) => { if (e.lsize) labMain = Math.max(labMain, (horiz ? e.lsize.w : e.lsize.h)); });
    const hasTwinLabels = g.edges.some((e) => e.twin && e.lsize);
    const twinCross = Math.max(0, ...g.edges.filter((e) => e.twin && e.lsize).map((e) => (horiz ? e.lsize.h : e.lsize.w)));
    const L = layout(g, dir, sizes, {
      gapCross: fsz * 1.7 + (hasTwinLabels ? twinCross : 0),
      gapMain: Math.max(fsz * 2.6, labMain + fsz * 1.6),
      groupGap: (g.groups && g.groups.length) ? fsz * 2.4 : 0,
    });
    // porte: gli archi che escono/entrano dallo stesso lato si distribuiscono
    const sideOf = (id, other) => {
      const p = L.pos.get(id), o = L.pos.get(other);
      if (L.horiz) return o.x >= p.x ? 'R' : 'L';
      return o.y >= p.y ? 'B' : 'T';
    };
    const ports = new Map();
    const addPort = (node, side, key, toward) => {
      const k = node + side;
      if (!ports.has(k)) ports.set(k, []);
      ports.get(k).push({ key, toward });
    };
    const routes = g.edges.map((e, k) => {
      let chain = L.chains[k].slice();
      if (L.E[k].rev) chain = chain.reverse();
      const first = chain[1], last = chain[chain.length - 2];
      let sA = sideOf(e.from, first);
      const sB = sideOf(e.to, last);
      // verticale: se il nodo d'arrivo (livello successivo) è tutto spostato di lato, si esce dal fianco
      let elbow = false;
      if (!L.horiz && chain.length === 2 && !e.twin) {
        const p = L.pos.get(e.from), q = L.pos.get(e.to), a = sizes.get(e.from), b = sizes.get(e.to);
        if (Math.abs(q.x - p.x) > (a.w + b.w) / 2 + fsz && q.y > p.y) { sA = q.x > p.x ? 'R' : 'L'; elbow = true; }
      }
      addPort(e.from, sA, k + 'a', L.pos.get(first));
      addPort(e.to, sB, k + 'b', L.pos.get(last));
      return { e, k, chain, sA, sB, elbow };
    });
    const portPos = new Map();
    ports.forEach((list, key) => {
      const node = key.slice(0, -1), side = key.slice(-1);
      const p = L.pos.get(node), s = sizes.get(node);
      const alongSide = side === 'B' || side === 'T';
      list.sort((u, v) => (alongSide ? u.toward.x - v.toward.x : u.toward.y - v.toward.y));
      const n = list.length;
      const span = Math.min((alongSide ? s.w : s.h) * 0.55, (n - 1) * fsz * 1.1);
      list.forEach((it, i) => {
        const off = n > 1 ? -span / 2 + span * i / (n - 1) : 0;
        let x = p.x, y = p.y;
        if (side === 'B') { x += off; y += s.h / 2; } else if (side === 'T') { x += off; y -= s.h / 2; }
        else if (side === 'R') { y += off; x += s.w / 2; } else { y += off; x -= s.w / 2; }
        portPos.set(it.key, { x, y });
      });
    });
    // punti del percorso: porta, canali dei nodi fittizi, porta
    routes.forEach((r) => {
      const pts = [portPos.get(r.k + 'a')];
      for (let i = 1; i < r.chain.length - 1; i++) {
        const d = L.V.get(r.chain[i]), p = L.pos.get(r.chain[i]);
        const [b0, b1] = L.band[d.rank];
        const forward = L.horiz ? (L.pos.get(r.chain[r.chain.length - 1]).x > L.pos.get(r.chain[0]).x) : (L.pos.get(r.chain[r.chain.length - 1]).y > L.pos.get(r.chain[0]).y);
        const a = forward ? b0 : b1, b = forward ? b1 : b0;
        if (L.horiz) { pts.push({ x: a, y: p.y }); pts.push({ x: b, y: p.y }); } else { pts.push({ x: p.x, y: a }); pts.push({ x: p.x, y: b }); }
        if (d.carries) r.labelAt = { x: p.x, y: p.y };
      }
      pts.push(portPos.get(r.k + 'b'));
      r.pts = pts;
    });
    // etichette: sul nodo fittizio che le porta, altrimenti a metà; per le coppie, ai lati opposti
    const twinSeen = new Map();
    routes.forEach((r) => {
      if (!r.e.lsize) return;
      if (r.labelAt) { r.lab = r.labelAt; return; }
      const a = r.pts[0], b = r.pts[r.pts.length - 1];
      let x = (a.x + b.x) / 2, y = (a.y + b.y) / 2;
      if (r.e.twin) {
        const key = twinKey(r.e);
        const kth = twinSeen.get(key) || 0;
        twinSeen.set(key, kth + 1);
        const sgn = kth === 0 ? -1 : 1;
        if (L.horiz) y += sgn * (r.e.lsize.h / 2 + fsz * 0.25);
        else x += sgn * (r.e.lsize.w / 2 + fsz * 0.45);
      }
      r.lab = { x, y };
    });
    // ingombro complessivo
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    const grow = (cx, cy, w, h) => { x0 = Math.min(x0, cx - w / 2); x1 = Math.max(x1, cx + w / 2); y0 = Math.min(y0, cy - h / 2); y1 = Math.max(y1, cy + h / 2); };
    g.nodes.forEach((n) => { const p = L.pos.get(n.id), s = sizes.get(n.id); grow(p.x, p.y, s.w, s.h); });
    routes.forEach((r) => { if (r.lab) grow(r.lab.x, r.lab.y, r.e.lsize.w, r.e.lsize.h); r.pts.forEach((p) => grow(p.x, p.y, 2, 2)); });
    const pad = fsz * 0.8;
    const groups = (g.groups || []).map((gr) => {
      let a = Infinity, b = Infinity, c = -Infinity, d = -Infinity;
      gr.nodes.forEach((id) => { const p = L.pos.get(id), s = sizes.get(id); a = Math.min(a, p.x - s.w / 2); c = Math.max(c, p.x + s.w / 2); b = Math.min(b, p.y - s.h / 2); d = Math.max(d, p.y + s.h / 2); });
      routes.forEach((r) => {
        if (r.lab && gr.nodes.includes(r.e.from) && gr.nodes.includes(r.e.to)) {
          a = Math.min(a, r.lab.x - r.e.lsize.w / 2); c = Math.max(c, r.lab.x + r.e.lsize.w / 2);
          b = Math.min(b, r.lab.y - r.e.lsize.h / 2); d = Math.max(d, r.lab.y + r.e.lsize.h / 2);
        }
      });
      const q = { gr, x0: a - pad, y0: b - pad - fsz * 1.3, x1: c + pad, y1: d + pad };
      grow((q.x0 + q.x1) / 2, (q.y0 + q.y1) / 2, q.x1 - q.x0, q.y1 - q.y0);
      return q;
    });
    const M = 6;
    const W = Math.ceil(x1 - x0 + 2 * M), H = Math.ceil(y1 - y0 + 2 * M);
    if (measureOnly) return { W, H };
    const tx = (x) => x - x0 + M, ty = (y) => y - y0 + M;
    inner.style.width = W + 'px';
    inner.style.height = H + 'px';
    const svg = document.createElementNS(SVGNS, 'svg');
    svg.setAttribute('class', 'dgm-svg');
    svg.setAttribute('width', W);
    svg.setAttribute('height', H);
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    inner.prepend(svg);
    groups.forEach((q) => {
      const d = document.createElement('div');
      d.className = 'dgm-group';
      Object.assign(d.style, { left: tx(q.x0) + 'px', top: ty(q.y0) + 'px', width: (q.x1 - q.x0) + 'px', height: (q.y1 - q.y0) + 'px' });
      const l = document.createElement('span');
      l.className = 'dgm-group-l';
      l.innerHTML = q.gr.html;
      d.append(l);
      svg.after(d);
    });
    g.nodes.forEach((n) => {
      const el = nodeEl.get(n.id), p = L.pos.get(n.id), s = sizes.get(n.id);
      el.style.left = tx(p.x - s.w / 2) + 'px';
      el.style.top = ty(p.y - s.h / 2) + 'px';
      el.style.width = s.w + 'px';
      el.style.height = s.h + 'px';
      if (n.shape === 'diamond') {
        const X = tx(p.x - s.w / 2), Y = ty(p.y - s.h / 2), w = s.w, h = s.h, k = Math.min(h / 2, w / 5);
        const poly = document.createElementNS(SVGNS, 'polygon');
        poly.setAttribute('class', 'dia');
        poly.setAttribute('points', [[X, Y + h / 2], [X + k, Y], [X + w - k, Y], [X + w, Y + h / 2], [X + w - k, Y + h], [X + k, Y + h]].map((q) => q.join(',')).join(' '));
        svg.append(poly);
      }
    });
    routes.forEach((r) => {
      const P = r.pts.map((p) => ({ x: tx(p.x), y: ty(p.y) }));
      const style = r.e.style;
      const head = style === 'line' ? 0 : style === 'thick' ? 9 : 7.5;
      // accorcia l'ultimo tratto per la punta
      const last = P[P.length - 1], prev = P[P.length - 2];
      const dl = Math.hypot(last.x - prev.x, last.y - prev.y) || 1;
      const ux = (last.x - prev.x) / dl, uy = (last.y - prev.y) / dl;
      const end = { x: last.x - ux * head * 0.85, y: last.y - uy * head * 0.85 };
      const Q = P.slice(0, -1).concat([end]);
      let d = `M${Q[0].x.toFixed(1)},${Q[0].y.toFixed(1)}`;
      if (r.elbow) {
        const a = Q[0], b = Q[1];
        d += ` C${(a.x + (b.x - a.x) * 0.8).toFixed(1)},${a.y.toFixed(1)} ${b.x.toFixed(1)},${(a.y + (b.y - a.y) * 0.25).toFixed(1)} ${b.x.toFixed(1)},${b.y.toFixed(1)}`;
      }
      for (let i = r.elbow ? 1 : 0; i + 1 < Q.length; i++) {
        const a = Q[i], b = Q[i + 1];
        const straight = L.horiz ? Math.abs(a.y - b.y) < 0.5 : Math.abs(a.x - b.x) < 0.5;
        if (straight) { d += ` L${b.x.toFixed(1)},${b.y.toFixed(1)}`; continue; }
        if (L.horiz) { const mx = (a.x + b.x) / 2; d += ` C${mx.toFixed(1)},${a.y.toFixed(1)} ${mx.toFixed(1)},${b.y.toFixed(1)} ${b.x.toFixed(1)},${b.y.toFixed(1)}`; }
        else { const my = (a.y + b.y) / 2; d += ` C${a.x.toFixed(1)},${my.toFixed(1)} ${b.x.toFixed(1)},${my.toFixed(1)} ${b.x.toFixed(1)},${b.y.toFixed(1)}`; }
      }
      const path = document.createElementNS(SVGNS, 'path');
      path.setAttribute('class', 'e' + (style === 'dotted' ? ' dotted' : style === 'thick' ? ' thick' : ''));
      path.setAttribute('d', d);
      svg.append(path);
      if (head) {
        // la punta segue la tangente finale (verticale o orizzontale) del percorso
        let vx, vy;
        if (L.horiz) { vx = Math.sign(last.x - prev.x) || 1; vy = 0; } else { vx = 0; vy = Math.sign(last.y - prev.y) || 1; }
        const w = style === 'thick' ? 6.5 : 4.8;
        const bx = last.x - vx * head, by = last.y - vy * head;
        const tri = document.createElementNS(SVGNS, 'path');
        tri.setAttribute('class', 'ah' + (style === 'thick' ? ' thick' : ''));
        tri.setAttribute('d', `M${last.x},${last.y} L${bx - vy * w},${by + vx * w} L${bx + vy * w},${by - vx * w} Z`);
        svg.append(tri);
      }
      if (r.lab) {
        r.e._el.style.left = tx(r.lab.x) + 'px';
        r.e._el.style.top = ty(r.lab.y) + 'px';
      }
    });
    return { W, H };
  }

  GAL.diagram = function (box) {
    if (!box._g) box._g = JSON.parse(box.dataset.graph);
    const g = box._g;
    const avail = (box.clientWidth || box.parentElement.clientWidth) - 4;
    const decl = g.dir === 'LR' ? 'LR' : 'TD';
    const other = decl === 'LR' ? 'TD' : 'LR';
    const a = draw(box, g, decl, true);
    if (a.W <= avail) { draw(box, g, decl); return; }
    const b = draw(box, g, other, true);
    // sceglie l'orientamento che entra; altrimenti quello che sborda meno
    if (b.W <= avail || b.W < a.W) draw(box, g, other); else draw(box, g, decl);
  };
})();
