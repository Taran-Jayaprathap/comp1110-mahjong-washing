# Drift model fit to the real trials

10 trials at 20.0 s. Fit error = Pearson chi-square over the 16 cells of the pooled start-pile x end-wall table, (O - E)^2 / E, with E = 10 x the mean of 400 simulated tables. About 12 is what a perfect model would get by chance. Grid search, numpy default_rng, seed 1110. Run time 1021 s.

| Washers | Best stroke rate (/s) | Best swirl (rad) | Fit error | Best fit with no swirl |
|---|---|---|---|---|
| E+W (real seating) | 32 | -0.09 | 27.8 | 65.4 (rate 128) |
| all four | 16 | -0.06 | 25.9 | 57.4 (rate 45.3) |

Fit error by rate and swirl, E+W washers:

| rate \ swirl | 0.0 | -0.03 | -0.06 | -0.09 | -0.12 | -0.15 | -0.2 |
|---|---|---|---|---|---|---|---|
| 4 | 1220.9 | 1147.7 | 1054.5 | 1016.5 | 945.8 | 856.4 | 755.3 |
| 5.7 | 894.5 | 804.8 | 745.3 | 695.0 | 622.0 | 554.7 | 412.1 |
| 8 | 652.0 | 579.9 | 507.4 | 441.3 | 380.7 | 316.6 | 207.5 |
| 11.3 | 420.1 | 357.4 | 300.2 | 220.2 | 167.4 | 128.6 | 76.4 |
| 16 | 285.4 | 216.8 | 151.7 | 106.7 | 69.9 | 54.0 | 54.8 |
| 22.6 | 193.8 | 119.9 | 72.8 | 41.3 | 37.9 | 47.8 | 71.3 |
| 32 | 120.9 | 64.2 | 29.5 | 27.8 | 43.5 | 63.8 | 77.4 |
| 45.3 | 81.2 | 43.5 | 31.1 | 50.1 | 64.1 | 72.2 | 75.8 |
| 64 | 68.3 | 33.6 | 40.4 | 64.7 | 80.7 | 77.6 | 73.5 |
| 90.5 | 65.7 | 49.3 | 57.4 | 69.2 | 59.6 | 61.6 | 67.0 |
| 128 | 65.4 | 58.5 | 60.4 | 69.8 | 65.0 | 66.6 | 66.0 |
