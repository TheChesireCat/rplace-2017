# Pre-registration: wasted placements come in runs (chapter 3, half B)

Dated 2026-10-22, under the holdout in `prereg/03-wasted-holdout.md`. Committed and pushed before any wasted-placement
statistic is computed on half B (blocks with bx + by odd).

## What half A showed (exploration)

On half A, 99.3% of wasted placements repaint a colour that another account placed; wasted placements are more
likely right after another wasted placement on the same pixel than after a colour change ("runs"). The run excess,
Δ = P(wasted | previous placement on the pixel wasted) − P(wasted | previous not wasted), was 0.292 in the data and
0.204 under a null that shuffles the order of colours within each pixel (5 shuffles), a difference of +0.088 (block
bootstrap of the data Δ over 61 blocks: [0.270, 0.314]). Pixels with 100 or more colour changes had a higher wasted
share than pixels with 2 to 9 (0.349 vs 0.250).

## Hypotheses for half B

**H1 (primary): runs beyond the pixel's own colour mix.** On half B, Δ_data − Δ_null ≥ 0.044 (half the half-A value),
and the 95% block-bootstrap interval of Δ_data − Δ_null excludes 0.

**H2 (secondary): contested pixels waste more.** On half B, the wasted share of pixels with ≥ 100 colour changes minus
that of pixels with 2 to 9 is > 0, with a 95% block-bootstrap interval excluding 0.

## Method (as on half A)

- Placements from launch on, on half-B pixels only; `rplace17.pixel_history` run on half-B pixels (each pixel's whole
  history lies in one half).
- Δ uses consecutive placements on the same pixel; the first placement on each pixel has no predecessor and is
  dropped.
- Null: the colours of each pixel's placements put in random order (times kept), flags recomputed; 5 shuffles,
  seeds 0 to 4; Δ_null is their mean.
- Block bootstrap: 1,000 resamples of the 100 × 100 blocks of half B with replacement; for H1 each block carries its
  data and null counts together.
- N: number of half-B blocks, placements and pixels, reported.

## Failure criteria

- H1 fails if the estimate is below 0.044 or the interval includes 0. Then the half-A run excess is reported as not
  replicated.
- H2 fails if the interval includes 0.

The time trend in the wasted share seen on half A is not tested: both halves share the same clock and crowd, so its
replication on half B would not be independent evidence.
