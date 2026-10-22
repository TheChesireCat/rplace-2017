# Pre-registration: where do people go next? (chapter 4)

Written 2026-10-22, before any jump between placements was computed. Committed and pushed to the `analysis` branch
before the analysis runs; the commit hash is the timestamp of record.

**What had been seen before writing this:** chapters 1-3 (gaps, the cooldown schedule, per-pixel histories). No
displacement between an account's consecutive placements has been computed or plotted. The tail-fitting code
(`rplace17.tails`) was built and tested on waiting times in chapter 2 and is used here unchanged.

**Context, not yet read for this book:** human mobility studies report heavy-tailed jump lengths, often described as
Lévy-flight-like (Brockmann, Hufnagel and Geisel 2006, doi:10.1038/nature04292; González, Hidalgo and Barabási 2008,
doi:10.1038/nature06958), and a tendency to return to visited places (Song, Koren, Wang and Barabási 2010,
doi:10.1038/nphys1760). No number from these papers is used below.

## Question

When an account places a pixel and then another, how far away is the second one? Is the jump-length distribution
heavy-tailed in a way that goes beyond (a) the geometry of a bounded 1001 × 1001 canvas and (b) people splitting their
time between a few places?

## The object

A **jump** is the displacement between an account's consecutive placements after launch (`rplace17.LAUNCH_US`):
components dx, dy (pixels) and length r = √(dx² + dy²). Jumps with r = 0 (the same pixel again) are counted and
reported, and excluded from the tail fits (the fits need r > 0).

## Conditioning and strata (fixed here)

Jump length plausibly depends on the gap since the last placement, on the cooldown in force, and on the time since
launch (Rappaz et al. 2018 report that the distance between consecutive placements fell over the first day; not yet
checked here). So every analysis is within strata:

- **Cooldown:** gaps that start and end in the same period (as in chapter 2). Primary: the five-minute periods.
  Secondary: the ten-minute periods (600 and 603 s merged). The 15- and 20-minute periods are too short and are only
  described.
- **Gap:** *prompt* (gap ≤ cooldown + 60 s, the account placing again as soon as it could), *later* (cooldown + 60 s
  to 1 h), *after a break* (over 1 h). **Primary: prompt.**
- **Time block** (five-minute periods only): **A** = launch to 04-01 00:10 UTC (the five-minute parts of the first
  seven hours), **B** = 04-01 21:30 to 04-02 21:30, **C** = 04-02 21:30 to the close.

The **primary strata** are the three blocks A, B, C of prompt jumps in five-minute periods.

## Outcomes

**O1 (primary): the tail of r**, in each primary stratum, with `rplace17.tails`: the power law above the KS-optimal
cutoff against the exponential, lognormal, stretched exponential and truncated power law; the fitted range in decades;
whether the cutoff sits at the edge of its search.

**O2 (descriptive): components.** Mean, standard deviation and excess kurtosis of dx and dy (not of r) per stratum.
No test; on a bounded canvas every moment is finite, so moments do not diagnose a tail here.

**O3 (descriptive): spread per account.** Each account's radius of gyration (root mean squared distance of its
placements from their centre) against its number of placements, by the bands used in chapter 2. No diffusion exponent
is fitted.

**O4 (descriptive): return.** The number of distinct pixels an account has visited after n placements, and the share of
jumps that land within 5 px of one of the account's own previous 10 placements.

## Nulls (fixed here)

- **N1 geometry:** each jump keeps its origin; its destination is uniform over the canvas. What a bounded square alone
  gives.
- **N2 own places, random order:** each account's placements (within the stratum's time block) are put in a random
  order; jumps are recomputed between consecutive ones. Keeps each account's footprint, destroys its sequence.
- **N3 two scales:** each account's jumps in the stratum are split into *local* (r ≤ R_loc) and *far* (r > R_loc),
  R_loc = 20 px. The null keeps the account's local share; local jumps are drawn as r ~ exponential with the account's
  own mean local r (random direction), far jumps as in N1. Sensitivity: R_loc = 10 and 40 px, reported, not used for
  the decision. N3 is a mixture with no heavy tail inside either scale.

Each null is drawn 20 times per stratum.

## Decision rule for O1

The jump lengths are called **Lévy-flight-like** in a stratum only if all of these hold:

1. the power law beats each alternative by Vuong's test (normalised R > 0, p < 0.05), and is not rejected in favour of
   the truncated power law (p ≥ 0.05);
2. 1 < α < 3;
3. the fitted tail spans at least 1.5 decades and its cutoff is not at the edge of the search;
4. the data's distribution of r above R_loc differs from N3's by more than N3's replicates differ from each other:
   KS distance between data and the pooled N3 draws greater than the largest KS distance between any two N3 replicates.

The overall claim requires all four in **each** of A, B and C. Otherwise the chapter reports "no evidence of
Lévy-flight-like jumps" for the failing strata, with the full tables.

## Expected difficulties, stated in advance

- On a canvas 1001 px across, r cannot exceed about 1,415 px, so a tail above a cutoff of a few pixels spans at most
  about 2.5 decades, and condition 3 may fail by geometry alone.
- With millions of jumps, likelihood-ratio tests reject small differences, so condition 1 is demanding in both
  directions.
- O2–O4 are descriptive and carry no claim.

## N

Reported per stratum: number of jumps, of accounts, and of jumps with r = 0.
