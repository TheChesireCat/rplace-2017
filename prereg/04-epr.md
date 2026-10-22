# Pre-registration: exploration and preferential return (chapter 4)

Dated 2026-10-22. Committed and pushed before any quantity below was computed.

**What had been seen before writing this:** chapter 4's results: prompt jumps are mostly local; 47% of placements land
within 5 px of one of the account's previous 10 (35% in random order); at the scale of single pixels, accounts with
≥ 200 placements touch about 174 distinct pixels in their first 200 placements, about the same in random order. No
quantity defined below (places as blocks, exploration probability against S, return choice) has been computed.

**The model** (Song, Koren, Wang and Barabási 2010, doi:10.1038/nphys1760; main text read, arXiv:1010.0436, pp. 1-8):
at each move, with probability P_new = ρ S^−γ the individual goes to a new place (S = places visited so far);
otherwise it returns to visited place i with probability Π_i = f_i, the share of its past visits that went to i. It
predicts S ~ n^{1/(1+γ)} in moves n, and visit frequencies f_k ~ k^−ζ with ζ = 1 + γ. The paper reports γ = 0.21 ± 0.02,
⟨ρ⟩ ≈ 0.6 and ζ ≈ 1.2 for mobile-phone users.

## Places, moves, accounts

- **Place:** a block of b × b pixels, (x // b, y // b). **Primary b = 10.** Sensitivity: b = 5 and 25 (reported, not
  used for the decision). Single pixels (b = 1) are reported descriptively.
- **Move:** each placement after launch is a visit to its block; a placement in the same block as the account's
  previous placement is a stay, not a move, and is skipped (as the model counts changes of location).
- **Accounts:** at least 100 placements after launch.

## Rival explanations of returns

- **EPR:** returns go to places in proportion to past visits (Π_i ∝ f_i).
- **Uniform return:** returns pick any visited place with equal probability.
- **Recency:** returns go to recently visited places, whatever their visit count.

## Measurements

- **M1 exploration:** for each move, whether it goes to a new place, against S at that moment. P_new(S) is pooled over
  accounts in logarithmic bins of S (from S = 2 to the largest S with at least 1,000 moves); γ is the negative slope of
  log P_new on log S (least squares over bins weighted by moves); ρ the intercept. 95% interval by resampling accounts
  (200 resamples).
- **M2 return choice:** for return moves, a conditional logit over the account's visited places, with two features:
  log of past visits to the place (log m_i) and log of moves since the account was last there (log recency). Under EPR
  the coefficient on log m_i is 1 and on recency 0; under uniform return both are 0; under recency the recency
  coefficient is negative and carries the fit. Fitted on a random sample of 200,000 return moves (seed 0); 95%
  intervals by resampling accounts (100 resamples). Also reported: the model with log m_i alone.
- **M3 consistency:** the exponent of S(n) (least squares of log median S on log n, n = 10 to 100, accounts with ≥ 100
  placements) against 1 / (1 + γ); the Zipf exponent ζ of visit frequency by rank (least squares, ranks 1 to 10,
  pooled over accounts) against 1 + γ.

## Decision rule (primary, b = 10)

EPR is **supported** if all hold:

1. γ > 0, its interval excluding 0;
2. in the two-feature logit, the coefficient on log m_i is positive with its interval excluding 0, and its 95% interval
   overlaps [0.5, 1.5];
3. adding recency does not reduce the log m_i coefficient below half its value in the model with log m_i alone;
4. M3: the S(n) exponent within 0.1 of 1/(1 + γ), and ζ within 0.2 of 1 + γ.

If 1 fails, there is no exploration slowdown to explain. If 2 or 3 fails, returns are not preferential in the model's
sense (uniform or recency instead, by which coefficient carries the fit). If only 4 fails, the ingredients hold but the
model's predicted scaling does not.

## Known limits

The event lasts three days and the busiest account has 656 placements, so S stays small (tens to a few hundred places)
and scaling exponents are fitted over about one decade; the paper's predictions are asymptotic. The canvas holds only
10,201 blocks of 10 × 10.
