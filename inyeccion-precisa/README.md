# Inyección Precisa de Querétaro — Reel 15 s (1080×1920)

Animación vertical 9:16 en HTML/CSS/JS puro (sin dependencias en el navegador), con
efectos de sonido sintetizados con Web Audio API (sin música).

## Ver la animación
Abre `index.html` en Chrome/Edge y da clic en **Play**. Si el navegador bloquea las
fuentes locales en `file://`, sírvelo con un servidor estático:

```bash
npx serve .        # o: python3 -m http.server
```

## Exportar a MP4 (con audio)
Requisitos: Node 18+, `ffmpeg` en el PATH.

```bash
npm install                       # instala Playwright
npx playwright install chromium   # solo la primera vez
npm run export                    # -> inyeccion-precisa.mp4 a 30 fps
npm run export:60                 # 60 fps
node export.mjs --stills 1.5,7,13.5   # cuadros sueltos para revisión
```

El script también funciona con Puppeteer si lo tienes instalado en lugar de Playwright.

Cómo funciona: toda la animación es una función pura del tiempo (`render(t)`), así que
el exportador avanza cuadro por cuadro con `window.__seek(t)` y toma una captura
(sin caídas de cuadros ni desfases). El audio se renderiza con el **mismo** código de
efectos en un `OfflineAudioContext`, se guarda como WAV y ffmpeg lo une al video
(H.264 + AAC, `yuv420p`, `faststart`, listo para Reels/TikTok/WhatsApp).

## Estructura
| Archivo | Contenido |
|---|---|
| `index.html` | Animación, filtros SVG de bloom, partitura de SFX |
| `export.mjs` | Exportador Playwright/Puppeteer + ffmpeg |
| `assets/logo.png` | Logo original (solo recortado el margen transparente) |
| `assets/whatsapp.png` | Ícono de WhatsApp |
| `assets/fonts/` | Inter y Instrument Serif Italic (Google Fonts, OFL) |

## Línea de tiempo
| Tiempo | Escena | Sonido |
|---|---|---|
| 0–3 s | Punto de luz y anillos, "¿QUIERES AHORRAR GASOLINA?" | whoosh + impact |
| 3–5 s | "Es más fácil de lo que crees…" palabra por palabra | pop por palabra |
| 5–8 s | Morph a tarjeta 3D, trazo del inyector, destello de limpieza | swoosh + sparkle |
| 8–10 s | Volteo, gota, aguja cae, acento rojo | goteo + power-down |
| 10–12 s | Contadores +5 / +20 dentro de una estela de infinito | ticks + ding |
| 12–15 s | El infinito converge y revela el logo, CTA y WhatsApp (fijo desde 13.0 s) | whoosh + notificación |

Para ajustar tiempos, edita el objeto `T` en `index.html`: animación y audio usan los
mismos valores, así que se mantienen sincronizados.
