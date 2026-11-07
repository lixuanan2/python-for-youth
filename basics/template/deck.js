/* === IDE LINKS: the platform and its options come from site.json === */
const LANGUAGE = '{{language}}';
const IDE = {
  config: {{ide}},
  defaults() {
    return Object.fromEntries(this.config.settings.map(s => [s.param, s.options[0][0]]));
  },
  load() {
    try { return {...this.defaults(), ...JSON.parse(localStorage.getItem('ide-settings') || '{}')}; }
    catch { return this.defaults(); }
  },
  save(settings) {
    try { localStorage.setItem('ide-settings', JSON.stringify(settings)); } catch {}
  },
  url(code, settings) {
    const q = {...this.config.fixed, ...settings, [this.config.codeParam]: code};
    return this.config.base + '?' + Object.entries(q).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
  }
};

/* === SLIDE CONTROLLER: scale the stage, turn pages, play steps before turning === */
class SlidePresentation {
  constructor() {
    this.stage = document.getElementById('deckStage');
    this.slides = [...this.stage.querySelectorAll('.slide')];
    this.bar = document.getElementById('controls');
    this.counter = document.getElementById('counter');
    this.settings = document.getElementById('ide-settings');
    this.help = document.getElementById('help-panel');
    this.blank = document.getElementById('blank');
    this.index = 0;
    addEventListener('resize', () => this.scale());
    addEventListener('hashchange', () => this.fromHash());
    addEventListener('beforeprint', () => this.finishAll());
    addEventListener('afterprint', () => this.undoFinish());
    document.addEventListener('keydown', e => this.key(e));
    document.addEventListener('mousemove', () => this.reveal());
    document.addEventListener('fullscreenchange', () => {
      document.body.classList.toggle('full', Boolean(document.fullscreenElement));
      this.scale();
    });
    this.stage.addEventListener('click', e => {
      if (e.target.closest('a,button,.pick,pre,.tb,.live-out')) return;
      this.move(e.clientX < innerWidth / 3 ? -1 : 1);
    });
    let startX = null;
    this.stage.addEventListener('touchstart', e => { startX = e.touches[0].clientX; }, {passive: true});
    this.stage.addEventListener('touchend', e => {
      const dx = e.changedTouches[0].clientX - startX;
      if (Math.abs(dx) > 50) this.move(dx < 0 ? 1 : -1);
    });
    document.getElementById('prev').onclick = () => this.move(-1);
    document.getElementById('next').onclick = () => this.move(1);
    document.getElementById('full').onclick = () => this.fullscreen();
    document.getElementById('toggle-thumbs').onclick = () => {
      this.toggleThumbs();
      try { localStorage.setItem('deck-thumbs', document.body.classList.contains('thumbs-open') ? '1' : '0'); } catch {}
    };
    document.getElementById('help').onclick = () => this.help.showModal();
    document.getElementById('help-close').onclick = () => this.help.close();
    this.blank.onclick = () => { this.blank.hidden = true; };
    this.setupChanges();
    this.buildThumbs();
    this.buildTimeline();
    this.buildChapters();
    this.setupJump();
    this.setupIde();
    this.setupQuizzes();
    this.setupBugHunt();
    this.setupGates();
    this.setupLive();
    this.toggleThumbs(this.thumbsPreference());
    this.fromHash();
  }

