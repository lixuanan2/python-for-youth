// Real Chrome over CDP on file://: render every page and step, then exercise each interaction.
// Run in basics/:
//   node tools/check_browser.mjs                 every lesson (CI does this weekly and when the template changes)
//   node tools/check_browser.mjs 06-for-loop …   only these lessons
//   node tools/check_browser.mjs --changed       lessons changed since they last passed here, and --sample if the template changed
//   node tools/check_browser.mjs --sample        three lessons that stand for all: the shortest, the longest title, the most widgets
//   node tools/check_browser.mjs --shard 2/4     the second quarter of the lessons chosen (CI splits a full check this way)
//   node tools/check_browser.mjs --status        when each lesson last changed and passed; runs nothing
// A lesson that passes gets its fingerprint written to .check-state.json and its screenshots kept in .check-shots/ (neither in
// Git: CI on main is the proof). Each run lists the screens that look different from the last pass in .preview/changed.txt,
// so only those need a look. Screenshots land in .preview/. Set CHROME_PATH if Chrome is not in a usual place.
import assert from 'node:assert/strict';
import {execFileSync, spawn} from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';

/* === WHICH LESSONS: arguments, and the local record of what passed === */
const RECORD = '.check-state.json', SHOTS = '.check-shots', SHARED_KEY = '(template)';
const allLessons = JSON.parse(fs.readFileSync('course.json', 'utf8')).filter(l => l.id);
const files = dir => fs.readdirSync(dir, {withFileTypes: true}).sort((a, b) => a.name < b.name ? -1 : 1)
  .flatMap(e => e.isDirectory() ? files(path.join(dir, e.name)) : [path.join(dir, e.name)]);
// What decides how every lesson renders and what this check does with it: the course index, the shared template and this
// file. A lesson's own fingerprint is its built pages and starters; a change here is checked on the sample, and in full by CI.
const SHARED = [path.join('dist', 'index.html'), ...files('template'), path.join('tools', 'check_browser.mjs')];
const digest = list => {
  const hash = crypto.createHash('sha256');
  for (const file of list) {
    hash.update(file.split(path.sep).join('/') + '\0');
    hash.update(fs.readFileSync(file));
  }
  return hash.digest('hex');
};
const fingerprint = id => digest(files(path.join('dist', id)).filter(f => !f.endsWith('.pdf')));
const sharedPrint = () => digest(SHARED);
const readRecord = () => { try { return JSON.parse(fs.readFileSync(RECORD, 'utf8')); } catch { return {}; } };
const git = (...args) => { try { return execFileSync('git', args, {encoding: 'utf8'}).trim(); } catch { return ''; } };
const args = process.argv.slice(2);
const shardAt = args.indexOf('--shard');
const shard = shardAt < 0 ? null : (args[shardAt + 1] || '').match(/^(\d+)\/(\d+)$/);
assert(shardAt < 0 || (shard && +shard[1] >= 1 && +shard[1] <= +shard[2]), 'Write the shard as K/N, for example --shard 2/4');
const words = args.filter((a, i) => !(shardAt >= 0 && i === shardAt + 1));
const known = new Set(allLessons.map(l => l.id));
const unknown = words.filter(a => !a.startsWith('--') && !known.has(a));
assert(!unknown.length, `No such lesson: ${unknown.join(', ')}. Lessons are: ${[...known].join(' ')}`);
const badFlag = words.filter(a => a.startsWith('--') && !['--changed', '--status', '--sample', '--shard'].includes(a));
assert(!badFlag.length, `Unknown option: ${badFlag.join(', ')}`);
const record = readRecord();
const needs = id => record[id]?.hash !== fingerprint(id);
const sharedNeeds = () => record[SHARED_KEY]?.hash !== sharedPrint();

