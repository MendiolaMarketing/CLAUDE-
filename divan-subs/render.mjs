// Uso: node render.mjs video out_basename   -> out_basename_alpha.mov (QuickTime Animation, con alfa) + out_basename_preview.mp4
//      node render.mjs stills dir t1 t2 ...  -> PNGs sueltos (t en segundos)
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { writeFileSync, readFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const [mode, target, ...rest] = process.argv.slice(2);
const browser = await chromium.launch({ args: ['--force-color-profile=srgb', '--allow-file-access-from-files'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
await page.goto('file://' + path.join(here, 'subs.html'));
console.log('grupos:', await page.evaluate(s => window.init(s), readFileSync(path.join(here, 'subs.srt'), 'utf8')));
const grab = async i => Buffer.from((await page.evaluate(i => window.renderFrame(i), i)).split(',')[1], 'base64');
if (mode === 'stills') {
  mkdirSync(target, { recursive: true });
  for (const s of rest) { const i = Math.round(parseFloat(s) * 24); writeFileSync(path.join(target, `f_${String(i).padStart(4, '0')}.png`), await grab(i)); }
} else {
  const N = await page.evaluate(() => window.FRAMES);
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', '24', '-c:v', 'png', '-i', '-',
    '-f', 'lavfi', '-i', 'color=c=0x3a3840:s=1080x1920:r=24',
    '-filter_complex', '[0:v]split[a][b];[1:v][b]overlay=shortest=1:format=auto,format=yuv420p[p]',
    '-map', '[a]', '-c:v', 'qtrle', '-pix_fmt', 'argb', `${target}_alpha.mov`,
    '-map', '[p]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-movflags', '+faststart', `${target}_preview.mp4`],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const buf = await grab(i);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 120 === 0) console.log(`frame ${i}/${N}  ${((Date.now() - t0) / 1000).toFixed(1)}s`);
  }
  ff.stdin.end(); await new Promise(r => ff.on('close', r));
}
await browser.close();
