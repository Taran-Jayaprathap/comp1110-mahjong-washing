"""Washing simulation with a circular drift ("swirl"), fitted to the real trials.

Adds one parameter to the existing washing model in mahjong_model.py: every stroke also turns the
tiles under the hand about the table centre by up to `swirl` radians, always in the same direction
(negative = clockwise in the model's frame = towards the previous seat, E->N->W->S->E).
Everything else (start layout, washer styles, wall building) is reused unchanged.
"""
import math, os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import mahjong_model as mm

def wash_swirl(pos, seconds, styles, rng, swirl):
    runs = pos.shape[0]
    strokes = rng.poisson(styles["rate"] * seconds)
    c = np.array([0.5, 0.5])
    for j in range(int(strokes.max(initial=0))):
        for k in range(4):
            active = j < strokes[:, k]
            if not active.any():
                continue
            local = np.stack([rng.random(runs), rng.random(runs) * styles["reach"][:, k]], axis=-1)
            centre = mm.rotate(local, k)[:, None, :]
            angle = rng.uniform(0, 2 * math.pi, runs)
            dist = rng.uniform(0, 1, runs) * styles["push"][:, k]
            shift = np.stack([np.cos(angle) * dist, np.sin(angle) * dist], axis=-1)[:, None, :]
            r2 = styles["radius"][:, k][:, None] ** 2
            hit = (((pos - centre) ** 2).sum(-1) < r2) & active[:, None]
            th = (swirl * rng.uniform(0, 1, runs))[:, None]                  # turn about the centre
            d = pos - c
            rot = np.stack([d[..., 0] * np.cos(th) - d[..., 1] * np.sin(th),
                            d[..., 0] * np.sin(th) + d[..., 1] * np.cos(th)], axis=-1) + c - pos
            jitter = rng.normal(0, 0.01, pos.shape)
            pos += hit[..., None] * (shift + rot + jitter)
            np.clip(pos, 0, 1, out=pos)
    return pos

def simulate(seconds, runs, rng, rate, swirl, washer_cv=0.25, seats=(0, 1, 2, 3)):
    """seats = which seats wash (0=E, 1=S, 2=W, 3=N); the others don't wash."""
    pos = mm.start_layout(runs, rng)
    st = mm.draw_styles(runs, rng, {"rate": rate}, washer_cv)
    for k in range(4):
        if k not in seats:
            st["rate"][:, k] = 0.0
    wash_swirl(pos, seconds, st, rng, swirl)
    walls = mm.build_walls(pos)
    start = np.repeat(np.arange(4), mm.WALL)
    t = np.zeros((runs, 4, 4), dtype=int)
    for s in range(4):
        for w in range(4):
            t[:, s, w] = (walls[:, start == s] == w).sum(axis=1)
    return t

def offsets(tables):
    """Share of tiles ending 0 (own), +1 (next seat), +2 (opposite), -1 (previous seat) seats away."""
    tables = np.asarray(tables, float)
    if tables.ndim == 2: tables = tables[None]
    out = np.zeros((len(tables), 4))
    for o in range(4):
        out[:, o] = sum(tables[:, s, (s + o) % 4] for s in range(4)) / 144
    return out
