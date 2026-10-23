# Result of `07-labour-limited-growth.md` (run 2026-10-22, `notes/scripts/07-growth-elasticity.py`)

1,731 region-switch pairs (1,143 growing regions, 83,450 builds before the switches; 40-minute windows).

- **Pooled elasticity of builds to placements: +1.062 [1.038, 1.088].** The pre-registered rule asks for an interval
  containing 1 (H1) or 0 (H0); it contains neither, so the verdict is **intermediate**.
- **Placebo check: +1.056 [1.025, 1.098]** at the six times without a switch. Builds scale with placements one for one
  whatever moves the placements, so the switches add no information beyond this ordinary co-variation: the test cannot
  separate labour-limited growth from builds being a fixed share of placements.
- 20-minute windows (sensitivity): +1.085 [1.046, 1.125]; placebo +1.083 [1.005, 1.156].
- Per switch, placements did not always move with the direction of the rule (after switch 5, a loosening, they fell:
  mean Δlog −0.23), another sign of the load confound noted in chapter 3.
- Deviation, disclosed in the script: counts +1 before logs.

**Status: UNRESOLVED.** Consistent with labour-limited growth, not a test of it. A discriminating design would need a
change in labour that does not also change everything else in proportion, which the switches do not provide here.
