// Exporta la animación a MP4 1080x1920 con audio.
//
//   node export.mjs                       -> inyeccion-precisa.mp4 a 30 fps
//   node export.mjs --fps 60 --out reel.mp4
//   node export.mjs --stills 1.5,6.9,13.5 -> PNGs sueltos para revisar
//
// Requiere: ffmpeg en el PATH y Playwright (npm i) o Puppeteer instalado.
// Cada cuadro se renderiza de forma determinista con window.__seek(t);
// el audio se genera con el mismo código Web Audio vía OfflineAudioContext.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdirSync, rmSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const arg = (k, d) => { const i = process.argv.indexOf('--' + k); return i > 0 ? process.argv[i + 1] : d; };
const FPS = parseInt(arg('fps', '30'), 10);
const OUT = path.resolve(arg('out', path.join(here, 'inyeccion-precisa.mp4')));
const STILLS = arg('stills', null);

async function openPage() {
  const url = pathToFileURL(path.join(here, 'index.html')).href + '?export=1';
  const args = ['--force-color-profile=srgb', '--autoplay-policy=no-user-gesture-required', '--allow-file-access-from-files'];
  try {
    const { chromium } = await import('playwright');
    const browser = await chromium.launch({ args });
    const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
    page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
    await page.goto(url);
    return { browser, page, shot: () => page.screenshot({ type: 'png' }) };
  } catch (e) {
    if (e.code !== 'ERR_MODULE_NOT_FOUND') throw e;
    const puppeteer = (await import('puppeteer')).default;
    const browser = await puppeteer.launch({ args });
    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
    page.on('pageerror', e => { console.error('PAGE ERROR', e); process.exit(1); });
    await page.goto(url);
    return { browser, page, shot: () => page.screenshot({ type: 'png' }) };
  }
}

const { browser, page, shot } = await openPage();
await page.evaluate(() => window.__ready);
const DUR = await page.evaluate(() => window.__duration);
const frameAt = async t => { await page.evaluate(t => window.__seek(t), t); return shot(); };

if (STILLS) {
  const dir = path.join(here, 'stills'); mkdirSync(dir, { recursive: true });
  for (const s of STILLS.split(',')) writeFileSync(path.join(dir, `t_${parseFloat(s).toFixed(2)}.png`), await frameAt(parseFloat(s)));
  console.log('Stills ->', dir);
} else {
  const tmp = path.join(os.tmpdir(), `ipq-${process.pid}`); mkdirSync(tmp, { recursive: true });
  const wav = path.join(tmp, 'sfx.wav');
  console.log('Renderizando audio…');
  writeFileSync(wav, Buffer.from(await page.evaluate(() => window.__renderAudioWav()), 'base64'));

  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-i', wav,
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-ar', '48000',
    '-t', String(DUR), '-movflags', '+faststart', OUT], { stdio: ['pipe', 'inherit', 'inherit'] });

  const N = Math.round(DUR * FPS), t0 = Date.now();
  for (let i = 0; i < N; i++) {
    const buf = await frameAt(i / FPS);
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % FPS === 0) console.log(`cuadro ${i}/${N}  (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  rmSync(tmp, { recursive: true, force: true });
  if (code !== 0) { console.error('ffmpeg falló con código', code); process.exit(code); }
  console.log('Listo ->', OUT);
}
await browser.close();