// The sample: the lesson with the fewest pages, the one with the longest title (the status bar's longest label) and the one
// with the most widgets (quizzes, bug hunts, logic switches, yellow boxes, code changes, algorithm demos). Worked out from
// the built pages each time, so it follows the course as lessons are added.
const sample = (() => {
  const built = id => fs.readFileSync(path.join('dist', id, 'index.html'), 'utf8');
  const pages = id => built(id).match(/<section id="page-/g).length;
  const widgets = id => (built(id).match(/class="(?:quiz|pick|gate|slot|algo)\b|class="code was\b/g) || []).length;
  const picked = [];
  for (const score of [l => -pages(l.id), l => [...l.title].length, l => widgets(l.id)]) {
    const left = allLessons.filter(l => !picked.includes(l));
    picked.push(left.reduce((best, l) => score(l) > score(best) ? l : best));
  }
  return allLessons.filter(l => picked.includes(l));
})();

if (words.includes('--status')) {
  const local = iso => { const d = new Date(iso), two = n => String(n).padStart(2, '0'); return `${d.getFullYear()}-${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:${two(d.getMinutes())}`; };
  const row = (name, key, where, now) => {
    const dirty = git('status', '--porcelain', '--', ...where);
    const changed = dirty ? '未提交的改动' : (git('log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M', '--', ...where) || '没有提交');
    const passed = record[key] ? `${local(record[key].passed)}（${record[key].commit}）` : '没查过';
    return [name, changed, passed, now];
  };
  const rows = allLessons.map(({id}) => row(id, id, [`lessons/${id}`, `dist/${id}`], !record[id] ? '要查（还没查过）' : needs(id) ? '要查（改过了）' : '不用'));
  rows.push(row('模板和检查', SHARED_KEY, ['template', 'dist/index.html', 'tools/check_browser.mjs'],
    sharedNeeds() ? `要查 --sample（${sample.map(l => l.id).join(' ')}）` : '不用'));
  const head = ['课', '最近改动', '本机浏览器检查通过', '现在'];
  const width = text => [...text].reduce((n, ch) => n + (ch.charCodeAt(0) > 0x2e7f ? 2 : 1), 0);
  const cols = head.map((h, i) => Math.max(...[h, ...rows.map(r => r[i])].map(width)));
  for (const r of [head, ...rows]) console.log(r.map((c, i) => c + ' '.repeat(cols[i] - width(c))).join('  ').trimEnd());
  console.log('本机记录只在这台电脑上，不进 Git；main 上 CI 的完整检查通过才算数。');
  process.exit(0);
}
const chosen = words.filter(a => !a.startsWith('--'));
const wanted = l => chosen.includes(l.id) || (words.includes('--sample') && sample.includes(l))
  || (words.includes('--changed') && (needs(l.id) || (sharedNeeds() && sample.includes(l))));
const picked = chosen.length || words.includes('--sample') || words.includes('--changed') ? allLessons.filter(wanted) : allLessons;
const targets = shard ? picked.filter((_, i) => i % +shard[2] === +shard[1] - 1) : picked;
if (!targets.length) {
  console.log(shard ? `Shard ${shard[0]} has no lesson.` : 'Nothing changed since the last local pass: no lesson to check. CI still checks what changed.');
  process.exit(0);
}
const scope = shard ? `shard ${shard[0]}: ${targets.map(l => l.id).join(' ')}`
  : targets.length === allLessons.length ? 'every lesson' : targets.map(l => l.id).join(' ');
const commit = () => git('rev-parse', '--short', 'HEAD');
const pass = id => {
  if (process.env.CI) return;  // CI keeps no record
  const now = readRecord();
  now[id] = {hash: fingerprint(id), passed: new Date().toISOString(), commit: commit() + (git('status', '--porcelain', '--', `lessons/${id}`, `dist/${id}`, 'template', 'tools') ? '+改动' : '')};
  fs.writeFileSync(RECORD, JSON.stringify(now, null, 1) + '\n');
};
// The template counts as checked here once every sample lesson passed with it.
const passShared = () => {
  if (process.env.CI || !sample.every(l => targets.includes(l))) return;
  const now = readRecord();
  now[SHARED_KEY] = {hash: sharedPrint(), passed: new Date().toISOString(), commit: commit() + (git('status', '--porcelain', '--', 'template', 'tools', 'dist/index.html') ? '+改动' : '')};
  fs.writeFileSync(RECORD, JSON.stringify(now, null, 1) + '\n');
};

// Chrome compresses the same picture differently from run to run, so screens are compared by their pixels, not their bytes.
const pixels = file => {
  const buf = fs.readFileSync(file), idat = [];
  let pos = 8, width = 0, height = 0, type = 2;
  while (pos < buf.length) {
    const len = buf.readUInt32BE(pos), kind = buf.toString('latin1', pos + 4, pos + 8), data = buf.subarray(pos + 8, pos + 8 + len);
    if (kind === 'IHDR') { width = data.readUInt32BE(0); height = data.readUInt32BE(4); type = data[9]; }
    if (kind === 'IDAT') idat.push(data);
    pos += 12 + len;
  }
  const bpp = {0: 1, 2: 3, 4: 2, 6: 4}[type], stride = width * bpp, raw = zlib.inflateSync(Buffer.concat(idat)), out = Buffer.alloc(stride * height);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)], row = y * (stride + 1) + 1, o = y * stride;
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? out[o + x - bpp] : 0, b = y ? out[o - stride + x] : 0, c = x >= bpp && y ? out[o - stride + x - bpp] : 0;
      const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
      out[o + x] = (raw[row + x] + [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][filter]) & 255;
    }
  }
  return {width, height, bpp, data: out};
};
// Text edges may come out one shade apart between runs; a real change moves far more than 3 steps of 255. The thumbnail
// rail on the left is left out: its edge sits on a fraction of a pixel and its scroll position varies, and every thumbnail
// is a copy of a page that is compared full size anyway.
let railWidth = 0;
const samePicture = (x, y, rail = railWidth) => {
  try {
    const a = pixels(x), b = pixels(y);
    if (a.width !== b.width || a.height !== b.height || a.bpp !== b.bpp) return false;
    const skip = rail * a.bpp, stride = a.width * a.bpp;
    for (let row = 0; row < a.data.length; row += stride)
      for (let i = row + skip; i < row + stride; i++) if (Math.abs(a.data[i] - b.data[i]) > 3) return false;
    return true;
  } catch { return false; }
};
const measureRail = async () => {
  railWidth = await run(`(() => { const r = document.getElementById('thumbs'); return r && document.body.classList.contains('thumbs-open') ? Math.ceil(r.getBoundingClientRect().right * devicePixelRatio) + 2 : 0; })()`);
};
// Screens against the last pass: same pixels, same picture. Returns the screens that changed, appeared or went away, then keeps this pass as the new baseline.
const compareShots = id => {
  if (process.env.CI) return [];
  const now = path.join('.preview', id), then = path.join(SHOTS, id);
  const names = dir => fs.existsSync(dir) ? fs.readdirSync(dir).filter(f => f.endsWith('.png')).sort() : [];
  const before = new Set(names(then)), after = names(now);
  const out = [];
  for (const name of after) {
    if (!before.has(name)) out.push(`${id}/${name} 新的`);
    else if (!samePicture(path.join(now, name), path.join(then, name))) out.push(`${id}/${name} 变了`);
  }
  for (const name of before) if (!after.includes(name)) out.push(`${id}/${name} 没了`);
  fs.rmSync(then, {recursive: true, force: true});
  fs.mkdirSync(then, {recursive: true});
  for (const name of after) fs.copyFileSync(path.join(now, name), path.join(then, name));
  return out;
};

