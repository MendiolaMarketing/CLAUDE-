# Reel 20 de octubre — motion graphics + subtítulos

Capa para Instagram (1080×1920, 24 fps, 1513 cuadros = 00:01:03:01) con fondo transparente para poner encima del video grabado.

Identidad de Germán Mendiola:
- Colores: oscuro `#141313`, crema `#f2ecdd` (es el "fondo blanco") y dorado `#cd9c20`. El dorado nunca se usa de fondo: solo va en texto, líneas, contornos e íconos.
- Tipografías: Cal Sans para títulos, en minúsculas como el logo, y Raleway para etiquetas y subtítulos. Ambas están en `fonts/`.
- Logo: la palabra "german mendiola" va en una pestaña sobre la línea dorada de los paneles negros y arriba al centro en las pantallas completas.

- `out/reel_20oct_preview.mp4`: vista previa sobre un fondo gris de referencia.
- `out/reel_20oct_overlay_alpha.webm`: capa con transparencia (VP9 con alfa), archivo ligero.
- `out/reel_20oct_overlay_alpha.mov`: máster ProRes 4444 con alfa (no está en git, se regenera con el renderizador).

| Rango | Tipo | Contenido |
|---|---|---|
| 00:00:02:10–04:20 | Mitad de arriba (negro) | Depende de 2 cosas: tiempo + dinero |
| 00:00:04:21–06:09 | Pantalla completa (blanco) | Opción 01: mucho tiempo 100% / poco dinero 0% |
| 00:00:08:14–11:07 | Pantalla completa (blanco) | Tú haces todo: idea, grabar, editar, publicar |
| 00:00:11:08–16:08 | Mitad de arriba (negro) | Solo necesitas: celular, luz natural, cero ruido |
| 00:00:20:08–21:22 | Pantalla completa (blanco) | Opción 02: tiempo 50% y dinero 50%, a la par |
| 00:00:25:21–30:17 | Mitad de arriba (negro) | Por video o por paquete: más económico |
| 00:00:34:15–36:11 | Pantalla completa (blanco) | Opción 03: poco tiempo 30% / más inversión 70% |
| 00:00:38:11–40:15 | Mitad de arriba (negro) | Agencia o freelance: se encarga de todo |
| 00:00:44:19–49:05 | Mitad de arriba (negro) | Muchísimas horas: grabando, editando, ideas, etc. |
| 00:00:54:11–57:00 | Mitad de arriba (negro) | 3 opciones: ¿cuál es la correcta? |
| 00:00:58:08–59:23 | Pantalla completa (blanco) | ¿En qué etapa estás? |

Los subtítulos salen palabra por palabra de `subs.srt` (la palabra que se está diciendo va en dorado). Dentro de los paneles negros se colocan en la parte baja del panel. Durante las pantallas completas se ocultan porque la animación ya muestra el texto.

## Volver a renderizar

```
# words.js ya está generado a partir de subs.srt
node render.mjs stills /tmp/st 3.5 12 27    # cuadros de prueba
node render.mjs video out/reel_20oct_overlay_alpha.mov
```
