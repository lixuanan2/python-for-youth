// Screenshots against the last local pass, shared by basics/tools/check_browser.mjs and project/tools/check_browser.mjs
// (the project course imports this file and never changes it). Screens land in .preview/<name>/, the last pass is kept in
// .check-shots/<name>/; neither is in Git.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';

export const SHOTS = '.check-shots';

// Chrome compresses the same picture differently from run to run, so screens are compared by their pixels, not their bytes.
export const pixels = file => {
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
// rail on the left (rail px wide) is left out: its edge sits on a fraction of a pixel and its scroll position varies, and
// every thumbnail is a copy of a page that is compared full size anyway.
export const samePicture = (x, y, rail = 0) => {
  try {
    const a = pixels(x), b = pixels(y);
    if (a.width !== b.width || a.height !== b.height || a.bpp !== b.bpp) return false;
    const skip = rail * a.bpp, stride = a.width * a.bpp;
    for (let row = 0; row < a.data.length; row += stride)
      for (let i = row + skip; i < row + stride; i++) if (Math.abs(a.data[i] - b.data[i]) > 3) return false;
    return true;
  } catch { return false; }
};

// The screens of one lesson or project against the last pass (folders inside are followed): what changed, appeared or went
// away, as lines for .preview/changed.txt. Then this pass becomes the new baseline. railFor(file) gives the rail width to
// leave out of that screen. Locally only: CI has no last pass.
export const compareShots = (name, railFor = () => 0) => {
  if (process.env.CI) return [];
  const pngs = dir => fs.existsSync(dir) ? fs.readdirSync(dir, {recursive: true}).filter(f => f.endsWith('.png')).sort() : [];
  const now = path.join('.preview', name), then = path.join(SHOTS, name);
  const before = new Set(pngs(then)), after = pngs(now), out = [];
  for (const f of after) {
    if (!before.has(f)) out.push(`${name}/${f} 新的`);
    else if (!samePicture(path.join(now, f), path.join(then, f), railFor(f))) out.push(`${name}/${f} 变了`);
  }
  for (const f of before) if (!after.includes(f)) out.push(`${name}/${f} 没了`);
  fs.rmSync(then, {recursive: true, force: true});
  for (const f of after) { fs.mkdirSync(path.dirname(path.join(then, f)), {recursive: true}); fs.copyFileSync(path.join(now, f), path.join(then, f)); }
  return out;
};

// Leftovers: screenshots the tool did not write (taken by hand, or of something renamed) and baselines of what is gone.
// kept names what may stay at the top of .preview and .check-shots. Locally only.
export const clearStray = kept => {
  if (process.env.CI) return;
  const keep = new Set(kept);
  for (const dir of ['.preview', SHOTS]) {
    if (!fs.existsSync(dir)) continue;
    for (const name of fs.readdirSync(dir)) if (!keep.has(name)) fs.rmSync(path.join(dir, name), {recursive: true, force: true});
  }
};
