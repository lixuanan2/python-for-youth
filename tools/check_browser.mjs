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
const port = 9344, sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'deck-check-'));
const proc = spawn(chrome, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--no-first-run', '--window-size=1920,1080', 'about:blank'], {stdio: 'ignore'});

let target;
for (let i = 0; i < 50 && !target; i++) {
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch { await sleep(200); }
}
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
const next = async () => {
  for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', {type, key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39});
  await sleep(800);
};

const OVERFLOW = `(() => {
  const out = [];
  document.querySelector('.slide.active').querySelectorAll('*').forEach(e => {
    if (e.closest('.wire') || e.classList.contains('ln')) return;
    const b = e.getBoundingClientRect();
    if (!b.width) return;
    if (b.left < -1 || b.top < -1 || b.right > 1921 || b.bottom > 1081) out.push('outside: ' + e.textContent.slice(0, 24));
    if (e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0 && getComputedStyle(e).display !== 'inline') out.push('overflow: ' + e.textContent.slice(0, 24));
  });
  return out;
})()`;

const INTERACT = `(async () => {
  await document.fonts.ready;
  const links = [...document.querySelectorAll('a.ide')];
  const quizzes = [...document.querySelectorAll('.quiz')].map(q => {
    const buttons = q.querySelectorAll('button');
    [...buttons].forEach(b => b.click());
    buttons[Number(q.dataset.right)].click();
    return buttons[Number(q.dataset.right)].className === 'yes';
  });
  const picks = [...document.querySelectorAll('.pick')].map(c => {
    const lines = c.querySelectorAll('.ln');
    lines[Number(c.dataset.bug) - 1].click();
    return lines[Number(c.dataset.bug) - 1].classList.contains('yes');
  });
  const before = links[0].href;
  const theme = document.getElementById('ide-theme');
  theme.value = 'JupyterLab Light'; theme.onchange();
  const changed = links[0].href !== before;
  theme.value = 'JupyterLab Dark'; theme.onchange();
  return {
    font: [400, 700, 800].every(w => document.fonts.check(w + ' 40px "JetBrains Mono"')),
    badLinks: links.filter(a => !a.href.startsWith('https://') || a.target !== '_blank' || !new URL(a.href).searchParams.get('code')).length,
    links: links.length, quizzes, picks, changed
  };
})()`;

try {
  await send('Page.enable');
  await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.5, mobile: false});
  const lessons = JSON.parse(fs.readFileSync('course.json', 'utf8'));
  for (const lesson of lessons) {
    const dir = path.join('.preview', lesson.id);
    fs.mkdirSync(dir, {recursive: true});
    await send('Page.navigate', {url: 'file://' + encodeURI(path.resolve('dist', lesson.id, 'index.html'))});
    await sleep(1500);
    assert.equal(await run('location.protocol'), 'file:');
    const total = await run(`document.querySelectorAll('.slide').length`);
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
    console.log(`PASS: ${lesson.id}: ${total} pages, ${shots} screens, no overflow; ${result.quizzes.length} quizzes, ${result.picks.length} bug hunts, ${result.links} IDE links.`);
  }
} finally {
  proc.kill();
}
