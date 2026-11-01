# What we are actually doing: the plan, corrected, and the step-by-step experiment

For Taran, after the 3 Oct call. Part 1 explains the terms and fixes the parts of the plan that were mixed up. Part 2 is the literal protocol for the real trials. Numbers come from `mc_demo.py`.

---

# Part 1: the plan in plain terms

## What a p-value is

A p-value answers one question: **"If the washing really were perfectly random, how often would we see a result at least this uneven just by luck?"**

- Small p-value (below 0.05, i.e. under 5% of the time): luck is a poor explanation, so we conclude the washing is **not** random.
- Large p-value: the result is the kind of thing a perfect shuffle produces, so we **cannot** say it is non-random. That is not proof it is random, only that we found no evidence against it.

Example: our real washes leave tiles in their own player's wall noticeably more than ¼ of the time. We run 10,000 perfect computer shuffles and find that only 3 of them are that uneven. p = 3 / 10,000 = 0.0003, so the washing is clearly not random.

## The three things that were mixed up

**1. There is no "average p-value" from 10,000 simulations.** The 10,000 computer shuffles do not produce a p-value on their own. They produce the **yardstick**: the range of results a perfect shuffle gives. The p-value comes from **comparing our real data against that yardstick**. So the order is: collect real data, then compare it with the 10,000 runs. (The yardstick can be computed any time, even today.)

**2. "Monte Carlo" means two different things in our project, and only one is the ideal.**

| | What it is | Ideal or prediction? |
|---|---|---|
| **Perfect-shuffle baseline** | Python's `random.shuffle` on 144 tiles, dealt into 4 walls, 10,000 times | **The ideal.** It does not depend on seconds: a perfect shuffle is perfect at any time. |
| **Washing simulation** | A computer model of hands pushing tiles around a table | **A prediction** of real hand washing, only trustworthy once tuned to our real data. |

So the sentence "in an ideal world this is how much it should have shuffled after 76 seconds" is not quite right. The ideal has no time in it. The right comparison is: "after 76 seconds of real washing, tiles stay in their own player's wall X% of the time; a perfect shuffle gives 25%; is the gap more than luck?" The **washing simulation** is what talks about seconds ("hand washing would need about Y seconds to look random").

**3. The Markov chain is not the real-world part.** The real-world part is just the **experiment**: we wash real tiles and record where they end up. A Markov chain is one possible way to *analyse* real data, and it needs extra photos in the middle of every wash. If the group goes with Monte Carlo, **drop the Markov chain from the experiment** and keep it as a one-paragraph theory idea at most. The real trials then only need the start and the end.

## The corrected pipeline

1. **Find the typical washing time** (step 0 in Part 2).
2. **Real experiment:** 40 washes at that time, recording which wall each tile ends in.
3. **Monte Carlo baseline:** 10,000 perfect shuffles give the yardstick.
4. **Method 1, the answer:** compare the real result with the yardstick and get a p-value. "Is typical Hong Kong washing random?"
5. **Method 2, the simulation:** tune the washing model until it matches the real result, then ask it about other times ("how many seconds would be enough?").

## One design change to be aware of

Using **one** washing time (the typical one) answers "is normal washing random?", which is clean and simple. It no longer answers "how long must you wash?" from real data alone; only the simulation answers that, and with one real time it is tuned on a single point. **Recommendation:** if there is time, add a short second condition, 15 trials at **half** the typical time. That gives the simulation two points to fit and shows a trend. The base plan below works without it.

## Is 40 trials enough?

Yes. A perfect shuffle of a single game gives a "distance from random" (TV) of about 0.14 just by luck. Pooling 40 games shrinks that luck to about 0.02 (95% of perfect shuffles stay under 0.033). So with 40 games, even a small leftover bias, such as tiles going to their own wall 30% of the time instead of 25%, stands out clearly.

---

# Part 2: the step-by-step experiment

## The key trick: you don't need to play the game, and you don't need stickers

The only thing that matters is **where tiles start** and **which wall they end in**. So we skip playing entirely and set up a known start in about a minute, using the suits as labels:

| Player (seat) | Starts with | Count |
|---|---|---|
| East | All dots (circles) | 36 |
| South | All bamboo | 36 |
| West | All characters | 36 |
| North | All honours (winds + dragons, 28) + all 8 flowers/seasons | 36 |

That is exactly 36 each, which is exactly one wall each (18 stacks of 2). A tile's suit tells you which player it started with, so **no stickers and no tracking are needed**. At the end you flip each wall and count suits.

Why this is a fair start: at the end of a real game, the tiles in front of each player (their hand and discards) are the ones they are most likely to pull back into their own wall. Our start is the extreme version of that, "every tile starts with one owner", which is the clearest way to see whether ownership survives washing. Say this in the plan as a deliberate choice.

