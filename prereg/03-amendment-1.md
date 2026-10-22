# Amendment 1 to `03-cooldown-switches.md`

Dated 2026-10-21, committed before any outcome, control or pre-trend in the pre-registration was computed. The
original file is left unchanged; where they differ, this amendment applies.

## What changed and why

**1. Switches 5 and 6 are merged into one switch.** They are 27 minutes apart (20 → 15 at 05:00, 15 → 10 at 05:27).
With the windows as written, the after-window of switch 5 and the before-window of switch 6 are the same stretch of the
15-minute period, so the two Δ's share data, and in T their terms reduce to one 20 → 10 comparison. They are not two
independent switches. The merged switch is a loosening, 1200 → 603 s:

- before window: [05:00 − W, 05:00);
- after window: [05:27 + δ, 05:27 + δ + W), with δ = 603 s;
- the 15-minute stretch itself is not used.

There are now **six** switches:

| k | time | from → to (s) | direction |
|---|---|---|---|
| 1 | 03-31 21:10 | 300 → 600 | +1 |
| 2 | 03-31 22:41 | 600 → 300 | −1 |
| 3 | 04-01 00:10 | 300 → 600 | +1 |
| 4 | 04-01 03:03 | 600 → 1200 | +1 |
| 5 | 04-01 05:00 / 05:27 | 1200 → 603 | −1 |
| 6 | 04-01 21:30 | 600 → 300 | −1 |

All twelve windows fit at W = 20 minutes without crossing another regime or a δ exclusion.

**2. One primary outcome.** With six switches the exact sign-flip test has 2⁶ = 64 assignments, so the smallest
two-sided p is 2/64 = 0.031. That cannot pass Holm's first threshold across three outcomes (0.05/3 = 0.017), so the
test as written could never succeed. The amended test has a single primary outcome:

- **Primary: O2, overwrite share** (among non-wasted placements, the share whose pixel's current colour was placed by
  a different account). It is the most direct measure of conflict, which is the book's question. Two-sided exact
  sign-flip, α = 0.05. It passes only if Δ has the direction-consistent sign at all six switches.
- **Secondary: O1 (wasted share) and O3 (undo share)**, reported with their exact p-values, labelled exploratory.
  No confirmatory claim rests on them.

A one-sided test was considered and rejected: it needs a predicted direction for each outcome, and none was written
before this point.

**3. Counts.** Every window reports its number of placements and of active accounts. In the 20-minute-cooldown windows,
each account can place at most once per window; a window with fewer than 1,000 placements is flagged.

## Unchanged

M1 positive control (now over six switches; it can reach p = 2/64), the pre-trend check, the composition check, the
bootstrap intervals, W = 20 with sensitivity W = 10 and 40, and the failure criteria. The placebo uses six
pseudo-switches at the same clock times 48 hours later, merged the same way (04-03 05:00 / 05:27).

## State when written

Nothing in the pre-registration has been computed: no outcome, no M1, no pre-trend.
