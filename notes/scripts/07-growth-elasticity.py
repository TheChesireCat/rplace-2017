#!/usr/bin/env python3
"""
notes/scripts/07-growth-elasticity.py
prereg/07-labour-limited-growth.md: across the cooldown switches, do builds in growing regions scale with placements?

Input:  data/placements.parquet (via rplace17)
Output: printed results
Deviation from the pre-registration, disclosed: builds and placements are counted +1 before taking logs, so that a
region with no builds after a switch does not drop out.
"""
import numpy as np
import polars as pl
import rplace17 as r

REGION = 20
NB = (r.SIZE + REGION - 1) // REGION
rng = np.random.default_rng(0)

d = r.load()
hist = r.pixel_history(d)
t = d["t_us"].to_numpy(); x = d["x"].to_numpy().astype(np.int64); y = d["y"].to_numpy().astype(np.int64)
c = d["color"].to_numpy().astype(np.int64); prev = hist["prev_color"].to_numpy().astype(np.int64)
pix = y * r.SIZE + x
reg_of_pix = ((np.arange(r.SIZE * r.SIZE) % r.SIZE) // REGION) * NB + (np.arange(r.SIZE * r.SIZE) // r.SIZE) // REGION
n_px = np.bincount(reg_of_pix, minlength=NB * NB)

# settled colour: the longest-held colour state of each pixel over the whole event (look-ahead outcome definition)
close = t.max()
states = (hist.with_row_index("i").filter(~pl.col("wasted"))
              .with_columns((pl.col("y").cast(pl.Int64) * r.SIZE + pl.col("x").cast(pl.Int64)).alias("pix"))
              .sort("pix", "t_us", "i").with_columns(pl.col("t_us").shift(-1).over("pix").fill_null(close).alias("t_end"))
              .with_columns((pl.col("t_end") - pl.col("t_us")).alias("dur")))
best = states.sort("dur", descending=True).group_by("pix").first()
settled = np.zeros(r.SIZE * r.SIZE, np.int64)              # never-touched pixels stay white (0)
settled[best["pix"].to_numpy()] = best["color"].to_numpy()
is_build = (c == settled[pix]) & (prev != settled[pix])

def canvas_at(t_us):
    cv = np.zeros(r.SIZE * r.SIZE, np.int64)
    k = np.searchsorted(t, t_us)
    cv[pix[:k]] = c[:k]                                   # later placements overwrite earlier ones (time-sorted)
    return cv

def pairs(switches, W_min):
    W = W_min * 60_000_000
    out = []
    for k, (sb, sa, new_c, direction) in enumerate(switches, start=1):
        b = r._us(sb); a = r._us(sa) + new_c * 1_000_000
        cv = canvas_at(b - W)
        comp = np.bincount(reg_of_pix, weights=(cv == settled), minlength=NB * NB) / n_px
        def counts(lo, hi):
            i0, i1 = np.searchsorted(t, lo), np.searchsorted(t, hi)
            rr = reg_of_pix[pix[i0:i1]]
            return np.bincount(rr, minlength=NB * NB), np.bincount(rr, weights=is_build[i0:i1], minlength=NB * NB)
        Lb, Bb = counts(b - W, b); La, Ba = counts(a, a + W)
        grow = (comp >= 0.2) & (comp <= 0.8) & (Bb >= 20)
        for g in np.nonzero(grow)[0]:
            out.append({"k": k, "direction": direction, "region": g, "Lb": Lb[g], "La": La[g], "Bb": Bb[g], "Ba": Ba[g]})
    p = pl.DataFrame(out)
    return p.with_columns((np.log((pl.col("La") + 1) / (pl.col("Lb") + 1))).alias("dL"),
                          (np.log((pl.col("Ba") + 1) / (pl.col("Bb") + 1))).alias("dB"))

def slope(p):
    x_, y_ = p["dL"].to_numpy(), p["dB"].to_numpy()
    return float((x_ * y_).sum() / (x_ * x_).sum())

def boot(p, B=500):
    regs = p["region"].unique().to_numpy(); by = {g: s for (g,), s in p.group_by("region")}
    return np.quantile([slope(pl.concat([by[g] for g in rng.choice(regs, len(regs))])) for _ in range(B)], [0.025, 0.975])

for W_min in (40, 20):
    p = pairs(r.SWITCHES, W_min)
    eps, ci = slope(p), boot(p)
    print(f"\nW = {W_min} min: {p.height} region-switch pairs, {p['region'].n_unique()} regions, {int(p['Bb'].sum()):,} builds before")
    for k in range(1, 7):
        q = p.filter(pl.col("k") == k)
        if q.height:
            print(f"  switch {k} ({'tighten' if q['direction'][0] > 0 else 'loosen'}): {q.height} regions, mean dlog placements {q['dL'].mean():+.2f}, "
                  f"mean dlog builds {q['dB'].mean():+.2f}, slope {slope(q):+.2f}")
    verdict = ("labour-limited (H1)" if ci[0] > 0.5 and ci[0] <= 1 <= ci[1] else
               "limited by something else (H0)" if ci[0] <= 0 <= ci[1] and ci[1] < 0.5 else "intermediate")
    print(f"  pooled elasticity {eps:+.3f} [{ci[0]:+.3f}, {ci[1]:+.3f}] -> {verdict}")
    pp = pairs(r.PLACEBO, W_min)
    print(f"  placebo: {pp.height} pairs, mean |dlog placements| {pp['dL'].abs().mean():.2f}, slope {slope(pp):+.3f} {np.round(boot(pp, 200), 3)}")
