"""The whole pre-registered analysis in one step (COMP1110 Group 16, mahjong washing).

    python3 run_analysis.py data/real_trials.csv        # the real data, when it exists
    python3 run_analysis.py                             # synthetic placeholder data
    python3 run_analysis.py data/real_trials.csv --quick   # fast check (fewer runs, ~1 min)

Writes results/<data file name>/report.md, summary.json and the plots.
Steps (fixed in advance, see README.md "Analysis plan"):
  1. read and check the data (every wall and every suit must total 36)
  2. Method 1: pooled TV vs 10,000 perfect-shuffle experiments of the same size -> p-value,
     with own-wall share, bootstrap CIs and a chi-square cross-check, for each washing time
  3. washer variation in the real data: washer, seat and drift permutation tests
  4. Method 2: fit the washing simulation's stroke rate to the real data
  5. use the fitted simulation to predict other washing times and washer mixes
"""
import argparse
import json
import math
import os
import time
import numpy as np
import mahjong_model as m

HERE = os.path.dirname(os.path.abspath(__file__))
ALPHA = 0.05
PREDICT_SECONDS = [0, 5, 10, 15, 20, 30, 45, 60, 90, 120, 180, 240]


def fmt_p(p, runs):
    return f"< {1 / runs:.4f}" if p <= 1 / (runs + 1) + 1e-12 else f"{p:.4f}"


def predict_curve(rate, seconds_list, n_trials, runs, seed, washer_cv):
    """Simulated own share and detection chance for each washing time, at a given stroke rate.
    Experiments of n_trials games are made by resampling `runs` simulated games, which makes their
    TV a little larger than truly separate experiments would. So the detection threshold comes from
    perfect-shuffle games resampled the same way (same pool size): a fully mixed simulation then
    scores about 5%, as it should."""
    rng = np.random.default_rng([seed, 5])
    null_95 = float(np.percentile(m.pooled_tv_distribution(m.perfect_shuffle_tables(runs, rng), n_trials, rng), 95))
    rows = []
    for i, sec in enumerate(seconds_list):
        rng = np.random.default_rng([seed, 7, i])
        tabs = m.simulate_tables(sec, runs, rng, {"rate": rate}, washer_cv)
        share = m.own_share(tabs)
        pooled = m.pooled_tv_distribution(tabs, n_trials, rng)
        rows.append({"seconds": sec, "own_share_mean": float(share.mean()),
                     "own_share_lo": float(np.percentile(share, 2.5)),
                     "own_share_hi": float(np.percentile(share, 97.5)),
                     "pooled_tv_median": float(np.median(pooled)),
                     "pooled_tv_lo": float(np.percentile(pooled, 2.5)),
                     "pooled_tv_hi": float(np.percentile(pooled, 97.5)),
                     "detect_chance": float((pooled > null_95).mean())})
    return rows


def seconds_needed(curve):
    """Shortest simulated time at which a 40-trial experiment would detect non-randomness less
    than half the time, interpolated between grid points. None if never reached."""
    for a, b in zip(curve, curve[1:]):
        if a["detect_chance"] >= 0.5 > b["detect_chance"]:
            f = (a["detect_chance"] - 0.5) / (a["detect_chance"] - b["detect_chance"])
            return a["seconds"] + f * (b["seconds"] - a["seconds"])
    return curve[0]["seconds"] if curve[0]["detect_chance"] < 0.5 else None


def washer_scenarios(rate, seconds, runs, seed):
    """What-ifs for CX's washer-variation point, at the typical time and the fitted rate."""
    out = {}
    base = {**m.DEFAULT_STYLE, "rate": rate}
    cases = {
        "identical washers": dict(washer_cv=0.0),
        "typical differences (25%)": dict(washer_cv=0.25),
        "large differences (50%)": dict(washer_cv=0.5),
        "one lazy washer at E (30% of the rate)": dict(fixed=[{**base, "rate": rate * 0.3}] + [base] * 3),
        "one keen washer at E (twice the rate)": dict(fixed=[{**base, "rate": rate * 2}] + [base] * 3),
    }
    for i, (name, kw) in enumerate(cases.items()):
        rng = np.random.default_rng([seed, 9, i])
        tabs = m.simulate_tables(seconds, runs, rng, {"rate": rate}, **kw)
        diag = np.diagonal(tabs, axis1=1, axis2=2) / m.WALL
        out[name] = {"own_share": float(m.own_share(tabs).mean()),
                     "own_share_E_wall": float(diag[:, 0].mean()),
                     "own_share_other_walls": float(diag[:, 1:].mean())}
    return out


