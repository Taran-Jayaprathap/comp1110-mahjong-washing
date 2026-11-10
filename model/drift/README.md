# Drift ("swirl") model, fitted to the 10 real trials

Real data: `../data/real_trials_prelim.csv` (10 trials, 26 Oct 2026, 20 s washes, two washers on the
East and West sides, tiles re-sorted before every trial; 1,440 tiles counted from photos).

| File | What it does |
|---|---|
| `drift_model.py` | The washing simulation from `../mahjong_model.py` plus one parameter, `swirl`: each stroke also turns the tiles under the hand about the table centre by `swirl x U(0,1)` radians (negative = clockwise in the model's frame). |
| `fit_drift.py` | Grid search over stroke rate and swirl. Writes `results/fit.json` and `results/fit_report.md`. |
| `typical_tv.py` | Typical largest TV distance (T) the fitted model gives for a 10-trial experiment at 20 s. Writes `results/typical_tv.json`. |
| `time_curve.py` | Washing-time predictions at the best fit: destination shares and the chance a 10- or 40-trial test says "not random", for 0-120 s. Writes `results/time_curve.json`, `time_curve.csv`, `sim_drift_vs_time.png`. |
| `noise_check.py` | Re-scores the best points with 4 other seeds, to show how much of the fit error is simulation noise. |

Reproduce (from `model/`, about 20 min on 4 cores):

    python3 drift/fit_drift.py data/real_trials_prelim.csv
    python3 drift/noise_check.py data/real_trials_prelim.csv
    python3 drift/typical_tv.py data/real_trials_prelim.csv
    python3 drift/time_curve.py data/real_trials_prelim.csv     # about 4 min

## Fit error

Pearson chi-square between the real pooled 4x4 table (start pile x end wall, all 10 trials added up)
and what the model expects for the same experiment:

    fit error = sum over the 16 cells of (O - E)^2 / E
    O = real count, E = 10 x the mean of 400 simulated tables

Lower is better. A model that was exactly right would still score about 12 by chance (16 cells, 4 row
totals fixed). Random numbers: `numpy.random.default_rng` (PCG64), seed `[1110, 1]` at every grid point
(common random numbers, so grid points are compared on the same random draws). Stroke radius 0.15,
push 0.2, reach 0.7 and the 25% washer spread are fixed guesses from `mahjong_model.DEFAULT_STYLE`.

## Results (seed 1110, 400 tables per point)

| Washers | Best stroke rate | Best swirl | Fit error | Same, 4 other seeds | Best with no swirl |
|---|---|---|---|---|---|
| E+W (real seating) | 32 /s per washer | -0.09 rad | 27.8 | 28.4 +/- 2.2 | 65.4 (63.5 +/- 4.7 over 4 seeds) |
| All four | 16 /s per washer | -0.06 rad | 25.9 | 23.5 +/- 3.5 | 57.4 (58.9 +/- 6.5 over 4 seeds) |

- The swirl roughly halves the fit error (about 28 vs about 64 for the real seating). Without it no
  stroke rate gets close: the no-swirl error levels off around 65 even at 128 strokes/s.
- E+W and four washers fit about equally well; the difference is within simulation noise, so this fit
  cannot tell the seating from the data.
- Only one washing time (20 s) was measured, and the grid is coarse (rates step by x1.41, swirl by
  0.03 rad), so treat 32 /s and -0.09 rad as rough values.

## Typical T at the best fit

1,600 simulated tables at 32 /s, swirl -0.09, E+W; 10,000 pretend 10-trial experiments resampled from
them (seed 1110). Median T = 0.108 (quartiles 0.092 to 0.125); the real T is 0.111. 95% of simulated
experiments are above the perfect-shuffle 95% cutoff of 0.067. T was not used in the fit.

Full grid: `results/fit_report.md`.

## Washing-time predictions at the best fit

`time_curve.py`, seed 1110, 800 simulated tables per washing time, 10,000 resampled experiments per point.
"Detected" = largest TV distance above the perfect-shuffle 95% cutoff (0.067 for 10 trials, 0.033 for 40).

Where tiles end up at 20 s:

| | Own wall | Next seat | Opposite | Previous seat |
|---|---|---|---|---|
| Real 10 trials | 25.3% | 20.3% | 23.1% | 31.3% |
| Model | 24.4% | 19.9% | 25.2% | 30.5% |

| Time (s) | 10 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 60 | 90 | 120 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Detected, 10 trials | 100% | 93% | 80% | 68% | 54% | 44% | 34% | 38% | 32% | 29% | 30% |
| Detected, 40 trials | 100% | 100% | 99.7% | 98% | 85% | 70% | 48% | 54% | 38% | 39% | 43% |

- Detection drops below 50% after about 37 s for a 10-trial experiment and about 45 s for 40 trials.
- It levels off around 30% (10 trials) and 40% (40 trials), not 5%: in the model, tiles pressed against the
  table edge never fully mix. The 50 s bump is noise around that floor.
- Fitted at one washing time (20 s) only, so other times are extrapolations; treat them as rough.
