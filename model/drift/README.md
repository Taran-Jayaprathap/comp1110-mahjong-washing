# Drift ("swirl") model, fitted to the 10 real trials

Real data: `../data/real_trials_prelim.csv` (10 trials, 26 Oct 2026, 20 s washes, two washers on the
East and West sides, tiles re-sorted before every trial; 1,440 tiles counted from photos).

| File | What it does |
|---|---|
| `drift_model.py` | The washing simulation from `../mahjong_model.py` plus one parameter, `swirl`: each stroke also turns the tiles under the hand about the table centre by `swirl x U(0,1)` radians (negative = clockwise in the model's frame). |
| `fit_drift.py` | Grid search over stroke rate and swirl. Writes `results/fit.json` and `results/fit_report.md`. |
| `noise_check.py` | Re-scores the best points with 4 other seeds, to show how much of the fit error is simulation noise. |

Reproduce (from `model/`, about 20 min on 4 cores):

    python3 drift/fit_drift.py data/real_trials_prelim.csv
    python3 drift/noise_check.py data/real_trials_prelim.csv

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

Full grid: `results/fit_report.md`.
