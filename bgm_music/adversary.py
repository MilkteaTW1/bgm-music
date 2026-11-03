"""Adversarial loop: the critic attacks a track, the composer repairs what was attacked, repeat.

Generator = compose.render. Critic = review.review (and any extra critics plugged in later).
The critic does not just score: each penalty maps to a concrete repair, so an attack steers the next draft.
Only the best draft of each lineage survives a round, like a tournament.
"""
import copy

import numpy as np

from .profiles import PROFILES


def _clip(v, lo, hi):
    return float(min(hi, max(lo, v)))


def repairs(rep, pl, rng):
    """Turn the strongest attacks in a review into adjustments for the next draft."""
    prof = PROFILES[pl["profile"]]
    m, pen = rep["metrics"], rep["penalties"]
    adj = dict(pl.get("adj", {}))
    mul = lambda k, f: adj.__setitem__(k, _clip(adj.get(k, 1.0) * f, 0.3, 2.2))
    add = lambda k, d, lo, hi: adj.__setitem__(k, _clip(adj.get(k, 0.0) + d, lo, hi))
    strength = float(rng.uniform(0.6, 1.2))
    attacks = sorted((k for k, v in pen.items() if v > 0.4), key=lambda k: -pen[k])[:3]
    for a in attacks:
        if a == "voice_space":
            mul("melody", 1 - 0.3 * strength)
            mul("arp", 1 - 0.15 * strength)
            add("dip", -1.5 * strength, -8, 0)
        elif a == "brightness":
            add("bright", (0.12 if m["centroid_hz"] < m["centroid_target"] else -0.12) * strength, -0.5, 0.5)
        elif a == "harsh":
            add("bright", -0.12 * strength, -0.5, 0.5)
            mul("hat", 1 - 0.3 * strength)
        elif a == "pacing":
            lo, hi = prof["onsets"]
            if m["onsets_per_sec"] < lo:
                mul("arp", 1 + 0.25 * strength)
                mul("hat", 1 + 0.3 * strength)
            else:
                mul("arp", 1 - 0.2 * strength)
                mul("hat", 1 - 0.3 * strength)
        elif a == "repetition":
            mul("melody", 1 + 0.25 * strength if m["similarity"] > 0.96 else 1 - 0.2 * strength)
        elif a == "dynamics":
            mul("pad", 1 + (0.2 if m["bar_db_std"] < 1 else -0.2) * strength)
        elif a in ("ending", "loop_seam"):
            mul("pad", 1 + 0.15 * strength)
            add("reverb", 0.05 * strength, -0.3, 0.3)
        elif a == "rumble":
            mul("bass", 1 - 0.25 * strength)
        elif a == "silence":
            mul("pad", 1.2)
    # small random jitter so lineages do not stall on the same local optimum
    for k in ("pad", "arp", "bass"):
        mul(k, float(rng.uniform(0.92, 1.08)))
    return adj, attacks


def tournament(evaluate, first_round, rounds=3, children=3, survivors=3, seed=0, log=print):
    """first_round: list of (plan, review). evaluate(plan) -> review. Returns every draft, best first."""
    rng = np.random.default_rng(seed)
    pool = sorted(first_round, key=lambda x: -x[1]["score"])
    lineages = pool[:survivors]
    history = list(pool)
    for r in range(1, rounds + 1):
        nxt = []
        for pl, rep in lineages:
            best = (pl, rep)
            for _ in range(children):
                adj, attacks = repairs(best[1], best[0], rng)
                child = copy.deepcopy(best[0])
                child["adj"] = adj
                crep = evaluate(child)
                history.append((child, crep))
                if crep["score"] > best[1]["score"]:
                    best = (child, crep)
                    log(f"  round {r} seed {child['plan_seed'] if 'plan_seed' in child else child['seed']}: attacked {attacks} -> {crep['score']}")
            nxt.append(best)
        lineages = nxt
    history.sort(key=lambda x: -x[1]["score"])
    return history