const chrome = [process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome'].find(p => p && fs.existsSync(p));
assert(chrome, 'Chrome not found; set CHROME_PATH');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'deck-check-'));
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--window-size=1920,1080', 'about:blank'], {stdio: 'ignore'});

// Port 0 lets Chrome pick a free port, so two checks can run at once without meeting.
let target;
for (let i = 0; i < 300 && !target; i++) {  // up to a minute: a fresh CI runner can be slow to start Chrome
  try {
    const port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0];
    target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page');
  } catch { await sleep(200); }
}
assert(target, 'Chrome did not start');
const ws = new WebSocket(target.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.onmessage = e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m.result ?? m.error); pending.delete(m.id); } };
await new Promise(r => { ws.onopen = r; });
const send = (method, params = {}) => new Promise(r => { pending.set(++id, r); ws.send(JSON.stringify({id, method, params})); });
const run = async expression => {
  const r = await send('Runtime.evaluate', {expression, returnByValue: true, awaitPromise: true});
  assert(!r.exceptionDetails, JSON.stringify(r.exceptionDetails));
  return r.result?.value;
};
const open = async url => {
  await send('Page.navigate', {url});
  for (let i = 0; i < 100; i++) {
    await sleep(200);
    const state = await send('Runtime.evaluate', {expression: `document.readyState === 'complete' && location.href`, returnByValue: true});
    if (state.result?.value && decodeURI(state.result.value).split('#')[0] === decodeURI(url).split('#')[0]) return sleep(300);
  }
  throw new Error('Page did not load: ' + url);
};
const next = async () => {
  for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', {type, key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39});
  await sleep(800);
};

const OVERFLOW = `(() => {
  const out = [];
  const area = document.getElementById('deckStage').getBoundingClientRect();
  document.querySelector('#deckStage .slide.active').querySelectorAll('*').forEach(e => {
    if (e.closest('.wire') || e.classList.contains('ln')) return;
    const b = e.getBoundingClientRect();
    if (!b.width) return;
    if (b.left < area.left - 1 || b.top < area.top - 1 || b.right > area.right + 1 || b.bottom > area.bottom + 1) out.push('outside: ' + e.textContent.slice(0, 24));
    if (e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0 && getComputedStyle(e).display !== 'inline') out.push('overflow: ' + e.textContent.slice(0, 24));
  });
  return out;
})()`;

