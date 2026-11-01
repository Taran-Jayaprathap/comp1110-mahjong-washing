"""Monte Carlo demo for mahjong washing (COMP1110 Group 16). Plain Python, no libraries.
Run: python3 mc_demo.py
Parameters are NOT calibrated to real washing yet; numbers only show what the output looks like."""
import random, math

N = 144            # tiles
WALL = N // 4      # 36 tiles per wall
ZONES = "ESWN"     # East=bottom, South=right, West=top, North=left (any fixed labelling works)

def zone_of(x, y):
    """Which table edge a point at (x, y) in the unit square is closest to: 0..3."""
    d = [y, 1 - x, 1 - y, x]
    return d.index(min(d))

def start_layout():
    """Tiles start in front of the player who discarded them: 36 per zone."""
    tiles = []
    for z in range(4):
        while sum(1 for t in tiles if t[2] == z) < WALL:
            x, y = random.random(), random.random()
            if zone_of(x, y) == z:
                tiles.append([x, y, z])
    return tiles

def wash(tiles, steps, radius=0.15, push=0.12):
    """Each step = 4 hands. A hand picks a random spot and pushes every tile within
    `radius` by one shared random displacement (size up to `push`), then tiles are clamped
    to the table. A simplified Diaconis-Pal spatial model."""
    for _ in range(steps):
        for _hand in range(4):
            cx, cy = random.random(), random.random()
            a = random.uniform(0, 2 * math.pi); r = random.uniform(0, push)
            dx, dy = r * math.cos(a), r * math.sin(a)
            for t in tiles:
                if (t[0] - cx) ** 2 + (t[1] - cy) ** 2 < radius ** 2:
                    t[0] = min(1, max(0, t[0] + dx + random.gauss(0, 0.01)))
                    t[1] = min(1, max(0, t[1] + dy + random.gauss(0, 0.01)))
    return tiles

def build_walls(tiles):
    """Each player takes the 36 tiles nearest their edge (greedy, closest first)."""
    edge_d = lambda t, z: [t[1], 1 - t[0], 1 - t[1], t[0]][z]
    pairs = sorted((edge_d(t, z), i, z) for i, t in enumerate(tiles) for z in range(4))
    wall, count = {}, [0] * 4
    for d, i, z in pairs:
        if i not in wall and count[z] < WALL:
            wall[i] = z; count[z] += 1
    return [wall[i] for i in range(len(tiles))]

def tv_from_uniform(starts, walls):
    """Our randomness measure: max over start zones of the TV distance between
    'where tiles from this zone ended up' and (1/4, 1/4, 1/4, 1/4)."""
    worst = 0
    for z in range(4):
        dest = [w for s, w in zip(starts, walls) if s == z]
        tv = 0.5 * sum(abs(dest.count(k) / len(dest) - 0.25) for k in range(4))
        worst = max(worst, tv)
    return worst

def one_trial(steps):
    tiles = wash(start_layout(), steps)
    return tv_from_uniform([t[2] for t in tiles], build_walls(tiles))

def perfect_shuffle_trial():
    """Baseline: random.shuffle, the 'truly random' reference."""
    starts = [z for z in range(4) for _ in range(WALL)]
    walls = starts[:]; random.shuffle(walls)
    return tv_from_uniform(starts, walls)

def summary(xs):
    xs = sorted(xs); m = sum(xs) / len(xs)
    return m, xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]

if __name__ == "__main__":
    random.seed(1110)
    base = [perfect_shuffle_trial() for _ in range(10000)]
    m, lo, hi = summary(base)
    cut95 = sorted(base)[int(0.95 * len(base))]
    print(f"perfect shuffle (10,000 runs): mean TV {m:.3f}, 95% range {lo:.3f}-{hi:.3f}, 95th pct {cut95:.3f}")
    print("steps  mean TV  95% range      share of runs above the 95th pct of a perfect shuffle")
    for steps in (0, 5, 10, 20, 40, 80):
        res = [one_trial(steps) for _ in range(300)]
        m, lo, hi = summary(res)
        above = sum(r > cut95 for r in res) / len(res)
        print(f"{steps:5d}  {m:.3f}    {lo:.3f}-{hi:.3f}    {above:.0%}")
