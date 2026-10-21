"""Efectos de sonido sincronizados con reel.html (transiciones, pops, golpes, checks).
Todos los tiempos salen de las mismas marcas que usa la animación.
Uso: python3 sfx.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
FPS = 24
FRAMES = 63 * FPS + 1                     # 00:01:03:01
DUR = FRAMES / FPS
N = int(round(SR * DUR))
rng = np.random.default_rng(20)
L = np.zeros(N); R = np.zeros(N)          # dry bus
VL = np.zeros(N); VR = np.zeros(N)        # reverb send


def add(sig, t0, gain=1.0, pan=0.0, verb=0.0):
    i = int(t0 * SR)
    if i >= N or i < 0: return
    sig = sig[: N - i] * gain
    gl, gr = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
    L[i:i + len(sig)] += sig * gl; R[i:i + len(sig)] += sig * gr
    if verb:
        VL[i:i + len(sig)] += sig * gl * verb; VR[i:i + len(sig)] += sig * gr * verb


def tt(d): return np.arange(int(d * SR)) / SR


def onepole_lp(x, cutoff):
    """cutoff may be scalar or per-sample array (Hz)."""
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def hp(x, cutoff): return x - onepole_lp(x, cutoff)


# ---------------- sounds ----------------
def whoosh(d, lo=250, hi=7000, peak=.55):
    """air swoosh: filter sweeps up then down, envelope peaks at `peak`"""
    t = tt(d); p = t / d
    shape = np.where(p < peak, p / peak, (1 - p) / (1 - peak))
    cut = lo * (hi / lo) ** shape
    n = onepole_lp(onepole_lp(rng.standard_normal(len(t)), cut), cut * 1.4)
    env = np.where(p < peak, (p / peak) ** 2.2, ((1 - p) / (1 - peak)) ** 1.6)
    return hp(n, 120) * env * 2.2


def thump(f0=150, f1=48, d=.4, drive=1.4):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)
    s += .35 * onepole_lp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 120)
    return np.tanh(s * drive) * .8


def impact(size=1.0):
    t = tt(1.4)
    sub = np.sin(2 * np.pi * np.cumsum(40 + 110 * np.exp(-t * 20)) / SR) * np.exp(-t * 3.5)
    n = onepole_lp(rng.standard_normal(len(t)), 2600 * np.exp(-t * 5) + 150) * np.exp(-t * 7)
    return np.tanh((sub * 1.2 + n * 1.3) * 1.3) * size


def pop(f=700, d=.12):
    t = tt(d)
    fr = f * (.55 + .9 * np.exp(-t * 60))
    s = np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 38)
    return s * np.minimum(1, t / .002) * .7


def click(f=2600):
    t = tt(.03)
    s = np.sin(2 * np.pi * f * t) * np.exp(-t * 260) * .5
    s += hp(rng.standard_normal(len(t)), 3000) * np.exp(-t * 600) * .35
    return s


def wood(f=1300):
    t = tt(.06)
    return (np.sin(2 * np.pi * f * t) + .4 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * 90) * .45


def bell(f, d=.9):
    t = tt(d)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 5)
         + .45 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 8)
         + .25 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 14))
    return s * np.minimum(1, t / .002) * .35


def coin():
    a = bell(1975.5, .25)[: int(.08 * SR)]
    b = bell(2637.0, .9)
    out = np.zeros(len(a) + len(b)); out[: len(a)] += a; out[len(a):] += b
    return out * 1.1


def swish(d=.16):
    return whoosh(d, 1500, 11000, .3) * .7


def riser(d, f0=300, f1=1400):
    t = tt(d); p = t / d
    f = f0 * (f1 / f0) ** p
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + .3 * np.sin(2 * ph)) * p ** 1.5 * np.minimum(1, (d - t) / .02)
    return s * .22 + whoosh(d, 300, 6000, .95) * .35


def boing(f=500, d=.22):
    t = tt(d)
    fr = f * (1 + .9 * (1 - np.exp(-t * 25)))
    return np.sin(2 * np.pi * np.cumsum(fr) / SR) * np.exp(-t * 16) * .45


def low_blip():
    t = tt(.32)
    f = np.where(t < .13, 220, 165)
    s = np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR))
    env = np.minimum(1, t / .004) * np.where(t < .13, np.exp(-t * 8), np.exp(-(t - .13) * 14)) * (np.abs(t - .13) > .012)
    return onepole_lp(s * env, 1800) * .35


def ticks(t0, t1, n, gain=.35, f=3200, pan=0.):
    for k in range(n):
        add(click(f), t0 + (t1 - t0) * (k / max(1, n - 1)) ** 1.6, gain, pan)


# ---------------- segments (same timecodes as reel.html) ----------------
def tc(s):
    h, m, sec, f = map(int, s.split(':')); return (h * 3600 + m * 60 + sec) * FPS + f
SEGS = [('00:00:02:10', '00:00:04:20', 'A'), ('00:00:04:21', '00:00:06:09', 'B'), ('00:00:08:14', '00:00:11:07', 'B'),
        ('00:00:11:08', '00:00:16:08', 'A'), ('00:00:20:08', '00:00:21:22', 'B'), ('00:00:25:21', '00:00:30:17', 'A'),
        ('00:00:34:15', '00:00:36:11', 'B'), ('00:00:38:11', '00:00:40:15', 'A'), ('00:00:44:19', '00:00:49:05', 'A'),
        ('00:00:54:11', '00:00:57:00', 'A'), ('00:00:58:08', '00:00:59:23', 'B')]
SEGS = [(tc(a) / FPS, (tc(b) + 1) / FPS, k, tc(a), tc(b)) for a, b, k in SEGS]

# panel transitions: whoosh in on every entry, whoosh out when the panel leaves
for i, (t0, t1, kind, f0, f1) in enumerate(SEGS):
    hold = i + 1 < len(SEGS) and SEGS[i + 1][3] == f1 + 1
    pan = -.25 if kind == 'A' else .25
    add(whoosh(.42, 220, 6500, .62), t0 - .26, .55, pan, .35)      # peaks as the panel lands
    add(thump(120, 45, .3, 1.1), t0 + .02, .35, 0, .2)
    if not hold:
        add(whoosh(.3, 300, 8000, .7), t1 - .26, .42, -pan, .3)

# ---------------- per-scene accents ----------------
# A1 — depende de dos cosas
add(click(), 2.42, .3); add(pop(520), 2.93, .7, 0, .3); add(impact(.55), 2.96, .5, 0, .3)
add(click(2900), 3.16, .25); add(swish(.22), 3.42, .4, .3)
add(pop(640), 3.56, .65, -.4, .3)
for k in range(5): add(wood(1500 if k % 2 else 1200), 3.62 + k * .14, .18, -.4)
add(pop(900, .08), 4.2, .45, 0, .2); add(coin(), 4.31, .55, .4, .5)
# B1 — mucho tiempo, poco dinero
add(click(), 4.92, .28, -.5); add(click(2400), 4.88, .25)
add(thump(170, 55, .35), 5.14, .6, 0, .25); ticks(5.25, 5.8, 11, .22, 3400, -.2)
add(bell(1318.5, .6), 5.8, .25, -.2, .4)
add(click(2400), 5.6, .25); add(thump(170, 55, .35), 5.98, .6, 0, .25); add(low_blip(), 6.05, .55, .2)
# B2 — idea, grabar, editar, publicar (rising pops)
add(click(), 8.62, .28); add(swish(.2), 8.64, .3)
for k, t in enumerate([8.74, 9.28, 9.99, 10.66]):
    add(pop(520 * 1.26 ** k), t, .75, (-.4, .4)[k % 2], .35)
    add(thump(140, 50, .25), t, .3)
add(bell(1567.98, .9), 10.7, .3, .4, .5)
# A2 — solo necesitas: rows pop, checks ding
add(click(), 11.4, .3)
for k, (tr, tch) in enumerate([(12.12, 13.2), (13.54, 14.62), (15.04, 16.0)]):
    add(pop(560 + 80 * k), tr, .6, -.5, .3)
    add(bell([1046.5, 1318.5, 1568.0][k]), tch, .5, .55, .55)
    add(click(4200), tch, .2, .55)
# B3 — tiempo y dinero a la par
add(click(), 20.38, .28, -.5)
add(thump(170, 55, .35), 20.42, .55); ticks(20.6, 20.95, 7, .2, 3400, -.2)
add(thump(170, 55, .35), 20.88, .55); ticks(21.0, 21.3, 6, .2, 3600, .2)
add(impact(1.0), 21.33, .75, 0, .5); add(bell(1046.5, 1.2), 21.36, .25, 0, .7)
# A3 — por video o por paquete, más económico
add(click(), 25.92, .28); add(pop(600), 26.0, .65, -.5, .3); add(click(2600), 27.05, .22, -.5)
add(pop(880, .09), 27.34, .5, 0, .2)
for i in range(4): add(pop(620 + 70 * i, .09), 27.97 + i * .09, .45, .5, .2)
add(swish(.24), 28.36, .45, .5); add(click(2600), 28.4, .2, .5); add(pop(1100, .08), 28.5, .45, .7)
add(impact(.9), 30.03, .7, .4, .45); add(coin(), 30.1, .45, .4, .5)
# B4 — poco tiempo, más inversión
add(click(), 34.67, .28, -.5)
add(thump(170, 55, .35), 35.05, .55); ticks(35.15, 35.45, 5, .2, 3400, -.2)
add(thump(170, 55, .35), 35.93, .6); ticks(36.0, 36.3, 10, .22, 3600, .2)
# A4 — agencia o freelance, se encarga de todo
add(pop(560), 38.85, .65, -.3, .3); add(pop(900, .08), 39.27, .4, 0, .2); add(pop(680), 39.35, .65, .3, .3)
add(impact(.85), 39.95, .7, 0, .45); add(bell(1318.5, 1.0), 39.98, .28, 0, .6)
# A5 — muchísimas horas, tareas tachadas
add(click(), 44.85, .28, -.5); add(pop(500), 44.9, .6, -.5, .3)
for k in range(10): add(wood(1500 if k % 2 else 1200), 44.95 + k * .075, .14, -.5)
add(riser(.7, 250, 1300), 45.7, .45, -.3, .3)
for k in range(18): add(wood(1600 if k % 2 else 1300), 45.75 + .65 * (k / 18) ** .7, .12, -.5)
add(click(2600), 45.68, .22); add(impact(.7), 46.19, .65, 0, .4)
for k, t in enumerate([46.84, 47.3, 48.13, 48.76]):
    add(pop(600 + 60 * k, .1), t, .5, (-.4, .4)[k % 2], .25)
    add(swish(.14), t + .25, .45, (-.4, .4)[k % 2])
# A6 — tres opciones, ¿cuál es la correcta?
add(pop(520), 54.5, .55, 0, .3)
for i in range(3): add(pop(600 + 90 * i, .1), 54.62 + i * .12, .5, (-.6, 0, .6)[i], .25)
k = 0
while 55.75 + k * .145 < 56.62:
    add(click(3000 + 300 * (k % 3)), 55.75 + k * .145, .3, (-.6, 0, .6)[k % 3]); k += 1
add(click(2400), 55.95, .2)
add(impact(.9), 56.62, .7, 0, .45); add(swish(.18), 56.64, .45)
for i, f in enumerate([1046.5, 1318.5, 1568.0]): add(bell(f, 1.0), 56.64, .16, (-.6, 0, .6)[i], .6)
# B5 — ¿en qué etapa estás?
add(click(), 58.36, .28)
for i in range(3): add(thump(110 + 25 * i, 45, .3), 58.45 + i * .1, .45, (-.5, 0, .5)[i], .2)
add(swish(.2), 58.9, .4, -.3); add(thump(170, 55, .3), 58.92, .45)
add(pop(800, .1), 59.0, .55, -.4, .3)
add(boing(480), 59.3, .5, 0, .3); add(boing(600), 59.6, .5, .4, .3)
add(click(2400), 59.62, .22)
# cierre — "comienza a grabarte YA"
add(whoosh(.5, 200, 5000, .9), 62.12, .35, 0, .3)
add(impact(1.0), 62.6, .8, 0, .5); add(bell(1568.0, 1.4), 62.62, .22, 0, .8)

# ---------------- mix ----------------
ir_t = tt(1.4)
def reverb(x, seed):
    r = np.random.default_rng(seed)
    ir = r.standard_normal(len(ir_t)) * np.exp(-ir_t * 4.0)
    ir = onepole_lp(ir, 4500)
    n = len(x) + len(ir)
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)] * .05

mix = np.stack([L + reverb(VL, 1), R + reverb(VR, 2)], 1)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.3)                # gentle glue
mix = mix / np.max(np.abs(mix)) * 10 ** (-6 / 20)             # peak -6 dBFS, room for the voice
fade = np.minimum(1, (DUR - np.arange(N) / SR) / .05)[:, None]
pcm = (mix * fade * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[1], f'{N / SR:.4f}s')
