"""Synthesized score + SFX for the Ingram Micro 20s spot.
120 BPM, A minor. Every scene cut (2/6/10/14/17 s) lands on a downbeat.
Counter ticks live on their own bus, mixed above the music.
Usage: python3 audio.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
DUR = 20.0
N = int(SR * DUR)
BEAT = 0.5
rng = np.random.default_rng(11)
buses = {k: np.zeros((N, 2)) for k in ('music', 'sfx', 'tick', 'verb')}


def add(sig, t0, gain=1.0, pan=0.0, bus='music', verb=0.0):
    i = int(round(t0 * SR))
    if i >= N or i < 0: return
    sig = sig[: N - i] * gain
    g = np.array([np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))])
    buses[bus][i:i + len(sig)] += sig[:, None] * g
    if verb: buses['verb'][i:i + len(sig)] += sig[:, None] * g * verb


def tt(d): return np.arange(int(d * SR)) / SR


def onepole_lp(x, cutoff):
    c = np.broadcast_to(np.asarray(cutoff, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * c / SR)
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s); y[i] = s
    return y


def hp(x, cutoff): return x - onepole_lp(x, cutoff)
def note(n): return 440 * 2 ** ((n - 69) / 12)
def saw(f, t): return 2 * ((f * t) % 1.0) - 1


# ---------------- instruments ----------------
def kick(d=0.4, f0=150, f1=45, drive=1.8):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8)
    s += 0.4 * rng.standard_normal(len(t)) * np.exp(-t * 350)
    return np.tanh(s * drive)


def clap():
    t = tt(0.3)
    n = hp(rng.standard_normal(len(t)), 1000)
    env = sum((t >= o) * np.exp(-np.clip(t - o, 0, None) * 70) for o in (0, 0.01, 0.021)) + 0.4 * np.exp(-t * 16)
    return n * env * 0.55


def hat(d=0.05, open_=False):
    t = tt(0.22 if open_ else d)
    n = hp(hp(rng.standard_normal(len(t)), 7000), 7000)
    return n * np.exp(-t * (16 if open_ else 95)) * 0.5


def snare(d=0.18):
    t = tt(d)
    n = hp(rng.standard_normal(len(t)), 1500) * np.exp(-t * 28)
    b = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 35)
    return (n * 0.7 + b * 0.5)


def impact(size=1.0, low=38):
    t = tt(2.4)
    sub = np.sin(2 * np.pi * np.cumsum(low + 100 * np.exp(-t * 16)) / SR) * np.exp(-t * 1.9)
    n = onepole_lp(rng.standard_normal(len(t)), 2200 * np.exp(-t * 3) + 120) * np.exp(-t * 4.5)
    return np.tanh((sub * 1.4 + n * 1.4) * 1.4) * size


def dry_hit():  # short, punchy "landing" hit
    t = tt(0.35)
    body = np.sin(2 * np.pi * np.cumsum(60 + 220 * np.exp(-t * 40)) / SR) * np.exp(-t * 14)
    click = hp(rng.standard_normal(len(t)), 2500) * np.exp(-t * 120)
    return np.tanh((body + click * 0.8) * 2.0) * 0.8


def whoosh(d, up=True, lo=200, hi=9000):
    t = tt(d); p = t / d
    cut = lo * (hi / lo) ** (p if up else 1 - p)
    n = onepole_lp(rng.standard_normal(len(t)), cut)
    env = p ** 2.2 if up else np.sin(np.pi * p) ** 1.5
    return n * env * 1.4


def swoosh(d=0.22):  # fast band-passed pass-by
    t = tt(d); p = t / d
    n = rng.standard_normal(len(t))
    cut = 600 + 7000 * np.sin(np.pi * p)
    return hp(onepole_lp(n, cut), 400) * np.sin(np.pi * p) ** 2 * 1.4


def riser(d, f0=200, f1=1800):
    t = tt(d); p = t / d
    f = f0 * (f1 / f0) ** (p ** 1.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.5 * np.sin(ph * 2.01) + 0.3 * np.sin(ph * 0.5)) * p ** 2
    return s * 0.35 + whoosh(d, True) * 0.6


def swell(d):
    t = tt(d); p = t / d
    return hp(rng.standard_normal(len(t)), 2500) * p ** 3 * 0.9


def glitch(d=0.12):
    t = tt(d); out = np.zeros(len(t)); k = 0
    while k < len(t):
        L = int(SR * rng.uniform(0.008, 0.025))
        f = rng.uniform(150, 3000)
        seg = np.sign(np.sin(2 * np.pi * f * t[:L])) if rng.random() < .6 else rng.standard_normal(L)
        out[k:k + L] = seg[: len(out) - k] * rng.uniform(.2, .6)
        k += L
    return out


def tick(f=3400):
    t = tt(0.018)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * f * 2.3 * t)) * np.exp(-t * 420) * 0.5


def ping(freq, d=0.7):
    t = tt(d)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 12)) * np.exp(-t * 7) * 0.4


def pluck(freq, d=0.3):
    t = tt(d)
    return sum((0.6 ** k) * np.sin(2 * np.pi * freq * (k + 1) * t) * np.exp(-t * (10 + 7 * k)) for k in range(5)) * 0.5


def bass(freq, d):
    t = tt(d)
    ph = 2 * np.pi * freq * t
    s = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.tanh(4 * np.sin(ph))
    env = np.minimum(1, t / 0.004) * np.exp(-t * 4) * np.minimum(1, (d - t) / 0.02)
    return np.tanh(s * 1.4) * env * 0.5


def stab(freqs, d=0.25, cutoff=3000):
    t = tt(d)
    s = sum(saw(f * (1 + det), t) for f in freqs for det in (-0.007, 0, 0.008)) / (len(freqs) * 3)
    return onepole_lp(s, cutoff * np.exp(-t * 10) + 400) * np.exp(-t * 9)


def pad(freqs, d, cutoff=2400, att=0.02):
    t = tt(d)
    s = sum(saw(f * (1 + det), t) for f in freqs for det in (-0.006, 0, 0.007)) / (len(freqs) * 3)
    s = onepole_lp(s, cutoff * np.exp(-t * 0.5) + 300)
    return s * np.minimum(1, t / att) * np.exp(-t * 0.6)


def shimmer(d=1.2):
    out = np.zeros(int(d * SR))
    for k, n in enumerate([88, 91, 93, 96, 100, 103, 105, 108]):
        s = ping(note(n), 0.7) * 0.5
        i = int(k * 0.045 * SR); out[i:i + len(s)] += s[: len(out) - i]
    t = tt(d)
    return out + hp(rng.standard_normal(len(t)), 9000) * np.exp(-t * 3) * 0.12


# ---------------- helpers mirrored from spot.html ----------------
def count_ease_inv(y): return -np.log2(1 - y * (1 - 2 ** -10)) / 10


def counter_ticks(t0, dur, steps=34, f=3400):
    last = -1
    for k in range(1, steps + 1):
        tk = t0 + count_ease_inv(k / steps) * dur
        if tk - last < 0.028: continue
        add(tick(f * (1 + 0.15 * (k % 2))), tk, 0.9, 0.25 * np.sin(k), 'tick'); last = tk


Am, F, C_, G = [57, 60, 64], [53, 57, 60], [55, 60, 64], [55, 59, 62]
PROG = [Am, F, C_, G]
ROOT = [33, 29, 36, 31]


def groove(a, b, kick_g=0.9, hats=True, clap_g=0.5, stabs=True, bass_g=0.6):
    for i, bt in enumerate(np.arange(a, b - 1e-6, BEAT)):
        bar = int((bt - 2.0) // 2) % 4
        add(kick(), bt, kick_g)
        add(bass(note(ROOT[bar] + 12), 0.22), bt + 0.25, bass_g)
        if hats:
            add(hat(), bt + 0.25, 0.3, 0.3)
            add(hat(0.03), bt + 0.125, 0.12, -0.3); add(hat(0.03), bt + 0.375, 0.12, -0.3)
        if clap_g and i % 2 == 1: add(clap(), bt, clap_g, 0, 'music', 0.3)
        if stabs and i % 4 == 3: add(stab([note(n) for n in PROG[bar]]), bt + 0.25, 0.25, 0.2, 'music', 0.4)


# ---------------- score ----------------
# 0–2 HOOK
add(glitch(0.14), 0.0, 0.6, 0, 'sfx')
add(whoosh(0.5, False, 300, 9000), 0.0, 0.8, -0.3, 'sfx', 0.3)
for i, wt in enumerate([.1, .27, .45, .58, .7, .9, 1.1]):
    add(kick(0.18, 220, 80, 2.5), wt, 0.45)
    add(swoosh(0.12), wt - 0.04, 0.35, (-1) ** i * 0.5, 'sfx')
add(pad([note(n) for n in (45, 52, 57, 60)], 2.0, 900, 0.6), 0.0, 0.35, 0, 'music', 0.5)
for s in range(8): add(hat(0.03), 1.0 + s * 0.125, 0.15 + s * 0.03, 0.3)
add(riser(1.0, 180, 2400), 1.0, 0.6, 0, 'sfx', 0.2)
add(swell(0.5), 1.5, 0.7, 0, 'sfx')
add(glitch(0.1), 1.96, 0.5, 0.2, 'sfx')

# 2–6 CLIENTES
add(impact(1.2), 2.0, 1.0, 0, 'sfx', 0.4)
groove(2.0, 5.5)
add(pad([note(n) for n in (45, 52, 57, 60)], 3.5, 1600), 2.0, 0.18, 0, 'music', 0.5)
counter_ticks(2.1, 1.3)
add(dry_hit(), 3.4, 1.0, 0, 'sfx')
for s in range(8): add(snare(), 5.5 + s * 0.0625, 0.15 + s * 0.05, 0, 'music', 0.2)
add(riser(0.7, 250, 3500), 5.3, 0.7, 0, 'sfx', 0.2)
add(whoosh(0.6, True, 200, 12000), 5.4, 0.6, 0, 'sfx')
add(glitch(0.08), 5.94, 0.35, 0, 'sfx')

# 6–10 PROVEEDORES
add(impact(1.0), 6.0, 0.9, 0, 'sfx', 0.3)
groove(6.0, 10.0)
add(pad([note(n) for n in (41, 48, 53, 57)], 4.0, 1800), 6.0, 0.18, 0, 'music', 0.5)
counter_ticks(6.15, 1.3, 30, 3800)
for i in range(8): add(swoosh(0.24), 6.12 + i * 0.12 - 0.06, 0.5, np.cos(-np.pi / 2 + 2 * np.pi * (i + .5) / 8), 'sfx')
add(dry_hit(), 7.45, 1.0, 0, 'sfx')
for k in range(8): add(pluck(note(76 + [0, 3, 7, 10, 12, 10, 7, 3][k])), 8.0 + k * 0.125, 0.2, 0.4 * np.sin(k), 'music', 0.4)
add(whoosh(0.5, False, 300, 10000), 9.52, 0.9, -0.6, 'sfx', 0.3)

# 10–14 PAISES
add(impact(0.9), 10.0, 0.8, 0, 'sfx', 0.4)
groove(10.0, 13.5, clap_g=0.4)
add(pad([note(n) for n in (48, 55, 60, 64)], 3.5, 2000), 10.0, 0.2, 0, 'music', 0.6)
PENT = [69, 72, 74, 76, 79, 81, 84, 86, 88, 91]
for k in range(1, 58):
    tk = 10.15 + count_ease_inv((k - .5) / 57) * 1.3
    add(ping(note(PENT[(k * 3) % len(PENT)]), 0.5), tk, 0.35 if tk - 10.15 > 0.15 else 0.18, rng.uniform(-.6, .8), 'tick', 0.0)
add(dry_hit(), 11.45, 0.9, 0, 'sfx')
for k in range(18): add(ping(note(PENT[(k * 5) % len(PENT)]), 0.4), 11.6 + k * 0.1, 0.12, rng.uniform(-.5, .8), 'sfx', 0.6)
add(riser(0.65, 300, 3000), 13.35, 0.7, 0, 'sfx', 0.2)
for s in range(4): add(snare(), 13.5 + s * 0.125, 0.25, 0, 'music', 0.2)

# 14–17 POBLACION
add(impact(0.8), 14.0, 0.7, 0, 'sfx', 0.3)
for bt in np.arange(14.0, 15.45, 0.25): add(kick(0.2), bt, 0.55 + 0.2 * (bt - 14))
add(riser(1.45, 150, 4000), 14.0, 0.8, 0, 'sfx', 0.2)
counter_ticks(14.15, 1.3, 28, 3000)
add(impact(1.6, 30), 15.45, 1.1, 0, 'sfx', 0.5)          # deep impact on 90%
add(kick(0.6, 120, 35, 2.2), 15.45, 1.0)
for k in range(10): add(pluck(note(PENT[k])), 15.5 + k * 0.03, 0.12, -0.8 + k * .18, 'sfx', 0.7)
groove(15.5, 16.5, kick_g=0.7, clap_g=0.0, stabs=False, bass_g=0.4)
for s in range(16): add(snare(), 16.5 + s * 0.03125, 0.08 + s * 0.02, 0, 'music', 0.2)
add(swell(0.5), 16.5, 0.9, 0, 'sfx')
add(glitch(0.08), 16.94, 0.35, 0, 'sfx')

# 17–20 LOGO (drop)
add(impact(1.8, 32), 17.0, 1.2, 0, 'sfx', 0.6)            # sub boom
add(kick(0.7, 140, 34, 2.4), 17.0, 1.0)
chord = [note(n) for n in (45, 52, 57, 60, 64, 71)]
add(pad(chord, 3.0, 3200), 17.0, 0.55, 0, 'music', 0.8)
add(bass(note(33), 2.4), 17.0, 0.55)
for bt in np.arange(17.5, 19.01, 0.5): add(kick(0.35), bt, 0.55 - 0.08 * (bt - 17.5))
for s in range(12): add(hat(), 17.25 + s * 0.125, 0.18, 0.3)
add(whoosh(0.6, False, 400, 12000), 17.55, 0.5, -0.5, 'sfx', 0.4)
add(shimmer(1.4), 17.62, 0.9, 0.2, 'sfx', 0.8)           # light-mask reveal
for k, n in enumerate([69, 72, 76, 81]): add(pluck(note(n), 0.6), 18.3 + k * 0.09, 0.25, -0.4 + k * .25, 'music', 0.7)

# ---------------- mix ----------------
ir_t = tt(1.8)
def reverb(x, seed):
    r = np.random.default_rng(seed)
    ir = onepole_lp(r.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.0), 5000)
    n = len(x) + len(ir)
    return np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)] * 0.05

verb = np.stack([reverb(buses['verb'][:, 0], 1), reverb(buses['verb'][:, 1], 2)], 1)
music = buses['music'] + verb
music = np.tanh(music / np.max(np.abs(music)) * 1.5) * 0.62
sfx = buses['sfx'] / np.max(np.abs(buses['sfx'])) * 0.6
ticks = buses['tick'] / np.max(np.abs(buses['tick'])) * 0.5
mixd = music + sfx + ticks
mixd = np.tanh(mixd * 1.1)
fade = np.minimum(1, (DUR - np.arange(N) / SR) / 0.6)[:, None]
mixd = mixd * fade
mixd = mixd / np.max(np.abs(mixd)) * 0.89
pcm = (mixd * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[1])
