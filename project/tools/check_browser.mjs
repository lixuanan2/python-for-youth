// Real Chrome over CDP on file://: every screen of each project's deck, the quizzes, the IDE links, and the map on a phone.
// Run in project/ after build.py:
//   node tools/check_browser.mjs              every project
//   node tools/check_browser.mjs tictactoe    only these projects (CI passes the ones a push changed)
// Screenshots land in .preview/; the ones that look different from the last local pass are listed in .preview/changed.txt,
// and this pass is kept in .check-shots/ for next time (not in Git). Set CHROME_PATH if Chrome is not in a usual place.
import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import zlib from 'node:zlib';

const site = JSON.parse(fs.readFileSync('site.json', 'utf8'));
const chosen = process.argv.slice(2);
const unknown = chosen.filter(name => !site.projects.includes(name));
assert(!unknown.length, `No such project: ${unknown.join(', ')}. Projects are: ${site.projects.join(' ')}`);
const projects = chosen.length ? site.projects.filter(name => chosen.includes(name)) : site.projects;
const chrome = [process.env.CHROME_PATH, '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  'C:/Program Files/Google/Chrome/Application/chrome.exe', '/usr/bin/google-chrome'].find(p => p && fs.existsSync(p));
assert(chrome, 'Chrome not found; set CHROME_PATH');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'project-check-'));
const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--no-first-run', '--window-size=1920,1080', 'about:blank'], {stdio: 'ignore'});
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
// Screens against the last local pass: same pixels, same picture. Lists what changed, then keeps this pass.
const SHOTS = '.check-shots';
const compareShots = name => {
  if (process.env.CI) return [];
  const pngs = dir => fs.existsSync(dir) ? fs.readdirSync(dir, {recursive: true}).filter(f => f.endsWith('.png')).sort() : [];
  const now = path.join('.preview', name), then = path.join(SHOTS, name);
  const before = new Set(pngs(then)), after = pngs(now), out = [];
  for (const f of after) {
    if (!before.has(f)) out.push(`${name}/${f} 新的`);
    else if (!samePicture(path.join(now, f), path.join(then, f), f.startsWith('slides') ? railWidth : 0)) out.push(`${name}/${f} 变了`);
  }
  for (const f of before) if (!after.includes(f)) out.push(`${name}/${f} 没了`);
  fs.rmSync(then, {recursive: true, force: true});
  for (const f of after) { fs.mkdirSync(path.dirname(path.join(then, f)), {recursive: true}); fs.copyFileSync(path.join(now, f), path.join(then, f)); }
  return out;
};
const sum = {pages: 0, screens: 0, quizzes: 0, ide: 0, sheets: 0}, changedShots = [];

try {
  await send('Page.enable');
  // Locally, scrollbars fade in and out with timing and would mark screens as changed; on macOS they take no room anyway.
  if (!process.env.CI) await send('Emulation.setScrollbarsHidden', {hidden: true});
  for (const name of projects) {
   try {
    for (const stage of ['slides']) {
      const dir = path.join('.preview', name, stage);
      fs.rmSync(dir, {recursive: true, force: true});
      fs.mkdirSync(dir, {recursive: true});
      await send('Emulation.setDeviceMetricsOverride', {width: 1920, height: 1080, deviceScaleFactor: 0.6, mobile: false});
      await open(path.join('dist', name, stage, 'index.html'));
      assert(await run(`document.fonts.ready.then(() => document.fonts.check('700 40px "JetBrains Mono"'))`), 'JetBrains Mono did not load');
      await measureRail();
      const total = await run(`document.querySelectorAll('#deckStage .slide').length`);
      const problems = [];
      let screens = 0;
      for (;;) {
        screens++;
        // Entry motion finishes first, so a screen is the same picture every run.
        await run(`Promise.all(document.getAnimations().filter(a => isFinite(a.effect.getComputedTiming().endTime)).map(a => a.finished.catch(() => {}))).then(() => true)`);
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
        // Each IDE names its own parameter (JupyterLite code=, cpp.sh source=); any non-empty one carries the program.
        const ide = [...stage.querySelectorAll('a.ide')];
        const bad = ide.filter(a => !a.href.startsWith('https://') || a.target !== '_blank' || ![...new URL(a.href).searchParams.values()].some(v => v.trim())).length;
        return {quizzes, ide: ide.length, bad};
      })()`);
      assert(result.quizzes.every(Boolean), `${name}/${stage}: a quiz does not mark its right answer`);
      assert.equal(result.bad, 0, `${name}/${stage}: an IDE link carries no code`);
      sum.pages += total; sum.screens += screens; sum.quizzes += result.quizzes.length; sum.ide += result.ide;
    }
    // The map, the development document and the module index are read on phones too: nothing may scroll sideways.
    fs.rmSync(path.join('.preview', name, 'pages'), {recursive: true, force: true});
    fs.mkdirSync(path.join('.preview', name, 'pages'), {recursive: true});
    for (const page of [path.join('dist', name, 'index.html'), path.join('dist', name, 'guide.html'), path.join('dist', 'index.html')]) {
      await send('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
      await open(page);
      assert(await run('document.documentElement.scrollWidth <= innerWidth'), `${page} scrolls sideways on a phone`);
      await send('Emulation.setDeviceMetricsOverride', {width: 1280, height: 900, deviceScaleFactor: 1, mobile: false});
      await open(page);
      const r = await send('Page.captureScreenshot', {format: 'png', captureBeyondViewport: true, clip: {x: 0, y: 0, width: 1280, height: await run('document.documentElement.scrollHeight'), scale: 1}});
      fs.writeFileSync(path.join('.preview', name, 'pages', page.replaceAll(path.sep, '-').replace('.html', '.png')), Buffer.from(r.data, 'base64'));
      sum.sheets++;
    }
    changedShots.push(...compareShots(name));
   } catch (error) {
    console.error(`FAIL: ${name}`);
    error.message = `${name}: ${error.message}`;
    throw error;
   }
  }
  if (!process.env.CI) fs.writeFileSync(path.join('.preview', 'changed.txt'), changedShots.join('\n') + (changedShots.length ? '\n' : ''));
  const look = process.env.CI ? '' : changedShots.length ? `; ${changedShots.length} screens differ from the last pass, see .preview/changed.txt` : '; no screen differs from the last pass';
  console.log(`PASS: ${projects.join(' ')}: ${sum.pages} pages, ${sum.screens} screens, no overflow; ${sum.quizzes} quizzes, ${sum.ide} IDE links; ${sum.sheets} pages fit a phone${look}.`);
} finally {
  ws.close();
  proc.kill();
}
