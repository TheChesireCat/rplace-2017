# Evolving a lead: the life of an artwork

Dated 2026-10-22. One round of the playground's idea-evolution protocol (seed, red-team, novelty, evolve, re-check,
finesse). Everything measured here is **exploratory**: it was computed on the whole canvas after looking at the
activity video, so none of it can be confirmed on the same data. Numbers are from scratch scripts, not yet in the book.

## 0. Seed

**Claim.** An artwork's life is governed by a labour budget. Defenders can each place once per cooldown. While an
artwork is incomplete their labour builds it, along local fronts; once it is complete the same labour goes into repair,
and what is left over shows up as *wasted* repaints of pixels that are already right; when attacks outrun the labour
that defends it, it loses ground.

**Figure.** Placement mix (build, attack, repair, reinforce) against completion, and the chance of losing ground
against repairs ÷ attacks.

**Prediction that could fail.** Holding completion fixed, the wasted share rises with labour per damaged pixel. If it is
flat, wasted placements are not spare capacity.

### What the data showed first (exploratory, 20 × 20 regions, 15-minute windows)

- **Labour stays:** placements per pixel are flat across completion (median about 0.09 per 15 min).
- **The mix shifts:** from low to high completion, building 12% → 2% of placements, repair 6% → 24%, reinforcement
  14% → 42%, attacks 12% → 24%.
- **Region-specific, not a global trend:** aligned on each region's own 50%-completion time, reinforcement rises by 0.105
  within hours; with times permuted across regions, at most 0.027.
- **Growth is local:** 46% of newly built pixels have a neighbour built in the previous 30 minutes, against 16% with build
  times shuffled within the region; but rarely from a single seed (rank correlation with distance from the first-built
  pixel: median 0.01 in grid regions). On colour domains of ≥ 1,000 px it is 0.27 (shuffle 0.00), with both expanding
  colonies (blue corner, 0.84) and template fills (the red text block, −0.06).
- **Shape-following:** neighbours inside a colour domain were built a median 0.35 h apart; across a domain border, 12 h.
- **Damage is clustered:** of wrong pixels inside finished domains, 20% are isolated specks (random scatter: 74%) and
  41% sit in clusters of ≥ 10 (random: 0%).
- **Balance and loss:** in maintenance windows, repairs are 89% of attacks; when repairs fall below half of attacks, the
  region loses 2.1 completion points over the next 2 h on average and loses more than 10 points 9% of the time, against
  about 2% when repairs keep up.

What looking at zoomed crops of the canvas over time suggested (descriptive): an expanding domain that later becomes
ground for other artworks (blue corner); letters first, then a sweeping fill (text block); early chaos, crystallisation,
an erasing wave (the "Void"), then new artworks in its place (centre); a flag growing along one axis, raids, merging
(lower left).

## 1. Red-team

- **Known, renamed?** Partly. Territory size set by the cost of defending it is *economic defendability* in behavioural
  ecology (Brown 1964; not yet read or verified here). Vandalism repair in Wikipedia is a related maintenance process.
  The labour-budget account of r/place artworks as a whole: not found (see 2).
- **Would a trivial baseline draw the same plot?** Three:
  - *definitions*: high completion forces building down and makes a right-colour placement more likely to be wasted;
  - *a global trend*: everything matures over the event (handled by the permuted-time null for the lifecycle);
  - *persistence of raids*: a window with a repair deficit may simply be the start of a raid that continues.
- **What would change minds?** The capacity test (wasted share against spare labour at fixed completion), and the
  deficit → loss link surviving a control for attacks in the following window.
- **Well defined on our data?** Only partly: the unit should be an artwork, but colour domains and grid regions are not
  artworks (black outlines join many; the blue corner hosts many). Artwork recovery from placements (the 2023 project's
  estimator) or the 2017 Atlas, as a weak check, is needed for artwork-level claims.

## 2. Novelty (searched: three web searches on r/place lifecycle, transitions and early warnings; no Scholar search)

