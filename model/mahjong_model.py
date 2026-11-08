"""Mahjong washing: data checks, Monte Carlo test and washing simulation (COMP1110 Group 16).

This file is the library. You normally do not run it directly; run `run_analysis.py`.

Conventions used everywhere
  seats / walls / start piles are numbered 0..3 = E, S, W, N
  suits are numbered 0..3 = dots, bamboo, characters, honours_flowers
  the protocol gives East all dots, South all bamboo, West all characters, North all
  honours+flowers, so "start suit s" and "start seat s" are the same number.
  A "table" is a 4x4 count matrix C[s, w] = tiles of start suit s that ended in wall w.
  In a perfect shuffle every row is about (1/4, 1/4, 1/4, 1/4).

Needs numpy. matplotlib is optional (only for plots).
"""
import csv
import math
import numpy as np

SEATS = "ESWN"
SUITS = ["dots", "bamboo", "characters", "honours_flowers"]
N_TILES = 144
WALL = 36
REQUIRED_COLUMNS = ["trial", "date", "seconds", "wall_seat", "washer_name"] + SUITS


# ---------------------------------------------------------------------------
# 1. Reading and checking the real data (format from experiment-protocol.md)
# ---------------------------------------------------------------------------

class DataError(Exception):
    pass


def load_trials(path):
    """Read the recording CSV (one row per wall, 4 rows per trial) and check it.

    Returns a list of trials, each a dict:
      {"trial": int, "date": str, "seconds": float,
       "table": 4x4 np.array C[suit, wall], "washers": [name at E, S, W, N]}
    Raises DataError listing every problem found, so the recorder can fix them all at once.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:   # utf-8-sig copes with Excel CSVs
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise DataError(f"{path} is empty")
        header = [h.strip().lower() for h in reader.fieldnames]
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise DataError(f"missing columns: {', '.join(missing)} (need {','.join(REQUIRED_COLUMNS)})")
        rows = [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in reader]

    problems, by_trial = [], {}
    for line, r in enumerate(rows, start=2):           # line 1 is the header
        if not any(r.values()):
            continue                                   # skip blank lines
        try:
            t = int(r["trial"])
            sec = float(r["seconds"])
            counts = [int(r[s]) for s in SUITS]
        except ValueError:
            problems.append(f"line {line}: trial, seconds and the four counts must be numbers")
            continue
        seat = r["wall_seat"].upper()
        if seat not in SEATS or len(seat) != 1:
            problems.append(f"line {line}: wall_seat must be one of E, S, W, N (got '{r['wall_seat']}')")
            continue
        if any(c < 0 for c in counts):
            problems.append(f"line {line}: negative count")
        by_trial.setdefault(t, []).append((line, seat, sec, r["date"], r["washer_name"], counts))

    trials = []
    for t in sorted(by_trial):
        walls = by_trial[t]
        seats = [w[1] for w in walls]
        if sorted(seats) != sorted(SEATS):
            problems.append(f"trial {t}: needs exactly one row for each of E, S, W, N (got {''.join(seats)})")
            continue
        secs = {w[2] for w in walls}
        if len(secs) != 1:
            problems.append(f"trial {t}: the four rows have different seconds {sorted(secs)}")
            continue
        table = np.zeros((4, 4), dtype=int)
        washers = [""] * 4
        for line, seat, sec, date, name, counts in walls:
            w = SEATS.index(seat)
            table[:, w] = counts
            washers[w] = name
            if sum(counts) != WALL:
                problems.append(f"trial {t}, wall {seat} (line {line}): counts add to {sum(counts)}, not 36")
        for s in range(4):
            if table[s].sum() != WALL:
                problems.append(f"trial {t}: {SUITS[s]} add to {table[s].sum()} over the four walls, not 36")
        trials.append({"trial": t, "date": walls[0][3], "seconds": walls[0][2],
                       "table": table, "washers": washers})
    if problems:
        raise DataError("the data file has problems:\n  " + "\n  ".join(problems))
    if not trials:
        raise DataError(f"{path} has no trials")
    return trials


def group_by_seconds(trials):
    """{seconds: [trials]} so each washing time is analysed on its own."""
    groups = {}
    for tr in trials:
        groups.setdefault(tr["seconds"], []).append(tr)
    return dict(sorted(groups.items()))


# ---------------------------------------------------------------------------
# 2. Statistics
# ---------------------------------------------------------------------------

def tv_max(table):
    """Primary measure: worst start pile's TV distance from (1/4,1/4,1/4,1/4).
    Works on one 4x4 table or a stack of them (..., 4, 4)."""
    t = np.asarray(table, dtype=float)
    p = t / t.sum(axis=-1, keepdims=True)
    return (0.5 * np.abs(p - 0.25).sum(axis=-1)).max(axis=-1)


def own_share(table):
    """Share of tiles that ended in the wall of the seat they started at (perfect shuffle: 0.25)."""
    t = np.asarray(table, dtype=float)
    return np.trace(t, axis1=-2, axis2=-1) / t.sum(axis=(-2, -1))


def chi_square(table):
    """Pearson chi-square test of independence on a pooled 4x4 table, plus Cramer's V."""
    t = np.asarray(table, dtype=float)
    n = t.sum()
    expected = np.outer(t.sum(1), t.sum(0)) / n
    chi2 = float(((t - expected) ** 2 / expected).sum())
    df = 9
    return {"chi2": chi2, "df": df, "p": chi2_sf(chi2, df), "cramers_v": math.sqrt(chi2 / (n * 3))}


