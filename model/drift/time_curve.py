"""Washing-time predictions from the fitted drift model (best fit in results/fit.json, East + West).

For each washing time: simulate RUNS tables, then
  * destination shares: share of tiles ending in their own wall, the next seat's, the opposite and the
    previous seat's wall (drift_model.offsets), mean over the simulated tables;
  * detection rate: resample 10,000 pretend experiments of n tables (n = 10 and 40), compute the largest
    TV distance T of each pooled table, and count how often T is above the perfect-shuffle 95% cutoff
    for that experiment size (the main test's p < 0.05 decision rule).
Run from model/:  python3 drift/time_curve.py data/real_trials_prelim.csv
Output: drift/results/time_curve.json, time_curve.csv, sim_drift_vs_time.png
"""
import csv, json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
import mahjong_model as mm
import drift_model as dm

SEED, RUNS, EXPERIMENTS = 1110, 800, 10000
TIMES = [0, 10, 20, 25, 30, 35, 40, 45, 50, 60, 90, 120]
SIZES = [10, 40]


def sim(args):
    i, seconds, rate, swirl = args
    return seconds, dm.simulate(seconds, RUNS, np.random.default_rng([SEED, 30, i]), rate, swirl, seats=(0, 2))


if __name__ == "__main__":
    trials = mm.load_trials(sys.argv[1])
    real = sum(np.asarray(t["table"], float) for t in trials)
    best = json.load(open(os.path.join(HERE, "results", "fit.json")))["summary"]["E+W (real seating)"]["best"]
    rate, swirl = best["rate"], best["swirl"]

    rng0 = np.random.default_rng([SEED, 31])
    cutoff = {n: float(np.percentile(mm.tv_max(mm.perfect_shuffle_pooled(n, rng0, EXPERIMENTS)), 95)) for n in SIZES}

    with ProcessPoolExecutor(os.cpu_count()) as ex:
        sims = dict(ex.map(sim, [(i, s, rate, swirl) for i, s in enumerate(TIMES)]))

    rng = np.random.default_rng([SEED, 32])
    rows = []
    for s in TIMES:
        tabs = sims[s]
        off = dm.offsets(tabs)
        row = {"seconds": s, "own": float(off[:, 0].mean()), "next_seat": float(off[:, 1].mean()),
               "opposite": float(off[:, 2].mean()), "previous_seat": float(off[:, 3].mean())}
        for n in SIZES:
            T = mm.tv_max(tabs[rng.integers(0, len(tabs), (EXPERIMENTS, n))].sum(axis=1))
            row[f"median_T_{n}"] = float(np.median(T))
            row[f"detect_{n}"] = float((T > cutoff[n]).mean())
        rows.append(row)

    real_off = dm.offsets(real / len(trials))[0]
    def crossing(key):
        """First washing time (linear interpolation) at which detection drops below 50%."""
        for a, b in zip(rows, rows[1:]):
            if a[key] >= 0.5 > b[key]:
                return a["seconds"] + (a[key] - 0.5) / (a[key] - b[key]) * (b["seconds"] - a["seconds"])
        return None
    out = {"rate": rate, "swirl": swirl, "seats": "E+W", "seed": SEED, "tables_per_time": RUNS,
           "experiments": EXPERIMENTS, "perfect_95_cutoff": cutoff,
           "real_shares_20s": dict(zip(["own", "next_seat", "opposite", "previous_seat"], map(float, real_off))),
           "detect_below_50pct_after_s": {n: crossing(f"detect_{n}") for n in SIZES}, "rows": rows}
    R = os.path.join(HERE, "results")
    json.dump(out, open(os.path.join(R, "time_curve.json"), "w"), indent=1)
    with open(os.path.join(R, "time_curve.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    t = [r["seconds"] for r in rows]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    for key, lab, c, m in [("own", "own wall", "#2c3e50", "o"), ("previous_seat", "wall of previous seat (drift)", "#c0392b", "s"),
                           ("next_seat", "wall of next seat", "#27ae60", "^"), ("opposite", "opposite wall", "#8e44ad", "D")]:
        a1.plot(t, [100 * r[key] for r in rows], marker=m, color=c, label=lab)
        a1.plot([20], [100 * out["real_shares_20s"][key]], marker=m, color=c, mfc="white", ms=11, ls="none")
    a1.axhline(25, ls="--", color="grey", lw=1); a1.set_ylim(0, 60)
    a1.set_xlabel("Washing time (s)"); a1.set_ylabel("% of tiles"); a1.legend(fontsize=9)
    a1.text(22, 40, "hollow markers = your 10 trials (20 s)", fontsize=9)
    a1.set_title(f"Where a starting pile ends up (model: E+W, {rate:g}/s, swirl {swirl:g})", fontsize=10)
    for n, c, m in [(10, "#c0392b", "o"), (40, "#2c3e50", "s")]:
        a2.plot(t, [100 * r[f"detect_{n}"] for r in rows], marker=m, color=c, label=f"{n}-trial experiment")
    a2.axhline(50, ls="--", color="grey", lw=1); a2.axvline(20, ls=":", color="grey", lw=1)
    a2.text(21, 8, "your 20 s", fontsize=9); a2.set_ylim(0, 105)
    a2.set_xlabel("Washing time (s)"); a2.set_ylabel('Chance the test says "not random" (%)'); a2.legend(fontsize=9)
    a2.set_title("How long washing must last to pass the test", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(R, "sim_drift_vs_time.png"), dpi=150)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
    for r in rows: print(r)