const INTERACT = `(async () => {
  await document.fonts.ready;
  const stage = document.getElementById('deckStage');
  const links = [...stage.querySelectorAll('a.ide')];
  const quizzes = [...stage.querySelectorAll('.quiz')].map(q => {
    const buttons = q.querySelectorAll('button');
    [...buttons].forEach(b => b.click());
    buttons[Number(q.dataset.right)].click();
    return buttons[Number(q.dataset.right)].className === 'yes';
  });
  const picks = [...stage.querySelectorAll('.pick')].map(c => {
    const lines = c.querySelectorAll('.ln');
    lines[Number(c.dataset.bug) - 1].click();
    return lines[Number(c.dataset.bug) - 1].classList.contains('yes');
  });
  // Every switch combination must give what Python gives; the page must end as it started.
  const rule = {and: (a, b) => a && b, or: (a, b) => a || b, not: a => !a};
  const gates = [...stage.querySelectorAll('.gate')].map(g => {
    const inputs = [...g.querySelectorAll('button')], out = g.querySelector('b'), read = e => e.textContent === 'True';
    const start = inputs.map(i => i.textContent);
    const combos = 2 ** inputs.length;
    let ok = true;
    for (let n = 0; n < combos; n++) {
      inputs.forEach((input, bit) => { if (read(input) !== Boolean(n >> bit & 1)) input.click(); });
      ok &&= read(out) === rule[g.dataset.op](...inputs.map(read));
    }
    inputs.forEach((input, i) => { if (input.textContent !== start[i]) input.click(); });
    return ok;
  });
  // Slots: filter what students type, then try many values for a real run afterwards.
  const live = [...stage.querySelectorAll('.slide')].flatMap((slide, page) => {
    const slots = [...slide.querySelectorAll('.slot')];
    if (!slots.length) return [];
    const outs = [...slide.querySelectorAll('[data-eval]')], link = slide.querySelector('a.ide');
    const start = slots.map(s => s.value);
    const put = (slot, value) => { slot.value = value; slot.dispatchEvent(new Event('input', {bubbles: true})); };
    const typed = (slot, text) => { put(slot, text); return slot.value; };
    // A value the page cannot work out stays as typed, is marked, shows a hint and makes every result '？'.
    // The IDE still gets what was typed: a number as it is, text escaped only as the language needs, which runs for real later.
    const tip = slide.querySelector('.slot-tip');
    const ide = () => new URL(link.href).searchParams.get(IDE.config.codeParam);
    const kept = (slot, text, shown = text) => typed(slot, text) === shown && !slot.classList.contains('bad') && tip.hidden;
    const raw = [];
    const marked = (slot, text) => {
      const ok = typed(slot, text) === text && slot.classList.contains('bad') && !tip.hidden && !tip.classList.contains('calm') && outs.every(o => o.textContent === '？');
      const kind = slot.dataset.kind === 'text' ? 'text' : 'number';
      if (['-5', '2.5', 'a"b', 'a\\\\b'].includes(text)) raw.push({code: ide(), text, kind});
      return ok && (kind === 'text' || ide().includes(text));
    };
    const filter = slots.every(slot => slot.dataset.kind === 'text'
      ? kept(slot, '一二三四五六七八九十一二') && marked(slot, 'a"b') && marked(slot, "a'b") && marked(slot, '“ab”') && marked(slot, '‘a’') && marked(slot, 'a\\\\b') && marked(slot, '一二三四五六七八九十一二三')
        && kept(slot, '😀'.repeat(12)) && marked(slot, '😀'.repeat(13))
      : kept(slot, '12') && marked(slot, '1a2') && kept(slot, '007', '7') && kept(slot, '０７', '7') && marked(slot, '-5')
        && marked(slot, '2.5') && marked(slot, '12345') && kept(slot, '9999'));
    put(slots[0], '');
    // An empty box is not a mistake: the results wait and an amber hint, not a red one, says to fill it.
    const waits = outs.every(o => o.textContent === '？') && !tip.hidden && tip.classList.contains('calm') && !slots[0].classList.contains('bad');
    slots.forEach((s, i) => put(s, start[i]));
    const shown = outs.map(o => o.textContent);
    const numbers = ['0', '1', '2', '3', '5', '7', '10', '17', '59', '60', '99', '100', '999', '9999'];
    const words = ['你好', 'Hi there', '  两边空格  ', 'a+b=c', "x = 1", 'why??!', 'a{1}', '😀🎉', '测'.repeat(12), 'Hello, Py!'];
    let combos = [[]];
    for (const slot of slots) combos = combos.flatMap(c => (slot.dataset.kind === 'text' ? words : numbers).map(v => [...c, v]));
    const cases = combos.map(values => {
      values.forEach((v, i) => put(slots[i], v));
      return {code: new URL(link.href).searchParams.get(IDE.config.codeParam), outputs: outs.filter(o => !o.classList.contains('skip')).map(o => o.textContent)};
    });
    const longest = combos.map((values, i) => [values, cases[i].outputs.join('').length]).sort((x, y) => y[1] - x[1])[0][0];
    put(slots[0], slots[0].dataset.kind === 'text' ? '测' : '1');
    dispatchEvent(new Event('beforeprint'));
    const printed = slots.every((s, i) => s.value === start[i]) && outs.every((o, i) => o.textContent === shown[i]);
    dispatchEvent(new Event('afterprint'));
    return [{page: page + 1, filter, waits, printed, cases, raw, slots: slots.length, longest, few: slots.length <= 2}];
  });
  const before = links[0].href;
  const select = document.querySelector('#ide-fields select');
  let changed = !select;
  if (select) {
    const first = select.value;
    select.value = select.options[1].value; select.onchange();
    changed = links[0].href !== before;
    select.value = first; select.onchange();
  }
  const shell = {};
  const show = i => document.querySelectorAll('.thumb')[i].click();
  shell.thumbs = document.querySelectorAll('.thumb').length === document.querySelectorAll('#deckStage .slide').length;
  const codePage = [...stage.querySelectorAll('.slide')].findIndex(s => s.querySelector('pre.code .ln'));
  show(codePage);
  shell.thumbJump = document.getElementById('counter').textContent.startsWith((codePage + 1) + ' /');
  shell.thumbOn = document.querySelectorAll('.thumb.on').length === 1;
  shell.ideHasPageCode = Boolean(new URL(document.getElementById('ide-quick').href).searchParams.get(IDE.config.codeParam).trim());
  const slider = document.getElementById('slider');
  slider.value = 3; slider.dispatchEvent(new Event('input'));
  shell.slider = document.getElementById('counter').textContent.startsWith('3 /');
  shell.segOn = document.querySelectorAll('.seg.on').length === 1 && document.querySelectorAll('.seg.done').length === 2;
  const chips = [...document.querySelectorAll('#chips button')];
  chips.at(-1).click();
  shell.chip = chips.at(-1).classList.contains('on') && document.querySelector('#deckStage .slide.active').dataset.chapter === chips.at(-1).textContent;
  const jump = document.getElementById('jump');
  jump.value = 2; jump.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
  shell.jump = document.getElementById('counter').textContent.startsWith('2 /');
  const stageBox = () => document.getElementById('deckStage').getBoundingClientRect();
  const before2 = stageBox();
  document.body.classList.contains('thumbs-open') || document.getElementById('toggle-thumbs').click();
  const open = stageBox();
  document.getElementById('toggle-thumbs').click();
  const closed = stageBox();
  shell.stageGrows = closed.width > open.width && before2.left >= 232;
  document.getElementById('toggle-thumbs').click();
  const rail = document.getElementById('thumbs').getBoundingClientRect(), barBox = document.getElementById('controls').getBoundingClientRect();
  shell.noOverlap = stageBox().left >= rail.right - 1 && stageBox().bottom <= barBox.top + 1;
  shell.coverStaysWide = document.querySelector('.thumb .cover-row b').getBoundingClientRect().height < 40;
  shell.thumbsHideAnswers = [...document.querySelectorAll('.thumb .slide[data-steps]')].every(s => s.dataset.at === '1');
  const stepped = [...stage.querySelectorAll('.slide')].findIndex(s => s.dataset.steps);
  show(stepped);
  dispatchEvent(new Event('beforeprint'));
  shell.printShowsAll = Boolean(stage.querySelector('.quiz .yes')) && stage.querySelector('.slide.active').dataset.at === stage.querySelector('.slide.active').dataset.steps;
  dispatchEvent(new Event('afterprint'));
  shell.printLeavesNoAnswers = !stage.querySelector('.quiz .yes') && stage.querySelector('.slide.active').dataset.at === '1';
  const lastPage = [...stage.querySelectorAll('.slide')].at(-1);
  shell.thanksLast = lastPage.classList.contains('thanks') && lastPage.querySelector('.gh-link')?.href.startsWith('https://') && lastPage.querySelector('.gh-link').target === '_blank' && Boolean(lastPage.querySelector('.go-next'));
  shell.noLigatures = [document.body, ...stage.querySelectorAll('pre.code')].every(e => getComputedStyle(e).fontVariantLigatures === 'none');
  shell.ids = new Set([...document.querySelectorAll('[id]')].map(e => e.id)).size === document.querySelectorAll('[id]').length;
  return {
    shell,
    font: [400, 700, 800].every(w => document.fonts.check(w + ' 40px "JetBrains Mono"')),
    badLinks: links.filter(a => !a.href.startsWith('https://') || a.target !== '_blank' || !new URL(a.href).searchParams.get(IDE.config.codeParam)).length,
    links: links.length, quizzes, picks, gates, live, changed
  };
})()`;

