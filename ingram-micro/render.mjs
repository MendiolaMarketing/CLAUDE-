// Usage: node render.mjs video out.mp4   |  node render.mjs stills dir t1 t2 ...
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const [mode, target, ...rest] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
await page.goto('file://' + path.join(here, 'spot.html'));
await page.evaluate(() => window.ready);
const FPS = await page.evaluate(() => window.FPS);
const grab = async i => Buffer.from((await page.evaluate(i => window.renderFrame(i), i)).split(',')[1], 'base64');
if (mode === 'stills') {
  mkdirSync(target, { recursive: true });
  for (const s of rest) { const i = Math.round(parseFloat(s) * FPS); writeFileSync(path.join(target, `f_${String(i).padStart(4, '0')}.png`), await grab(i)); }
} else {
  const N = await page.evaluate(() => window.FRAMES);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', target], { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const buf = await grab(i);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 60 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