def chi2_sf(x, df):
    """P(chi-square with df degrees of freedom >= x), via the regularised upper gamma Q(df/2, x/2).
    (Saves needing scipy.)"""
    a, x = df / 2.0, x / 2.0
    if x <= 0:
        return 1.0
    if x < a + 1:                                   # series for P, then Q = 1 - P
        term = total = 1.0 / a
        k = a
        while abs(term) > 1e-15 * abs(total):
            k += 1
            term *= x / k
            total += term
        return max(0.0, 1.0 - total * math.exp(-x + a * math.log(x) - math.lgamma(a)))
    b, c, d = x + 1 - a, 1e300, 1.0 / (x + 1 - a)   # continued fraction for Q (Lentz)
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        h *= d * c
        if abs(d * c - 1) < 1e-15:
            break
    return min(1.0, math.exp(-x + a * math.log(x) - math.lgamma(a)) * h)


def bootstrap_ci(trials_tables, stat, rng, reps=10000):
    """95% CI of a pooled statistic by resampling whole trials (trials are the independent units)."""
    tabs = np.asarray(trials_tables)
    idx = rng.integers(0, len(tabs), size=(reps, len(tabs)))
    vals = stat(tabs[idx].sum(axis=1))
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


# ---------------------------------------------------------------------------
# 3. Method 1: the perfect-shuffle yardstick and the Monte Carlo test
# ---------------------------------------------------------------------------

