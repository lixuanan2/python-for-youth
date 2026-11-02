/* === IDE LINKS: one place to change the platform or its defaults === */
const IDE = {
  base: 'https://jupyterlite.github.io/demo/repl/index.html',
  defaults: {theme: 'JupyterLab Dark', layout: 'left', run: '0'},
  load() {
    try { return {...this.defaults, ...JSON.parse(localStorage.getItem('ide-settings') || '{}')}; }
    catch { return {...this.defaults}; }
  },
  save(settings) {
    try { localStorage.setItem('ide-settings', JSON.stringify(settings)); } catch {}
  },
  url(code, settings) {
    const q = {kernel: 'python', toolbar: '1', theme: settings.theme, promptCellPosition: settings.layout, showBanner: '0',
      clearCellsOnExecute: '1', hideCodeInput: '1', clearCodeContentOnExecute: '0', execute: settings.run, code};
    return this.base + '?' + Object.entries(q).map(([k, v]) => k + '=' + encodeURIComponent(v)).join('&');
  }
};

/* === SLIDE CONTROLLER: scale the stage, turn pages, play steps before turning === */
class SlidePresentation {
  constructor() {
    this.slides = [...document.querySelectorAll('.slide')];
    this.stage = document.getElementById('deckStage');
    this.counter = document.getElementById('counter');
    this.dialog = document.getElementById('ide-settings');
    this.index = 0;
    addEventListener('resize', () => this.scale());
    addEventListener('hashchange', () => this.fromHash());
    addEventListener('beforeprint', () => this.finishAll());
    document.addEventListener('keydown', e => this.key(e));
    document.addEventListener('mousemove', () => this.reveal());
    this.stage.addEventListener('click', e => {
      if (e.target.closest('a,button,.pick,pre,.tb')) return;
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
    this.setupIde();
    this.setupQuizzes();
    this.setupBugHunt();
    this.scale();
    this.fromHash();
  }
  codeOf(slide) {
    return [...slide.querySelectorAll('pre.code .ln')].map(l => l.textContent).join('\n');
  }
  linkIde() {
    const settings = IDE.load();
    document.querySelectorAll('a.ide').forEach(a => {
      a.href = IDE.url(a.dataset.code ?? this.codeOf(a.closest('.slide')), settings);
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
    });
  }
  setupIde() {
    const fields = {theme: 'ide-theme', layout: 'ide-layout', run: 'ide-run'};
    const settings = IDE.load();
    for (const [key, id] of Object.entries(fields)) {
      const el = document.getElementById(id);
      el.value = settings[key];
      el.onchange = () => { settings[key] = el.value; IDE.save(settings); this.linkIde(); };
    }
    document.getElementById('ide-open').onclick = () => this.dialog.showModal();
    document.getElementById('ide-close').onclick = () => this.dialog.close();
    this.linkIde();
  }
  setupQuizzes() {
    document.querySelectorAll('.quiz').forEach(quiz => {
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
    document.querySelectorAll('.pick').forEach(code => {
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
  scale() {
    const f = Math.min(innerWidth / 1920, innerHeight / 1080);
    this.stage.style.transform = `translate(${(innerWidth - 1920 * f) / 2}px, ${(innerHeight - 1080 * f) / 2}px) scale(${f})`;
  }
  steps(slide) { return Number(slide.dataset.steps || 1); }
  show(index, atEnd = false) {
    this.slides.forEach(s => s.classList.remove('active', 'visible'));
    this.index = Math.max(0, Math.min(index, this.slides.length - 1));
    const slide = this.slides[this.index];
    slide.classList.add('active', 'visible');
    if (slide.dataset.steps) slide.dataset.at = atEnd ? slide.dataset.steps : 1;
    history.replaceState(null, '', '#page-' + (this.index + 1));
    this.label();
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
    if (e.ctrlKey || e.metaKey || e.altKey || this.dialog.open) return;
    const k = e.key;
    if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(k)) { e.preventDefault(); this.move(e.shiftKey ? -1 : 1); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(k)) { e.preventDefault(); this.move(-1); }
    else if (k === 'Home') this.show(0);
    else if (k === 'End') this.show(this.slides.length - 1);
    else if (k === 'f' || k === 'F') this.fullscreen();
    else if (k === 'i' || k === 'I') this.dialog.showModal();
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
    const c = document.getElementById('controls');
    c.classList.add('show');
    clearTimeout(this.hide);
    this.hide = setTimeout(() => c.classList.remove('show'), 2000);
  }
  finishAll() {
    this.slides.forEach(s => { if (s.dataset.steps) s.dataset.at = s.dataset.steps; });
    document.querySelectorAll('.quiz').forEach(q => q.querySelectorAll('button')[Number(q.dataset.right)].click());
  }
}
new SlidePresentation();
