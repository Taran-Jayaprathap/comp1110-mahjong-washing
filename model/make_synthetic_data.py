"""Make PLACEHOLDER data in exactly the recording format of experiment-protocol.md.

The numbers come from the washing simulation with made-up washer styles, so the analysis can be
built and tested before the real trials exist. Never report these numbers as results.

Run: python3 make_synthetic_data.py            (writes data/synthetic_trials.csv)
     python3 make_synthetic_data.py --no-half  (only the 40 main trials)
"""
import argparse
import csv
import os
import numpy as np
import mahjong_model as m

MEMBERS = ["Taran", "Pankhuri", "Riyaan", "Ganesh", "Jathin"]
# Invented "true" styles: a stroke-rate multiplier per person (Jathin washes lazily).
PERSONAL_RATE = {"Taran": 1.0, "Pankhuri": 1.2, "Riyaan": 0.9, "Ganesh": 1.1, "Jathin": 0.6}
TRUE_BASE_RATE = 6.0        # strokes per second per washer, invented
TYPICAL_SECONDS = 30        # placeholder until step 0 (timing videos) gives the real median


def seating(block):
    """Roles rotate every 10 trials: one member records, the other four sit in a rotated order."""
    recorder = MEMBERS[(len(MEMBERS) - 1 - block) % len(MEMBERS)]
    washers = [p for p in MEMBERS if p != recorder]
    return washers[block % 4:] + washers[:block % 4]          # names at E, S, W, N


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "data", "synthetic_trials.csv"))
    ap.add_argument("--no-half", action="store_true", help="skip the optional 15 trials at half time")
    ap.add_argument("--seed", type=int, default=2026)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    plan = [(t, TYPICAL_SECONDS, "2026-10-24") for t in range(1, 41)]
    if not args.no_half:
        plan += [(t, TYPICAL_SECONDS // 2, "2026-10-31") for t in range(41, 56)]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(m.REQUIRED_COLUMNS)
        for trial, seconds, date in plan:
            names = seating((trial - 1) // 10)
            styles = [{**m.DEFAULT_STYLE, "rate": TRUE_BASE_RATE * PERSONAL_RATE[n]} for n in names]
            table = m.simulate_tables(seconds, 1, rng, fixed=styles)[0]      # C[suit, wall]
            for w, seat in enumerate(m.SEATS):
                out.writerow([trial, date, seconds, seat, names[w]] + list(table[:, w]))
    print(f"wrote {len(plan)} synthetic trials to {args.out}")


if __name__ == "__main__":
    main()
