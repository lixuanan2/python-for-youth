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

/* === ALGORITHM DEMO: build.py ran the page's program and wrote every step into data-trace; this plays them === */
const ALGO_SPEEDS = {slow: ['慢', 2600], mid: ['中', 1600], fast: ['快', 600]};
const ALGO_KEYS = {p: 'play', ',': 'back', '.': 'next', '0': 'reset', s: 'speed'};
const quiet = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const listText = (list, cpp) => cpp ? `{${list.join(', ')}}` : `[${list.join(', ')}]`;

class AlgoPlayer {
  constructor(box) {
    this.box = box;
    const data = JSON.parse(box.dataset.trace);
    this.kind = data.kind;
    this.names = data.names;
    this.steps = data.steps;
    this.cpp = data.language === 'cpp';
    // A page may show only some lines of the program it runs: data.first is the program line its first row shows.
    this.first = data.first || 1;
    this.lines = [...box.closest('.slide').querySelectorAll('pre.code:not(.was) .ln')];
    this.speed = box.dataset.speed || 'mid';
    this.at = 0;
    box.player = this;
    box.innerHTML = `<div class="algo-live"><div class="algo-stage"></div>
      <p class="algo-say" aria-live="polite"></p><div class="algo-out"><i>屏幕上</i><pre></pre></div>
      <div class="algo-bar">
        <button type="button" data-do="play" class="algo-play" title="播放或暂停（P）">▶ 播放</button>
        <button type="button" data-do="back" title="上一步（,）">◀ 上一步</button>
        <button type="button" data-do="next" title="下一步（.）">下一步 ▶</button>
      </div>
      <div class="algo-bar algo-small"><button type="button" data-do="reset" title="重来（0）">⟲ 重来</button><span>速度</span>${
        Object.entries(ALGO_SPEEDS).map(([k, [label]]) => `<button type="button" data-speed="${k}" title="换速度（S）">${label}</button>`).join('')}<span class="algo-count"></span></div></div>
      <div class="algo-film" aria-hidden="true"></div>`;
    this.stage = box.querySelector('.algo-stage');
    this.say = box.querySelector('.algo-say');
    this.out = box.querySelector('.algo-out pre');
    this.count = box.querySelector('.algo-count');
    this.playButton = box.querySelector('.algo-play');
    // A click must not leave focus on a button, or the next space or Enter would press it again instead of turning the page.
    box.addEventListener('mousedown', e => { if (e.target.closest('button')) e.preventDefault(); });
    box.addEventListener('click', e => {
      const button = e.target.closest('button');
      if (button) this.do(button.dataset.do || 'speed', button.dataset.speed);
    });
    matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change', () => { this.pause(); this.draw(false); });
    this.buildFilm();
    this.draw(false);
  }
  do(action, speed) {
    if (action === 'play') return this.timer ? this.pause() : this.play();
    if (action === 'speed') {
      const keys = Object.keys(ALGO_SPEEDS);
      this.speed = speed || keys[(keys.indexOf(this.speed) + 1) % keys.length];
      if (this.timer) { this.pause(); this.play(); }
      return this.draw(false);
    }
    this.pause();
    if (action === 'reset') this.go(0);
    if (action === 'back') this.go(this.at - 1);
    if (action === 'next') this.go(this.at + 1);
  }
  go(at) {
    if (at < 0 || at >= this.steps.length) return;
    this.at = at;
    this.draw(!quiet());
  }
  play() {
    if (quiet()) return;  // with reduced motion the demo only moves when someone presses a step
    if (this.at === this.steps.length - 1) this.go(0);
    const tick = () => {
      if (this.at >= this.steps.length - 1) return this.pause();
      this.go(this.at + 1);
      this.timer = setTimeout(tick, ALGO_SPEEDS[this.speed][1]);
    };
    this.timer = setTimeout(tick, Math.min(700, ALGO_SPEEDS[this.speed][1]));
    this.draw(false);
  }
  pause() {
    clearTimeout(this.timer);
    this.timer = null;
    this.draw(false);
  }
  draw(animate) {
    const step = this.steps[this.at];
    this.box.classList.toggle('moving', animate);
    this.box.dataset.at = this.at;
    this.box.dataset.playing = this.timer ? '1' : '';
    this.box.dataset.speed = this.speed;
    this.render(this.stage, this.at);
    this.say.textContent = this.caption(this.at);
    this.out.textContent = step.out.split('\n').slice(0, -1).slice(-3).join('\n');
    this.box.querySelector('.algo-out').classList.toggle('empty', !step.out);
    this.count.textContent = `${this.at + 1} / ${this.steps.length}`;
    this.playButton.textContent = this.timer ? '❚❚ 暂停' : '▶ 播放';
    this.playButton.disabled = quiet();
    this.box.querySelectorAll('[data-speed]').forEach(b => b.classList.toggle('on', b.dataset.speed === this.speed));
    this.lines.forEach((line, i) => line.classList.toggle('run', step.line === i + this.first));
  }
  // Each place keeps its own bar, so a swap moves the two bars instead of relabelling them.
  render(stage, at) {
    const step = this.steps[at];
    if (this.kind === 'sort') return this.renderBars(stage, step);
    return this.renderTrack(stage, at);
  }
  renderBars(stage, step) {
    const list = step.list, top = Math.max(...this.steps.flatMap(s => s.list));
    let bars = [...stage.querySelectorAll('.algo-bar-item')];
    if (bars.length !== list.length) {
      stage.innerHTML = list.map((_, i) => `<div class="algo-bar-item"><b></b></div><span class="algo-index" style="left:${(i + .5) * 100 / list.length}%">${i}</span>`).join('');
      bars = [...stage.querySelectorAll('.algo-bar-item')];
      bars.forEach((bar, i) => { bar.dataset.place = i; bar.dataset.value = list[i]; });
    }
    const free = new Set(bars);
    const placed = list.map((value, i) => {
      const keep = bars.find(b => free.has(b) && Number(b.dataset.place) === i && Number(b.dataset.value) === value)
        || bars.find(b => free.has(b) && Number(b.dataset.value) === value) || [...free][0];
      free.delete(keep);
      return keep;
    });
    stage.querySelectorAll('.algo-tag').forEach(tag => tag.remove());
    placed.forEach((bar, i) => {
      bar.dataset.place = i;
      bar.dataset.value = list[i];
      bar.querySelector('b').textContent = list[i];
      bar.style.left = `${(i + .5) * 100 / list.length}%`;
      bar.style.height = `${18 + 72 * list[i] / top}%`;
      bar.className = 'algo-bar-item';
      if ((step.at || []).includes(i)) bar.classList.add(step.type === 'swap' ? 'swapped' : 'looking');
      if (step.done.includes(i)) bar.classList.add('done');
    });
    if (step.type === 'compare') step.at.forEach((i, k) => {
      stage.insertAdjacentHTML('beforeend', `<span class="algo-tag" style="left:${(i + .5) * 100 / list.length}%">${this.names.list}[${this.names.at[k]}]</span>`);
    });
  }
  renderTrack(stage, at) {
    const step = this.steps[at], [from, to] = this.steps[0].range, size = to - from + 1;
    if (!stage.querySelector('.algo-track')) {
      stage.innerHTML = `<div class="algo-track">${Array.from({length: size}, () => '<i></i>').join('')}</div>`;
    }
    const cells = [...stage.querySelectorAll('.algo-track i')];
    // Marks keep their element, so lo, hi and the guess slide along the track when they change.
    const mark = (key, v, text, where) => {
      let m = stage.querySelector(`.algo-mark[data-key="${key}"]`);
      if (!m) { m = document.createElement('span'); m.dataset.key = key; stage.append(m); }
      m.hidden = v == null;
      if (v == null) return;
      const spot = (v - from + .5) / size;
      m.className = `algo-mark ${where}${spot < .12 ? ' edge-l' : spot > .88 ? ' edge-r' : ''}`;
      m.style.left = `${spot * 100}%`;
      m.textContent = text;
    };
    if (this.kind === 'search') {
      cells.forEach((cell, i) => {
        const v = from + i;
        cell.className = v < step.lo || v > step.hi ? 'out' : '';
        if (v === step.mid && step.type !== 'start') cell.className += ' looking';
        if (v === step.target) cell.className += ' goal';
      });
      mark('lo', step.lo, `${this.names.lo} ${step.lo}`, 'below');
      mark('hi', step.hi, `${this.names.hi} ${step.hi}`, 'lower');
      mark('mid', step.type === 'start' ? null : step.mid, `猜 ${step.mid}`, 'above');
    } else {
      const tried = new Set(this.steps.slice(0, at + 1).filter(s => s.type === 'try').map(s => s.value));
      const hits = new Set(this.steps.slice(0, at + 1).filter(s => s.hit).map(s => s.value));
      cells.forEach((cell, i) => {
        const v = from + i;
        cell.className = hits.has(v) ? 'done' : tried.has(v) ? 'out' : '';
        if (step.type === 'try' && v === step.value) cell.className += ' looking';
      });
      mark('from', from, from, 'below');
      mark('to', to, to, 'below');
      mark('now', step.type === 'try' ? step.value : null, `${this.names.var} = ${step.value}`, 'above');
    }
  }
  caption(at) {
    const step = this.steps[at], n = this.names;
    if (this.kind === 'sort') {
      const newly = step.done.filter(i => !(this.steps[at - 1]?.done || []).includes(i)).map(i => step.list[i]);
      const settled = newly.length && step.type !== 'end' ? `${newly.join('、')} 站好了位置，以后不用再比。` : '';
      if (step.type === 'start') return `开始：${n.list} 是 ${listText(step.list, this.cpp)}。挨着的两个比一比。`;
      if (step.type === 'compare') {
        const [x, y] = step.at.map(i => step.list[i]);
        const how = x === y ? `${x} 和 ${y} 一样大` : `${x} 比 ${y} ${x > y ? '大' : '小'}`;
        return `比 ${n.list}[${step.at[0]}] 和 ${n.list}[${step.at[1]}]：${how}，${step.swap ? '要换' : '不用换'}。`;
      }
      if (step.type === 'swap') return `换好了：${step.list[step.at[1]]} 往后挪了一格。${settled}`;
      if (step.type === 'print') return `输出现在的 ${n.list}：${step.text.trim()}。${settled}`;
      const order = step.sorted ? '从小到大排好了' : '';
      return order ? `全部比完，${order}。` : `比完了。${step.done.map(i => step.list[i]).join('、')} 已经站好，前面的还没排好。`;
    }
    if (this.kind === 'search') {
      if (step.type === 'start') return `秘密数是 ${step.target}。一开始 ${step.lo} 到 ${step.hi} 都有可能。`;
      if (step.type === 'pick') return `猜中间：(${step.before[0]} + ${step.before[1]}) ${this.cpp ? '/' : '//'} 2 是 ${step.mid}。`;
      if (step.type === 'hi') return `${step.mid} 比 ${step.target} 大，${step.mid} 和后面的都不可能了：${n.hi} 变成 ${step.hi}。`;
      if (step.type === 'lo') return `${step.mid} 比 ${step.target} 小，${step.mid} 和前面的都不可能了：${n.lo} 变成 ${step.lo}。`;
      return step.found ? `猜中了！第 ${step.count} 次猜到 ${step.target}，循环停下。` : `范围空了，没有找到 ${step.target}。`;
    }
    const [from, to] = this.steps[0].range;
    if (step.type === 'start') return `${n.var} 从 ${from} 试到 ${to}，一个一个试。`;
    if (step.type === 'try') return step.hit
      ? `${n.var} 是 ${step.value}：算出 ${step.left}，对上了！${step.text ? `输出 ${step.text.trim()}。` : ''}`
      : `${n.var} 是 ${step.value}：算出 ${step.left}，不是 ${step.right}，试下一个。`;
    return `试完了，一共试了 ${step.count} 个，${step.hits.length ? `对上的只有 ${step.hits.join('、')}` : '一个也没对上'}。`;
  }
  // Print shows a few key steps, not only the last one: the start, one or two in the middle, the end.
  buildFilm() {
    const last = this.steps.length - 1;
    const picks = [...new Set([0, Math.round(last / 3), Math.round(2 * last / 3), last])];
    const film = this.box.querySelector('.algo-film');
    film.innerHTML = picks.map(at => `<figure><div class="algo-stage"></div><figcaption><b>第 ${at + 1} 步</b>${this.caption(at)}</figcaption></figure>`).join('');
    film.querySelectorAll('.algo-stage').forEach((stage, k) => this.render(stage, picks[k]));
  }
}

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
    this.stage.querySelectorAll('.algo[data-trace]').forEach(box => new AlgoPlayer(box));
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
    // The button follows the step: the IDE link the page shows now, else the one it ends with.
    const at = Number(slide.dataset.at || 1), links = [...slide.querySelectorAll('a.ide')];
    const from = (a, re) => Number([...a.classList].find(c => re.test(c))?.replace(/\D/g, '') || 0);
    const shown = a => from(a, /^only\d$/) ? from(a, /^only\d$/) === at : from(a, /^s\d$/) <= at;
    const onPage = links.find(shown) || links.find(a => !from(a, /^only\d$/)) || links[0];
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
        if (/["'“”‘’\r\n]/.test(slot.value)) return 'quote';
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
      big: '最大只能填 9999。', quote: '两边的引号已经写好了，框里只填字。', slash: '反斜杠 \\ 这里用不了，到 IDE 里试。',
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
          const indent = text => text.length - text.trimStart().length;
          if (now.textContent.trim() === then.textContent.trim()) {
            line.classList.add('indent');  // only moved: the old line slides over instead of fading into the new one
            line.style.setProperty('--shift', indent(now.textContent) - indent(then.textContent));
          }
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
  /* Lines that read the same once the indent is trimmed are kept (longest common run): unchanged, or only moved
     right or left, as when a loop is wrapped around them. The rest of each gap is matched to an old line that reads
     about the same, such as print(i) becoming print(i * 2), or else counted as added or removed. */
  diffLines(a, b) {
    const n = a.length, m = b.length;
    const same = (i, j) => a[i].trim() === b[j].trim();
    const common = Array.from({length: n + 1}, () => new Array(m + 1).fill(0));
    for (let i = n - 1; i >= 0; i--) for (let j = m - 1; j >= 0; j--) {
      common[i][j] = same(i, j) ? common[i + 1][j + 1] + 1 : Math.max(common[i + 1][j], common[i][j + 1]);
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
      if (i < n && j < m && same(i, j)) { flush(); rows.push(a[i] === b[j] ? {kind: 'same', to: j} : {kind: 'edit', from: i, to: j}); i++; j++; }
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
    this.stage.querySelectorAll('.algo').forEach(box => box.player?.pause());
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
    if (slide.dataset.steps && next >= 1 && next <= this.steps(slide)) { slide.dataset.at = next; this.syncChanges(true); this.updateQuickIde(); this.label(); return; }
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
    // Demo keys are letters and the < > keys, so arrows, space and a clicker still turn pages on a demo page.
    const player = this.slides[this.index].querySelector('.algo')?.player;
    if (player && ALGO_KEYS[k.toLowerCase()]) { e.preventDefault(); player.do(ALGO_KEYS[k.toLowerCase()]); return; }
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
    this.stage.querySelectorAll('.algo').forEach(box => box.player?.pause());
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
