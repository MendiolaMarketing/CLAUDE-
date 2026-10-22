// Uso: node render.mjs            -> renderiza las 3 escenas (MP4 fondo verde + MOV ProRes 4444 con alfa)
//      node render.mjs stills     -> cuadros de prueba en ./stills
import { chromium } from '/opt/node-tools/node_modules/playwright/index.mjs';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const mode = process.argv[2] || 'video';
const out = path.join(here, mode === 'stills' ? 'stills' : 'render');
mkdirSync(out, { recursive: true });

const browser = await chromium.launch({ args: ['--force-color-profile=srgb'] });
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
await page.goto('file://' + path.join(here, 'textos.html'));
const scenes = await page.evaluate(() => window.SCENES.map(s => ({ id: s.id, frames: s.frames })));

const grab = async f => { await page.evaluate(f => window.draw(f), f); return page.screenshot({ omitBackground: true }); };

const ffmpeg = args => {
  const p = spawn('ffmpeg', ['-y', '-loglevel', 'error', ...args], { stdio: ['pipe', 'inherit', 'inherit'] });
  return { p, done: new Promise(r => p.on('close', r)) };
};

for (let i = 0; i < scenes.length; i++) {
  const { id, frames } = scenes[i];
  await page.evaluate(i => window.setup(i), i);
  if (mode === 'stills') {
    for (const f of [0, 4, 8, 12, 18, 30, frames - 1])
      writeFileSync(path.join(out, `${id}_f${String(f).padStart(2, '0')}.png`), await grab(f));
    continue;
  }
  const inArgs = ['-f', 'image2pipe', '-framerate', '30', '-c:v', 'png', '-i', '-'];
  // fondo verde croma #00FF00, H.264
  const green = ffmpeg([...inArgs, '-f', 'lavfi', '-i', `color=c=0x00FF00:s=1080x1920:r=30:d=${frames / 30}`,
    '-filter_complex', '[1][0]overlay=format=auto,format=yuv420p', '-frames:v', String(frames),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '12', '-r', '30', '-movflags', '+faststart',
    path.join(out, `${id}_verde.mp4`)]);
  // transparente: ProRes 4444 con canal alfa
  const alpha = ffmpeg([...inArgs, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le',
    '-vendor', 'apl0', '-r', '30', path.join(out, `${id}_alfa.mov`)]);
  for (let f = 0; f < frames; f++) {
    const buf = await grab(f);
    for (const { p } of [green, alpha]) if (!p.stdin.write(buf)) await new Promise(r => p.stdin.once('drain', r));
  }
  green.p.stdin.end(); alpha.p.stdin.end();
  await Promise.all([green.done, alpha.done]);
  console.log(`${id}: ${frames} cuadros`);
}
await browser.close();
