// Real Chrome over CDP on file://: render every page and step, then exercise each interaction.
// Run from the repository root: node tools/check_browser.mjs
// Screenshots land in .preview/. Set CHROME_PATH if Chrome is not in a usual place.
import assert from 'node:assert/strict';
import {execFileSync, spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const chrome = [process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome'].find(p => p && fs.existsSync(p));
assert(chrome, 'Chrome not found; set CHROME_PATH');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'deck-check-'));
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--window-size=1920,1080', 'about:blank'], {stdio: 'ignore'});

// Port 0 lets Chrome pick a free port, so two checks can run at once without meeting.
let target;
for (let i = 0; i < 75 && !target; i++) {
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
    const tip = slide.querySelector('.slot-tip');
    const kept = (slot, text, shown = text) => typed(slot, text) === shown && !slot.classList.contains('bad') && tip.hidden;
    const marked = (slot, text) => typed(slot, text) === text && slot.classList.contains('bad') && !tip.hidden
      && outs.every(o => o.textContent === '？') && !new URL(link.href).searchParams.get(IDE.config.codeParam).includes(text);
    const filter = slots.every(slot => slot.dataset.kind === 'text'
      ? kept(slot, '一二三四五六七八九十一二') && marked(slot, 'a"b') && marked(slot, 'a\\\\b') && marked(slot, '一二三四五六七八九十一二三')
        && kept(slot, '😀'.repeat(12)) && marked(slot, '😀'.repeat(13))
      : kept(slot, '12') && marked(slot, '1a2') && kept(slot, '007', '7') && kept(slot, '０７', '7') && marked(slot, '-5')
        && marked(slot, '2.5') && marked(slot, '12345') && kept(slot, '9999'));
    put(slots[0], '');
    const waits = outs.every(o => o.textContent === '？');
    slots.forEach((s, i) => put(s, start[i]));
    const shown = outs.map(o => o.textContent);
    const numbers = ['0', '1', '2', '3', '5', '7', '10', '17', '59', '60', '99', '100', '999', '9999'];
    const words = ['你好', 'Hi there', '  两边空格  ', 'a+b=c', "it's", '😀🎉', '测'.repeat(12), 'Hello, Py!'];
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
    return [{page: page + 1, filter, waits, printed, cases, longest, few: slots.length <= 2}];
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

// C++ divides by zero without a message, so those cases are left to the page text; the rest must match g++ or clang.
function runCpp(cases) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'live-'));
  for (const c of cases.filter(c => !c.outputs.includes('除数不能是 0'))) {
    const code = c.code.includes('main(') ? c.code : `#include <iostream>\nusing namespace std;\nint main() {\n${c.code}\n}\n`;
    const exe = path.join(dir, 'a.out');
    execFileSync(process.env.CXX || 'c++', ['-std=c++11', '-x', 'c++', '-', '-o', exe], {input: code});
    assert.deepEqual(execFileSync(exe).toString().split('\n').filter((l, i, all) => i < all.length - 1 || l), c.outputs, code);
  }
}

const key = async (name, code = name) => {
  await send('Input.dispatchKeyEvent', {type: 'keyDown', key: name, code, text: name.length === 1 ? name : undefined});
  await send('Input.dispatchKeyEvent', {type: 'keyUp', key: name, code});
};

// Every result must equal real Python; real keys must type into the slot, not turn the page.
async function checkLive(live, dir) {
  assert(live.filter && live.waits && live.printed && live.few, `Slot failed on page ${live.page}`);
  if (JSON.parse(fs.readFileSync('site.json', 'utf8')).language === 'python') execFileSync('python3', ['-c', RUN_PYTHON], {input: JSON.stringify(live.cases)});
  else runCpp(live.cases);
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

try {
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
  const lessons = JSON.parse(fs.readFileSync('course.json', 'utf8'));
  // LESSON=09-max-min checks one lesson while working on it; run without it before committing.
  for (const lesson of lessons.filter(l => l.id && (!process.env.LESSON || l.id === process.env.LESSON))) {
    const dir = path.join('.preview', lesson.id);
    fs.rmSync(dir, {recursive: true, force: true});
    fs.mkdirSync(dir, {recursive: true});
    await open('file://' + encodeURI(path.resolve('dist', lesson.id, 'index.html')));
    assert.equal(await run('location.protocol'), 'file:');
    const total = await run(`document.querySelectorAll('#deckStage .slide').length`);
    const problems = [];
    let shots = 0;
    for (;;) {
      shots++;
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
    console.log(`PASS: ${lesson.id}: ${total} pages, ${shots} screens, no overflow; thumbnails, timeline, chapters and jump work; ${result.quizzes.length} quizzes, ${result.picks.length} bug hunts, ${result.gates.length} logic switches, ${result.links} IDE links.`);
  }
} finally {
  ws.close();
  proc.kill();
}
