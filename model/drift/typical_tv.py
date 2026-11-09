"""Typical largest TV distance (T) the fitted drift model gives for an experiment like ours.

Simulates 1,600 tables at the best fit in results/fit.json (East + West washers), then makes 10,000
pretend experiments by resampling `n_trials` tables each and computes T = mahjong_model.tv_max of the
pooled table. Compares with the real T and the perfect-shuffle 95% cutoff from the main test.
Run from model/:  python3 drift/typical_tv.py data/real_trials_prelim.csv
Output: drift/results/typical_tv.json
"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..')); sys.path.insert(0, HERE)
import mahjong_model as mm
import drift_model as dm

SEED, CHUNKS, RUNS = 1110, 4, 400
PERFECT_95 = 0.067                     # 95th percentile of T under perfect shuffles, 10 trials (main test)


def chunk(args):
    i, seconds, rate, swirl = args
    return dm.simulate(seconds, RUNS, np.random.default_rng([SEED, 20, i]), rate, swirl, seats=(0, 2))


if __name__ == "__main__":
    trials = mm.load_trials(sys.argv[1])
    n, seconds = len(trials), trials[0]["seconds"]
    real_T = float(mm.tv_max(sum(np.asarray(t["table"], float) for t in trials)))
    best = json.load(open(os.path.join(HERE, "results", "fit.json")))["summary"]["E+W (real seating)"]["best"]
    with ProcessPoolExecutor(CHUNKS) as ex:
        tabs = np.concatenate(list(ex.map(chunk, [(i, seconds, best["rate"], best["swirl"]) for i in range(CHUNKS)])))
    rng = np.random.default_rng([SEED, 21])
    T = mm.tv_max(tabs[rng.integers(0, len(tabs), (10000, n))].sum(axis=1))
    out = {"rate": best["rate"], "swirl": best["swirl"], "seconds": seconds, "n_trials": n,
           "simulated_tables": int(len(tabs)), "experiments": 10000, "seed": SEED,
           "median_T": float(np.median(T)), "mean_T": float(T.mean()),
           "quartiles_T": [float(q) for q in np.percentile(T, [25, 75])],
           "real_T": real_T, "share_at_or_above_real": float((T >= real_T).mean()),
           "share_above_perfect_95": float((T > PERFECT_95).mean())}
    json.dump(out, open(os.path.join(HERE, "results", "typical_tv.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))
