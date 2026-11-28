/* === PEN AND WHITEBOARD (template/tool/pen.js, with pen.css, pen.html and pen-help.html beside it) ===
   The build puts this file before deck.js in the page's one <script>. deck.js copies every method of PenAndBoard onto the
   deck (SlidePresentation) before it starts, so inside these methods `this` is the deck. See PEN.md before changing them.

   What the pen uses of the deck:
     this.stage           the 1920 x 1080 stage (#deckStage); the ink layer, the shade and the board are added to it
     this.reveal()        shows the control bar and the ball for a while (setupPen calls it on every touch, as the
                          mouse does in deck.js)
     this.index           the page shown (read only): page ink is kept by page
   What the deck uses of the pen (keep these names and what they do):
     setupPen()           called once from the deck's constructor
     this.pen             true while the pen is out: a click does not turn the page, keys 1 2 3 pick a colour, 4 does nothing
     this.board           true while the whiteboard is open: algorithm keys stay off, Esc closes the board first
     this.ball            the ball holder (#pen-ball); the deck adds and removes the class show with the control bar
     clearInk()           the deck calls it on every page turn (the page shows its own ink; the board and its ink stay),
                          and for C and Esc (the page's ink is wiped, Ctrl+Z brings it back)
     clearBoard()         key C while the board is open (else clearInk)
     togglePen(on)        key D, and Esc when the board is shut
     toggleBoard(on)      key W, and Esc
     pickColor(i)         keys 1 2 3 while the pen is out: the slot in hand (0 and 1 pens, red and blue at first; 2 the
                          highlighter, yellow at first); each slot's colour is picked on the tools
     placeBall()          the deck calls it when the stage is resized
   The keys themselves are read in deck.js (key()), except Ctrl+Z and Ctrl+Shift+Z (deck.js reads no keys held with Ctrl),
   E (the eraser, a key deck.js does not use) and Shift held while drawing (a straight line), which setupPen reads; their
   help lines are pen-help.html. localStorage: deck-pen-ball, deck-board, deck-board-ink, deck-pen-colors. */
