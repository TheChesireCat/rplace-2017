# Pre-registration: are wasted placements spare defensive capacity?

Dated 2026-10-22. Committed and pushed before the regression below was computed.

**What had been seen:** the exploratory artwork-life analysis (`notes/01-evolve-artwork-life.md`): on the whole canvas,
using a look-ahead "settled colour", the wasted share rises with completion and labour per pixel is flat across
completion. The relation of the wasted share to labour per *wrong* pixel, holding completion fixed, has not been
computed, nor anything with the causal reference defined here.

## Three readings of wasted placements

- **H1 spare capacity (this book):** defenders target damage; when there is little damage for the labour present, the
  rest repaints correct pixels. At fixed completion, the wasted share **rises with labour per wrong pixel**.
- **H2 coordination inefficiency (Wu and Silva 2024, §5.1):** waste grows with the number of participants, whatever the
  damage. At fixed completion and labour per wrong pixel, the wasted share **rises with the number of accounts**.
- **H3 name attachment or other motives unrelated to damage (Falmagne et al. 2026, SI):** the wasted share does not
  depend on labour per wrong pixel at fixed completion.

## Definitions

- **Regions and windows:** 20 × 20 pixel blocks, 15-minute windows from launch.
- **Reference colour (causal, after Falmagne et al.):** a pixel's most common colour across the 12 canvas snapshots at
  the ends of the previous twelve 15-minute windows (the previous 3 hours); windows in the first 3 hours are skipped.
- **At the start of window w:** a pixel is *wrong* if its colour differs from its reference; **completion** is the
  region's share of pixels that are not wrong; **W** the number of wrong pixels.
- **In window w:** **L** placements in the region, **A** accounts placing there; a placement is *wasted* if it repaints
  the pixel's current colour (`pixel_history`).
- **Region-windows used:** L ≥ 20 and completion ≥ 0.5.

## Test

Least squares: wasted share ~ log(L / (W + 1)) + log(A) + fixed effects for completion in bins of 0.05. Intervals by
resampling regions (200 resamples, seed 0).

- **H1 supported** if the coefficient on log(L / (W + 1)) is positive with its 95% interval above 0.
- **H2 supported** if the coefficient on log(A) is positive with its 95% interval above 0 (both can hold).
- **H3** if neither interval is above 0.

## Controls (fixed here, run through the same code)

- **Positive control:** a simulated region of 400 pixels; each window, attacks hit random correct pixels (Poisson,
  mean varied) and L defender placements (varied) go to wrong pixels when any remain, otherwise to correct pixels as
  wasted repaints, with 10% placed at random. The H1 coefficient must come out positive.
- **Negative control:** the same simulation with every placement at a random pixel (wasted if that pixel was correct).
  The H1 coefficient must be about 0 (interval including 0).
- If either control fails, the regression is not informative and the test stops there.

## Secondary (replication, not a novelty test)

Change in completion over the next 2 hours ~ log((repairs + 1) / (attacks + 1)) + attacks per pixel in this and in the
next window + completion fixed effects, where a repair returns a wrong pixel to its reference and an attack changes a
correct pixel away from it. Falmagne et al. (2026) report that low defence and dominating attacks precede transitions in
2022-23; this asks whether the same holds in 2017 once persistence of attacks into the next window is controlled.
