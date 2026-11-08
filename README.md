# Does your discard come back to you? Mahjong washing simulation

COMP1110 Group 16 project code (Taran, Pankhuri, Riyaan, Ganesh, Jathin): is Hong Kong mahjong "washing" random enough, and how does tile locality depend on washing time?

| Path | What it is |
|---|---|
| `model/` | Full simulation and analysis model. Start with `model/README.md`. |
| `experiment-protocol.md` | How to run and record the real washing trials. |
| `mc_demo.py` | Earlier small Monte Carlo demo (perfect-shuffle baseline). |
| `ueoka_check.py` | Quick check of the numbers in Ueoka (2022), viXra 2201.0198. |

Quick start: `pip install numpy matplotlib`, then `cd model && python3 run_analysis.py data/synthetic_trials.csv --quick`.

Note: everything in `model/data/synthetic_trials.csv` and `model/results/synthetic_trials/` is invented placeholder data. Do not quote those numbers. Real trials go in `model/data/real_trials.csv`.

## Real trials (added 8 Nov 2026)

- `model/data/real_trials_prelim.csv`: the 10 real trials (20 s washes, two washers E and W).
- `model/results/real_trials_prelim/`: plots of the real data and the main Monte Carlo test (`python3 run_analysis.py data/real_trials_prelim.csv` from `model/`).
- `model/drift/`: the drift ("swirl") model, its fitting script, the fit error definition and the fitted values. See `model/drift/README.md`.
