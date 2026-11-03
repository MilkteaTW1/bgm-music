"""python -m bgm_forge --video vlog --duration 45 --candidates 8"""
import argparse
import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

from . import adversary, compose, profiles, review


def _write_wav(path, x):
    pcm = (np.clip(x, -1, 1).T * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(compose.SR)
        w.writeframes(pcm.tobytes())


def _read_wav(path):
    with wave.open(str(path), "rb") as w:
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2")
    return (raw.reshape(-1, 2).T / 32768.0).astype(np.float32)


def normalise(src, dst, lufs):
    """Loudness-normalise with ffmpeg (EBU R128) so every candidate is compared at the same level."""
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", f"loudnorm=I={lufs}:TP=-1.5:LRA=7", "-ar", str(compose.SR), str(dst)]
    subprocess.run(cmd, check=True)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bgm_forge")
    ap.add_argument("--video", help="video type, e.g. vlog / 教學 / gaming")
    ap.add_argument("--duration", type=float, default=45, help="seconds")
    ap.add_argument("--candidates", type=int, default=8)
    ap.add_argument("--rounds", type=int, default=3, help="adversarial rounds (0 = just pick the best of the first batch)")
    ap.add_argument("--loop", action="store_true", help="make it loop seamlessly instead of ending")
    ap.add_argument("--out", default="out")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list or not a.video:
        for k, p in profiles.PROFILES.items():
            print(f"{k:10} {p['label']}  | {p['why']}")
        return 0
    key = profiles.find(a.video)
    if not key:
        print("unknown video type; run with --list", file=sys.stderr)
        return 2
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prof = profiles.PROFILES[key]
    counter = [0]

    def evaluate(pl):
        counter[0] += 1
        raw, fin = out / "_raw.wav", out / f"cand{counter[0]}.wav"
        _write_wav(raw, compose.render(pl))
        normalise(raw, fin, prof["lufs"])
        raw.unlink()
        rep = review.review(_read_wav(fin), pl)
        rep["file"] = fin.name
        return rep

    first = []
    for seed in range(1, a.candidates + 1):
        pl = compose.plan(key, a.duration, seed, a.loop)
        rep = evaluate(pl)
        first.append((pl, rep))
        print(f"seed {seed}: score {rep['score']:5.1f}  bpm {pl['bpm']:.0f}  key {pl['key']}  prog {pl['prog']}  penalties {({k: v for k, v in rep['penalties'].items() if v > 0.5})}")
    base_best = max(r["score"] for _, r in first)
    history = adversary.tournament(evaluate, first, rounds=a.rounds) if a.rounds else sorted(first, key=lambda x: -x[1]["score"])
    results = []
    for pl, rep in history:
        rep["plan"] = pl
        results.append(rep)
    print()
    print(f"best before the critic fought back: {base_best}  after: {results[0]['score']}")
    best = results[0]
    stem = f"{key}_{int(a.duration)}s{'_loop' if a.loop else ''}"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(out / best["file"]), "-b:a", "192k", str(out / f"{stem}.mp3")], check=True)
    (out / f"{stem}.review.json").write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in results:
        if r is not best:
            (out / r["file"]).unlink(missing_ok=True)
    (out / best["file"]).unlink(missing_ok=True)
    print(f"\nBEST: seed {best['plan']['seed']} score {best['score']} -> {out / (stem + '.mp3')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
