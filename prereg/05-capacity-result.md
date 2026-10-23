# Result of `05-capacity.md` (run 2026-10-22, `notes/scripts/05-capacity-test.py`)

**Controls.** Positive (simulated spare capacity): coefficient on log(L/(W+1)) = +0.187, as required. **Negative
(simulated random targeting): +0.029** (three further seeds: +0.026, +0.027, +0.025), not about 0 as required. The
cause is mechanical: within a 15-minute window, random placements also fix wrong pixels, so the more placements per
wrong pixel, the more of the window is spent on an already-fixed region, and the wasted share rises without any
spare-capacity behaviour.

**Verdict, as pre-registered: the test is not informative.** A control failed, so the H1 and H2 coefficients from the
data (+0.060 [0.055, 0.064] and +0.020 [0.015, 0.026]) do not decide between the three readings.

**Secondary (replication).** Change in completion over 2 h against log((repairs + 1) / (attacks + 1)): +0.020
[0.0195, 0.0206], with attacks in the next window controlled (−0.75 [−0.86, −0.64]), n = 621,049 region-windows.
Repair deficits precede losses in 2017 beyond the persistence of attacks: this reproduces, in another edition, what
Falmagne et al. (2026) report for 2022-23.
