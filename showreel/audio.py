"""Synthesized soundtrack for the showreel. 120 BPM, every hit locked to a cut.
Usage: python3 audio.py out.wav
"""
import sys, wave
import numpy as np

SR = 48000
DUR = 15.0
N = int(SR * DUR)
rng = np.random.default_rng(7)
L = np.zeros(N); R = np.zeros(N)          # dry bus
VL = np.zeros(N); VR = np.zeros(N)        # reverb send


def add(sig, t0, gain=1.0, pan=0.0, verb=0.0):
    i = int(t0 * SR)
    if i >= N: return
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


# ---------------- instruments ----------------
def kick(d=0.45, f0=160, f1=42, drive=1.6):
    t = tt(d)
    f = f1 + (f0 - f1) * np.exp(-t * 28)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * np.exp(-t * 7.5)
    s += 0.5 * rng.standard_normal(len(t)) * np.exp(-t * 300)
    return np.tanh(s * drive)


def clap():
    t = tt(0.3)
    n = hp(rng.standard_normal(len(t)), 900)
    env = np.zeros(len(t))
    for o in (0, 0.011, 0.022):
        env += (t >= o) * np.exp(-np.clip(t - o, 0, None) * 60)
    env += 0.4 * np.exp(-t * 14)
    return n * env * 0.6


def hat(d=0.05, open_=False):
    t = tt(0.25 if open_ else d)
    n = hp(hp(rng.standard_normal(len(t)), 6000), 6000)
    return n * np.exp(-t * (14 if open_ else 90)) * 0.5


def impact(size=1.0):
    t = tt(2.2)
    sub = np.sin(2 * np.pi * np.cumsum(38 + 90 * np.exp(-t * 18)) / SR) * np.exp(-t * 2.2)
    n = onepole_lp(rng.standard_normal(len(t)), 1800 * np.exp(-t * 3) + 120) * np.exp(-t * 4)
    s = np.tanh((sub * 1.3 + n * 1.6) * 1.4) * size
    return s


def whoosh(d, up=True, lo=200, hi=9000):
    t = tt(d); p = t / d
    cut = lo * (hi / lo) ** (p if up else 1 - p)
    n = onepole_lp(rng.standard_normal(len(t)), cut)
    env = (np.sin(np.pi * p) ** 1.5) if not up else p ** 2.2
    return n * env * 1.4


def riser(d, f0=200, f1=1600):
    t = tt(d); p = t / d
    f = f0 * (f1 / f0) ** (p ** 1.5)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = (np.sin(ph) + 0.5 * np.sin(ph * 1.007 * 2) + 0.3 * np.sin(ph * 0.5)) * p ** 2
    return s * 0.35 + whoosh(d, True) * 0.6


def swell(d):  # reverse cymbal-ish suck
    t = tt(d); p = t / d
    n = hp(rng.standard_normal(len(t)), 2500)
    return n * p ** 3 * 0.9


def pluck(freq, d=0.35, bright=1.0):
    t = tt(d)
    s = sum((0.6 ** k) * np.sin(2 * np.pi * freq * (k + 1) * t) * np.exp(-t * (9 + 6 * k * bright)) for k in range(5))
    return s * 0.5


def ping(freq, d=0.6):
    t = tt(d)
    return (np.sin(2 * np.pi * freq * t) + 0.3 * np.sin(2 * np.pi * freq * 2.76 * t) * np.exp(-t * 12)) * np.exp(-t * 6) * 0.4


def tick():
    t = tt(0.02)
    return np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 400) * 0.5


def bass(freq, d, wob=0.0):
    t = tt(d)
    lfo = 1 + wob * np.sin(2 * np.pi * 6 * t)
    ph = 2 * np.pi * np.cumsum(freq * lfo) / SR
    s = np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.tanh(3 * np.sin(ph))
    env = np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.03)
    return np.tanh(s * 1.3) * env * 0.5


def saw(freq, t):
    return 2 * ((freq * t) % 1.0) - 1


def pad(freqs, d, cutoff=2200):
    t = tt(d)
    s = np.zeros(len(t))
    for f in freqs:
        for det in (-0.006, 0, 0.007):
            s += saw(f * (1 + det), t)
    s /= len(freqs) * 3
    s = onepole_lp(s, cutoff * np.exp(-t * 0.6) + 300)
    env = np.minimum(1, t / 0.01) * np.exp(-t * 0.9)
    return s * env


