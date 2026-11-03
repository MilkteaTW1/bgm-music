"""Automatic review of a rendered track against its profile.

This checks things a machine can measure (clipping, rumble, harshness, voice space, pacing, repetition, seams).
It cannot tell whether the music is beautiful: that is still the listener's call.
"""
import numpy as np
from scipy import signal

from .compose import SR
from .profiles import PROFILES


def _band(f, p, lo, hi):
    return float(p[(f >= lo) & (f < hi)].sum() / max(1e-12, p.sum()))


def review(x, pl):
    """x: (2, n) float audio after loudness normalisation. Returns metrics, penalties and a 0-100 score."""
    prof = PROFILES[pl["profile"]]
    mono = x.mean(axis=0)
    f, pxx = signal.welch(mono, SR, nperseg=8192)
    m, pen = {}, {}

    m["clip_ratio"] = float((np.abs(x) > 0.99).mean())
    pen["clipping"] = min(25, m["clip_ratio"] * 5000)

    m["rumble"] = _band(f, pxx, 0, 40)
    pen["rumble"] = min(10, max(0, m["rumble"] - 0.01) * 400)

    m["harsh"] = _band(f, pxx, 8000, 22000)
    pen["harsh"] = min(12, max(0, m["harsh"] - (0.02 + 0.05 * prof["bright"])) * 300)

    m["voice_band"] = _band(f, pxx, 1000, 4000)
    pen["voice_space"] = min(15, max(0, m["voice_band"] - 0.22) * 120) if prof["voice"] else 0.0

    cen = float((f * pxx).sum() / pxx.sum())
    want = 350 + prof["bright"] * 1000
    m["centroid_hz"], m["centroid_target"] = cen, want
    pen["brightness"] = min(10, abs(cen - want) / want * 12)

    hop = 1024
    n = len(mono) // hop
    rms = np.sqrt((mono[: n * hop].reshape(n, hop) ** 2).mean(axis=1)) + 1e-9
    env_db = 20 * np.log10(rms)
    bar = max(1, int(round(240 / pl["bpm"] * SR / hop)))
    nb = len(rms) // bar
    bar_db = 20 * np.log10(np.sqrt((rms[: nb * bar].reshape(nb, bar) ** 2).mean(axis=1)))
    body = bar_db[1:-2] if nb > 6 else bar_db
    m["bar_db_std"] = float(body.std())
    top = 4.0 if prof["voice"] else 5.5
    pen["dynamics"] = min(10, max(0, 0.8 - m["bar_db_std"]) * 8 + max(0, m["bar_db_std"] - top) * 5)

    flux = np.maximum(0, np.diff(env_db))
    peaks, _ = signal.find_peaks(flux, height=flux.mean() + flux.std(), distance=int(0.08 * SR / hop))
    m["onsets_per_sec"] = float(len(peaks) / (len(mono) / SR))
    lo, hi = prof["onsets"]
    pen["pacing"] = min(10, max(0, lo - m["onsets_per_sec"]) * 4 + max(0, m["onsets_per_sec"] - hi) * 3)

    # bar-to-bar similarity of the spectrum: too identical is boring, too different is incoherent
    spec = []
    for i in range(nb):
        seg = mono[i * bar * hop:(i + 1) * bar * hop]
        if len(seg) < 2048:
            continue
        s = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        edges = np.unique(np.geomspace(2, len(s) - 1, 48).astype(int))
        spec.append(np.log1p(np.add.reduceat(s, edges)))
    spec = np.array(spec)
    sim = []
    for i in range(len(spec) - 1):
        a, b = spec[i], spec[i + 1]
        sim.append(float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9)))
    m["similarity"] = float(np.mean(sim)) if sim else 1.0
    pen["repetition"] = min(10, max(0, m["similarity"] - 0.992) * 600 + max(0, 0.93 - m["similarity"]) * 60)

    gaps = (env_db[2:-int(3 * SR / hop)] < -55) if len(env_db) > 10 + int(3 * SR / hop) else np.zeros(1, bool)
    m["silent_ratio"] = float(gaps.mean())
    pen["silence"] = min(10, m["silent_ratio"] * 100)

    if pl["loop"]:
        k = int(0.25 * SR)
        m["seam_jump"] = float(abs(mono[0] - mono[-1]) / (np.abs(mono).max() + 1e-9))
        m["seam_level_db"] = float(20 * np.log10(np.sqrt((mono[:k] ** 2).mean()) + 1e-9) - 20 * np.log10(np.sqrt((mono[-k:] ** 2).mean()) + 1e-9))
        pen["loop_seam"] = min(15, m["seam_jump"] * 60 + abs(m["seam_level_db"]) * 1.5)
    else:
        k = int(0.4 * SR)
        end_db = 20 * np.log10(np.sqrt((mono[-k:] ** 2).mean()) + 1e-9)
        mid_db = 20 * np.log10(np.sqrt((mono ** 2).mean()) + 1e-9)
        m["ending_drop_db"] = float(mid_db - end_db)
        pen["ending"] = min(10, max(0, 14 - m["ending_drop_db"]) * 1.5)

    score = max(0.0, 100 - sum(pen.values()))
    return dict(score=round(score, 1), metrics={k: round(v, 4) for k, v in m.items()}, penalties={k: round(v, 2) for k, v in pen.items()})