class PenAndBoard {
  /* --- pen and whiteboard: the teacher circles code, marks a line or works something out on a board. Ink on the page is
     put away when the page turns and comes back with the page (for this visit); C or putting the pen away wipes it. The
     whiteboard floats over a dimmed page and stays while pages turn; what is on it stays when it closes, and on this
     computer, until C wipes it. Every stroke and wipe can be undone. Where the board and the ball sit is kept too. --- */
  setupPen() {
    this.pen = false;
    this.board = false;
    this.color = 0;  // the slot in hand: 0 and 1 are pens, 2 the highlighter (keys 1 2 3)
    this.erasing = false;
    // Widths are in stage pixels. Pen ink swells a little where the hand slows and thins where it hurries (or follows the
    // pressure of a drawing pen); the highlighter is a chisel tip of one width. Strokes keep the index of their colour, so
    // 0 1 2 keep meaning red pen, blue pen, yellow highlighter. Every pen colour reads on paper, on a dark code box and on
    // the clay and olive pages (the paper halo does the rest); the highlighters are the three that stay light under text.
    this.colors = [
      {name: '红', stroke: '#d03a2e', width: 7}, {name: '蓝', stroke: '#1f4fbf', width: 7},
      {name: '黄', stroke: '#ffe100', width: 30, hl: true}, {name: '黑', stroke: '#1f1e1d', width: 7},
      {name: '绿', stroke: '#2e7d3c', width: 7}, {name: '绿', stroke: '#86e05c', width: 30, hl: true},
      {name: '粉', stroke: '#ff8fd0', width: 30, hl: true}];
    this.choices = [[0, 1, 3, 4], [0, 1, 3, 4], [2, 5, 6]];  // the colours each slot can take
    this.slots = [0, 1, 2];  // each slot's colour now; kept on this computer
    try {
      const saved = JSON.parse(localStorage.getItem('deck-pen-colors') || 'null');
      if (Array.isArray(saved) && saved.length === 3 && saved.every((c, i) => this.choices[i].includes(c))) this.slots = saved;
    } catch {}
    const canvas = name => `<canvas class="${name}" width="1920" height="1080"></canvas>`;
    const icon = d => `<svg viewBox="0 0 26 26" aria-hidden="true"><path d="${d}"/></svg>`;
    const layer = document.createElement('div');
    layer.className = 'ink-layer';
    layer.setAttribute('aria-hidden', 'true');
    layer.innerHTML = canvas('halo') + canvas('hl') + canvas('hl glow') + canvas('ink') + canvas('draft');
    const shade = document.createElement('div');
    shade.className = 'board-shade';
    const board = document.createElement('div');
    board.className = 'board';
    board.setAttribute('role', 'dialog');
    board.setAttribute('aria-label', '白板');
    const day = new Date();
    board.innerHTML = `<div class="board-bar"><b>白板</b><i class="board-date">${day.getMonth() + 1} 月 ${day.getDate()} 日</i><small>拖这条移动 · 拖折角改大小</small>`
      + '<button type="button" class="board-act" data-act="undo" title="撤销上一笔（Ctrl+Z）" aria-label="撤销">' + icon('M9.5 6.8L4.6 11.4l4.9 4.5M5 11.4c4.6-.3 9.4-.5 12.2 1.4 2.9 2 2.8 5.7.4 7.6') + '</button>'
      + '<button type="button" class="board-act" data-act="redo" title="重做（Ctrl+Shift+Z）" aria-label="重做">' + icon('M16.5 6.8l4.9 4.6-4.9 4.5M21 11.4c-4.6-.3-9.4-.5-12.2 1.4-2.9 2-2.8 5.7-.4 7.6') + '</button>'
      + '<button type="button" class="board-act" data-act="wipe" title="擦掉白板（C），擦错了按 Ctrl+Z 找回" aria-label="擦掉白板">' + icon('M14.6 5.2l6.3 6.3-8.6 8.6H7.9l-3-3a1.6 1.6 0 010-2.3zM10 9.8l6.3 6.3M12.3 20.1h8.4') + '</button>'
      + '<button type="button" class="board-x" title="关掉白板（W 或 Esc），写的留着，下次打开还在" aria-label="关掉白板">'
      + icon('M5.5 5.2C10 9.6 15.6 15.8 20.8 20.6M20.4 5.6C15.4 10.4 10.2 15.6 5.4 20.8') + '</button></div>'
      + '<div class="board-paper">' + canvas('hl') + canvas('ink') + canvas('draft') + '</div><div class="board-size" title="拖这里改大小"></div>';
    this.stage.append(layer, shade, board);
    this.layer = layer;
    this.shade = shade;
    this.boardEl = board;
    this.paper = board.querySelector('.board-paper');
    // What is written is kept as strokes, so it can be undone and drawn again: page ink by page for this visit (a page
    // turned away from is clean, and its ink is back when it comes back), the board's on this computer for this lesson.
    this.inks = new Map();
    this.inkPage = -1;
    this.boardInk = {strokes: this.loadBoardInk(), undo: [], redo: []};
    this.layerSheet = this.sheet(layer, () => this.pageInk());
    this.paperSheet = this.sheet(this.paper, () => this.boardInk);
    // The dimmed page takes every click: no answers, no selecting, no IDE, no page turn.
    shade.addEventListener('pointerdown', e => e.preventDefault());
    shade.addEventListener('click', e => e.stopPropagation());
    board.addEventListener('click', e => e.stopPropagation());
    board.querySelector('.board-x').onclick = () => this.toggleBoard(false);
    const acts = {undo: () => this.undoInk(true), redo: () => this.undoInk(false), wipe: () => this.clearBoard()};
    board.querySelectorAll('.board-act').forEach(b => { b.onclick = acts[b.dataset.act]; });
    this.ball = document.getElementById('pen-ball');
    // Keep focus off the ball, so space and a clicker still turn the page instead of pressing it again.
    this.ball.querySelectorAll('button').forEach(b => b.addEventListener('mousedown', e => e.preventDefault()));
    board.querySelectorAll('button').forEach(b => b.addEventListener('mousedown', e => e.preventDefault()));
    // A slot already in hand, clicked again, opens its colours beside the tools; a colour picked closes them.
    this.palette = document.getElementById('pen-colors');
    this.ball.querySelectorAll('.swatch').forEach(b => {
      b.onclick = () => {
        const i = Number(b.dataset.color);
        if (this.pen && !this.erasing && this.color === i) this.showColors(this.palette.dataset.slot === String(i) ? -1 : i);
        else { this.showColors(-1); this.pickColor(i); }
      };
    });
    document.addEventListener('pointerdown', e => { if (!e.target.closest?.('.pen-tools')) this.showColors(-1); });
    document.getElementById('pen-eraser').onclick = () => this.toggleEraser();
    document.getElementById('whiteboard').onclick = () => this.toggleBoard();
    document.getElementById('pen-off').onclick = () => this.togglePen(false);
    document.getElementById('pen-undo').onclick = () => this.undoInk(true);
    document.getElementById('pen-redo').onclick = () => this.undoInk(false);
    document.addEventListener('touchstart', () => this.reveal(), {passive: true});
    // Ctrl+Z (⌘Z on a Mac) undoes a stroke or a wipe, Ctrl+Shift+Z or Ctrl+Y does it again. deck.js reads no keys held
    // with Ctrl or ⌘, so these are the pen's own; a yellow box or a dialog keeps its own undo.
    document.addEventListener('keydown', e => {
      const k = e.key.toLowerCase();
      // E picks up or puts down the eraser while the pen is out (deck.js reads no E).
      if (k === 'e' && this.pen && !(e.ctrlKey || e.metaKey || e.altKey) && !e.defaultPrevented && document.getElementById('blank')?.hidden !== false
        && !e.target.closest?.('input,textarea,select,[contenteditable],.slot') && !document.querySelector('dialog[open]')) { this.toggleEraser(); return; }
      if (!(e.ctrlKey || e.metaKey) || e.altKey || !(k === 'z' || (k === 'y' && e.ctrlKey))) return;
      if (e.target.closest?.('input,textarea,select,[contenteditable],.slot') || document.querySelector('dialog[open]')) return;
      if (this.undoInk(!(e.shiftKey || k === 'y'))) e.preventDefault();
    });
    addEventListener('pagehide', () => this.storeBoardInk());
    this.draws(this.layerSheet, () => this.pen && !this.board);
    this.draws(this.paperSheet, () => this.board);
    this.setupBoardMoves();
    this.setupBallDrag();
    this.markTools();
  }
  /* A surface to write on: its canvases, and where its strokes are kept (the page's, or the board's). */
  sheet(el, record) {
    return {el, record, all: [...el.querySelectorAll('canvas')], ink: el.querySelector('canvas.ink'), halo: el.querySelector('canvas.halo'),
      hl: [...el.querySelectorAll('canvas.hl')], draft: el.querySelector('canvas.draft')};
  }
  pageInk() {
    let r = this.inks.get(this.inkPage);
    if (!r) this.inks.set(this.inkPage, r = {strokes: [], undo: [], redo: []});
    return r;
  }
  /* The canvases a stroke goes on, ready to draw: pen ink with a paper halo under it on the page, the highlighter on both
     of its canvases. A canvas with nothing on it is not shown (class used), so an unmarked page composites no canvas. */
  ends(sheet, look) {
    const list = look.hl ? sheet.hl.map(c => [c, 0]) : sheet.halo ? [[sheet.halo, 6], [sheet.ink, 0]] : [[sheet.ink, 0]];
    return list.map(([c, grow]) => {
      const pen = c.getContext('2d'), color = grow ? '#faf9f5' : look.stroke;
      Object.assign(pen, {strokeStyle: color, fillStyle: color, lineCap: 'round', lineJoin: 'round'});
      c.classList.add('used');
      return {pen, grow};
    });
  }
  /* A stroke is kept as {c: colour, p: [x, y, width, ...], e: the width it ends with, or 0}. The first point is a dot; each
     next point bends a curve from the middle of the last step to the middle of this one, as it was drawn. Drawing it again
     puts the steps of one width in one path, so a page of strokes comes back in a few milliseconds. */
  paint(sheet, s) {
    const p = s.p;
    for (const {pen, grow} of this.ends(sheet, this.colors[s.c])) {
      pen.beginPath();
      pen.arc(p[0], p[1], (p[2] + grow) / 2, 0, 2 * Math.PI);
      pen.fill();
      let lx = p[0], ly = p[1], mx = lx, my = ly, w = -1;
      for (let i = 3; i < p.length; i += 3) {
        const nx = (lx + p[i]) / 2, ny = (ly + p[i + 1]) / 2;
        if (p[i + 2] !== w) {
          if (w >= 0) { pen.lineWidth = w + grow; pen.stroke(); }
          w = p[i + 2];
          pen.beginPath();
          pen.moveTo(mx, my);
        }
        pen.quadraticCurveTo(lx, ly, nx, ny);
        [lx, ly, mx, my] = [p[i], p[i + 1], nx, ny];
      }
      if (w >= 0) { pen.lineWidth = w + grow; pen.stroke(); }
      if (s.e) {
        pen.beginPath();
        pen.moveTo(mx, my);
        pen.quadraticCurveTo(lx, ly, lx, ly);
        pen.lineWidth = s.e + grow;
        pen.stroke();
      }
    }
  }
  wipe(sheet) {
    for (const c of sheet.all) {
      if (!c.classList.contains('used')) continue;
      c.getContext('2d').clearRect(0, 0, c.width, c.height);
      c.classList.remove('used');
    }
  }
  redraw(sheet) {
    this.wipe(sheet);
    for (const s of sheet.record().strokes) this.paint(sheet, s);
  }
  draws(sheet, allowed) {
    // Pointer position in the canvas's own pixels: the surface is drawn at stage size, then scaled with the stage.
    // Each move draws at once, in the same event (no waiting for a frame): a curve from the middle of the last step to the
    // middle of this one, bent through the point between, so the line is smooth and never more than half a step behind.
    // Widths are kept in quarter pixels, so drawing the stroke again later gives the same line.
    const surface = sheet.el, quarter = w => Math.round(w * 4) / 4;
    let line = null;
    const segment = (to, width) => {
      for (const {pen, grow} of line.ends) {
        pen.lineWidth = width + grow;
        pen.beginPath();
        pen.moveTo(...line.mid);
        pen.quadraticCurveTo(...line.last, ...to);
        pen.stroke();
      }
    };
    const add = (point, time, force) => {
      const [x, y] = point, [lx, ly] = line.last, d = Math.hypot(x - lx, y - ly);
      if (d < 1.5) return;
      const look = line.look;
      if (!look.hl) {
        // Fast is thin, slow is full; a drawing pen's pressure wins when there is one.
        const speed = d / Math.max(4, time - line.time);
        const want = force ? look.width * (0.55 + force * 0.9) : look.width * Math.min(1.2, Math.max(0.68, 1.22 - speed * 0.28));
        line.width += (want - line.width) * 0.3;
      }
      const mid = [(lx + x) / 2, (ly + y) / 2], w = quarter(line.width);
      segment(mid, w);
      line.s.p.push(x, y, w);
      Object.assign(line, {mid, last: point, time});
    };
    const at = (ev, box, f) => [(ev.clientX - box.left) / f, (ev.clientY - box.top) / f];
    surface.addEventListener('pointerdown', e => {
      if (!allowed() || e.button > 0) return;
      e.preventDefault();
      const box = surface.getBoundingClientRect(), f = box.width / surface.offsetWidth, p = at(e, box, f), record = sheet.record();
      try { surface.setPointerCapture(e.pointerId); } catch {}  // keep drawing when the pointer leaves the surface
      if (this.erasing) {
        line = {erase: true, id: e.pointerId, box, f, last: p, record, before: record.strokes};
        this.rub(sheet, record, p, p);
        return;
      }
      const c = this.slots[this.color], look = this.colors[c], width = look.hl ? look.width : look.width * 0.8;
      // With Shift held the stroke is a straight line, shown as a draft until the button is let go.
      if (e.shiftKey) {
        line = {straight: true, id: e.pointerId, box, f, look, c, from: p, to: p, width: quarter(look.hl ? width : look.width), record};
        sheet.draft.classList.add('used');
        this.draftLine(sheet, line);
        return;
      }
      const ends = this.ends(sheet, look).sort((a, b) => b.grow - a.grow);
      line = {look, ends, id: e.pointerId, box, f, last: p, mid: p, time: e.timeStamp, width, record, s: {c, p: [...p, width], e: 0}};
      for (const {pen, grow} of ends) {
        pen.beginPath();
        pen.arc(...p, (width + grow) / 2, 0, 2 * Math.PI);
        pen.fill();
      }
    });
    surface.addEventListener('pointermove', e => {
      if (!line || e.pointerId !== line.id) return;
      // A fast hand sends several points per frame; take them all, so a quick circle stays round.
      const all = e.getCoalescedEvents?.() || [];
      if (line.straight) { line.to = this.snap(line.from, at(e, line.box, line.f)); this.draftLine(sheet, line); return; }
      for (const ev of all.length ? all : [e]) {
        const p = at(ev, line.box, line.f);
        if (line.erase) { this.rub(sheet, line.record, line.last, p); line.last = p; }
        else add(p, ev.timeStamp, ev.pointerType === 'pen' ? ev.pressure : 0);
      }
    });
    const stop = e => {
      if (!line || e.pointerId !== line.id) return;
      const r = line.record;
      if (line.erase) {
        // One drag of the eraser is one step to undo.
        if (r.strokes !== line.before) { r.undo.push({from: line.before, to: r.strokes}); r.redo = []; }
      } else if (line.straight) {
        this.draftLine(sheet, null);
        const {from, to, width} = line;
        if (Math.hypot(to[0] - from[0], to[1] - from[1]) >= 3) {
          const s = {c: line.c, p: [...from, width, ...to, width], e: width};
          this.paint(sheet, s);
          r.strokes.push(s);
          r.undo.push({add: s});
          r.redo = [];
        }
      }
      if (line.erase || line.straight) {
        line = null;
        if (sheet === this.paperSheet) this.saveBoardInk();
        this.markUndo();
        return;
      }
      add(at(e, line.box, line.f), e.timeStamp, 0);
      // Finish at the last point, tapering a little, as a pen lifts.
      if (line.mid !== line.last) {
        line.s.e = quarter(line.look.hl ? line.width : line.width * 0.85);
        segment(line.last, line.s.e);
      }
      r.strokes.push(line.s);
      r.undo.push({add: line.s});
      r.redo = [];
      line = null;
      if (sheet === this.paperSheet) this.saveBoardInk();
      this.markUndo();
    };
    surface.addEventListener('pointerup', stop);
    surface.addEventListener('pointercancel', stop);
  }
  /* Undo (back) or redo the last stroke or wipe: on the board while it is open, else on the page. True if there was one. */
  undoInk(back = true) {
    const sheet = this.board ? this.paperSheet : this.layerSheet, r = sheet.record();
    const step = (back ? r.undo : r.redo).pop();
    if (!step) return false;
    (back ? r.redo : r.undo).push(step);
    if (step.add && back) { r.strokes.pop(); this.redraw(sheet); }
    else if (step.add) { r.strokes.push(step.add); this.paint(sheet, step.add); }
    else { r.strokes = back ? step.from : step.to; this.redraw(sheet); }
    if (sheet === this.paperSheet) this.saveBoardInk();
    this.markUndo();
    return true;
  }
  /* Wipe what a sheet shows, as one step that can be undone. */
  wipeInk(sheet) {
    const r = sheet.record();
    if (r.strokes.length) {
      r.undo.push({from: r.strokes, to: []});
      r.strokes = [];
      r.redo = [];
    }
    this.wipe(sheet);
    this.markUndo();
  }
  /* The eraser takes away every stroke it touches (within 16 stage pixels of its path), and the sheet is drawn again. */
  rub(sheet, r, a, b) {
    const near = (p, q, z) => {  // distance from point p to the segment q-z
      const dx = z[0] - q[0], dy = z[1] - q[1], l = dx * dx + dy * dy;
      const t = l ? Math.max(0, Math.min(1, ((p[0] - q[0]) * dx + (p[1] - q[1]) * dy) / l)) : 0;
      return Math.hypot(p[0] - q[0] - t * dx, p[1] - q[1] - t * dy);
    };
    const touched = s => {
      const reach = 16 + this.colors[s.c].width / 2, p = s.p;
      if (!s.box) {
        s.box = [p[0], p[1], p[0], p[1]];
        for (let i = 3; i < p.length; i += 3) s.box = [Math.min(s.box[0], p[i]), Math.min(s.box[1], p[i + 1]), Math.max(s.box[2], p[i]), Math.max(s.box[3], p[i + 1])];
      }
      if (Math.max(a[0], b[0]) < s.box[0] - reach || Math.min(a[0], b[0]) > s.box[2] + reach
        || Math.max(a[1], b[1]) < s.box[1] - reach || Math.min(a[1], b[1]) > s.box[3] + reach) return false;
      for (let i = 0; i < p.length; i += 3) {
        const q = [p[i], p[i + 1]], z = i + 3 < p.length ? [p[i + 3], p[i + 4]] : q;
        if (near(q, a, b) < reach || near(a, q, z) < reach || near(b, q, z) < reach) return true;
      }
      return false;
    };
    const keep = r.strokes.filter(s => !touched(s));
    if (keep.length === r.strokes.length) return;
    r.strokes = keep;
    this.redraw(sheet);
  }
  /* A straight line keeps to level, upright or a diagonal when it is within 5 degrees of one. */
  snap(from, to) {
    const dx = to[0] - from[0], dy = to[1] - from[1], len = Math.hypot(dx, dy), angle = Math.atan2(dy, dx), step = Math.PI / 4;
    const near = Math.round(angle / step) * step;
    return Math.abs(angle - near) < Math.PI / 36 ? [from[0] + len * Math.cos(near), from[1] + len * Math.sin(near)] : to;
  }
  /* The draft canvas shows the straight line while it is being pulled: only the box it was in is cleared each move. */
  draftLine(sheet, line) {
    const pen = sheet.draft.getContext('2d');
    if (sheet.drafted) pen.clearRect(...sheet.drafted);
    sheet.drafted = null;
    if (!line) { sheet.draft.classList.remove('used'); return; }
    const {from, to, look, width} = line, m = width / 2 + 4;
    Object.assign(pen, {strokeStyle: look.stroke, lineWidth: width, lineCap: 'round', globalAlpha: look.hl ? 0.55 : 1});
    pen.beginPath();
    pen.moveTo(...from);
    pen.lineTo(...to);
    pen.stroke();
    sheet.drafted = [Math.min(from[0], to[0]) - m, Math.min(from[1], to[1]) - m, Math.abs(to[0] - from[0]) + 2 * m, Math.abs(to[1] - from[1]) + 2 * m];
  }
  toggleEraser(on = !this.erasing) {
    this.erasing = on;
    if (on && !this.pen) this.togglePen(true);
    this.showColors(-1);
    this.markTools();
  }
  /* The colours of one slot, in a row beside the tools (on the stage's side of them); -1 closes the row. */
  showColors(slot) {
    const row = this.palette;
    if (!row) return;
    if (slot < 0) { row.hidden = true; delete row.dataset.slot; return; }
    const swatch = this.ball.querySelector(`.swatch[data-color="${slot}"]`);
    row.innerHTML = '';
    for (const c of this.choices[slot]) {
      const look = this.colors[c], b = document.createElement('button');
      b.type = 'button';
      b.className = 'pen-color' + (look.hl ? ' hl' : '') + (this.slots[slot] === c ? ' on' : '');
      b.style.setProperty('--c', look.stroke);
      b.title = b.ariaLabel = (look.hl ? '荧光笔' : '笔') + '：' + look.name;
      b.addEventListener('mousedown', e => e.preventDefault());
      b.onclick = () => {
        this.slots[slot] = c;
        try { localStorage.setItem('deck-pen-colors', JSON.stringify(this.slots)); } catch {}
        this.showColors(-1);
        this.markTools();
      };
      row.append(b);
    }
    row.dataset.slot = slot;
    row.classList.toggle('to-right', this.ballAt?.side === 'left');
    row.hidden = false;
    row.style.top = swatch.offsetTop + swatch.offsetHeight / 2 - row.offsetHeight / 2 + 'px';
  }
  /* The pointer while the pen is out: a dot of the ink in hand, ringed so it shows on light and dark pages; a chisel tip for
     the highlighter; a ring for the eraser. */
  cursor() {
    const svg = body => `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='32' height='32'>${body}</svg>`)}") 16 16,crosshair`;
    if (this.erasing) return svg(`<circle cx='16' cy='16' r='13' fill='#faf9f5' fill-opacity='.35' stroke='#1f1e1d' stroke-opacity='.7' stroke-width='1.5'/><circle cx='16' cy='16' r='13' fill='none' stroke='#faf9f5' stroke-dasharray='3 3'/>`);
    const look = this.colors[this.slots[this.color]], c = look.stroke;
    return svg(look.hl
      ? `<rect x='9' y='5' width='14' height='22' rx='3' fill='${c}' fill-opacity='.8' stroke='#1f1e1d' stroke-opacity='.55' transform='rotate(35 16 16)'/><circle cx='16' cy='16' r='1.6' fill='#1f1e1d'/>`
      : `<circle cx='16' cy='16' r='9' fill='none' stroke='#1f1e1d' stroke-opacity='.45'/><circle cx='16' cy='16' r='5.5' fill='${c}' stroke='#faf9f5' stroke-width='2.5'/>`);
  }
  markUndo() {
    const page = this.board ? this.boardInk : this.pageInk(), board = this.boardInk;
    document.getElementById('pen-undo').disabled = !page.undo.length;
    document.getElementById('pen-redo').disabled = !page.redo.length;
    this.boardEl.querySelector('[data-act="undo"]').disabled = !board.undo.length;
    this.boardEl.querySelector('[data-act="redo"]').disabled = !board.redo.length;
    this.boardEl.querySelector('[data-act="wipe"]').disabled = !board.strokes.length;
  }
  /* The board's strokes are kept in localStorage under deck-board-ink, one entry per lesson page, newest kept when the
     whole goes over about a megabyte. Saving waits for a pause in the writing; anything wrong with it is skipped. */
  loadBoardInk() {
    try {
      const kept = JSON.parse(localStorage.getItem('deck-board-ink') || '{}')[location.pathname];
      return (kept?.s || []).filter(a => Array.isArray(a) && a.length >= 5 && (a.length - 2) % 3 === 0 && a.every(Number.isFinite) && this.colors[a[0]])
        .map(a => ({c: a[0], e: a[1], p: a.slice(2)}));
    } catch { return []; }
  }
  saveBoardInk() {
    clearTimeout(this.boardSaving);
    this.boardSaving = setTimeout(() => this.storeBoardInk(), 800);
  }
  storeBoardInk() {
    if (!this.boardSaving) return;
    clearTimeout(this.boardSaving);
    this.boardSaving = null;
    try {
      let all = {};
      try { all = JSON.parse(localStorage.getItem('deck-board-ink') || '{}') || {}; } catch {}
      const round = v => Math.round(v * 10) / 10, strokes = this.boardInk.strokes.map(s => [s.c, s.e, ...s.p.map(round)]);
      if (strokes.length) all[location.pathname] = {t: Date.now(), s: strokes};
      else delete all[location.pathname];
      let text = JSON.stringify(all);
      const others = Object.keys(all).filter(k => k !== location.pathname).sort((a, b) => all[a].t - all[b].t);
      while (text.length > 1e6 && others.length) { delete all[others.shift()]; text = JSON.stringify(all); }
      while (text.length > 1e6 && all[location.pathname]?.s.length > 1) { all[location.pathname].s.splice(0, Math.ceil(all[location.pathname].s.length / 10)); text = JSON.stringify(all); }
      localStorage.setItem('deck-board-ink', text);
    } catch {}
  }
  /* The board moves by its top bar and grows from its corner, in stage pixels, never past the stage. */
  setupBoardMoves() {
    const W = 1920, H = 1080, MIN = [600, 400];
    const fit = b => {
      const w = Math.min(W, Math.max(MIN[0], b.w)), h = Math.min(H, Math.max(MIN[1], b.h));
      return {w, h, x: Math.min(W - w, Math.max(0, b.x)), y: Math.min(H - h, Math.max(0, b.y))};
    };
    let box = {w: 1152, h: 648, x: 384, y: 216};
    try {
      const saved = JSON.parse(localStorage.getItem('deck-board') || 'null');
      if (saved && ['x', 'y', 'w', 'h'].every(k => Number.isFinite(saved[k]))) box = fit(saved);
    } catch {}
    const place = () => Object.assign(this.boardEl.style, {left: box.x + 'px', top: box.y + 'px', width: box.w + 'px', height: box.h + 'px'});
    place();
    const drag = (handle, change) => {
      handle.addEventListener('pointerdown', e => {
        if (e.button > 0 || e.target.closest('button')) return;
        e.preventDefault();
        const f = this.stage.getBoundingClientRect().width / W, from = {...box, px: e.clientX, py: e.clientY};
        try { handle.setPointerCapture(e.pointerId); } catch {}
        const moved = ev => { box = fit(change(from, (ev.clientX - from.px) / f, (ev.clientY - from.py) / f)); place(); };
        const done = () => {
          handle.removeEventListener('pointermove', moved);
          try { localStorage.setItem('deck-board', JSON.stringify(box)); } catch {}
        };
        handle.addEventListener('pointermove', moved);
        handle.addEventListener('pointerup', done, {once: true});
        handle.addEventListener('pointercancel', done, {once: true});
      });
    };
    drag(this.boardEl.querySelector('.board-bar'), (b, dx, dy) => ({...b, x: b.x + dx, y: b.y + dy}));
    // Growing never pushes the board off the stage: the far edge stops at the stage's edge.
    drag(this.boardEl.querySelector('.board-size'), (b, dx, dy) => ({...b, w: Math.min(W - b.x, b.w + dx), h: Math.min(H - b.y, b.h + dy)}));
  }
  /* The ball can be dragged anywhere; let go and it sits against the nearer side of the stage, at the height it was let go.
     Moving less than 6px from press to release is a tap that opens or closes the tools. */
  setupBallDrag() {
    const ball = document.getElementById('pen');
    this.ballAt = {side: 'right', y: 0.5};
    try {
      const saved = JSON.parse(localStorage.getItem('deck-pen-ball') || 'null');
      if (saved && ['left', 'right'].includes(saved.side) && Number.isFinite(saved.y)) this.ballAt = {side: saved.side, y: Math.min(1, Math.max(0, saved.y))};
    } catch {}
    let press = null;
    ball.addEventListener('pointerdown', e => {
      if (e.button > 0) return;
      press = {x: e.clientX, y: e.clientY, id: e.pointerId, moved: false};
      try { ball.setPointerCapture(e.pointerId); } catch {}
    });
    ball.addEventListener('pointermove', e => {
      if (!press || e.pointerId !== press.id) return;
      if (!press.moved && Math.hypot(e.clientX - press.x, e.clientY - press.y) < 6) return;
      press.moved = true;
      this.ball.classList.add('dragging');
      // The holder's top is the ball's centre (the tools open above it), so the ball sits under the pointer.
      Object.assign(this.ball.style, {left: e.clientX - this.ball.offsetWidth / 2 + 'px', right: 'auto', top: e.clientY + 'px'});
    });
    const release = e => {
      if (!press || e.pointerId !== press.id) return;
      const {moved} = press;
      press = null;
      this.ball.classList.remove('dragging');
      if (!moved) { if (e.type === 'pointerup') this.openTools(!this.ball.classList.contains('open')); return; }
      const s = this.stage.getBoundingClientRect();
      this.ballAt = {side: e.clientX < s.left + s.width / 2 ? 'left' : 'right', y: Math.min(1, Math.max(0, (e.clientY - s.top) / s.height))};
      try { localStorage.setItem('deck-pen-ball', JSON.stringify(this.ballAt)); } catch {}
      this.placeBall();
    };
    ball.addEventListener('pointerup', release);
    ball.addEventListener('pointercancel', release);
    // A keyboard press (Enter or space on a focused ball) still opens it; pointer taps are handled on release.
    ball.addEventListener('click', e => { if (e.detail === 0) this.openTools(!this.ball.classList.contains('open')); });
  }
  placeBall() {
    if (!this.ball || !this.ballAt || this.ball.classList.contains('dragging')) return;
    // The holder's top is the ball's centre; the tools above it and the ball itself stay on the stage.
    const s = this.stage.getBoundingClientRect(), r = 32;
    const y = Math.max(s.top + this.ball.offsetHeight - r, Math.min(s.bottom - r, s.top + this.ballAt.y * s.height));
    const side = this.ballAt.side === 'left' ? {left: s.left + 14 + 'px', right: 'auto'} : {left: 'auto', right: innerWidth - s.right + 14 + 'px'};
    Object.assign(this.ball.style, side, {top: y + 'px'});
  }
  markTools() {
    this.markUndo();
    // The ball, the slots and the pointer show the ink in hand.
    const look = this.colors[this.slots[this.color]];
    this.ball.dataset.color = this.layer.dataset.color = this.paper.dataset.color = this.color;
    this.ball.style.setProperty('--now', this.erasing ? '#8c8579' : look.stroke);
    this.ball.classList.toggle('light', !this.erasing && Boolean(look.hl));
    this.ball.classList.toggle('erasing', this.erasing);
    this.ball.querySelectorAll('.swatch').forEach(b => {
      b.style.setProperty('--c', this.colors[this.slots[Number(b.dataset.color)]].stroke);
      b.classList.toggle('on', !this.erasing && Number(b.dataset.color) === this.color);
    });
    document.getElementById('pen-eraser').classList.toggle('on', this.erasing);
    this.layer.style.cursor = this.paper.style.cursor = this.pen ? this.cursor() : '';
    if (!this.pen) this.showColors(-1);
    document.getElementById('whiteboard').classList.toggle('on', this.board);
    document.getElementById('pen').setAttribute('aria-expanded', String(this.ball.classList.contains('open') || this.pen));
    this.placeBall();
  }
  openTools(open) {
    this.ball.classList.toggle('open', open);
    this.markTools();
  }
  pickColor(i) {
    this.color = i;
    this.erasing = false;
    if (!this.pen) this.togglePen(true);
    this.markTools();
  }
  togglePen(on = !this.pen, wipe = true) {
    this.pen = on;
    document.body.classList.toggle('pen', on);
    if (!on) {
      this.erasing = false;
      if (this.board) this.toggleBoard(false);
      if (wipe) this.clearInk();
      this.ball.classList.remove('open');
    }
    this.markTools();
  }
  toggleBoard(on = !this.board) {
    if (on === this.board) return;
    this.board = on;
    if (on) this.leaving?.remove();
    document.body.classList.toggle('board-open', on);
    if (on) {
      if (document.activeElement.matches('.slot')) document.activeElement.blur();
      getSelection().removeAllRanges();
      this.penBefore = this.pen;
      if (!this.pen) this.togglePen(true);
      this.redraw(this.paperSheet);  // what was on it last time
    } else {
      this.liftBoard();
      this.wipe(this.paperSheet);  // the strokes are kept for next time; C wipes them
      if (!this.penBefore) this.togglePen(false, false);  // the pen goes back; the page keeps its ink
    }
    this.markTools();
  }
  /* Closing shuts the board at once (its state, its ink); a copy with the ink on it lifts off the page and goes. */
  liftBoard() {
    this.leaving?.remove();
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const copy = this.boardEl.cloneNode(true), from = this.boardEl.querySelectorAll('canvas');
    copy.removeAttribute('role');
    copy.querySelectorAll('canvas').forEach((c, i) => c.getContext('2d').drawImage(from[i], 0, 0));
    const leave = document.createElement('div');
    leave.className = 'board-leave';
    leave.setAttribute('aria-hidden', 'true');
    leave.append(document.createElement('i'), copy);
    this.stage.append(leave);
    this.leaving = leave;
    copy.addEventListener('animationend', () => { leave.remove(); if (this.leaving === leave) this.leaving = null; }, {once: true});
    setTimeout(() => leave.remove(), 800);  // in case the animation never runs (a hidden tab)
  }
  /* The deck calls clearInk on every page turn, and for C and Esc: a new page shows its own ink (none, or what was left on
     it earlier in this visit); the same page is wiped, as one step that Ctrl+Z brings back. */
  clearInk() {
    if (!this.layerSheet) return;
    const page = this.index ?? 0;
    if (page === this.inkPage) { this.wipeInk(this.layerSheet); return; }
    this.inkPage = page;
    this.redraw(this.layerSheet);
    this.markUndo();
  }
  clearBoard() {
    if (!this.paperSheet) return;
    this.wipeInk(this.paperSheet);
    this.saveBoardInk();
  }
}
