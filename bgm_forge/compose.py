"""Compose and render one background track from a profile and a seed. Pure numpy/scipy, no sound fonts."""
import numpy as np
from scipy import signal

from .profiles import MODES, PROFILES

SR = 44100
TAIL = 3.0  # seconds of reverb tail rendered past the end


def _hz(midi):
    return 440.0 * 2 ** ((np.asarray(midi, dtype=float) - 69) / 12)


def _adsr(n, a, d, s, r):
    env = np.ones(n)
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    na, nr = min(na, n), min(nr, n)
    if na:
        env[:na] = np.linspace(0, 1, na)
    if nd and na + nd < n:
        env[na:na + nd] = np.linspace(1, s, nd)
        env[na + nd:] = s
    elif na < n:
        env[na:] = s
    if nr:
        env[-nr:] *= np.linspace(1, 0, nr)
    return env


def _pad(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for cents in (-7, 0, 7):
        ff = f * 2 ** (cents / 1200)
        out += np.sin(2 * np.pi * ff * t) + 0.35 * np.sin(4 * np.pi * ff * t) + 0.12 * np.sin(6 * np.pi * ff * t)
    return out / 3 * _adsr(n, 0.5, 0.2, 0.85, min(0.9, dur / 2))


def _pluck(f, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * f * t) + 0.45 * np.sin(4 * np.pi * f * t) * np.exp(-t * 9) + 0.2 * np.sin(6 * np.pi * f * t) * np.exp(-t * 14)
    return tone * np.exp(-t * 6.5) * _adsr(n, 0.004, 0, 1, 0.03)


def _bass(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)) * _adsr(n, 0.01, 0.08, 0.8, 0.08)


def _lead(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.003 * np.sin(2 * np.pi * 5 * t) * np.minimum(1, t / 0.4)
    ph = 2 * np.pi * f * t * vib
    return (np.sin(ph) + 0.25 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph)) * _adsr(n, 0.02, 0.1, 0.7, 0.15)


def _kick():
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = 45 + 80 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 11)


def _noise(rng, dur, lo, decay):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    sos = signal.butter(2, lo / (SR / 2), "highpass", output="sos")
    return signal.sosfilt(sos, x) * np.exp(-t * decay)


