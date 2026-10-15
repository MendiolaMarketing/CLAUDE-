# Ingram Micro — motion graphic 20 s

`ingram_micro_20s.mp4`: 1920×1080, 30 fps, 20.0 s, H.264 + AAC (música y SFX sintetizados, sin voz).

| Escena | Tiempo | Contenido |
|---|---|---|
| Hook | 0–2 s | Fibra óptica / circuitos, titular palabra por palabra, convergencia y estallido |
| 1 | 2–6 s | 0 → 165,000+ CLIENTES, grid de puntos que se enciende, zoom al último "0" |
| 2 | 6–10 s | 0 → 1,500+ PROVEEDORES DE TECNOLOGÍA, 8 íconos genéricos conectados, wipe diagonal de luz |
| 3 | 10–14 s | Globo de puntos (continentes reales), 0 → 57 PAÍSES, arcos entre puntos, globo → anillo |
| 4 | 14–17 s | Anillo de progreso 0% → 90%, pulso y partículas |
| Cierre | 17–20 s | Partículas forman el logo, revelado con máscara de luz, "¿HASTA DÓNDE PUEDES CRECER?", último 0.5 s quieto |

Música a 120 BPM (todos los cortes caen en tiempo fuerte: 2/6/10/14/17 s); ticks de contadores en bus propio por encima de la música.

## Logo oficial
Por defecto se usa un wordmark tipográfico "INGRAM MICRO" (Inter Black, #2F75BB) como sustituto.
Para usar el logo oficial, coloca `logo.png` (fondo transparente) en esta carpeta y vuelve a renderizar:
las partículas y el revelado se adaptan automáticamente a la forma del logo.

## Re-render
```
node render.mjs video /tmp/video.mp4          # vista previa: abrir spot.html en el navegador
python3 audio.py /tmp/score.wav
ffmpeg -i /tmp/video.mp4 -i /tmp/score.wav -c:v copy -c:a aac -b:a 256k -shortest ingram_micro_20s.mp4
```
`land.js`: máscara de tierra (puntos del globo) generada a partir del paquete `global-land-mask`.