- **Falmagne, Stephenson and Levin (2026), PNAS 123(1) e2503493122** (abstract read): early warnings of *transitions*
  (one composition rapidly replacing another) in 2022, tested on 2023, with gradient-boosted trees; the patterns that
  drive warnings include critical slowing down or speeding up, lack of innovation or coordination, and turbulent
  histories. **This is the work that hurts most** for anything about predicting losses.
- **Litherland and Mørch (2021), Computers in Human Behavior 122, 106845** (pp. 1–3 read): mixed-methods study of 2017
  centred on one artwork (Mona Lisa with the Swiss flag), with plant-growth and disturbed-anthill metaphors, noting
  that "users of neighboring regions expand their territory as unused space became scarce" and "creative destruction".
  Qualitative; closest to the lifecycle framing.
- **Wu and Silva (2024, v3)**: define wasted actions and treat them as *coordination inefficiency*. The seed reads the
  same quantity the opposite way, as spare defensive capacity.

**Rating:** *partial*. The lifecycle as a qualitative idea exists (Litherland and Mørch); transition prediction exists
(Falmagne et al.); what was not found in the searched scope is a measured labour-budget mechanism (spare capacity,
balance, deficit → loss) or measured front growth.

## 3. Evolve

| Operator | Offspring |
|---|---|
| Split | (a) growth mechanics, (b) maintenance economics, (c) loss |
| Mutate the knob | front speed and spare capacity across the cooldown switches (the natural experiment of chapters 2–3) |
| Invert | wasted placements as inefficiency (Wu and Silva): true if the wasted share is unrelated to labour or attack pressure |
| Orthogonal (ecology) | competition–colonisation trade-off (Tilman 1994, not yet read): fast colonisers with little labour per pixel (blue corner) are invaded more; dense template fills defend better |
| Transplant | economic defendability: artworks shrink or fragment to a size their labour can defend |
| Cross | defence margin × early warnings: a mechanistic warning (falling repair ÷ attack) against Falmagne et al.'s statistical ones (variance, autocorrelation) |
| Match the budget | same labour, different shape: maintenance cost grows with perimeter, so compact shapes are cheaper (the flag and curvature idea from the first conversation) |

## 4. Re-check: keep two

**Kept A — the defence budget** (b + c + invert + cross). One mechanism, three signatures: spare capacity in
maintenance (wasted share), balance (repairs ≈ attacks), and loss when the margin turns negative. It contrasts directly
with Wu and Silva's reading of wasted actions, and with Falmagne et al.'s statistical warnings by offering a mechanism.

**Kept B — labour-limited growth** (a + mutate). If building is limited by labour, a front advances by the builders'
placements divided by its length, so front speed should change with the cooldown at each switch, in proportion to
placements, and should be slower for longer fronts.

**Discarded (kept as negative or parked results):**

- *Competition–colonisation trade-off* — parked: needs artwork identity and an outcome (invaded or not) with
  popularity as a large confound; revisit after artwork recovery.
- *Economic defendability / perimeter cost* — parked for the borders chapter, where perimeter is the object; it
  absorbs the flag-curvature idea.
- *Critical-slowing-down warnings on their own* — dropped as a separate line: already the subject of Falmagne et al.; it
  stays only as the rival that A must beat.

## 5. Finesse

### A. The defence budget

1. **Key figure.** Two panels: wasted share against spare labour (placements per wrong pixel) at fixed completion;
   chance of losing ground against repairs ÷ attacks, with and without control for attacks in the next window.
2. **Falsified by:** a flat wasted share across spare labour at fixed completion (then wasted placements are not spare
   capacity); or the deficit → loss link vanishing once next-window attacks are controlled (then it is raid persistence,
   not capacity).
3. **Closest work and the difference.** Falmagne et al. (2026) predict transitions statistically in 2022–23; this
   proposes the mechanism (a labour balance) and tests it in 2017. Wu and Silva (2024) call wasted actions inefficiency;
   this predicts when they occur.