def boing(freq, d=0.25):
    t = tt(d)
    f = freq * (1 + 1.2 * np.exp(-t * 30))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) * 0.6


def blip(freq, d=0.03):
    t = tt(d)
    return np.sign(np.sin(2 * np.pi * freq * t)) * np.exp(-t * 80) * 0.15


def note(n):  # midi → Hz
    return 440 * 2 ** ((n - 69) / 12)


A_PENT = [57, 60, 62, 64, 67, 69, 72, 74, 76, 79, 81]

# ---------------- score ----------------
# Scene 1: the dot (0–2)
add(ping(note(81), 1.2), 0.0, 0.5, 0, 0.6)
add(kick(0.3, 120, 50, 1.0), 0.0, 0.35)
add(tick(), 0.30, 0.6); add(tick(), 0.40, 0.4)
add(riser(0.42, 300, 2400), 0.46, 0.55, 0, 0.3)
add(impact(0.9), 0.9, 0.9, 0, 0.35)
add(kick(), 0.9, 0.7)
for i in range(6): add(tick(), 0.9 + i * 0.035, 0.35, -0.6 + i * 0.24)
for k in range(17):
    add(blip(1800 + 900 * rng.random()), 1.15 + k / 30, 0.6, rng.uniform(-.7, .7))
add(ping(note(76), 0.9), 1.5, 0.35, 0.3, 0.7)
add(swell(0.5), 1.5, 0.7)
add(bass(note(33), 1.0, 0), 0.9, 0.35)

# Scene 2: kinetic type (2–4) — a slam on every beat
roots = [33, 36, 38, 40]
for k, b in enumerate([2.0, 2.5, 3.0, 3.5]):
    add(kick(), b, 1.0)
    add(impact(0.5), b, 0.5, 0, 0.2)
    add(clap(), b, 0.45 if k % 2 else 0.25, 0, 0.4)
    add(bass(note(roots[k]), 0.48), b, 0.8)
    add(whoosh(0.22, False, 400, 7000), b - 0.02, 0.35, (-1) ** k * 0.6)
for s in range(16):
    add(hat(), 2.0 + s * 0.125, 0.25 + 0.15 * (s % 2), 0.4)
for i in range(12): add(tick(), 3.0 + i * 0.02, 0.25, 0.5 - i * 0.08)   # clock ticks
for s in range(8): add(hat(0.03), 3.5 + s * 0.0625, 0.3, -0.4)            # rhythm
add(swell(0.45), 3.55, 0.6)

# Scene 3: grid groove (4–6.5)
for b in np.arange(4.0, 6.5, 0.5):
    add(kick(), b, 0.95)
for b in (4.5, 5.5): add(clap(), b, 0.6, 0, 0.35)
for s in range(16): add(hat(open_=(s % 4 == 2)), 4.0 + s * 0.125, 0.3, 0.3)
arp = [0, 4, 7, 9, 5, 9, 7, 4, 2, 6, 8, 10, 7, 10, 8, 6]
for s, i in enumerate(arp):
    add(pluck(note(A_PENT[i])), 4.0 + s * 0.125, 0.45, np.sin(s) * 0.7, 0.45)
for k, b in enumerate([4.0, 4.5, 5.0, 5.5]):
    add(bass(note([33, 33, 36, 31][k]), 0.45), b, 0.7)
add(riser(0.5, 150, 3000), 6.0, 0.7, 0, 0.2)
add(swell(0.5), 6.0, 0.7)

# Scene 4: fluid morph (6.5–8.5)
add(impact(1.2), 6.5, 1.0, 0, 0.5)
add(kick(), 6.5, 1.0)
add(bass(note(33), 1.0, 0.03), 6.5, 0.7)
for b in (7.0, 7.5, 8.0): add(kick(), b, 0.9)
for b in (7.5, 8.0):
    add(whoosh(0.35, False, 300, 6000), b - 0.15, 0.6, 0.3)
    add(impact(0.5), b, 0.45)
add(bass(note(36), 0.5, 0.05), 7.5, 0.7)
add(bass(note(38), 0.5, 0.05), 8.0, 0.7)
for s in range(16): add(hat(), 6.5 + s * 0.125, 0.22, -0.3)
add(pad([note(57), note(64), note(67), note(72)], 2.0, 1400), 6.5, 0.35, 0, 0.6)
add(riser(0.3, 400, 4000), 8.2, 0.9)

