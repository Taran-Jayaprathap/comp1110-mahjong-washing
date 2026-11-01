# Mahjong washing: full simulation and analysis model

Built 17 Oct 2026 while the real trials are being collected. Everything runs now on **synthetic placeholder data**; when the real data are in, it is one command.

## Plugging in the real data (the one step)

1. Save the recording sheet as `data/real_trials.csv`, in the format of `experiment-protocol.md` (header in `data/trials_template.csv`): one row per wall, four rows per trial.
   ```
   trial,date,seconds,wall_seat,washer_name,dots,bamboo,characters,honours_flowers
   1,2026-10-24,30,E,Taran,14,8,7,7
   ```
   `seconds` is the washing time of that trial. If you also do the optional half-time trials, just give them their own `seconds` value; the code analyses each washing time separately and treats the one with the most trials as the typical time.
2. Run:
   ```
   python3 run_analysis.py data/real_trials.csv
   ```
   Output goes to `results/real_trials/`: `report.md` (all tables), `summary.json` (every number), and plots.

The script first checks the data: every wall must hold 36 tiles, every suit must total 36 over the four walls, and each trial needs exactly one E, S, W and N row. If anything is wrong it stops and lists every problem with its line number, so you can recount from the photos.

Needs Python 3 with `numpy`; `matplotlib` for the plots (`pip install numpy matplotlib`). The full run takes about 10 minutes; `--quick` checks the pipeline in about 2.

## Files

| File | What it is |
|---|---|
| `run_analysis.py` | The whole analysis, in the order fixed below. |
| `mahjong_model.py` | The library: data checks, statistics, perfect shuffle, washing simulation, calibration. |
| `make_synthetic_data.py` | Makes placeholder data in the real format (40 trials at 30 s plus 15 at 15 s, roles rotating every 10 trials, one invented "lazy" washer). |
| `data/synthetic_trials.csv` | That placeholder data. **Not real; never quote its numbers.** |
| `data/trials_template.csv` | Empty sheet with the right header. |
| `results/synthetic_trials/` | What the report looks like, run on the placeholder data. |

`mc_demo.py` one folder up is the earlier no-library demo; this model replaces it but gives the same perfect-shuffle numbers (40 pooled trials: mean TV 0.022, 95th percentile 0.033).

## Analysis plan (pre-registered, per CX's feedback)

Fixed before the real data arrive; the code does exactly this.

**Randomness measure (primary).** For the pooled trials at one washing time, build the 4×4 table "where tiles started × which wall they ended in". For each starting pile, take the TV distance between where its tiles went and (¼, ¼, ¼, ¼); the measure is the largest of the four.

**Method 1, the answer.** Simulate the same experiment with a perfect shuffle (144 tiles, random order, four walls of 36, same number of trials, pooled) 10,000 times. p-value = share of those at least as uneven as our washes (Monte Carlo p, `(1 + count) / 10,001`). Decision rule: p < 0.05 means "typical washing is not random with respect to position"; otherwise "cannot be told apart from a perfect shuffle" (not "proved random").

**Reported alongside (secondary).** Own-wall share (perfect shuffle: 25%) with a 95% bootstrap CI over trials; chi-square test of independence on the pooled table with Cramér's V, as a cross-check that should agree.

**Washer variation (CX point 2).** At the typical time: does the washer who built a wall, or the seat, explain its own-suit count? (permutation tests, 10,000 shuffles of the labels). Does the own share drift over the session (washers getting lazy)? These are descriptive, since each wall depends on all four washers.

**Method 2, the simulation.** Tiles are points on a square table, starting in the triangle in front of their seat. Each washer has a personal style: stroke rate, stroke size, push distance and reach (how far from their own edge they wash), drawn around a base style with a 25% spread, so every simulated table has its own mix of people. A stroke moves every tile under the hand by one shared random push. Each player then builds a wall from the 36 tiles nearest their edge. Collisions and friction are left out on purpose; the dice break is not simulated because it does not change which tiles are in which wall.

- **Calibration:** the stroke rate is fitted so the simulated own-wall share matches the real one at every real washing time (grid search, common random numbers). The report gives the best rate and the range the data allow. With two washing times, the second one also checks that the model's trend is right.
- **Predictions:** own-wall share and the chance that a 40-trial experiment would call washing non-random, for 0–240 s, and the **washing time needed to look random** (when that chance falls below 50%).
- **What-ifs:** identical washers, bigger differences, one lazy washer, one keen washer.

## Things to know

- The other style settings (stroke size 0.15, push 0.2, reach 0.7 table widths) are guesses. If the group measures stroke sizes from the overhead video, change `DEFAULT_STYLE` in `mahjong_model.py` and rerun.
- With only one real washing time, the simulation is tuned on a single point, so its predictions for other times are extrapolations. The optional 15 half-time trials make them much more trustworthy.
- Detection chances come from resampling simulated games, so they compare against perfect shuffles resampled the same way (explained in `predict_curve`).
- Everything is seeded (`--seed 1110`), so a rerun gives identical numbers.