const RUN_PYTHON = `
import contextlib, io, json, sys
for case in json.load(sys.stdin):
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            exec(case['code'], {})
        got = out.getvalue().splitlines()
    except Exception as e:
        got = out.getvalue().splitlines() + [type(e).__name__]
    assert got == case['outputs'], (case, got)
`;

// Values the page itself refuses still go to the IDE: numbers must compile, text must print exactly as typed.
const RUN_RAW = `
import contextlib, io, json, sys
for case in json.load(sys.stdin):
    if case['kind'] == 'text':
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(case['code'], {})
        assert case['text'] in out.getvalue(), (case, out.getvalue())
    else:
        compile(case['code'], 'ide', 'exec')
`;

// C++ divides by zero without a message, so those cases are left to the page text; the rest must match g++ or clang.
function buildCpp(code) {
  const exe = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'live-')), 'a.out');
  const whole = code.includes('main(') ? code : `#include <iostream>\nusing namespace std;\nint main() {\n${code}\n}\n`;
  execFileSync(process.env.CXX || 'c++', ['-std=c++11', '-x', 'c++', '-', '-o', exe], {input: whole});
  return exe;
}
function runCpp(cases) {
  for (const c of cases.filter(c => !c.outputs.includes('除数不能是 0'))) {
    const out = execFileSync(buildCpp(c.code)).toString();
    assert.deepEqual(out.split('\n').filter((l, i, all) => i < all.length - 1 || l), c.outputs, c.code);
  }
}
function runCppRaw(cases) {
  for (const c of cases) {
    const exe = buildCpp(c.code);
    if (c.kind === 'text') assert(execFileSync(exe).toString().includes(c.text), c.code);
  }
}

const key = async (name, code = name) => {
  await send('Input.dispatchKeyEvent', {type: 'keyDown', key: name, code, text: name.length === 1 ? name : undefined});
  await send('Input.dispatchKeyEvent', {type: 'keyUp', key: name, code});
};

// Every result must equal real Python; real keys must type into the slot, not turn the page.
async function checkLive(live, dir) {
  assert(live.filter && live.waits && live.printed && live.few, `Slot failed on page ${live.page}`);
  assert.equal(live.raw.length, 2 * live.slots, `Slot values were not tried in the IDE on page ${live.page}`);
  if (JSON.parse(fs.readFileSync('site.json', 'utf8')).language === 'python') {
    execFileSync('python3', ['-c', RUN_PYTHON], {input: JSON.stringify(live.cases)});
    execFileSync('python3', ['-c', RUN_RAW], {input: JSON.stringify(live.raw)});
  } else {
    runCpp(live.cases);
    runCppRaw(live.raw);
  }
  const counter = `document.getElementById('counter').textContent`;
  await run(`location.hash = '#page-${live.page}'`);
  await sleep(300);
  await run(`document.querySelector('#deckStage .slide.active .slot').select()`);
  const page = await run(counter);
  const text = await run(`document.activeElement.dataset.kind === 'text'`);
  for (const name of ['1', ' ', 'r', 'f', 'g', 'b', 't', '2']) await key(name);
  for (const name of ['ArrowRight', 'ArrowLeft', 'ArrowDown', 'ArrowUp']) await key(name);
  const room = await run(`document.activeElement.maxLength`);
  const state = await run(`({counter: ${counter}, slot: document.activeElement.value, blank: document.getElementById('blank').hidden, full: Boolean(document.fullscreenElement)})`);
  assert.deepEqual(state, {counter: page, slot: '1 rfgbt2'.slice(0, room > 0 ? room : undefined), blank: true, full: false}, 'Typing in a slot reached the deck shortcuts');
  await run(`[...document.querySelectorAll('#deckStage .slide.active .slot')].forEach((s, i) => { s.value = ${JSON.stringify(live.longest)}[i]; s.dispatchEvent(new Event('input')); })`);
  const found = await run(OVERFLOW);
  assert.deepEqual(found, [], `Longest result overflows: ${found.join(' | ')}`);
  const shot = await send('Page.captureScreenshot', {format: 'png'});
  fs.writeFileSync(path.join(dir, `live-${live.page}.png`), Buffer.from(shot.data, 'base64'));
  await key('Enter');
  await key('PageDown');
  assert.notEqual(await run(counter), page, 'A clicker cannot leave a page with a focused slot');
}