def make_plots(outdir, tests, calib, curves, null_95_main, main_sec, washer_test, real_groups):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker
    except ImportError:
        print("matplotlib not installed: skipping plots (pip install matplotlib)")
        return []
    files = []
    blue, grey, orange = "#2a6fdb", "#8a8a8a", "#e07b00"

    for sec, t in tests.items():                                   # 1. Monte Carlo test
        fig, ax = plt.subplots(figsize=(6.4, 3.8))
        ax.hist(t["null_tv"], bins=60, color=grey, alpha=0.8, label=f"{len(t['null_tv']):,} perfect shuffles")
        ax.axvline(t["null_95"], color=grey, ls="--", lw=1, label="95th percentile")
        ax.axvline(t["tv"], color=orange, lw=2, label=f"our washes (p {fmt_p(t['p'], len(t['null_tv']))})")
        ax.set_xlabel(f"pooled TV distance from random ({t['n_trials']} trials)")
        ax.set_ylabel("count")
        ax.set_title(f"Monte Carlo test, {sec:g} s washing")
        ax.legend(frameon=False, fontsize=8)
        fig.tight_layout()
        files.append(f"mc_test_{sec:g}s.png")
        fig.savefig(os.path.join(outdir, files[-1]), dpi=150)
        plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))               # 2. headline: vs washing time
    best = curves["best"]
    xs = [r["seconds"] for r in best]
    ax = axes[0]
    for key, ls in (("low", ":"), ("high", ":")):
        ax.plot(xs, [r["own_share_mean"] for r in curves[key]], color=blue, ls=ls, lw=1)
    ax.fill_between(xs, [r["own_share_lo"] for r in best], [r["own_share_hi"] for r in best],
                    color=blue, alpha=0.15, label="simulation, 95% of single washes")
    ax.plot(xs, [r["own_share_mean"] for r in best], color=blue, lw=2, label="simulation (fitted), mean")
    ax.axhline(0.25, color=grey, ls="--", lw=1, label="perfect shuffle (25%)")
    for sec, t in tests.items():
        lo, hi = t["own_share_ci"]
        ax.errorbar([sec], [t["own_share"]], yerr=[[t["own_share"] - lo], [hi - t["own_share"]]],
                    fmt="o", color=orange, capsize=4, label="our washes, 95% CI" if sec == min(tests) else None)
    ax.set_xlabel("washing time (s)")
    ax.set_ylabel("share of tiles back in own wall")
    ax.set_ylim(0, 1)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Do tiles come back to you?")
    ax = axes[1]
    ax.fill_between(xs, [r["pooled_tv_lo"] for r in best], [r["pooled_tv_hi"] for r in best],
                    color=blue, alpha=0.15)
    ax.plot(xs, [r["pooled_tv_median"] for r in best], color=blue, lw=2, label="simulation (fitted)")
    ax.axhline(null_95_main, color=grey, ls="--", lw=1, label="perfect shuffle, 95th percentile")
    for sec, t in tests.items():
        ax.plot([sec], [t["tv"]], "o", color=orange, label="our washes" if sec == min(tests) else None)
    ax.set_xlabel("washing time (s)")
    ax.set_ylabel("pooled TV distance (40 trials)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%.2f"))
    ax.yaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_yticks([0.02, 0.05, 0.1, 0.2, 0.5])
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Distance from random")
    fig.tight_layout()
    files.append("headline_vs_time.png")
    fig.savefig(os.path.join(outdir, files[-1]), dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.6))                     # 3. calibration
    c = sorted(calib["curve"], key=lambda r: r["rate"])
    ax.plot([r["rate"] for r in c], [r["loss"] for r in c], "o-", color=blue, ms=3)
    ax.axvspan(*calib["rate_range"], color=blue, alpha=0.1, label="rates the data allow (95%)")
    ax.axvline(calib["best_rate"], color=orange, label=f"best fit {calib['best_rate']:.2f} strokes/s")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("stroke rate per washer (strokes per second)")
    ax.set_ylabel("misfit (sum of squared z)")
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Calibrating the washing simulation")
    fig.tight_layout()
    files.append("calibration.png")
    fig.savefig(os.path.join(outdir, files[-1]), dpi=150)
    plt.close(fig)

    g = washer_test["by_group"]                                    # 4. washers
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.bar(list(g), [v for v in g.values()], color=blue)
    ax.axhline(0.25, color=grey, ls="--", lw=1, label="perfect shuffle")
    ax.set_ylabel("own-suit share in the wall they built")
    ax.set_title(f"Washer differences at {main_sec:g} s (permutation p {washer_test['p']:.3f})")
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    files.append("washers.png")
    fig.savefig(os.path.join(outdir, files[-1]), dpi=150)
    plt.close(fig)
    return files


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", nargs="?", default=os.path.join(HERE, "data", "synthetic_trials.csv"))
    ap.add_argument("--out", help="output folder (default results/<data file name>)")
    ap.add_argument("--runs", type=int, default=10000, help="perfect-shuffle experiments (default 10000)")
    ap.add_argument("--sim-runs", type=int, default=300, help="simulated washes per setting (default 300)")
    ap.add_argument("--washer-cv", type=float, default=0.25, help="spread of washer styles in the simulation")
    ap.add_argument("--quick", action="store_true", help="fewer runs, for checking the pipeline")
    ap.add_argument("--seed", type=int, default=1110)
    args = ap.parse_args()
    if args.quick:
        args.runs, args.sim_runs = 2000, 80
    t0 = time.time()
    name = os.path.splitext(os.path.basename(args.data))[0]
    outdir = args.out or os.path.join(HERE, "results", name)
    os.makedirs(outdir, exist_ok=True)
    synthetic = "synthetic" in name.lower()
    rng = np.random.default_rng(args.seed)

    # 1. data
    try:
        trials = m.load_trials(args.data)
    except m.DataError as e:
        raise SystemExit(f"STOP: {e}")
    groups = m.group_by_seconds(trials)
    main_sec = max(groups, key=lambda s: (len(groups[s]), s))     # the typical time = most trials
    print(f"read {len(trials)} trials: " + ", ".join(f"{len(v)} at {k:g} s" for k, v in groups.items()))

    # 2. Method 1
    tests = {sec: m.monte_carlo_test(trs, rng, args.runs) for sec, trs in groups.items()}
    # 3. washer variation in the real data (main condition)
    recs = m.wall_records(groups[main_sec])
    washer_test = m.group_effect_test(recs, "washer", rng)
    seat_test = m.group_effect_test(recs, "seat", rng)
    drift = m.drift_test(groups[main_sec], rng)
    print(f"Method 1 done ({time.time() - t0:.0f} s); calibrating the simulation...")

    # 4. calibration: coarse grid, then a finer one around the best
    coarse = [0.25 * 2 ** k for k in range(10)]                   # 0.25 .. 128 strokes/s
    cal = m.calibrate(groups, args.seed, coarse, args.sim_runs // 2, washer_cv=args.washer_cv)
    fine = [cal["best_rate"] * 2 ** (k / 4) for k in range(-4, 5)]
    cal2 = m.calibrate(groups, args.seed, fine, args.sim_runs, washer_cv=args.washer_cv)
    cal2["curve"] += [c for c in cal["curve"] if not fine[0] <= c["rate"] <= fine[-1]]
    cal = cal2
    print(f"best stroke rate {cal['best_rate']:.2f}/s ({time.time() - t0:.0f} s); predicting...")

    # 5. predictions
    n_main = len(groups[main_sec])
    null_95_main = tests[main_sec]["null_95"]
    secs = sorted(set(PREDICT_SECONDS) | set(groups))
    curves = {k: predict_curve(r, secs, n_main, args.sim_runs, args.seed, args.washer_cv)
              for k, r in (("best", cal["best_rate"]), ("low", cal["rate_range"][0]),
                           ("high", cal["rate_range"][1]))}
    needed = {k: seconds_needed(c) for k, c in curves.items()}
    scenarios = washer_scenarios(cal["best_rate"], main_sec, args.sim_runs, args.seed)
    plots = make_plots(outdir, tests, cal, curves, null_95_main, main_sec, washer_test, groups)

    # report
    L = []
    if synthetic:
        L += ["> **SYNTHETIC PLACEHOLDER DATA.** These numbers come from `make_synthetic_data.py`, not from "
              "real washing. They only show what the report will look like. Do not quote them.", ""]
    L += [f"# Mahjong washing: analysis report", "",
          f"Data: `{os.path.basename(args.data)}`, {len(trials)} trials "
          f"({', '.join(f'{len(v)} at {k:g} s' for k, v in groups.items())}). "
          f"Typical (main) washing time: {main_sec:g} s. Perfect-shuffle runs: {args.runs:,}. "
          f"Seed {args.seed}.", "",
          "## 1. Is washing random? (Method 1, Monte Carlo test)", "",
          "| Washing time | Trials | Own-wall share (95% CI) | Pooled TV (95% CI) | Perfect shuffle: mean TV, 95th pct | p-value | Verdict |",
          "|---|---|---|---|---|---|---|"]
    for sec, t in tests.items():
        verdict = "not random" if t["p"] < ALPHA else "cannot tell from a perfect shuffle"
        L.append(f"| {sec:g} s | {t['n_trials']} | {t['own_share']:.1%} ({t['own_share_ci'][0]:.1%}–{t['own_share_ci'][1]:.1%}) "
                 f"| {t['tv']:.3f} ({t['tv_ci'][0]:.3f}–{t['tv_ci'][1]:.3f}) | {t['null_mean']:.3f}, {t['null_95']:.3f} "
                 f"| {fmt_p(t['p'], args.runs)} | {verdict} |")
    L += ["", "Chi-square cross-check (pooled 4×4 table, df 9):", ""]
    for sec, t in tests.items():
        c = t["chi_square"]
        L.append(f"- {sec:g} s: χ² = {c['chi2']:.1f}, p = {c['p']:.2g}, Cramér's V = {c['cramers_v']:.3f}")
    L += ["", f"Pooled table at {main_sec:g} s (rows = where tiles started, columns = wall they ended in):", "",
          "| start \\ wall | E | S | W | N |", "|---|---|---|---|---|"]
    for s in range(4):
        L.append(f"| {m.SEATS[s]} ({m.SUITS[s]}) | " + " | ".join(str(v) for v in tests[main_sec]["pooled_table"][s]) + " |")
    L += ["", f"## 2. Do washers differ? (real data, {main_sec:g} s)", "",
          "| Washer | Walls built | Own-suit share in their wall |", "|---|---|---|"]
    for g, v in washer_test["by_group"].items():
        L.append(f"| {g} | {washer_test['n_walls'][g]} | {v:.1%} |")
    L += ["", f"- Washer effect: permutation p = {washer_test['p']:.3f}",
          f"- Seat effect (E/S/W/N): permutation p = {seat_test['p']:.3f} "
          f"(by seat: {', '.join(f'{k} {v:.1%}' for k, v in seat_test['by_group'].items())})",
          f"- Drift over the session: r = {drift['r']:+.2f}, p = {drift['p']:.3f}",
          "", "Each wall's count depends on all four washers at once, so these tests are descriptive.", "",
          "## 3. Washing simulation fitted to our data (Method 2)", "",
          f"Fitted stroke rate: **{cal['best_rate']:.2f} strokes per second per washer** "
          f"(rates the data allow: {cal['rate_range'][0]:.2f}–{cal['rate_range'][1]:.2f}). "
          f"Other style settings fixed at {m.DEFAULT_STYLE | {'rate': 'fitted'}}, washer spread {args.washer_cv:.0%}.", "",
          "| Washing time | Real own-wall share | Simulated (fitted) |", "|---|---|---|"]
    for sec, (mean, se) in cal["real"].items():
        L.append(f"| {sec:g} s | {mean:.1%} ± {1.96 * se:.1%} | {cal['best_fit'][sec]:.1%} |")
    L += ["", f"Predictions (fitted rate; detection chance = how often a {n_main}-trial experiment would call it not random):", "",
          "| Washing time | Own-wall share, mean (95% of washes) | Pooled TV, median | Detection chance |",
          "|---|---|---|---|"]
    for r in curves["best"]:
        L.append(f"| {r['seconds']:g} s | {r['own_share_mean']:.1%} ({r['own_share_lo']:.0%}–{r['own_share_hi']:.0%}) "
                 f"| {r['pooled_tv_median']:.3f} | {r['detect_chance']:.0%} |")

    def show(x):
        return f"about {x:.0f} s" if x is not None else f"more than {secs[-1]} s"
    L += ["", f"**Washing time needed to look random** (a {n_main}-trial test would detect non-randomness "
          f"less than half the time): {show(needed['best'])} at the fitted rate; "
          f"{show(needed['high'])} to {show(needed['low'])} across the rates the data allow.", "",
          f"## 4. What if the washers were different? (simulation, {main_sec:g} s)", "",
          "| Washers | Own-wall share | E wall | Other walls |", "|---|---|---|---|"]
    for k, v in scenarios.items():
        L.append(f"| {k} | {v['own_share']:.1%} | {v['own_share_E_wall']:.1%} | {v['own_share_other_walls']:.1%} |")
    if plots:
        L += ["", "## Plots", ""] + [f"![{p}]({p})" for p in plots]
    L += ["", f"_Run time {time.time() - t0:.0f} s._"]
    with open(os.path.join(outdir, "report.md"), "w") as f:
        f.write("\n".join(L) + "\n")

    def clean(t):
        return {k: (v.tolist() if isinstance(v, np.ndarray) else v) for k, v in t.items() if k != "null_tv"}
    summary = {"data": os.path.basename(args.data), "synthetic": synthetic, "main_seconds": main_sec,
               "method1": {f"{k:g}": clean(v) for k, v in tests.items()},
               "washer_test": washer_test, "seat_test": seat_test, "drift": drift,
               "calibration": {k: v for k, v in cal.items() if k != "curve"}, "calibration_curve": cal["curve"],
               "predictions": curves, "seconds_needed": needed, "washer_scenarios": scenarios}
    with open(os.path.join(outdir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=lambda o: {str(k): v for k, v in o.items()} if isinstance(o, dict) else str(o))
    print(f"done in {time.time() - t0:.0f} s -> {outdir}/report.md")


if __name__ == "__main__":
    main()
