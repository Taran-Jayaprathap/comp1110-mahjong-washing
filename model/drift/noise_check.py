"""How much of the fit error is Monte Carlo noise? Re-evaluates the best points with 4 other seeds.
Run from model/ after fit_drift.py:  python3 drift/noise_check.py data/real_trials_prelim.csv"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import fit_drift as fd

if __name__ == "__main__":
    fit = json.load(open(os.path.join(HERE, "results", "fit.json")))
    trials = fd.mm.load_trials(sys.argv[1]); real = sum(np.asarray(t["table"], float) for t in trials)
    pts = []
    for name, s in fit["summary"].items():
        for key in ("best", "best_no_swirl"):
            pts.append((name, key, s[key]["rate"], s[key]["swirl"]))
    tasks = [(real, len(trials), fit["seconds"], r, sw, fd.SEAT_SETS[n], fit["runs_per_point"], seed)
             for n, k, r, sw in pts for seed in (1111, 1112, 1113, 1114)]
    with ProcessPoolExecutor() as ex:
        errs = [e for _, (e, _) in ex.map(fd.job, tasks)]
    out = []
    for i, (n, k, r, sw) in enumerate(pts):
        e = errs[4 * i:4 * i + 4]
        out.append({"seats": n, "point": k, "rate": r, "swirl": sw, "other_seeds": e,
                    "mean": float(np.mean(e)), "sd": float(np.std(e, ddof=1))})
    json.dump(out, open(os.path.join(HERE, "results", "noise_check.json"), "w"), indent=1)
    for o in out:
        print(f"{o['seats']:20s} {o['point']:14s} rate {o['rate']:6} swirl {o['swirl']:6}  "
              f"fit error over 4 other seeds: {o['mean']:.1f} +/- {o['sd']:.1f}")
