# Pre-registration: is building limited by labour? (2017, cooldown switches)

Dated 2026-10-22. Committed and pushed before anything below was computed. Offspring B of
`notes/01-evolve-artwork-life.md`.

**What had been seen:** chapter 3's switch analyses (placements per account drop after tightenings; window outcomes
on the whole canvas) and the exploratory growth statistics in the notes. No count of builds in growing regions around
the switches has been computed.

## Hypotheses

- **H1 labour-limited:** while a region is being built, its builders' placements are the binding constraint, so builds
  scale with placements across a switch: elasticity ε = Δlog(builds) / Δlog(placements) ≈ 1.
- **H0 limited by something else** (knowing the design, coordination, contested space): builds change less than
  placements; remaining labour is redirected from waste and other placements into building, ε ≈ 0.

## Definitions

- **Regions:** 20 × 20 px; the six switches of `rplace17.SWITCHES`; windows before [s − 40 min, s) and after
  [s + δ, s + δ + 40 min), δ = the new cooldown (sensitivity: 20-minute windows, reported only).
- **Build:** a placement that sets a pixel to its *settled colour* (the colour it held longest over the whole event) when
  it did not already show it. (A look-ahead definition, used here as an outcome; disclosed.)
- **Growing region at a switch:** settled-colour completion between 0.2 and 0.8 at the start of the before window, and at
  least 20 builds in the before window.
- **Placements:** all placements in the region in the window.

## Test

For each switch k, ε_k = Σ over growing regions of [log(builds_after / builds_before)] / Σ [log(L_after / L_before)]
is not robust to small denominators, so instead: ε_k is the least-squares slope through the origin of
log(builds_after / builds_before) on log(L_after / L_before) across growing regions; the pooled ε is the same slope over
all region-switch pairs. 95% intervals by resampling regions (500 resamples, seed 0).

- **H1 supported** if the pooled ε has a 95% interval that includes 1 and excludes 0.5.
- **H0 supported** if the interval includes 0 and excludes 0.5.
- **Intermediate** (neither): reported as partial labour limitation, with the estimate.

**Check (reported, not decisive):** the same slope at the six placebo times (`rplace17.PLACEBO`), where placement
changes are small and mostly noise; a large placebo slope would show that coupling between builds and placements is
partly mechanical (builds are placements).

## N

Region-switch pairs, regions and builds per switch, reported.
