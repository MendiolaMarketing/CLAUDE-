// Usage: node render.mjs video out.mov   |  node render.mjs stills dir t1 t2 ... (seconds)
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const [mode, target, ...rest] = process.argv.slice(2);
const FPS = 24, WORKERS = 4;
const browser = await chromium.launch({ args: ['--force-color-profile=srgb'] });
async function openPage() {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
  await page.goto('file://' + path.join(here, 'reel.html'));
  await page.evaluate(() => window.ready);
  return page;
}
const b64 = s => Buffer.from(s.split(',')[1], 'base64');
if (mode === 'stills') {
  const page = await openPage();
  mkdirSync(target, { recursive: true });
  for (const s of rest) {
    const i = Math.round(parseFloat(s) * FPS);
    writeFileSync(path.join(target, `f_${String(i).padStart(4, '0')}.jpg`), b64(await page.evaluate(i => window.renderStill(i), i)));
  }
} else {
  const pages = await Promise.all(Array.from({ length: WORKERS }, openPage));
  const N = await pages[0].evaluate(() => window.FRAMES);
  // ProRes 4444 with alpha, 24 fps
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-alpha_bits', '16', '-vendor', 'apl0', '-qscale:v', '9', target],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const pending = new Map(); let next = 0, issued = 0; const t0 = Date.now();
  async function worker(page) {
    while (issued < N) {
      const i = issued++;
      pending.set(i, b64(await page.evaluate(i => window.renderFrame(i), i)));
      while (pending.has(next)) {
        const buf = pending.get(next); pending.delete(next);
        if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
        if (next % 48 === 0) console.log(`frame ${next}/${N}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
        next++;
      }
    }
  }
  await Promise.all(pages.map(worker));
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
