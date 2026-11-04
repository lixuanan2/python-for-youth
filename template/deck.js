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
    const full = slide.querySelector('pre.code[data-full]');
    if (full) return full.dataset.full;
    return [...slide.querySelectorAll('pre.code .ln')].map(l => this.lineText(l)).join('\n');
  }
  lineText(line) {
    const slots = [...line.querySelectorAll('.slot')];
    const copy = line.cloneNode(true);
    copy.querySelectorAll('.slot').forEach((slot, i) => slot.replaceWith(slots[i].value));
    return copy.textContent;
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
    const clean = slot => slot.dataset.kind === 'text'
      ? Array.from(slot.value.replace(/["\\\r\n]/g, '')).slice(0, 12).join('')
      : slot.value.replace(/\D/g, '').replace(/^0+(?=\d)/, '').slice(0, 4);
    this.liveSlots = [...this.stage.querySelectorAll('.slot')];
    this.slides.filter(slide => slide.querySelector('.slot')).forEach(slide => {
      const slots = [...slide.querySelectorAll('.slot')];
      const results = [...slide.querySelectorAll('[data-eval]')];
      const update = () => {
        const value = Object.fromEntries(slots.map(slot => [slot.dataset.var, slot.value]));
        const missing = slots.some(slot => !slot.value);
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
        // Wait for a Chinese input method to finish the word before tidying the text.
        const tidy = e => { if (e.isComposing) return; slot.value = clean(slot); update(); };
        slot.addEventListener('input', tidy);
        slot.addEventListener('compositionend', tidy);
      });
      update();
    });
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
    if (slide.dataset.steps && next >= 1 && next <= this.steps(slide)) { slide.dataset.at = next; this.label(); return; }
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
    this.stage.querySelectorAll('.quiz').forEach(q => q.querySelectorAll('button')[Number(q.dataset.right)].click());
  }
  undoFinish() {
    const slide = this.slides[this.index];
    if (slide.dataset.steps) slide.dataset.at = this.atBeforePrint;
    this.label();
    this.stage.querySelectorAll('.quiz').forEach(q => {
      q.querySelectorAll('button').forEach(b => b.classList.remove('yes', 'no'));
      q.parentElement.querySelector('.fb').textContent = '';
    });
  }
}
new SlidePresentation();