4. **Minimal version on data we hold.** 20 × 20 regions, 15-minute windows, completion from settled colours: the
   tables above already exist as scratch scripts; the capacity test is one more regression.
5. **Controls.** Positive: a simulated region with a fixed number of defenders and an attack rate we set, where the
   capacity relation holds by construction, run through the same code. Negative: labour shuffled across regions within
   the same window, which must destroy the relation. Plus: the cooldown switches as an external change in capacity
   (wasted share should fall after a tightening, as chapter 3 saw exploratorily).

### B. Labour-limited growth

1. **Key figure.** Front speed (px/h) of growing domains against builders' placements per unit of front length, with
   the windows around cooldown switches marked.
2. **Falsified by:** front speed unchanged across switches while placements change; or no relation between speed and
   placements per unit front.
3. **Closest work and the difference.** Not found for r/place in the searched scope. In physics, spreading fronts
   (Fisher–KPP) have a speed set by growth and diffusion; the analogy breaks because growth here is limited by labour,
   not reproduction, and is reversible.
4. **Minimal version.** The 13 large colour domains with clear outward growth (rank correlation > 0.5), the boundary of
   the built set in each 15-minute window, and builds within 2 px of it. Small N; the cooldown switches add a within-
   domain comparison.
5. **Controls.** Placebo times without switches; template fills (no front) as a negative case where front speed is
   undefined.

## Stop rule

One round. A and B are new offspring; a second round would run them through steps 1–2 again after the capacity test
and a front-speed measurement. Before either becomes a pre-registered chapter test, it needs the full claim gate.

## Follow-up, 2026-10-22: chasing the leads

- **Falmagne et al. (2026), read further** (Methods and SI via arXiv HTML): their 19 predictors include attack fraction,
  return rate (defence), redundant changes (= wasted) and users; "low defense activity in the past is a transition
  signal". So *deficit → loss* is **KNOWN** for 2022-23; in 2017 it replicates with attack persistence controlled
  (`prereg/05-capacity-result.md`). They read redundant changes as users attaching their name to pixels.
- **Capacity test** (`prereg/05-capacity.md`): **not informative as pre-registered** (the random-targeting control gave
  +0.029, a mechanical within-window effect). A **post-hoc hinge test** (amendment 1, committed before fitting) finds
  the capacity shape: flat while placements are fewer than wrong pixels, rising once they exceed them (H = +0.061
  [0.054, 0.069]; random targeting −0.02). Holds at 10 and 20 px and at 1-6 h references; **fails at 50 px**.
  Status: SUPPORTED WITH LIMITATIONS.
- **Half B is spent** as a holdout (`prereg/03-wasted-holdout.md`, note).

| Claim | Status now |
|---|---|
| Wasted placements are (partly) spare defensive capacity | SUPPORTED WITH LIMITATIONS (post hoc; ≤ 20 px) |
| Coordination inefficiency also contributes | UNRESOLVED (positive participants coefficient) |
| Repair deficits precede losses | REPRODUCES KNOWN RESULT (Falmagne et al.) |
| Lifecycle mix shift with completion | EXPLAINED BY CONSTRUCTION (partly) |
| Labour-limited growth (offspring B) | UNRESOLVED: builds scale one for one with placements (+1.06), but equally at placebo times (+1.06), so the switches do not discriminate (`prereg/07-*`) |

### Literature, OpenAlex (2026-10-22)

172 works matching r/place, scanned by title; relevant abstracts read. No work found that tests redundant placements
as spare defensive capacity, in r/place or, by a semantic search, in peer production generally (closest:
over-contribution in shared databases; coordination-efficiency models). Unread gaps: Israeli and Tsur 2024 (ICWSM,
community success in 2022), Eisenmann and Winters 2026 (closed), Vachher et al. 2020 (closed). Müller and Winters 2018
(PLoS ONE) already describe the 2017 canvas moving from an unstructured to a structured state, so that whole-canvas
stage is known. The hinge test stays POTENTIALLY NEW in the searched scope.

The 2022 replication was pre-registered and then withdrawn unrun: the book uses only the 2017 log.
