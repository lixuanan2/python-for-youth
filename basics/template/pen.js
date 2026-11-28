/* === PEN AND WHITEBOARD (template/pen.js, with pen.css, pen.html and pen-help.html) ===
   The build puts this file before deck.js in the page's one <script>. deck.js copies every method of PenAndBoard onto the
   deck (SlidePresentation) before it starts, so inside these methods `this` is the deck. See PEN.md before changing them.

   What the pen uses of the deck:
     this.stage           the 1920 x 1080 stage (#deckStage); the ink layer, the shade and the board are added to it
     this.reveal()        shows the control bar and the ball for a while (setupPen calls it on every touch, as the
                          mouse does in deck.js)
   What the deck uses of the pen (keep these names and what they do):
     setupPen()           called once from the deck's constructor
     this.pen             true while the pen is out: a click does not turn the page, keys 1 2 3 pick a colour, 4 does nothing
     this.board           true while the whiteboard is open: algorithm keys stay off, Esc closes the board first
     this.ball            the ball holder (#pen-ball); the deck adds and removes the class show with the control bar
     clearInk()           the deck calls it on every page turn (the board and its ink stay)
     clearBoard()         key C while the board is open (else clearInk)
     togglePen(on)        key D, and Esc when the board is shut
     toggleBoard(on)      key W, and Esc
     pickColor(i)         keys 1 2 3 while the pen is out (0 red, 1 blue, 2 highlighter)
     placeBall()          the deck calls it when the stage is resized
   The keys themselves are read in deck.js (key()); their help lines are pen-help.html. */
class PenAndBoard {
  /* --- pen and whiteboard: the teacher circles code, marks a line or works something out on a board. Ink on the page goes
     when the page turns or the pen goes away. The whiteboard floats over a dimmed page and stays while pages turn; its
     ink goes when it closes. Where the board and the ball sit is kept on this computer. --- */
  setupPen() {
    this.pen = false;
    this.board = false;
    this.color = 0;
    this.colors = [{stroke: '#c6613f', width: 6}, {stroke: '#1f4fbf', width: 6}, {stroke: '#ffe100', width: 28, hl: true}];
    const canvases = '<canvas class="hl" width="1920" height="1080"></canvas><canvas class="ink" width="1920" height="1080"></canvas>';
    const layer = document.createElement('div');
    layer.className = 'ink-layer';
    layer.setAttribute('aria-hidden', 'true');
    layer.innerHTML = canvases;
    const shade = document.createElement('div');
    shade.className = 'board-shade';
    const board = document.createElement('div');
    board.className = 'board';
    board.setAttribute('role', 'dialog');
    board.setAttribute('aria-label', '白板');
    board.innerHTML = '<div class="board-bar"><span>白板</span><button type="button" class="board-x" title="关掉白板，写的清掉（W 或 Esc）" aria-label="关掉白板">×</button></div>'
      + '<div class="board-paper">' + canvases + '</div><div class="board-size" title="拖这里改大小"></div>';
    this.stage.append(layer, shade, board);
    this.layer = layer;
    this.boardEl = board;
    this.paper = board.querySelector('.board-paper');
    // The dimmed page takes every click: no answers, no selecting, no IDE, no page turn.
    shade.addEventListener('pointerdown', e => e.preventDefault());
    shade.addEventListener('click', e => e.stopPropagation());
    board.addEventListener('click', e => e.stopPropagation());
    board.querySelector('.board-x').onclick = () => this.toggleBoard(false);
    this.ball = document.getElementById('pen-ball');
    // Keep focus off the ball, so space and a clicker still turn the page instead of pressing it again.
    this.ball.querySelectorAll('button').forEach(b => b.addEventListener('mousedown', e => e.preventDefault()));
    board.querySelectorAll('button').forEach(b => b.addEventListener('mousedown', e => e.preventDefault()));
    this.ball.querySelectorAll('.swatch').forEach(b => { b.onclick = () => this.pickColor(Number(b.dataset.color)); });
    document.getElementById('whiteboard').onclick = () => this.toggleBoard();
    document.getElementById('pen-off').onclick = () => this.togglePen(false);
    document.addEventListener('touchstart', () => this.reveal(), {passive: true});
    this.draws(layer, () => this.pen && !this.board);
    this.draws(this.paper, () => this.board);
    this.setupBoardMoves();
    this.setupBallDrag();
    this.markTools();
  }
  draws(surface, allowed) {
    // Pointer position in the canvas's own pixels: the surface is drawn at stage size, then scaled with the stage.
    let line = null;
    surface.addEventListener('pointerdown', e => {
      if (!allowed() || e.button > 0) return;
      e.preventDefault();
      const look = this.colors[this.color], canvas = surface.querySelector(look.hl ? 'canvas.hl' : 'canvas.ink');
      const box = surface.getBoundingClientRect(), f = box.width / surface.offsetWidth;
      const at = ev => [(ev.clientX - box.left) / f, (ev.clientY - box.top) / f];
      const pen = canvas.getContext('2d');
      Object.assign(pen, {strokeStyle: look.stroke, fillStyle: look.stroke, lineWidth: look.width, lineCap: 'round', lineJoin: 'round'});
      try { surface.setPointerCapture(e.pointerId); } catch {}  // keep drawing when the pointer leaves the surface
      line = {pen, at, last: at(e), id: e.pointerId};
      pen.beginPath();
      pen.arc(...line.last, look.width / 2, 0, 2 * Math.PI);
      pen.fill();
    });
    surface.addEventListener('pointermove', e => {
      if (!line || e.pointerId !== line.id) return;
      const next = line.at(e);
      line.pen.beginPath();
      line.pen.moveTo(...line.last);
      line.pen.lineTo(...next);
      line.pen.stroke();
      line.last = next;
    });
    const stop = e => { if (line && e.pointerId === line.id) line = null; };
    surface.addEventListener('pointerup', stop);
    surface.addEventListener('pointercancel', stop);
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
    this.ball.querySelectorAll('.swatch').forEach(b => b.classList.toggle('on', Number(b.dataset.color) === this.color));
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
    if (!this.pen) this.togglePen(true);
    this.markTools();
  }
  togglePen(on = !this.pen) {
    this.pen = on;
    document.body.classList.toggle('pen', on);
    if (!on) {
      if (this.board) this.toggleBoard(false);
      this.clearInk();
      this.ball.classList.remove('open');
    }
    this.markTools();
  }
  toggleBoard(on = !this.board) {
    if (on === this.board) return;
    this.board = on;
    document.body.classList.toggle('board-open', on);
    if (on) {
      if (document.activeElement.matches('.slot')) document.activeElement.blur();
      getSelection().removeAllRanges();
      this.penBefore = this.pen;
      if (!this.pen) this.togglePen(true);
    } else {
      this.clearBoard();
      if (!this.penBefore) this.togglePen(false);
    }
    this.markTools();
  }
  clearInk() {
    this.layer?.querySelectorAll('canvas').forEach(c => c.getContext('2d').clearRect(0, 0, c.width, c.height));
  }
  clearBoard() {
    this.paper?.querySelectorAll('canvas').forEach(c => c.getContext('2d').clearRect(0, 0, c.width, c.height));
  }
}
