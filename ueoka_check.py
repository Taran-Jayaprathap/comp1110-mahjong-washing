"""Re-implementation of the hand-shuffle model in Ueoka (2022), viXra:2201.0198,
as described in the paper, plus a one-line fix. Run: python3 ueoka_check.py"""
import random, statistics as st

# 3 suits numbered 1-9, plus 7 honour types (number 0, each its own type)
TYPES = [(s, n) for s in range(3) for n in range(1, 10)] + [(3 + h, 0) for h in range(7)]

def energy(pile):
    """Paper's mixing energy: 9 - |d| for adjacent tiles of the same type."""
    return sum(9 - abs(a[1] - b[1]) for a, b in zip(pile, pile[1:]) if a[0] == b[0])

def paper_step(pile, x):
    """As described: take x tiles around the 17th, shuffle, put at the front.
    Note: tiles to the RIGHT of the removed block never move."""
    l = 17 - x // 2
    mid = pile[l:l + x]; random.shuffle(mid)
    return mid + pile[:l] + pile[l + x:]

def fixed_step(pile, x):
    """Same move, but the remainder rotates so every tile can reach the middle."""
    l = 17 - x // 2
    mid = pile[l:l + x]; random.shuffle(mid)
    return mid + pile[l + x:] + pile[:l]

def run(step, x, shuffles=3000, trials=100):
    out = []
    for _ in range(trials):
        p = list(TYPES)                  # sorted start, as in the paper
        for _ in range(shuffles):
            p = step(p, x)
        out.append(energy(p))
    return st.mean(out)

if __name__ == "__main__":
    random.seed(1)
    uni = st.mean(energy(random.sample(TYPES, 34)) for _ in range(5000))
    print(f"fully random wall (same 34 tiles): mean energy {uni:.1f}")
    for x in (11, 20, 30):
        l = 17 - x // 2
        print(f"x={x}: {34 - l - x} tiles never move | paper model {run(paper_step, x):.1f}"
              f" | fixed model {run(fixed_step, x):.1f}")