# Scene 5: tunnel + sphere (8.5–11)
add(impact(1.3), 8.5, 1.0, 0, 0.5)
t5 = tt(1.5); p5 = t5 / 1.5
drone = sum(saw(note(45) * (1 + det) * (1 + p5 * 1.0), t5) for det in (-0.01, 0, 0.012)) / 3
add(onepole_lp(drone, 400 + 5000 * p5 ** 2) * (0.3 + 0.7 * p5), 8.5, 0.35)
for b in np.arange(8.5, 10.0, 0.25): add(kick(0.25), b, 0.75 if (b * 4) % 2 == 0 else 0.45)
for s in range(24): add(hat(0.03), 8.5 + s * 0.0625, 0.18, 0.5 * np.sin(s))
add(whoosh(0.5, False, 200, 9000), 9.55, 1.0, 0.0, 0.3)  # DEPTH flies past
add(impact(1.0), 10.0, 0.9, 0, 0.4)
add(kick(), 10.0, 1.0)
for k, f in enumerate([81, 84, 88, 91, 93, 96]):
    add(ping(note(f), 0.8), 10.05 + k * 0.07, 0.25, -0.7 + k * 0.28, 0.8)
add(kick(), 10.5, 0.8)
add(pad([note(57), note(64), note(71), note(74)], 1.0, 3000), 10.0, 0.25, 0, 0.7)
add(swell(0.28), 10.72, 1.0)

# Scene 6: panels / glitch / burst (11–12.5)
add(impact(1.1), 11.0, 1.0, 0, 0.3)
for b in (11.0, 11.25): add(kick(), b, 0.9)
for k in range(3): add(whoosh(0.3, False, 300, 8000), 11.0 + k * 0.05, 0.4, (-1) ** k * 0.8)
add(bass(note(38), 0.45, 0.0), 11.0, 0.7)
add(impact(1.0), 11.5, 0.9)
for s in range(12):   # stutter glitch
    tt0 = 11.5 + s * 0.0417
    add(blip(200 + 1800 * rng.random(), 0.035), tt0, 2.5, rng.uniform(-1, 1))
    if s % 3 == 0: add(kick(0.08, 400, 100, 3), tt0, 0.5)
add(bass(note(29), 0.5, 0.2), 11.5, 0.8)
add(impact(0.8), 11.75, 0.6)
add(riser(0.5, 300, 5000), 12.0, 0.9, 0, 0.2)
add(whoosh(0.5, True, 300, 12000), 12.0, 0.7)

# Scene 7: identity (12.5–15)
add(impact(1.5), 12.5, 1.1, 0, 0.6)
add(kick(0.6), 12.5, 1.0)
chord = [note(n) for n in (45, 52, 57, 60, 64, 71)]   # Am(add9)
add(pad(chord, 2.5, 2600), 12.5, 0.6, 0, 0.8)
add(bass(note(33), 2.4, 0), 12.5, 0.55)
for i in range(6): add(tick(), 12.58 + i * 0.045, 0.3, -0.5 + i * 0.2)
for gt, a, f in ((13.35, 1.0, 660), (13.66, 0.55, 880), (13.81, 0.3, 990)):
    add(boing(f), gt, a * 0.8, 0.4, 0.4)
for i in range(15): add(blip(2400, 0.02), 13.4 + i / 30, 0.4, 0.3)
for k in range(5): add(pluck(note([69, 72, 76, 79, 81][k]), 0.6), 13.75 + k * 0.06, 0.35, -0.6 + k * 0.3, 0.7)
add(ping(note(88), 1.0), 13.9, 0.3, 0, 0.9)

# ---------------- mix ----------------
ir_t = tt(1.8)
def reverb(x, seed):
    r = np.random.default_rng(seed)
    ir = r.standard_normal(len(ir_t)) * np.exp(-ir_t * 3.2)
    ir = onepole_lp(ir, 5000)
    n = len(x) + len(ir)
    y = np.fft.irfft(np.fft.rfft(x, n) * np.fft.rfft(ir, n), n)[: len(x)]
    return y * 0.06

outL = L + reverb(VL, 1)
outR = R + reverb(VR, 2)
mix = np.stack([outL, outR], 1)
mix = np.tanh(mix / np.max(np.abs(mix)) * 1.6)      # glue / soft clip
fade = np.minimum(1, (DUR - np.arange(N) / SR) / 0.25)[:, None]
mix = mix * fade
mix = mix / np.max(np.abs(mix)) * 0.89
pcm = (mix * 32767).astype('<i2')
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('wrote', sys.argv[1])
