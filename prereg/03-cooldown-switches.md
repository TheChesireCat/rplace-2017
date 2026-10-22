# Pre-registration: does the cooldown change how people place? (chapter 3)

Written 2026-10-21, before any outcome below was computed. Committed to the `analysis` branch before the analysis
runs; the commit hash is the timestamp of record.

**What had been seen before writing this:** the gap distributions and the cooldown schedule (chapter 2: switch times
from the log at 1-minute resolution, matching Reddit's commit history). No per-placement colour outcome (wasted,
overwrite, undo, survival) has been computed in any window.

## Question

Reddit changed the wait between placements seven times during the 2017 event, for everyone at once. Does a longer
wait change *how* people place (behavioural), beyond the fact that it lets them place less often (mechanical)?

## The switches

From `rplace17.COOLDOWN_REGIMES` (log-effective times, UTC):

| k | time | from → to (s) | direction |
|---|---|---|---|
| 1 | 03-31 21:10 | 300 → 600 | tighten (+1) |
| 2 | 03-31 22:41 | 600 → 300 | loosen (−1) |
| 3 | 04-01 00:10 | 300 → 600 | tighten (+1) |
| 4 | 04-01 03:03 | 600 → 1200 | tighten (+1) |
| 5 | 04-01 05:00 | 1200 → 900 | loosen (−1) |
| 6 | 04-01 05:27 | 900 → 603 | loosen (−1) |
| 7 | 04-01 21:30 | 600 → 300 | loosen (−1) |

## Windows (fixed here)

- **After window** for switch k at time s: [s + δ, s + δ + W), with δ = the new cooldown (placements in the first
  cycle after a switch are a selected group: only people whose last placement was long enough ago).
- **Before window:** [s − W, s).
- **W = 20 minutes**, shortened symmetrically when a window would cross into another regime (or into the δ exclusion
  after the previous switch); the shortest allowed is 10 minutes. Expected effect: switches 5 and 6 get W = 12 min.
- **Sensitivity:** W = 10 and W = 40 (capped the same way), reported in full, not used for the decision.

## Outcomes, per placement

Computed from each pixel's history up to the placement (the colour sequence of that pixel). The first placement on a
never-placed pixel is excluded from O2 and O3.

- **M1 (mechanical, positive control):** placements per active account per minute (active = placed at least once in
  the window).
- **O1 wasted share:** the placement repaints the pixel's current colour (Wu & Silva 2024, v3, §5.1: "an update that
  repaints a pixel with its current color").
- **O2 overwrite share:** among non-wasted placements, the share whose pixel's current colour was placed by a different
  account.
- **O3 undo share:** among non-wasted placements on pixels with at least two earlier colour states, the share that
  restores the colour before the current one (the second A in A–B–A).
- **Secondary, descriptive only:** survival of the placed colour to 5 minutes; the pixel-level version of Wu & Silva's
  §4.1 categories (Final: persists to the close; Match: equals the pixel's final colour but is later overwritten;
  Adversarial: differs from the pixel's final colour). Survival is partly mechanical (a longer wait slows responses),
  so it is not part of the test.

For each switch and outcome, Δ_k = outcome(after) − outcome(before).

## Hypotheses and test

- **H1 (behavioural effect):** the sign of Δ follows the direction of the switch: tightenings move an outcome one way
  and loosenings the other, consistently.
- **H0:** Δ_k is unrelated to direction.
- **Statistic:** T = Σ_k dir_k · Δ_k. **Null distribution:** exact sign-flip over the 2⁷ = 128 assignments of signs to
  the Δ_k (H0 makes each Δ_k symmetric about 0). Two-sided p.
- **Primary outcomes:** O1, O2, O3. **Multiple comparisons:** Holm across the three, α = 0.05.
- **Power note:** with 7 switches the smallest two-sided p is 2/128 = 0.016, so under Holm only an outcome whose Δ has
  the predicted sign at all 7 switches can pass. This test detects only a fully consistent effect; a negative result
  is "no consistent effect detectable with 7 switches", not "no effect".

## Controls

- **Positive control (must pass or the analysis is invalid):** M1 falls after every tightening and rises after every
  loosening (the same sign-flip test; it should reach p = 2/128).
- **Pre-trend:** Δ_pre,k = outcome[s − 2W, s − W) − outcome[s − W, s). A switch whose |Δ_pre| exceeds half its |Δ| is
  flagged; flagged switches are reported, and the test is repeated without them.
- **Placebo:** the same analysis at seven pseudo-switches inside the stable five-minute period, at the same clock times
  48 hours later (04-02 21:10, 04-02 22:41, 04-03 00:10, 04-03 03:03, 04-03 05:00, 04-03 05:27, 04-02 21:30), with the
  same directions and windows. T should show nothing there.
- **Composition:** O1–O3 recomputed on accounts that placed in both windows of a switch (the same people before and
  after). Reported beside the main result.

## Uncertainty and N

For each Δ_k, a 95% interval from 1,000 bootstrap resamples of accounts within the two windows. N = number of
placements and of accounts in each window, reported per switch.

## Failure criteria

- If the positive control fails, the windows or the schedule are wrong; the analysis stops there.
- If no primary outcome passes Holm at α = 0.05, chapter 3 reports no consistent behavioural effect of the cooldown
  detectable with 7 switches, with all Δ_k and intervals shown.
- If the placebo T for any primary outcome reaches p ≤ 0.05, the effect seen at the real switches is not attributed to
  the cooldown.

## Known threats, not solved by this design

- The switches were probably made in response to server load, which follows activity, so they are not random. The
  short windows, the pre-trend check and the placebo limit this; they do not remove it.
- Switches 5 and 6 are 27 minutes apart, so their windows overlap the same regime.
