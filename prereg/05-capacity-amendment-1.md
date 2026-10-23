# Amendment 1 to `05-capacity.md`: a hinge test (post hoc, written after the original test proved uninformative)

Dated 2026-10-22. Written **after** seeing the original result and the descriptive table of wasted share by
log(L/(W+1)) within completion bands, so this is not a blind test; committed before the hinge model below was fitted to
the data or to the simulations.

**Idea.** Random targeting makes the wasted share rise smoothly with placements per wrong pixel. Spare capacity
predicts a hinge: little change while placements are fewer than wrong pixels (log(L/(W+1)) < 0), and a steep rise once
they exceed them.

**Model.** Wasted share ~ a·min(z, 0) + b·max(z, 0) + log(A) + completion fixed effects (bins of 0.05), z =
log(L/(W+1)); same region-windows and simulations as the original. Statistic: the hinge contrast H = b − a.

**Decision.** Spare capacity is supported if H in the data is positive with its 95% region-resampling interval above 0
**and** above the largest H from three random-targeting simulations (seeds 10-12). Otherwise not supported. The positive
control (simulated capacity) must give H > 0, else the test is not informative.
