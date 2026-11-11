// Real Chrome over CDP on file://: every screen of every stage deck, the quizzes, the IDE links, and the map on a phone.
// Run in project/ after build.py: node tools/check_browser.mjs
// Screenshots land in .preview/. Set CHROME_PATH if Chrome is not in a usual place.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const site = JSON.parse(fs.readFileSync('site.json', 'utf8'));
const chrome = [process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome'].find(p => p && fs.existsSync(p));
assert(chrome, 'Chrome not found; set CHROME_PATH');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'project-check-'));
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--window-size=1920,1080', 'about:blank'], {stdio: 'ignore'});
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
const open = async file => {
  await send('Page.navigate', {url: 'file://' + encodeURI(path.resolve(file))});
  for (let i = 0; i < 100; i++) { await sleep(200); if (await run(`document.readyState === 'complete'`)) return sleep(400); }
  throw new Error('Page did not load: ' + file);
};
const shot = async file => fs.writeFileSync(file, Buffer.from((await send('Page.captureScreenshot', {format: 'png'})).data, 'base64'));

// The same test the basics check uses: nothing on a screen may stick out of the stage or overflow its box.
const OVERFLOW = `(() => {
  const out = [];
  const area = document.getElementById('deckStage').getBoundingClientRect();
  document.querySelector('#deckStage .slide.active').querySelectorAll('*').forEach(e => {
    if (e.classList.contains('ln')) return;
    const b = e.getBoundingClientRect();
    if (!b.width) return;
    if (b.left < area.left - 1 || b.top < area.top - 1 || b.right > area.right + 1 || b.bottom > area.bottom + 1) out.push('outside: ' + e.textContent.slice(0, 24));
    if (e.scrollWidth > e.clientWidth + 1 && e.clientWidth > 0 && getComputedStyle(e).display !== 'inline') out.push('overflow: ' + e.textContent.slice(0, 24));
  });
  return out;
})()`;

try {
  await send('Page.enable');
  for (const name of site.projects) {
    const stages = fs.readdirSync(path.join('dist', name)).filter(d => /^stage\d+$/.test(d)).sort();
    for (const stage of stages) {
      const dir = path.join('.preview', name, stage);
      fs.rmSync(dir, {recursive: true, force: true});
      fs.mkdirSync(dir, {recursive: true});
      await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
      await open(path.join('dist', name, stage, 'index.html'));
      assert(await run(`document.fonts.ready.then(() => document.fonts.check('700 40px "JetBrains Mono"'))`), 'JetBrains Mono did not load');
      const total = await run(`document.querySelectorAll('#deckStage .slide').length`);
      const problems = [];
      let screens = 0;
      for (;;) {
        screens++;
        const label = await run(`document.getElementById('counter').textContent`);
        const found = await run(OVERFLOW);
        if (found.length) problems.push(`${label}: ${found.join(' | ')}`);
        await shot(path.join(dir, `${String(screens).padStart(2, '0')}.png`));
        if (new RegExp(`^${total} / ${total}`).test(label) || screens > 120) break;
        for (const type of ['keyDown', 'keyUp']) await send('Input.dispatchKeyEvent', {type, key: 'ArrowRight', code: 'ArrowRight', windowsVirtualKeyCode: 39});
        await sleep(700);
      }
      assert.deepEqual(problems, [], `${name}/${stage}:\n` + problems.join('\n'));
      const result = await run(`(() => {
        const stage = document.getElementById('deckStage');
        const quizzes = [...stage.querySelectorAll('.quiz')].map(q => {
          const buttons = q.querySelectorAll('button');
          [...buttons].forEach(b => b.click());
          buttons[Number(q.dataset.right)].click();
          return buttons[Number(q.dataset.right)].className === 'yes';
        });
        const ide = [...stage.querySelectorAll('a.ide')];
        const bad = ide.filter(a => !a.href.startsWith('https://') || a.target !== '_blank' || !new URL(a.href).searchParams.get('code')).length;
        return {quizzes, ide: ide.length, bad};
      })()`);
      assert(result.quizzes.every(Boolean), `${name}/${stage}: a quiz does not mark its right answer`);
      assert.equal(result.bad, 0, `${name}/${stage}: an IDE link carries no code`);
      console.log(`PASS: ${name}/${stage}: ${total} pages, ${screens} screens, no overflow; ${result.quizzes.length} quiz(zes), ${result.ide} IDE links.`);
    }
    // The map and the module index are read on phones too: nothing may scroll sideways.
    for (const page of [path.join('dist', name, 'index.html'), path.join('dist', 'index.html')]) {
      await send('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
      await open(page);
      assert(await run('document.documentElement.scrollWidth <= innerWidth'), `${page} scrolls sideways on a phone`);
      await send('Emulation.setDeviceMetricsOverride', {width: 1280, height: 900, deviceScaleFactor: 1, mobile: false});
      await open(page);
      const r = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true, clip: {x: 0, y: 0, width: 1280, height: await run('document.documentElement.scrollHeight'), scale: 1}});
      fs.writeFileSync(path.join('.preview', page.replaceAll(path.sep, '-').replace('.html', '.png')), Buffer.from(r.data, 'base64'));
      console.log(`PASS: ${page} fits a phone`);
    }
  }
} finally {
  ws.close();
  proc.kill();
}