def perfect_shuffle_tables(n_games, rng):
    """4x4 tables of n_games perfectly shuffled games (uniform random permutation of 144 tiles via numpy argsort, 4 walls of 36)."""
    order = rng.random((n_games, N_TILES)).argsort(axis=1)      # a random permutation per game
    suit_at_position = (order // WALL).reshape(n_games, 4, WALL) # [game, wall, slot] -> start suit
    tables = (suit_at_position[..., None] == np.arange(4)).sum(axis=2)   # [game, wall, suit]
    return tables.transpose(0, 2, 1)                               # -> [game, suit, wall]


def perfect_shuffle_pooled(n_trials, rng, runs=10000, chunk=50000):
    """`runs` pooled tables, each the sum of n_trials perfectly shuffled games."""
    out = np.empty((runs, 4, 4), dtype=int)
    per_chunk = max(1, chunk // n_trials)
    for start in range(0, runs, per_chunk):
        k = min(per_chunk, runs - start)
        out[start:start + k] = perfect_shuffle_tables(k * n_trials, rng).reshape(k, n_trials, 4, 4).sum(axis=1)
    return out


def monte_carlo_test(trials, rng, runs=10000):
    """Pooled TV of the real trials vs `runs` perfect-shuffle experiments of the same size.
    p = (1 + number at least as uneven) / (1 + runs), the standard Monte Carlo p-value."""
    tables = np.array([tr["table"] for tr in trials])
    pooled = tables.sum(axis=0)
    observed = float(tv_max(pooled))
    null = tv_max(perfect_shuffle_pooled(len(trials), rng, runs))
    p = (1 + int((null >= observed - 1e-12).sum())) / (1 + runs)
    return {"n_trials": len(trials), "pooled_table": pooled, "tv": observed, "p": p,
            "null_tv": null, "null_mean": float(null.mean()), "null_95": float(np.percentile(null, 95)),
            "own_share": float(own_share(pooled)),
            "own_share_ci": bootstrap_ci(tables, own_share, rng),
            "tv_ci": bootstrap_ci(tables, tv_max, rng),
            "chi_square": chi_square(pooled)}


# ---------------------------------------------------------------------------
# 4. Washer variation in the real data (CX feedback, point 2)
# ---------------------------------------------------------------------------

def wall_records(trials):
    """One record per wall: who built it, which seat, trial order, and its own-suit count."""
    recs = []
    for order, tr in enumerate(sorted(trials, key=lambda t: t["trial"])):
        for w in range(4):
            recs.append({"trial": tr["trial"], "order": order, "seat": SEATS[w],
                         "washer": tr["washers"][w], "own": int(tr["table"][w, w])})
    return recs


def group_effect_test(recs, key, rng, reps=10000):
    """Does `key` (washer or seat) explain differences in own-suit counts?
    Statistic: spread (weighted variance) of the group means. Permutation test: shuffle the labels
    across walls many times and see how often the spread is at least this big."""
    labels = np.array([r[key] for r in recs])
    own = np.array([r["own"] for r in recs], dtype=float)
    groups = sorted(set(labels))
    codes = np.array([groups.index(l) for l in labels])
    sizes = np.bincount(codes, minlength=len(groups))

    def spread(c):
        means = np.bincount(c, weights=own, minlength=len(groups)) / sizes
        return float((sizes * (means - own.mean()) ** 2).sum() / sizes.sum())

    observed = spread(codes)
    perm = np.array([spread(rng.permutation(codes)) for _ in range(reps)])
    means = {g: float(own[codes == i].mean() / WALL) for i, g in enumerate(groups)}
    return {"by_group": means, "n_walls": {g: int(sizes[i]) for i, g in enumerate(groups)},
            "spread": observed, "p": (1 + int((perm >= observed - 1e-12).sum())) / (1 + reps)}


def drift_test(trials, rng, reps=10000):
    """Do washes get lazier over the session? Correlation of each trial's own share with trial order,
    with a permutation p-value (two-sided)."""
    ts = sorted(trials, key=lambda t: t["trial"])
    y = np.array([own_share(t["table"]) for t in ts])
    x = np.arange(len(ts), dtype=float)
    if len(ts) < 3 or y.std() == 0:
        return {"r": 0.0, "p": 1.0}
    r = float(np.corrcoef(x, y)[0, 1])
    perm = np.array([np.corrcoef(x, rng.permutation(y))[0, 1] for _ in range(reps)])
    return {"r": r, "p": (1 + int((np.abs(perm) >= abs(r) - 1e-12).sum())) / (1 + reps)}


# ---------------------------------------------------------------------------
# 5. Method 2: the washing simulation
# ---------------------------------------------------------------------------
#
# The table is the unit square. Seat k's edge: E = bottom (y=0), S = right (x=1), W = top, N = left.
# Each washer has a style (CX feedback: model the people, not just the tiles):
#   rate    strokes per second
#   radius  how big an area one stroke sweeps (table widths)
#   push    how far a stroke moves the tiles it touches (table widths, maximum)
#   reach   how far from their own edge they wash (0.5 = up to the centre, 1 = right across)
# A stroke: the washer puts a hand at a random spot within their reach and moves every tile within
# `radius` by one shared random displacement (plus a little jitter); tiles stay on the table.
# Then each player builds a wall from the 36 tiles nearest their edge (nearest first).
# Collisions and friction are deliberately left out. The dice break does not change which tiles are
# in which wall, so it is not simulated (see experiment-protocol.md).

# Starting guesses only: `rate` is fitted to the real data (section 6); the others can be refined
# from the overhead video if the group measures stroke sizes.
DEFAULT_STYLE = {"rate": 2.0, "radius": 0.15, "push": 0.2, "reach": 0.7}


def rotate(points, k):
    """Rotate (x, y) points k quarter-turns about the table centre: maps seat 0's frame to seat k's."""
    x, y = points[..., 0], points[..., 1]
    for _ in range(k % 4):
        x, y = 1 - y, x
    return np.stack([x, y], axis=-1)


def start_layout(runs, rng):
    """Each seat's 36 tiles lie loose in the triangle of table nearest that seat. Shape (runs, 144, 2);
    tiles 0-35 start at E, 36-71 at S, 72-107 at W, 108-143 at N."""
    pos = np.empty((runs, N_TILES, 2))
    for k in range(4):
        pts = np.empty((runs, WALL, 2))
        todo = np.ones((runs, WALL), dtype=bool)
        while todo.any():                                      # rejection sampling in seat 0's triangle
            cand = rng.random((runs, WALL, 2))
            ok = (cand[..., 1] < cand[..., 0]) & (cand[..., 1] < 1 - cand[..., 0])
            take = todo & ok
            pts[take] = cand[take]
            todo &= ~ok
        pos[:, k * WALL:(k + 1) * WALL] = rotate(pts, k)
    return pos


def draw_styles(runs, rng, base=None, washer_cv=0.25, fixed=None):
    """Styles for 4 washers in each run: array of dicts per parameter, shape (runs, 4).
    Each parameter = base value x a random personal factor (lognormal, spread washer_cv), so every
    simulated table has its own mix of washers. `fixed` = list of 4 style dicts to use exactly instead."""
    base = {**DEFAULT_STYLE, **(base or {})}
    styles = {}
    for name, value in base.items():
        if fixed is not None:
            styles[name] = np.tile([f.get(name, value) for f in fixed], (runs, 1)).astype(float)
        else:
            sigma = math.sqrt(math.log(1 + washer_cv ** 2))
            styles[name] = value * rng.lognormal(-sigma ** 2 / 2, sigma, size=(runs, 4))
    styles["reach"] = np.clip(styles["reach"], 0.05, 1.0)
    return styles


def wash(pos, seconds, styles, rng):
    """Run the washing model for `seconds` on every run at once (pos is changed in place)."""
    runs = pos.shape[0]
    strokes = rng.poisson(styles["rate"] * seconds)                     # (runs, 4) strokes per washer
    for j in range(int(strokes.max(initial=0))):
        for k in range(4):                                              # the four washers take turns
            active = j < strokes[:, k]
            if not active.any():
                continue
            local = np.stack([rng.random(runs), rng.random(runs) * styles["reach"][:, k]], axis=-1)
            centre = rotate(local, k)[:, None, :]                       # (runs, 1, 2)
            angle = rng.uniform(0, 2 * math.pi, runs)
            dist = rng.uniform(0, 1, runs) * styles["push"][:, k]
            shift = np.stack([np.cos(angle) * dist, np.sin(angle) * dist], axis=-1)[:, None, :]
            r2 = styles["radius"][:, k][:, None] ** 2
            hit = (((pos - centre) ** 2).sum(-1) < r2) & active[:, None]
            jitter = rng.normal(0, 0.01, pos.shape)
            pos += hit[..., None] * (shift + jitter)
            np.clip(pos, 0, 1, out=pos)
    return pos


def build_walls(pos):
    """Each player takes the 36 tiles nearest their edge, nearest first. Returns wall[run, tile]."""
    runs = pos.shape[0]
    x, y = pos[..., 0], pos[..., 1]
    edge_dist = np.stack([y, 1 - x, 1 - y, x], axis=-1)               # (runs, 144, 4)
    walls = np.empty((runs, N_TILES), dtype=int)
    for r in range(runs):
        flat = edge_dist[r].ravel()
        wall, count = np.full(N_TILES, -1), [0] * 4
        placed = 0
        for j in np.argsort(flat, kind="stable"):
            tile, seat = divmod(int(j), 4)
            if wall[tile] < 0 and count[seat] < WALL:
                wall[tile] = seat
                count[seat] += 1
                placed += 1
                if placed == N_TILES:
                    break
        walls[r] = wall
    return walls


def simulate_tables(seconds, runs, rng, base=None, washer_cv=0.25, fixed=None):
    """Simulate `runs` washes of `seconds` and return their 4x4 tables (runs, 4, 4)."""
    pos = start_layout(runs, rng)
    wash(pos, seconds, draw_styles(runs, rng, base, washer_cv, fixed), rng)
    walls = build_walls(pos)
    start = np.repeat(np.arange(4), WALL)
    tables = np.zeros((runs, 4, 4), dtype=int)
    for s in range(4):
        for w in range(4):
            tables[:, s, w] = (walls[:, start == s] == w).sum(axis=1)
    return tables


def pooled_tv_distribution(tables, n_trials, rng, reps=2000):
    """TV of experiments of n_trials games, made by resampling simulated games."""
    idx = rng.integers(0, len(tables), size=(reps, n_trials))
    return tv_max(tables[idx].sum(axis=1))


# ---------------------------------------------------------------------------
# 6. Calibrating the simulation to the real data
# ---------------------------------------------------------------------------

def calibrate(groups, rng_seed, rates, runs=300, base=None, washer_cv=0.25):
    """Find the stroke rate that makes the simulated own share match the real one at every real
    washing time. Loss = sum over washing times of ((sim - real) / standard error)^2.
    The same random numbers are reused for every rate (common random numbers), so the loss curve
    is smooth. Returns the best rate, a 95% range of rates the data cannot rule out
    (loss within 3.84 of the minimum), and the full loss curve."""
    real = {}
    for sec, trs in groups.items():
        shares = np.array([own_share(t["table"]) for t in trs])
        se = max(shares.std(ddof=1) / math.sqrt(len(shares)) if len(shares) > 1 else 0.0, 0.005)
        real[sec] = (float(shares.mean()), se)
    curve = []
    for rate in rates:
        loss, fitted = 0.0, {}
        for i, (sec, (mean, se)) in enumerate(real.items()):
            rng = np.random.default_rng([rng_seed, i])                 # common random numbers
            sim = float(own_share(simulate_tables(sec, runs, rng, {**(base or {}), "rate": rate},
                                                  washer_cv)).mean())
            fitted[sec] = sim
            loss += ((sim - mean) / se) ** 2
        curve.append({"rate": float(rate), "loss": loss, "sim_own_share": fitted})
    best = min(curve, key=lambda c: c["loss"])
    ok = [c["rate"] for c in curve if c["loss"] <= best["loss"] + 3.84]
    return {"best_rate": best["rate"], "rate_range": (min(ok), max(ok)), "real": real,
            "best_fit": best["sim_own_share"], "curve": curve}