  /* --- left rail: live miniatures of the final state of every page --- */
  buildThumbs() {
    const rail = document.getElementById('thumbs');
    this.thumbs = this.slides.map((slide, i) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'thumb';
      button.setAttribute('aria-label', `第 ${i + 1} 页：${slide.getAttribute('aria-label')}`);
      const view = document.createElement('span');
      view.className = 'view';
      const copy = slide.cloneNode(true);
      copy.removeAttribute('id');
      copy.classList.remove('active');
      copy.classList.add('visible');
      if (copy.dataset.steps) copy.dataset.at = 1;
      copy.querySelectorAll('pre.change').forEach(pre => this.setChange(pre, 1, false));
      copy.inert = true;
      view.append(copy);
      const number = document.createElement('b');
      number.textContent = i + 1;
      button.append(number, view);
      button.onclick = () => this.show(i);
      rail.append(button);
      return button;
    });
  }
  thumbsPreference() {
    if (innerWidth < 900) return false;
    try {
      const saved = localStorage.getItem('deck-thumbs');
      if (saved) return saved === '1';
    } catch {}
    return true;
  }
  toggleThumbs(open = !document.body.classList.contains('thumbs-open')) {
    document.body.classList.toggle('thumbs-open', open);
    this.scale();
    this.thumbs[this.index].scrollIntoView({block: 'nearest'});
  }

  /* --- timeline: one coloured segment per page, a range input on top for dragging --- */
  roleOf(slide) {
    if (slide.querySelector('.band')) return 'turn';
    for (const name of ['clay', 'olive']) if (slide.classList.contains(name)) return name;
    return slide.classList.contains('dark') || slide.querySelector('.night') ? 'dark' : 'paper';
  }
  buildTimeline() {
    const segments = document.getElementById('segs');
    this.segments = this.slides.map(slide => {
      const seg = document.createElement('span');
      seg.className = 'seg ' + this.roleOf(slide);
      segments.append(seg);
      return seg;
    });
    const slider = this.slider = document.getElementById('slider');
    const bubble = document.getElementById('bubble');
    slider.max = this.slides.length;
    slider.oninput = () => this.show(Number(slider.value) - 1);
    slider.onchange = () => slider.blur();
    slider.onmousemove = e => {
      const box = slider.getBoundingClientRect();
      const i = Math.max(0, Math.min(this.slides.length - 1, Math.floor((e.clientX - box.left) / box.width * this.slides.length)));
      bubble.textContent = `${i + 1}  ${this.slides[i].getAttribute('aria-label')}`;
      bubble.style.left = Math.max(70, Math.min(box.width - 70, e.clientX - box.left)) + 'px';
      bubble.hidden = false;
    };
    slider.onmouseleave = () => { bubble.hidden = true; };
  }

  /* --- chapters: quick jumps taken from data-chapter on slides --- */
  buildChapters() {
    const holder = document.getElementById('chips');
    this.chapters = this.slides.flatMap((slide, i) => {
      if (!slide.dataset.chapter) return [];
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = slide.dataset.chapter;
      button.onclick = () => this.show(i);
      holder.append(button);
      return [{start: i, button}];
    });
  }
  setupJump() {
    const jump = this.jump = document.getElementById('jump');
    jump.max = this.slides.length;
    jump.onkeydown = e => {
      e.stopPropagation();
      if (e.key === 'Enter') { this.show(Number(jump.value) - 1); jump.blur(); }
      if (e.key === 'Escape') jump.blur();
    };
  }

  /* --- IDE: every button carries its own page's code --- */
  codeOf(slide) {
    if (slide.dataset.ide) return slide.dataset.ide;
    const full = slide.querySelector('pre.code[data-full]');
    if (full) return full.dataset.full;
    return [...slide.querySelectorAll('pre.code .ln:not(.cut)')].map(l => this.lineText(l)).join('\n');
  }
  lineText(line) {
    const slots = [...line.querySelectorAll('.slot')];
    const copy = line.cloneNode(true);
    copy.querySelectorAll('.then').forEach(old => old.remove());
    copy.querySelectorAll('.slot').forEach((slot, i) => slot.replaceWith(this.slotCode(slots[i])));
    return copy.textContent;
  }
  /* The IDE gets exactly what the student typed, even a value the page itself cannot work out, such as -3 or 2.5.
     Text sits inside quotes, so only what would end or change the string there is escaped: a backslash and the
     quote itself in both languages, {} in a Python f-string, and ?? in C++. C++11 turns ??! and the like into
     other characters before it reads escapes, so the second ? is escaped: ?? becomes ?\? and why??! stays why??!. */
  slotCode(slot) {
    if (slot.dataset.kind !== 'text') return slot.value;
    const before = slot.previousSibling?.textContent ?? '';
    const quote = /['"]$/.exec(before)?.[0] ?? '"';
    let text = slot.value.replace(/\\/g, '\\\\').replaceAll(quote, '\\' + quote);
    if (LANGUAGE === 'python' && /(?:^|\W)[a-z]*f[a-z]*['"]$/i.test(before)) text = text.replace(/[{}]/g, '$&$&');
    if (LANGUAGE === 'cpp') text = text.replace(/\?(?=\?)/g, '?\\');
    return text;
  }
  linkIde() {
    const settings = IDE.load();
    this.stage.querySelectorAll('a.ide').forEach(a => {
      a.href = IDE.url(a.dataset.code ?? this.codeOf(a.closest('.slide')), settings);
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
    });
    this.updateQuickIde();
  }
  updateQuickIde() {
    const slide = this.slides[this.index];
    const quick = document.getElementById('ide-quick');
    const onPage = slide.querySelector('a.ide');
    const code = this.codeOf(slide);
    quick.href = onPage ? onPage.href : code ? IDE.url(code, IDE.load()) : IDE.url(IDE.config.blank, IDE.load());
    quick.textContent = onPage || code ? '▶ 本页代码进 IDE' : '▶ 打开空白 IDE';
  }
  setupIde() {
    const settings = IDE.load();
    const fields = document.getElementById('ide-fields');
    for (const field of IDE.config.settings) {
      const label = document.createElement('label');
      const select = document.createElement('select');
      label.append(field.label, select);
      for (const [value, text] of field.options) select.add(new Option(text, value));
      select.value = settings[field.param];
      select.onchange = () => { settings[field.param] = select.value; IDE.save(settings); this.linkIde(); };
      fields.append(label);
    }
    document.getElementById('ide-name').textContent = IDE.config.name;
    const button = document.getElementById('ide-open');
    button.hidden = !IDE.config.settings.length;
    button.onclick = () => this.settings.showModal();
    document.getElementById('ide-close').onclick = () => this.settings.close();
    this.linkIde();
  }

  /* --- classroom interactions --- */
  setupQuizzes() {
    this.stage.querySelectorAll('.quiz').forEach(quiz => {
      const feedback = quiz.parentElement.querySelector('.fb');
      const buttons = [...quiz.querySelectorAll('button')];
      buttons.forEach((button, i) => button.addEventListener('click', () => {
        buttons.forEach(b => b.classList.remove('yes', 'no'));
        button.classList.add(i === Number(quiz.dataset.right) ? 'yes' : 'no');
        feedback.textContent = button.dataset.fb;
      }));
    });
  }
  setupBugHunt() {
    this.stage.querySelectorAll('.pick').forEach(code => {
      const feedback = code.closest('.slide').querySelector('.fb');
      const lines = [...code.querySelectorAll('.ln')];
      lines.forEach((line, i) => line.addEventListener('click', () => {
        lines.forEach(l => l.classList.remove('yes', 'no'));
        const right = i === Number(code.dataset.bug) - 1;
        line.classList.add(right ? 'yes' : 'no');
        feedback.textContent = right ? code.dataset.yes : code.dataset.no;
      }));
    });
  }

  setupGates() {
    this.stage.querySelectorAll('.gate').forEach(gate => {
      const inputs = [...gate.querySelectorAll('button')], result = gate.querySelector('b');
      const update = () => {
        const [a, b] = inputs.map(i => i.textContent === 'True');
        const value = {and: a && b, or: a || b, not: !a}[gate.dataset.op];
        inputs.forEach(i => i.classList.toggle('on', i.textContent === 'True'));
        result.textContent = value ? 'True' : 'False';
        result.classList.toggle('on', value);
      };
      inputs.forEach(input => input.addEventListener('click', () => {
        input.textContent = input.textContent === 'True' ? 'False' : 'True';
        update();
      }));
      update();
    });
  }

  /* The result of one small expression in the course language, so a slot can change a value with no compiler on the page. */
  setupLive() {
    const cpp = LANGUAGE === 'cpp';
    const truth = v => cpp ? (v ? '1' : '0') : (v ? 'True' : 'False');
    const calc = {
      '+': (a, b) => a + b, '-': (a, b) => a - b, '*': (a, b) => a * b,
      '/': (a, b) => cpp ? Math.trunc(a / b) : Number.isInteger(a / b) ? (a / b) + '.0' : String(a / b),
      '//': (a, b) => Math.floor(a / b), '%': (a, b) => a % b,
      '>': (a, b) => truth(a > b), '<': (a, b) => truth(a < b), '>=': (a, b) => truth(a >= b),
      '<=': (a, b) => truth(a <= b), '==': (a, b) => truth(a === b), '!=': (a, b) => truth(a !== b)
    };
    // Never turn what a student typed into a different value: a value the page cannot work out is marked and explained.
    // Full-width digits and leading zeros are the same number, so those alone are tidied.
    const problem = slot => {
      if (slot.dataset.kind === 'text') {
        if (/["\r\n]/.test(slot.value)) return 'quote';
        if (slot.value.includes('\\')) return 'slash';
        return Array.from(slot.value).length > 12 ? 'long' : null;
      }
      const digits = slot.value.replace(/[０-９]/g, d => String.fromCharCode(d.charCodeAt(0) - 0xFEE0));
      const tidy = /^\d+$/.test(digits) ? digits.replace(/^0+(?=\d)/, '') : digits;
      if (tidy !== slot.value) slot.value = tidy;
      if (/^\d{0,4}$/.test(tidy)) return null;
      if (/^\d+$/.test(tidy)) return 'big';
      if (/^[-－]\s*\d/.test(tidy)) return 'negative';
      return /^\d*[.。]\d+$|^\d+[.。]$/.test(tidy) ? 'decimal' : 'letters';
    };
    // Short enough to read from the back of the room; red means the page cannot use it, amber only that a box is empty.
    const tips = {
      letters: '这里只能填数字，比如 7。', negative: '负数这里算不了，到 IDE 里试。', decimal: '小数这里算不了，到 IDE 里试。',
      big: '最大只能填 9999。', quote: '英文引号 " 用不了，换成中文引号 “ ”。', slash: '反斜杠 \\ 这里用不了，到 IDE 里试。',
      long: '最多 12 个字，删掉几个吧。', empty: '框里空着，填上就有结果。'
    };
    this.liveSlots = [...this.stage.querySelectorAll('.slot')];
    this.slides.filter(slide => slide.querySelector('.slot')).forEach(slide => {
      const slots = [...slide.querySelectorAll('.slot')];
      const results = [...slide.querySelectorAll('[data-eval]')];
      const tip = Object.assign(document.createElement('p'), {className: 'slot-tip', hidden: true});
      tip.setAttribute('role', 'status');
      slide.append(tip);
      const update = () => {
        const value = Object.fromEntries(slots.map(slot => [slot.dataset.var, slot.value]));
        const bad = slots.find(slot => slot.classList.contains('bad'));
        const empty = slots.find(slot => !slot.value);
        const missing = Boolean(bad || empty);
        tip.hidden = !missing;
        slide.querySelectorAll('.tip-under').forEach(e => e.classList.remove('tip-under'));
        if (missing) {
          tip.classList.toggle('calm', !bad);
          tip.textContent = tips[bad ? bad.dataset.problem : 'empty'];
          // Under the editor and no wider than it, so the hint never hides another slot or the results beside it.
          const box = ((bad || empty).closest('.editor') || bad || empty).getBoundingClientRect(), base = slide.getBoundingClientRect(), f = base.width / 1920 || 1;
          tip.style.maxWidth = Math.max(560, box.width / f) + 'px';
          tip.style.left = Math.max(48, Math.min((box.left - base.left) / f, 1872 - tip.offsetWidth)) + 'px';
          tip.style.top = Math.min((box.bottom - base.top) / f + 22, 1032 - tip.offsetHeight) + 'px';
          // Words half covered by the hint are hard to read, so the page text under it steps aside until it goes.
          const t = tip.getBoundingClientRect();
          slide.querySelectorAll(':scope > p:not(.slot-tip)').forEach(p => {
            const b = p.getBoundingClientRect();
            if (b.width && b.left < t.right && b.right > t.left && b.top < t.bottom && b.bottom > t.top) p.classList.add('tip-under');
          });
        }
        let stopped = false;
        results.forEach(result => {
          // A name alone, or names and numbers joined by operators, worked out from left to right.
          // The page code must group the same way, e.g. (lo + hi) // 2; the browser check runs it for real.
          const [first, ...rest] = result.dataset.eval.split(' ');
          const num = name => Number(value[name] ?? name);
          let out = rest.length ? num(first) : value[first], failed = false;
          for (let i = 0; i < rest.length && !failed; i += 2) {
            const b = num(rest[i + 1]);
            failed = !missing && !stopped && b === 0 && ['/', '//', '%'].includes(rest[i]);
            if (!failed) out = calc[rest[i]](Number(out), b);
          }
          result.textContent = missing ? '？' : stopped ? '没有运行' : failed ? (cpp ? '除数不能是 0' : 'ZeroDivisionError') : out;
          result.classList.toggle('skip', !missing && stopped);
          result.classList.toggle('long', result.textContent.length > 18);
          stopped ||= failed;
        });
        this.linkIde();
      };
      slots.forEach(slot => {
        slot.dataset.start = slot.value;
        // Wait for a Chinese input method to finish the word before checking the text.
        const tidy = e => {
          if (e.isComposing) return;
          const why = problem(slot);
          slot.dataset.problem = why || '';
          slot.classList.toggle('bad', Boolean(why));
          update();
        };
        slot.addEventListener('input', tidy);
        slot.addEventListener('compositionend', tidy);
      });
      update();
    });
  }

  /* --- code changes: pre.code.was is the old version, the pre.code after it the new one, shown from step data-change.
     Both become one list of lines: kept lines stay put, new ones slide in, removed ones fade out, edited ones swap text.
     The IDE always gets the new version. --- */
  setupChanges() {
    this.changes = [...this.stage.querySelectorAll('pre.code.was')].map(old => {
      const pre = old.nextElementSibling;
      const lines = [...pre.querySelectorAll('.ln')];
      const rows = this.diffLines([...old.querySelectorAll('.ln')].map(l => l.textContent), lines.map(l => l.textContent));
      const olds = [...old.querySelectorAll('.ln')];
      pre.replaceChildren(...rows.map(row => {
        if (row.kind === 'cut') return Object.assign(olds[row.from], {className: olds[row.from].className + ' cut'});
        const line = lines[row.to];
        line.classList.add(row.kind);
        if (row.kind === 'edit') {
          const now = document.createElement('span'), then = document.createElement('span');
          now.className = 'now';
          now.append(...line.childNodes);
          then.className = 'then';
          then.setAttribute('aria-hidden', 'true');
          then.append(...olds[row.from].childNodes);
          line.append(now, then);
        }
        return line;
      }));
      old.remove();
      pre.classList.add('change');
      const slide = pre.closest('.slide');
      this.setChange(pre, Number(slide.dataset.at || slide.dataset.steps || 1), false);
      return {slide, pre};
    });
  }
  /* Lines in both versions are kept (longest common run); the rest of each gap is matched to an old line that reads
     about the same once spaces are trimmed, such as print(i) indented further, or else counted as added or removed. */
  diffLines(a, b) {
    const n = a.length, m = b.length;
    const common = Array.from({length: n + 1}, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) {
      common[i][j] = a[i] === b[j] ? common[i + 1][j + 1] + 1 : Math.max(common[i + 1][j], common[i][j + 1]);
    }
    const alike = (x, y) => {
      x = x.trim(); y = y.trim();
      const t = Array.from({length: x.length + 1}, () => new Array(y.length + 1).fill(0));
      for (let i = x.length - 1; i >= 0; i--) for (let j = y.length - 1; j >= 0; j--) {
        t[i][j] = x[i] === y[j] ? t[i + 1][j + 1] + 1 : Math.max(t[i + 1][j], t[i][j + 1]);
      }
      return 2 * t[0][0] / ((x.length + y.length) || 1) >= 0.6;
    };
    const rows = [];
    let cut = [], add = [];
    const flush = () => {
      let next = 0;
      for (const to of add) {
        const match = cut.slice(next).findIndex(from => alike(a[from], b[to]));
        if (match < 0) { rows.push({kind: 'add', to}); continue; }
        cut.slice(next, next + match).forEach(from => rows.push({kind: 'cut', from}));
        rows.push({kind: 'edit', from: cut[next + match], to});
        next += match + 1;
      }
      cut.slice(next).forEach(from => rows.push({kind: 'cut', from}));
      cut = []; add = [];
    };
    let i = 0, j = 0;
    while (i < n || j < m) {
      if (i < n && j < m && a[i] === b[j]) { flush(); rows.push({kind: 'same', to: j}); i++; j++; }
      else if (j < m && (i === n || common[i][j + 1] >= common[i + 1][j])) add.push(j++);
      else cut.push(i++);
    }
    flush();
    return rows;
  }
  setChange(pre, at, animate) {
    pre.classList.toggle('play', animate && !matchMedia('(prefers-reduced-motion: reduce)').matches);
    pre.classList.toggle('new', at >= Number(pre.dataset.change || 2));
  }
  syncChanges(animate) {
    this.changes.forEach(c => this.setChange(c.pre, Number(c.slide.dataset.at || 1), animate && c.slide === this.slides[this.index]));
  }

  /* --- stage and paging --- */
  scale() {
    const full = Boolean(document.fullscreenElement);
    const left = !full && document.body.classList.contains('thumbs-open') ? document.getElementById('thumbs').offsetWidth : 0;
    const bottom = full ? 0 : this.bar.offsetHeight;
    const width = innerWidth - left, height = innerHeight - bottom;
    const f = Math.min(width / 1920, height / 1080);
    this.stage.style.transform = `translate(${left + (width - 1920 * f) / 2}px, ${(height - 1080 * f) / 2}px) scale(${f})`;
  }
  steps(slide) { return Number(slide.dataset.steps || 1); }
  show(index, atEnd = false) {
    this.slides.forEach(s => s.classList.remove('active', 'visible'));
    this.index = Math.max(0, Math.min(index, this.slides.length - 1));
    const slide = this.slides[this.index];
    slide.classList.add('active', 'visible');
    if (document.activeElement.matches('.slot')) document.activeElement.blur();
    if (slide.dataset.steps) slide.dataset.at = atEnd ? slide.dataset.steps : 1;
    this.syncChanges(false);
    history.replaceState(null, '', '#page-' + (this.index + 1));
    this.label();
    this.segments.forEach((seg, i) => {
      seg.classList.toggle('done', i < this.index);
      seg.classList.toggle('on', i === this.index);
    });
    this.thumbs.forEach((thumb, i) => thumb.classList.toggle('on', i === this.index));
    this.thumbs[this.index].scrollIntoView({block: 'nearest'});
    this.slider.value = this.index + 1;
    this.jump.value = this.index + 1;
    const current = this.chapters.filter(c => c.start <= this.index).pop();
    this.chapters.forEach(c => c.button.classList.toggle('on', c === current));
    this.updateQuickIde();
  }
  label() {
    const slide = this.slides[this.index], total = this.steps(slide);
    this.counter.textContent = `${this.index + 1} / ${this.slides.length}` + (total > 1 ? ` · 第 ${slide.dataset.at} / ${total} 步` : '');
  }
  move(delta) {
    const slide = this.slides[this.index], at = Number(slide.dataset.at || 1), next = at + delta;
    if (slide.dataset.steps && next >= 1 && next <= this.steps(slide)) { slide.dataset.at = next; this.syncChanges(true); this.label(); return; }
    if (this.index + delta >= 0 && this.index + delta < this.slides.length) this.show(this.index + delta, delta < 0);
  }
  key(e) {
    if (e.ctrlKey || e.metaKey || e.altKey || this.settings.open || this.help.open) return;
    if (e.target.closest('select')) return;
    if (!this.blank.hidden) { this.blank.hidden = true; e.preventDefault(); return; }
    if (e.target.matches('.slot')) {
      if (['Enter', 'Escape'].includes(e.key)) e.target.blur();
      if (!['PageDown', 'PageUp'].includes(e.key)) return;
    }
    const k = e.key;
    const actions = {
      f: () => this.fullscreen(),
      i: () => { if (IDE.config.settings.length) this.settings.showModal(); },
      t: () => document.getElementById('toggle-thumbs').click(),
      r: () => document.getElementById('ide-quick').click(),
      b: () => { this.blank.hidden = false; },
      g: () => { e.preventDefault(); this.jump.select(); }
    };
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(k)) { e.preventDefault(); this.move(e.shiftKey ? -1 : 1); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(k)) { e.preventDefault(); this.move(-1); }
    else if (k === 'Home') this.show(0);
    else if (k === 'End') this.show(this.slides.length - 1);
    else if (k === '?') this.help.showModal();
    else if (actions[k.toLowerCase()]) actions[k.toLowerCase()]();
    else if (/^[1-4]$/.test(k)) this.slides[this.index].querySelectorAll('.quiz button')[Number(k) - 1]?.click();
  }
  fromHash() {
    const n = Number((location.hash.match(/^#page-(\d{1,3})$/) || [])[1] || 1);
    this.show(n - 1);
  }
  fullscreen() {
    document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
  }
  reveal() {
    this.bar.classList.add('show');
    clearTimeout(this.hide);
    this.hide = setTimeout(() => this.bar.classList.remove('show'), 2000);
  }
  finishAll() {
    this.liveSlots.forEach(slot => { slot.value = slot.dataset.start; slot.dispatchEvent(new Event('input')); });
    this.atBeforePrint = this.slides[this.index].dataset.at;
    this.slides.forEach(s => { if (s.dataset.steps) s.dataset.at = s.dataset.steps; });
    this.syncChanges(false);
    this.stage.querySelectorAll('.quiz').forEach(q => q.querySelectorAll('button')[Number(q.dataset.right)].click());
  }
  undoFinish() {
    const slide = this.slides[this.index];
    if (slide.dataset.steps) slide.dataset.at = this.atBeforePrint;
    this.syncChanges(false);
    this.label();
    this.stage.querySelectorAll('.quiz').forEach(q => {
      q.querySelectorAll('button').forEach(b => b.classList.remove('yes', 'no'));
      q.parentElement.querySelector('.fb').textContent = '';
    });
  }
}
new SlidePresentation();