// Code changes: read both versions from the built file with no deck.js, then play the change with real keys.
const VERSIONS = raw => `(() => {
  const doc = new DOMParser().parseFromString(${JSON.stringify(raw)}, 'text/html');
  const slides = [...doc.querySelectorAll('#deckStage .slide')];
  const lines = pre => [...pre.querySelectorAll('.ln')].map(l => l.textContent);
  return [...doc.querySelectorAll('pre.code.was')].map(old => ({page: slides.indexOf(old.closest('.slide')) + 1,
    before: lines(old), after: lines(old.nextElementSibling), at: old.nextElementSibling.dataset.change,
    whole: old.nextElementSibling.dataset.full ?? null}));
})()`;
const CHANGE_STATE = `(() => {
  const slide = document.querySelector('#deckStage .slide.active'), pre = slide.querySelector('pre.change');
  const seen = e => Number(getComputedStyle(e).opacity) > 0.5;
  const shown = [...pre.querySelectorAll('.ln')].filter(l => l.getBoundingClientRect().height > 1 && seen(l))
    .map(l => ([...l.querySelectorAll('.now, .then')].find(seen) || l).textContent);
  const thumb = document.querySelectorAll('.thumb')[[...document.querySelectorAll('#deckStage .slide')].indexOf(slide)];
  return {shown, at: slide.dataset.at, moving: pre.getAnimations({subtree: true}).length,
    ide: new URL(document.getElementById('ide-quick').href).searchParams.get(IDE.config.codeParam),
    marked: pre.classList.contains('new') && [...pre.querySelectorAll('.add, .edit')].every(l => getComputedStyle(l).backgroundColor !== 'rgba(0, 0, 0, 0)'),
    thumbOld: !thumb.querySelector('pre.change').classList.contains('new'),
    // a change line clips what does not fit, so the visible text must end inside its line
    clipped: [...pre.querySelectorAll('.ln')].filter(l => l.getBoundingClientRect().height > 1 && seen(l)).some(l => {
      const range = document.createRange();
      range.selectNodeContents([...l.querySelectorAll('.now, .then')].find(seen) || l);
      return range.getBoundingClientRect().right > l.getBoundingClientRect().right + 1;
    })};
})()`;
const ALGO_STATE = `(() => {
  const box = document.querySelector('#deckStage .slide.active .algo'), player = box.player;
  const data = JSON.parse(box.dataset.trace), step = data.steps[player.at];
  const bars = [...box.querySelectorAll('.algo-live .algo-bar-item')].sort((x, y) => parseFloat(x.style.left) - parseFloat(y.style.left))
    .map(b => Number(b.querySelector('b').textContent));
  const lines = [...box.closest('.slide').querySelectorAll('pre.code:not(.was) .ln')], row = step.line - (data.first || 1) + 1;
  return {at: player.at, total: data.steps.length, playing: box.dataset.playing === '1', speed: box.dataset.speed,
    bars, want: step.list || null, run: lines.findIndex(l => l.classList.contains('run')) + 1 || null,
    line: step.line && row >= 1 && row <= lines.length ? row : null,
    say: box.querySelector('.algo-live .algo-say').textContent, page: document.getElementById('counter').textContent,
    playOff: box.querySelector('.algo-play').disabled, frames: box.querySelectorAll('.algo-film figure').length,
    film: getComputedStyle(box.querySelector('.algo-film')).display !== 'none', live: getComputedStyle(box.querySelector('.algo-live')).display !== 'none'};
})()`;
// Play, pause, step, restart and speed work by button and by key; arrows still turn pages; reduced motion never plays.
async function checkAlgo(page, dir) {
  const shot = async name => fs.writeFileSync(path.join(dir, `algo-${page}-${name}.png`), Buffer.from((await send('Page.captureScreenshot', {format: 'png'})).data, 'base64'));
  const where = `Algorithm demo on page ${page}`;
  const press = what => run(`document.querySelector('#deckStage .slide.active .algo [data-${what}]').click()`);
  await run(`location.hash = '#page-${page}'`);
  await sleep(400);
  let state = await run(ALGO_STATE);
  assert(state.at === 0 && !state.playing && state.run === null && state.say, `${where} does not start at its first step`);
  await shot('1-start');
  await press('do="next"');
  state = await run(ALGO_STATE);
  assert(state.at === 1 && state.run === state.line, `${where}: the next button does not step or light the code line`);
  await press('do="back"');
  assert.equal((await run(ALGO_STATE)).at, 0, `${where}: the back button does not step back`);
  await key('.');
  assert.equal((await run(ALGO_STATE)).at, 1, `${where}: the . key does not step`);
  await key(',');
  assert.equal((await run(ALGO_STATE)).at, 0, `${where}: the , key does not step back`);
  // Walk every step: the bars are the list the program had, the lit line is the line it ran, and the words make sense.
  const middle = Math.floor(state.total / 2);
  for (let at = 1; at < state.total; at++) {
    await press('do="next"');
    state = await run(ALGO_STATE);
    assert(state.at === at && state.run === state.line, `${where}: step ${at + 1} lights the wrong line`);
    if (state.want) assert.deepEqual(state.bars, state.want, `${where}: step ${at + 1} shows other numbers than the program had`);
    assert(state.say && !/undefined|NaN|null/.test(state.say), `${where}: step ${at + 1} says "${state.say}"`);
    if (at === middle) { await sleep(500); await shot('2-middle'); }
  }
  await sleep(500);
  await shot('3-end');
  await key('0');
  assert.equal((await run(ALGO_STATE)).at, 0, `${where}: the 0 key does not restart`);
  await press('speed="fast"');
  await key('p');
  assert((await run(ALGO_STATE)).playing, `${where}: P does not play`);
  await sleep(1500);
  await key('p');
  state = await run(ALGO_STATE);
  assert(!state.playing && state.at >= 2 && state.speed === 'fast', `${where}: playing fast did not move on, or P did not pause`);
  const paused = state.at;
  await sleep(900);
  assert.equal((await run(ALGO_STATE)).at, paused, `${where} keeps going after pause`);
  await key('s');
  assert.equal((await run(ALGO_STATE)).speed, 'slow', `${where}: S does not change the speed`);
  await press('speed="mid"');
  await press('do="reset"');
  await press('do="play"');
  await sleep(300);
  const before = await run(ALGO_STATE);
  await key('ArrowRight', 'ArrowRight');
  await sleep(300);
  assert((await run(`document.getElementById('counter').textContent`)) !== before.page, `${where}: the arrow key does not turn the page`);
  await key('ArrowLeft', 'ArrowLeft');
  await sleep(300);
  state = await run(ALGO_STATE);
  assert(before.playing && !state.playing, `${where} keeps playing after the page was turned`);
  await send('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
  await press('do="reset"');
  await key('p');
  await sleep(1300);
  state = await run(ALGO_STATE);
  assert(state.playOff && !state.playing && state.at === 0, `${where} plays by itself with reduced motion`);
  await key('.');
  assert.equal((await run(ALGO_STATE)).at, 1, `${where} cannot be stepped with reduced motion`);
  await send('Emulation.setEmulatedMedia', {features: []});
  await press('do="reset"');
  await send('Emulation.setEmulatedMedia', {media: 'print'});
  state = await run(ALGO_STATE);
  assert(state.film && !state.live && state.frames >= 3, `${where}: print does not show the key steps`);
  await run(`document.querySelector('#deckStage .slide.active').scrollIntoView()`);
  await shot('4-print');
  await send('Emulation.setEmulatedMedia', {media: ''});
}
async function checkChange(change, dir) {
  const shot = async name => fs.writeFileSync(path.join(dir, `change-${change.page}-${name}.png`), Buffer.from((await send('Page.captureScreenshot', {format: 'png'})).data, 'base64'));
  const at = Number(change.at), where = `Code change on page ${change.page}`;
  await run(`location.hash = '#page-${change.page}'`);
  await sleep(400);
  for (let i = 1; i < at - 1; i++) { await key('ArrowRight'); await sleep(50); }
  let state = await run(CHANGE_STATE);
  assert.deepEqual(state.shown, change.before, `${where} does not start with the old version`);
  assert(state.thumbOld, `${where}: the thumbnail gives the new version away`);
  assert(!state.clipped, `${where}: a line of the old version is cut off at the right, widen the editor`);
  await shot('1-old');
  await key('ArrowRight');
  await sleep(150);
  assert((await run(CHANGE_STATE)).moving > 0, `${where} does not play when going forward`);
  await shot('2-moving');
  await sleep(900);
  state = await run(CHANGE_STATE);
  assert.deepEqual(state.shown, change.after, `${where} does not end with the new version`);
  assert(state.marked && !state.moving && state.at === String(at), `${where}: new and edited lines are not marked`);
  // A page that shows some lines of a longer program (C++ often does) sends the whole new program.
  assert.equal(state.ide, change.whole ?? change.after.join('\n'), `${where}: the IDE must get the new version`);
  assert(!state.clipped, `${where}: a line of the new version is cut off at the right, widen the editor`);
  await shot('3-new');
  await key('ArrowLeft');
  await sleep(150);
  assert((await run(CHANGE_STATE)).moving > 0, `${where} does not play back when going back`);
  await sleep(900);
  assert.deepEqual((await run(CHANGE_STATE)).shown, change.before, `${where} does not go back to the old version`);
  // Reduced motion: the same switch, at once.
  await send('Emulation.setEmulatedMedia', {features: [{name: 'prefers-reduced-motion', value: 'reduce'}]});
  await key('ArrowRight');
  state = await run(CHANGE_STATE);
  assert(!state.moving && JSON.stringify(state.shown) === JSON.stringify(change.after), `${where} animates with reduced motion`);
  await shot('4-reduced');
  await key('ArrowLeft');
  state = await run(CHANGE_STATE);
  assert(!state.moving && JSON.stringify(state.shown) === JSON.stringify(change.before), `${where} animates back with reduced motion`);
  await send('Emulation.setEmulatedMedia', {features: []});
  await run(`dispatchEvent(new Event('beforeprint'))`);
  state = await run(CHANGE_STATE);
  assert(!state.moving && state.marked && JSON.stringify(state.shown) === JSON.stringify(change.after), `${where}: print does not show the marked new version`);
  await run(`dispatchEvent(new Event('afterprint'))`);
  assert.deepEqual((await run(CHANGE_STATE)).shown, change.before, `${where}: after printing the page is not back where it was`);
}

const sum = {pages: 0, screens: 0, quizzes: 0, picks: 0, gates: 0, changes: 0, algos: 0, links: 0}, changedShots = [];
try {
  await send('Page.enable');
  // Locally, scrollbars fade in and out with timing and would mark screens as changed; on macOS they take no room anyway.
  if (!process.env.CI) await send('Emulation.setScrollbarsHidden', {hidden: true});
  await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
  for (const lesson of targets) {
   try {
    const dir = path.join('.preview', lesson.id);
    fs.rmSync(dir, {recursive: true, force: true});
    fs.mkdirSync(dir, {recursive: true});
    await open('file://' + encodeURI(path.resolve('dist', lesson.id, 'index.html')));
    assert.equal(await run('location.protocol'), 'file:');
    await measureRail();
    const total = await run(`document.querySelectorAll('#deckStage .slide').length`);
    const problems = [];
    let shots = 0;
    for (;;) {
      shots++;
      // Entry motion finishes first, so a screen is the same picture every run.
      await run(`Promise.all(document.getAnimations().filter(a => isFinite(a.effect.getComputedTiming().endTime)).map(a => a.finished.catch(() => {}))).then(() => true)`);
      const label = await run(`document.getElementById('counter').textContent`);
      const found = await run(OVERFLOW);
      if (found.length) problems.push(`${label}: ${found.join(' | ')}`);
      const shot = await send('Page.captureScreenshot', {format: 'png'});
      fs.writeFileSync(path.join(dir, `${String(shots).padStart(2, '0')}.png`), Buffer.from(shot.data, 'base64'));
      if (new RegExp(`^${total} / ${total}`).test(label) || shots > 200) break;
      await next();
    }
    assert.deepEqual(problems, [], problems.join('\n'));
    const result = await run(INTERACT);
    assert(result.font, 'JetBrains Mono did not load');
    assert.equal(result.badLinks, 0, 'Bad IDE link');
    assert(result.quizzes.length && result.quizzes.every(Boolean), 'Quiz answer not marked right');
    assert(result.picks.length && result.picks.every(Boolean), 'Bug hunt line not marked right');
    assert(result.gates.every(Boolean), 'Logic switch gave a wrong result');
    for (const live of result.live) await checkLive(live, dir);
    const changes = await run(VERSIONS(fs.readFileSync(path.resolve('dist', lesson.id, 'index.html'), 'utf8')));
    for (const change of changes) await checkChange(change, dir);
    const algos = await run(`[...document.querySelectorAll('#deckStage .slide')].flatMap((s, i) => s.querySelector('.algo') ? [i + 1] : [])`);
    for (const page of algos) await checkAlgo(page, dir);
    assert(result.changed, 'IDE settings did not change links');
    assert.deepEqual(Object.entries(result.shell).filter(([, ok]) => !ok), [], 'Workspace control failed');
    await send('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
    await open('file://' + encodeURI(path.resolve('dist', 'index.html')));
    assert(await run('document.documentElement.scrollWidth <= innerWidth'), 'Home page scrolls sideways on a phone');
    assert(await run(`(() => { const i = document.getElementById('name'); i.value = '小红'; i.oninput(); return document.getElementById('say').textContent.endsWith('小红'); })()`), 'Home program does not answer');
    const homeShot = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true});
    fs.writeFileSync(path.join('.preview', 'home-phone.png'), Buffer.from(homeShot.data, 'base64'));
    await open('file://' + encodeURI(path.resolve('dist', lesson.id, 'index.html')) + '#page-2');
    const phone = await run(`(() => { const s = document.getElementById('deckStage').getBoundingClientRect(), b = document.getElementById('controls').getBoundingClientRect(); return {fits: s.left >= -1 && s.right <= innerWidth + 1 && s.bottom <= b.top + 1 && s.width > innerWidth - 2, wide: document.documentElement.scrollWidth <= innerWidth}; })()`);
    assert(phone.fits && phone.wide, 'Deck does not fit a phone');
    const deckShot = await send('Page.captureScreenshot', {format: 'png'});
    fs.writeFileSync(path.join('.preview', 'deck-phone.png'), Buffer.from(deckShot.data, 'base64'));
    await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
    pass(lesson.id);
    changedShots.push(...compareShots(lesson.id));
    for (const [k, n] of Object.entries({pages: total, screens: shots, quizzes: result.quizzes.length, picks: result.picks.length,
      gates: result.gates.length, changes: changes.length, algos: algos.length, links: result.links})) sum[k] += n;
   } catch (error) {
    console.error(`FAIL: ${lesson.id}`);
    error.message = `${lesson.id}: ${error.message}`;
    throw error;
   }
  }
  passShared();
  // One line when everything passed; the screens to look at are listed in a file, not here.
  if (!process.env.CI) fs.writeFileSync(path.join('.preview', 'changed.txt'), changedShots.join('\n') + (changedShots.length ? '\n' : ''));
  const look = process.env.CI ? '' : changedShots.length ? `; ${changedShots.length} screens differ from the last pass, see .preview/changed.txt` : '; no screen differs from the last pass';
  console.log(`PASS: ${scope}: ${targets.length} lesson(s), ${sum.pages} pages, ${sum.screens} screens, no overflow; ${sum.quizzes} quizzes, ${sum.picks} bug hunts, ${sum.gates} logic switches, ${sum.changes} code changes, ${sum.algos} algorithm demos, ${sum.links} IDE links${look}.`);
} finally {
  ws.close();
  proc.kill();
}
