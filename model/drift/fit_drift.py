"""Fit the drift ("swirl") washing model to the real trials.

Fit error (what is minimised) = Pearson chi-square between the real pooled 4x4 table and the table
the model expects for the same experiment:
    fit_error = sum over the 16 (start pile, end wall) cells of (O - E)^2 / E
    O = real count pooled over all trials, E = n_trials x mean simulated table (at `--runs` tables).
A perfect fit gives about 12 by chance alone (16 cells, 4 row totals fixed). Lower is better.

Grid search over stroke rate and swirl, with common random numbers (the same random seed for every
grid point, so differences between points are not sampling noise). Every setting except rate and
swirl is the default washer style in mahjong_model.py.

Run from model/:  python3 drift/fit_drift.py data/real_trials_prelim.csv
Output: drift/results/fit.json and drift/results/fit_report.md
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import mahjong_model as mm
import drift_model as dm

SEAT_SETS = {"E+W (real seating)": (0, 2), "all four": (0, 1, 2, 3)}
RATES = [4, 5.7, 8, 11.3, 16, 22.6, 32, 45.3, 64, 90.5, 128]            # strokes per second per washer
SWIRLS = [0.0, -0.03, -0.06, -0.09, -0.12, -0.15, -0.2]       # radians, maximum turn per stroke


def fit_error(real, n_trials, seconds, rate, swirl, seats, runs, seed):
    rng = np.random.default_rng([seed, 1])                     # common random numbers
    sim = dm.simulate(seconds, runs, rng, rate, swirl, seats=seats).mean(axis=0)
    expected = n_trials * sim
    return float(((real - expected) ** 2 / expected).sum()), sim.tolist()


def job(args):
    return args, fit_error(*args)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--runs", type=int, default=400, help="simulated tables per grid point")
    ap.add_argument("--seed", type=int, default=1110)
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    a = ap.parse_args()

    trials = mm.load_trials(a.csv)
    secs = sorted({t["seconds"] for t in trials})
    assert len(secs) == 1, "this fit uses one washing time"
    seconds, n = secs[0], len(trials)
    real = sum(np.asarray(t["table"], float) for t in trials)

    tasks = [(real, n, seconds, r, s, seats, a.runs, a.seed)
             for name, seats in SEAT_SETS.items() for r in RATES for s in SWIRLS]
    t0 = time.time()
    with ProcessPoolExecutor(a.workers) as ex:
        out = list(ex.map(job, tasks))
    grid = [{"seats": [k for k, v in SEAT_SETS.items() if v == t[5]][0], "rate": t[3], "swirl": t[4],
             "fit_error": e, "sim_table": sim} for t, (e, sim) in out]

    def best(rows):
        return min(rows, key=lambda g: g["fit_error"])
    summary = {}
    for name in SEAT_SETS:
        rows = [g for g in grid if g["seats"] == name]
        summary[name] = {"best": best(rows), "best_no_swirl": best([g for g in rows if g["swirl"] == 0])}

    res = {"definition": "Pearson chi-square, sum over 16 cells of (O-E)^2/E, E = n_trials x mean simulated table",
           "seconds": seconds, "n_trials": n, "runs_per_point": a.runs, "seed": a.seed,
           "rng": "numpy.random.default_rng (PCG64), seed [seed, 1] at every grid point",
           "real_table": real.tolist(), "summary": summary, "grid": grid}
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", "fit.json"), "w") as f:
        json.dump(res, f, indent=1)

    L = ["# Drift model fit to the real trials", "",
         f"{n} trials at {seconds} s. Fit error = Pearson chi-square over the 16 cells of the pooled "
         f"start-pile x end-wall table, (O - E)^2 / E, with E = {n} x the mean of {a.runs} simulated tables. "
         "About 12 is what a perfect model would get by chance. Grid search, numpy default_rng, "
         f"seed {a.seed}. Run time {time.time() - t0:.0f} s.", "",
         "| Washers | Best stroke rate (/s) | Best swirl (rad) | Fit error | Best fit with no swirl |",
         "|---|---|---|---|---|"]
    for name, s in summary.items():
        b, b0 = s["best"], s["best_no_swirl"]
        L.append(f"| {name} | {b['rate']} | {b['swirl']} | {b['fit_error']:.1f} | "
                 f"{b0['fit_error']:.1f} (rate {b0['rate']}) |")
    L += ["", "Fit error by rate and swirl, E+W washers:", "",
          "| rate \\ swirl | " + " | ".join(str(s) for s in SWIRLS) + " |",
          "|---" * (len(SWIRLS) + 1) + "|"]
    for r in RATES:
        row = [g for g in grid if g["seats"].startswith("E+W") and g["rate"] == r]
        row.sort(key=lambda g: SWIRLS.index(g["swirl"]))
        L.append(f"| {r} | " + " | ".join(f"{g['fit_error']:.1f}" for g in row) + " |")
    with open(os.path.join(HERE, "results", "fit_report.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