def _put(buf, start, x, gain, pan=0.0):
    i = int(start * SR)
    if i >= buf.shape[1]:
        return
    x = x[: buf.shape[1] - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    buf[0, i:i + len(x)] += x * gain * l * 1.414
    buf[1, i:i + len(x)] += x * gain * r * 1.414


def _chord(scale, degree, key, octave, size=3):
    notes = []
    for k in range(size):
        idx = degree - 1 + 2 * k
        notes.append(key + 12 * octave + scale[idx % 7] + 12 * (idx // 7))
    return notes


def plan(profile_name, duration, seed, loop=False):
    """Pick every musical decision up front (so the reviewer can read them back)."""
    p = PROFILES[profile_name]
    rng = np.random.default_rng(seed)
    lo, hi = p["bpm"]
    bars = max(8, int(round(duration * np.mean(p["bpm"]) / 240)))
    bpm = bars * 240 / duration
    if not lo * 0.92 <= bpm <= hi * 1.08:  # too far: keep a natural tempo and trim to length instead
        bpm = float(np.clip(bpm, lo, hi))
        bars = int(duration * bpm / 240)
    key = int(rng.choice(p["keys"]))
    prog = p["progs"][int(rng.integers(len(p["progs"])))]
    return dict(profile=profile_name, seed=seed, bpm=bpm, bars=bars, key=key, prog=prog, loop=loop, duration=duration,
                mode=p["mode"], motif_seed=int(rng.integers(1 << 30)))


def render(pl):
    p = dict(PROFILES[pl["profile"]])
    adj = pl.get("adj", {})  # repairs proposed by the critic: gain multipliers and small EQ/space shifts
    for k in ("pad", "arp", "bass", "melody"):
        p[k] = p[k] * adj.get(k, 1.0)
    p["bright"] = float(np.clip(p["bright"] + adj.get("bright", 0.0), 0.0, 1.0))
    p["reverb"] = float(np.clip(p["reverb"] + adj.get("reverb", 0.0), 0.0, 0.7))
    hat = adj.get("hat", 1.0)
    rng = np.random.default_rng(pl["seed"] + 1)
    scale = MODES[p["mode"]]
    bpm, bars, key = pl["bpm"], pl["bars"], 48 + pl["key"]
    beat = 60 / bpm
    bar_len = 4 * beat
    total = bars * bar_len
    buf = np.zeros((2, int((total + TAIL) * SR)))
    prog = pl["prog"]

    mrng = np.random.default_rng(pl["motif_seed"])
    rhythm = [0, 1, 1.5, 2.5, 3] if p["melody"] else []
    motif = [int(mrng.integers(-2, 3)) for _ in rhythm]
    pent = [0, 1, 2, 4, 5]  # scale degrees used by the melody (pentatonic-ish, hard to make sound wrong)

    for b in range(bars):
        t0 = b * bar_len
        deg = prog[b % len(prog)]
        last = b >= bars - 2 and not pl["loop"]
        energy = 0.55 + 0.45 * min(1.0, b / max(4, bars * 0.25))
        if b < 2:
            energy *= 0.8
        if last:
            energy *= 0.7
        # pad: one chord per bar, mid octave
        chord = _chord(scale, deg, key, 1, 4 if p["pad"] > 0.5 else 3)
        for i, m in enumerate(chord):
            _put(buf, t0, _pad(_hz(m), bar_len + 0.4), 0.085 * p["pad"] * energy, pan=(i - 1.5) * 0.35)
        # bass: root on beat 1, fifth on beat 3 when the track is lively
        root = _hz(key - 12 + scale[(deg - 1) % 7])
        _put(buf, t0, _bass(root, beat * (3.6 if last else 1.8)), 0.20 * p["bass"] * energy)
        if not last and p["bass"] > 0.5:
            _put(buf, t0 + 2 * beat, _bass(root * 1.5, beat * 1.6), 0.14 * p["bass"] * energy)
        # arpeggio: starts after the opening bars, eighth notes up and down the chord
        if p["arp"] and b >= 2 and not last:
            tones = _chord(scale, deg, key, 2, 3) + [_chord(scale, deg, key, 3, 1)[0]]
            order = [0, 1, 2, 3, 2, 1, 2, 1]
            for k in range(8):
                _put(buf, t0 + k * beat / 2, _pluck(_hz(tones[order[k]])), 0.34 * p["arp"] * energy * (1.0 if k % 2 == 0 else 0.7),
                     pan=0.4 * np.sin(k))
        # drums: enter after four bars, drop out for the ending
        if p["groove"] != "none" and b >= 4 and not last:
            g = p["groove"]
            for k in range(8):
                tt = t0 + k * beat / 2
                if g in ("soft", "pop", "drive"):
                    _put(buf, tt, _noise(rng, 0.05, 7000, 90), 0.13 * hat * (1.2 if k % 2 else 0.7), pan=0.3)
                if g in ("pop", "drive") and k in (0, 5):
                    _put(buf, tt, _kick(), 0.30)
                if g == "drive" and k in (2, 4, 6) and k != 4:
                    _put(buf, tt, _kick(), 0.16)
                if g in ("pop", "drive") and k in (2, 6):
                    _put(buf, tt, _noise(rng, 0.14, 1800, 28), 0.14)
        # melody: four bars of phrase, four bars of rest, so it breathes
        if p["melody"] and b >= 4 and (b // 4) % 2 == 0 and not last:
            chord_idx = {(deg - 1) % 7, (deg + 1) % 7, (deg + 3) % 7}
            for pos, step in zip(rhythm, motif):
                d = pent[(step + (b // 4)) % len(pent)]
                if pos == 0:
                    d = min(chord_idx, key=lambda c: abs(c - d))
                m = key + 12 * 2 + scale[d % 7] + 12 * (d // 7)
                _put(buf, t0 + pos * beat, _lead(_hz(m), beat * 0.9), 0.24 * p["melody"] * energy, pan=-0.2)
    # ending: one held tonic chord
    if not pl["loop"]:
        t0 = (bars - 1) * bar_len
        for i, m in enumerate(_chord(scale, 1, key, 1, 3)):
            _put(buf, t0, _pad(_hz(m), bar_len * 1.5 + 1.0), 0.12 * p["pad"], pan=(i - 1) * 0.4)

    # reverb: synthetic exponential-decay noise impulse
    n_ir = int(1.6 * SR)
    ir = rng.standard_normal((2, n_ir)) * np.exp(-np.arange(n_ir) / SR * (7 - 4 * p["reverb"]))
    wet = np.stack([signal.fftconvolve(buf[c], ir[c])[: buf.shape[1]] for c in range(2)])
    wet /= max(1e-9, np.abs(wet).max()) / max(1e-9, np.abs(buf).max())
    buf = buf * (1 - p["reverb"] * 0.6) + wet * p["reverb"] * 0.9

    n = int(total * SR)
    if pl["loop"]:  # fold the tail back onto the start so the seam is invisible
        tail = buf[:, n:n + int(TAIL * SR)]
        buf[:, : tail.shape[1]] += tail
    out = buf[:, :n]

    # master: remove rumble, tame highs by profile brightness, carve space for a voice
    out = signal.sosfilt(signal.butter(2, 35 / (SR / 2), "highpass", output="sos"), out, axis=1)
    cutoff = 3500 + 8500 * p["bright"]
    out = signal.sosfilt(signal.butter(2, cutoff / (SR / 2), "lowpass", output="sos"), out, axis=1)
    if p["voice"]:
        out = _peak_eq(out, 2600, -4.5 + adj.get("dip", 0.0), 0.9)
    out = np.tanh(out / max(1e-9, np.abs(out).max()) * 1.4) / np.tanh(1.4) * 0.9
    if not pl["loop"]:
        fade = int(0.8 * SR)
        out[:, -fade:] *= np.linspace(1, 0, fade)
    if not pl["loop"]:
        out[:, : int(0.01 * SR)] *= np.linspace(0, 1, int(0.01 * SR))
    want = int(pl["duration"] * SR)
    if out.shape[1] > want:
        out = out[:, :want]
        if not pl["loop"]:
            f = int(0.8 * SR)
            out[:, -f:] *= np.linspace(1, 0, f)
    return out.astype(np.float32)


def _peak_eq(x, f0, gain_db, q):
    a = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * f0 / SR
    al = np.sin(w0) / (2 * q)
    b = [1 + al * a, -2 * np.cos(w0), 1 - al * a]
    aa = [1 + al / a, -2 * np.cos(w0), 1 - al / a]
    return signal.lfilter(np.array(b) / aa[0], np.array(aa) / aa[0], x, axis=1)
