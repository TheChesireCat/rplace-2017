# Holdout declaration: the wasted share (chapter 3)

Dated 2026-10-22, committed and pushed before any analysis that uses it.

**Why.** Chapter 3 saw the wasted share swing by tens of percentage points across the cooldown switches, on the
whole canvas. A test of that on the same data cannot be confirmatory. Splitting the canvas in space keeps one half
unseen, so that a test written after exploring the other half can be confirmatory there.

**What has been seen.** Only whole-canvas wasted shares: overall (26.4%) and in the 20-minute windows around the six
switches (chapter 3, for all three window widths and the placebo). No wasted-share statistic for any part of the
canvas, and no breakdown of wasted placements (by account, by own versus others' pixels, over time), has been computed.

**The split.** The canvas is cut into 100 × 100 blocks, (bx, by) = (x // 100, y // 100), with x and y from 0 to 1000
(the row and column at 1000 form their own thin blocks, bx or by = 10). Like a chequerboard:

- **half A (explore):** bx + by even;
- **half B (hold out):** bx + by odd.

**Rules.**

1. Every new analysis of wasted placements (who makes them, on whose pixels, when, where) is run on half A only.
2. Before anything about wasted placements is computed on half B, a pre-registration file for the half-B test is
   committed and pushed, citing this file. It states the hypothesis, the statistic, the threshold and the N.
3. Analyses that do not look at wasted placements may use the whole canvas.
4. If rule 1 or 2 is broken, half B stops being a holdout, and this file gets a dated note saying so.
