// Real Chrome over CDP on file://: render every page and step, then exercise each interaction.
// Run from the repository root: node tools/check_browser.mjs
// Screenshots land in .preview/. Set CHROME_PATH if Chrome is not in a usual place.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
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
  shell.thanksLast = [...stage.querySelectorAll('.slide')].at(-1).classList.contains('thanks');
  shell.noLigatures = [document.body, ...stage.querySelectorAll('pre.code')].every(e => getComputedStyle(e).fontVariantLigatures === 'none');
  shell.ids = new Set([...document.querySelectorAll('[id]')].map(e => e.id)).size === document.querySelectorAll('[id]').length;
  return {
    shell,
    font: [400, 700, 800].every(w => document.fonts.check(w + ' 40px "JetBrains Mono"')),
    badLinks: links.filter(a => !a.href.startsWith('https://') || a.target !== '_blank' || !new URL(a.href).searchParams.get(IDE.config.codeParam)).length,
    links: links.length, quizzes, picks, changed
  };
})()`;

try {
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
  const lessons = JSON.parse(fs.readFileSync('course.json', 'utf8'));
  for (const lesson of lessons.filter(l => l.id)) {
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
    console.log(`PASS: ${lesson.id}: ${total} pages, ${shots} screens, no overflow; thumbnails, timeline, chapters and jump work; ${result.quizzes.length} quizzes, ${result.picks.length} bug hunts, ${result.links} IDE links.`);
  }
} finally {
  ws.close();
  proc.kill();
}
