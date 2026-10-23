# Pre-registration: does the capacity hinge replicate in r/place 2022?

Dated 2026-10-22. Committed and pushed before any 2022 placement was loaded on this machine (the 2022 log is on an
external drive that is not mounted). The 2017 result being replicated is `prereg/05-capacity-result.md`
(hinge contrast H = +0.061 [0.054, 0.069], post hoc). This is the first blind test of it.

## Data

Reddit's 2022 canvas history (`2022_place_canvas_history.csv.gzip`, registered in the playground's data registry with
sha256 a2891c96…; columns timestamp, user_id, pixel_color, coordinate). It is condensed the same way as 2017 (integer
times, account ids, coordinates, colour index). Moderator rectangle edits (`coordinate` with four numbers) are expanded
to their pixels and applied to the canvas state, but **not** counted as placements (they are not users' labour).

**Period:** from the first placement to the start of the final whiteout. The whiteout start is fixed by rule, not by eye:
the first 15-minute window in which more than half of all placements are white, and every later window, are excluded.

**Canvas:** the 2022 canvas grew during the event. A region counts from the first window in which any placement has
landed in it.

## Method (as in 2017, unchanged)

- 20 × 20 pixel regions, 15-minute windows; causal reference colour = most common colour across the previous 12 window-end
  snapshots (3 h); windows in a region's first 3 hours are skipped.
- Per region-window: L placements, A accounts, W wrong pixels at the start (colour ≠ reference), completion = 1 − W / region
  pixels; wasted = repaints of the pixel's current colour.
- Region-windows with L ≥ 20 and completion ≥ 0.5.
- Model: wasted share ~ a·min(z, 0) + b·max(z, 0) + log(A) + completion fixed effects (bins of 0.05), z = log(L/(W+1));
  H = b − a; 95% interval by resampling regions (200 resamples, seed 0).
- Controls: the same simulations as in 2017 (they do not depend on the data): positive control H > 0 required; random
  targeting, seeds 10-12.

## Decision

- **Replicates** if H > 0, its 95% interval is above 0, and above the largest random-targeting H.
- **Fails to replicate** otherwise; the 2017 result is then reported as not replicated in 2022.
- Secondary, reported either way: the same test at 10 px regions; the coefficient on log(A).

## Differences from 2017 that could matter, stated in advance

32 colours instead of 16; a larger, expanding canvas; a different crowd; template overlays more widely used. None is
expected to remove the hinge if spare capacity is a general property of defended artworks; any of them could, and a
failure will be reported as a failure, not explained away.