## Step 0: find the typical washing time (no tiles needed)

- Watch 15–20 washes in YouTube videos of Hong Kong home mahjong, or time real family games. Start the timer when hands first push tiles, stop when the first player starts building a wall.
- Record each time in a list; use the **median** (the middle value) as our washing time, rounded to the nearest 5 s.
- This is the one part that can be done online. Tile positions cannot: tiles are face down, online mahjong uses a computer shuffle, and automatic tables don't involve washing. The tile data has to be physical.

## What you need

- One HK mahjong set: 144 tiles (remove any blanks or spares).
- A normal square table with a mat or cloth, the same one every session. No glass table needed: we flip the walls face up at the end instead of looking from underneath.
- Four chairs, one per side. Label the sides E, S, W, N with tape.
- A phone timer, a phone for photos, and a laptop or sheet for recording.
- Optional: a second phone on a stand filming from above (useful evidence and lets us check washing style later).

## People and seating

- **Four washers**, one per side, sitting normally. The fifth member is the **recorder** (timer, counting, typing).
- Wash **normally**: tell washers not to try harder or softer than usual, and not to look at tiles. (Tiles are face down, so nobody can see suits anyway.)
- **Rotate roles every 10 trials** so all five members wash and washer differences are spread out. Record who sat where on every trial (this covers CX's washer-variation point).
- The East seat always starts with dots, whoever sits there.

## One trial, step by step (about 4–5 minutes)

1. **Set up (about 1 min).** All 144 tiles face down. Each washer pulls their starting suit into a loose pile in front of them: East dots, South bamboo, West characters, North honours and flowers. Turning tiles face up to sort and then face down again is fine, as long as everything is face down before washing.
2. **Wash.** Recorder says "go" and starts the timer. All four wash as they normally would. Recorder says "stop" at the exact time. Hands off immediately.
3. **Build walls (about 1 min).** Each player builds their wall the usual HK way: 18 stacks of 2 from the tiles nearest them, face down, then pushes it forward as normal. Don't adjust or swap tiles to make it tidy.
4. **Flip and photograph (about 30 s).** Each player turns their wall face up in place, keeping it in order. Recorder takes one photo of each wall (4 photos, trial number written on a slip of paper in the frame).
5. **Count (about 1 min).** Each player counts the suits in their own wall and calls out four numbers: dots, bamboo, characters, honours+flowers. Recorder types them in.
6. **Check.** Each wall's four numbers must add to 36. Each suit's total across the four walls must be 36. If not, recount from the photo.
7. **Reset** and start the next trial.

**Skip the dice break.** It decides where drawing starts but doesn't change which tiles are in which wall, so it doesn't affect our measure. Mention this in the plan.

## What to record (one row per wall, so 4 rows per trial)

```
trial,date,seconds,wall_seat,washer_name,dots,bamboo,characters,honours_flowers
1,2026-10-10,30,E,Taran,14,8,7,7
1,2026-10-10,30,S,Punk,7,13,9,7
...
```

The "own suit" count is the key number: dots in E's wall, bamboo in S's, characters in W's, honours in N's. A perfect shuffle averages 9 of 36 (25%).

## Time budget

| Item | Time |
|---|---|
| One trial | about 4–5 min |
| 40 trials | about 3–3.5 hours |
| Optional 15 extra trials at half time | about 1–1.25 hours |
| Step 0 (timing videos) | about 1 hour, one person, online |

So the whole physical experiment fits in **one long session or two short ones** with all five present. That is much less than the old plan, which needed stickers, freezing and photos every 10 s, and transcribing all 144 tiles by position.

## Things that could go wrong, and the fix

| Risk | Fix |
|---|---|
| Washers get bored and wash less over a session | Rotate roles every 10 trials; note the time of each trial; take a break halfway. |
| Washers wash harder because they know it's an experiment | Ask them to wash "like at a family game"; the overhead video lets us check. Mention it as a limitation. |
| Counting mistakes | The two 36-totals checks catch nearly all of them; photos let us recount. |
| Our suit-sorted start is more extreme than a real game | Say it is deliberate: it is the clearest test of "do tiles come back to you". A real game would show a smaller effect, so our result is an upper bound. |
| Set has the wrong number of tiles | Count all 144 before the first trial: 36 of each suit, 28 honours, 8 flowers. |

## After the session: the analysis in three lines

1. For all 40 trials pooled, compute the share of "own suit" tiles in each player's wall, and the TV distance from ¼.
2. Run 10,000 perfect computer shuffles of 40 games and see how often they are that uneven. That share is the p-value.
3. Tune the washing simulation so it matches our result at the typical time (and half time, if done), then use it to predict other times.
