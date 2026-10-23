#!/usr/bin/env python3
"""
notes/scripts/05-capacity-test.py
The pre-registered capacity test (prereg/05-capacity.md): are wasted placements spare defensive capacity?

Input:  data/placements.parquet (via rplace17)
Output: printed tables; data/scratch/05-region-windows.parquet
"""
import time
from pathlib import Path

import numpy as np
import polars as pl
import rplace17 as r

T0 = time.time()
REGION, WIN_US, MEMORY = 20, 900_000_000, 12          # 20 x 20 px, 15 min, reference over the previous 12 windows
NB = (r.SIZE + REGION - 1) // REGION
rng = np.random.default_rng(0)

# ---------------------------------------------------------------- controls first: does the regression see capacity?
def fit(df):
    """wasted share ~ log(L / (W + 1)) + log(A) + completion fixed effects (bins of 0.05)."""
    y = df["wasted_share"].to_numpy()
    x1 = np.log(df["L"].to_numpy() / (df["W"].to_numpy() + 1)); x2 = np.log(df["A"].to_numpy())
    b = np.minimum((df["completion"].to_numpy() * 20).astype(int), 19)
    X = np.column_stack([x1, x2] + [(b == k).astype(float) for k in np.unique(b)])
    return np.linalg.lstsq(X, y, rcond=None)[0][:2]

def simulate(capacity, n=20_000):
    rows = []
    for _ in range(n):
        N = 400; c0 = rng.uniform(0.5, 1.0); W = int(round(N * (1 - c0))); L = int(rng.integers(20, 300))
        A = max(1, int(L / rng.uniform(1, 4)))
        if capacity:
            directed = int(round(0.9 * L)); fixes = min(directed, W); wasted = directed - fixes
            rand = L - directed; wasted += rng.binomial(rand, min(1, (N - W + fixes) / N))
        else:
            wrong = W; wasted = 0
            for _ in range(L):                               # each placement at a random pixel
                if rng.random() < wrong / N: wrong -= 1
                else: wasted += 1
        rows.append({"wasted_share": wasted / L, "L": L, "W": W, "A": A, "completion": c0})
    return pl.DataFrame(rows)

pos, neg = fit(simulate(True)), fit(simulate(False, n=5_000))
print(f"positive control (capacity): coef on log(L/(W+1)) {pos[0]:+.3f}, log(A) {pos[1]:+.3f}")
print(f"negative control (random targeting): coef on log(L/(W+1)) {neg[0]:+.3f}, log(A) {neg[1]:+.3f}", flush=True)

# ---------------------------------------------------------------- the data
d = r.load()
hist = r.pixel_history(d)                                 # same row order as d
t = d["t_us"].to_numpy(); x = d["x"].to_numpy().astype(np.int64); y = d["y"].to_numpy().astype(np.int64)
c = d["color"].to_numpy().astype(np.int64); u = d["user_id"].to_numpy()
wasted = hist["wasted"].to_numpy(); prev = hist["prev_color"].to_numpy().astype(np.int64)
pix = y * r.SIZE + x
reg_of_pix = ((np.arange(r.SIZE * r.SIZE) % r.SIZE) // REGION) * NB + (np.arange(r.SIZE * r.SIZE) // r.SIZE) // REGION
reg = reg_of_pix[pix]
n_px_reg = np.bincount(reg_of_pix, minlength=NB * NB)

canvas = np.zeros(r.SIZE * r.SIZE, np.int64)
pre = t < r.LAUNCH_US
canvas[pix[pre]] = c[pre]
counts = np.zeros((16, r.SIZE * r.SIZE), np.int16)       # colour counts over the last MEMORY snapshots
ring = []
n_win = int((t.max() - r.LAUNCH_US) // WIN_US) + 1
starts = r.LAUNCH_US + np.arange(n_win) * WIN_US
idx = np.searchsorted(t, np.r_[starts, t.max() + 1])
rows, completion_by_w = [], {}
for w in range(n_win):
    lo, hi = idx[w], idx[w + 1]
    if len(ring) == MEMORY:
        ref = counts.argmax(axis=0)
        wrong = canvas != ref
        Wr = np.bincount(reg_of_pix[wrong], minlength=NB * NB)
        comp = 1 - Wr / n_px_reg
        completion_by_w[w] = comp
        rr, cc, pp = reg[lo:hi], c[lo:hi], prev[lo:hi]
        R = ref[pix[lo:hi]]
        L = np.bincount(rr, minlength=NB * NB)
        Wa = np.bincount(rr, weights=wasted[lo:hi], minlength=NB * NB)
        rep = np.bincount(rr, weights=(pp != R) & (cc == R), minlength=NB * NB)
        att = np.bincount(rr, weights=(pp == R) & (cc != R), minlength=NB * NB)
        ru = np.unique(rr.astype(np.int64) * 10_000_000 + u[lo:hi])
        A = np.bincount(ru // 10_000_000, minlength=NB * NB)
        keep = np.nonzero(L > 0)[0]
        rows.append(pl.DataFrame({"w": w, "region": keep, "L": L[keep], "A": A[keep], "W": Wr[keep], "completion": comp[keep],
                                  "wasted": Wa[keep], "repairs": rep[keep], "attacks": att[keep], "n_px": n_px_reg[keep]}))
    canvas[pix[lo:hi]] = c[lo:hi]                         # advance to the end of window w
    snap = canvas.copy()
    np.add.at(counts, (snap, np.arange(snap.size)), 1)
    ring.append(snap)
    if len(ring) > MEMORY:
        old = ring.pop(0); np.subtract.at(counts, (old, np.arange(old.size)), 1)
    if w % 50 == 0:
        print(f"  window {w}/{n_win} ({time.time() - T0:.0f}s)", flush=True)

rw = pl.concat(rows).with_columns((pl.col("wasted") / pl.col("L")).alias("wasted_share"))
Path("data/scratch").mkdir(parents=True, exist_ok=True)
rw.write_parquet("data/scratch/05-region-windows.parquet")
use = rw.filter((pl.col("L") >= 20) & (pl.col("completion") >= 0.5))
coef = fit(use)
regions = use["region"].unique().to_numpy()
by_reg = {k: g for (k,), g in use.group_by("region")}
boot = np.array([fit(pl.concat([by_reg[k] for k in rng.choice(regions, len(regions))])) for _ in range(200)])
ci = np.quantile(boot, [0.025, 0.975], axis=0)
print(f"\nregion-windows used: {use.height:,} ({use['region'].n_unique():,} regions)")
print(f"H1 coef on log(L/(W+1)): {coef[0]:+.4f}  95% CI [{ci[0,0]:+.4f}, {ci[1,0]:+.4f}]  -> {'supported' if ci[0,0] > 0 else 'not supported'}")
print(f"H2 coef on log(A):        {coef[1]:+.4f}  95% CI [{ci[0,1]:+.4f}, {ci[1,1]:+.4f}]  -> {'supported' if ci[0,1] > 0 else 'not supported'}")
# descriptive: wasted share by labour per wrong pixel within completion bands
show = use.with_columns(pl.col("completion").cut([0.7, 0.9]).alias("completion band"),
                        (pl.col("L") / (pl.col("W") + 1)).log().cut([-1, 0, 1, 2]).alias("log(L/(W+1))"))
print(show.group_by("completion band", "log(L/(W+1))").agg(pl.len().alias("n"), pl.col("wasted_share").mean().round(3)).sort("completion band", "log(L/(W+1))"))

# ---------------------------------------------------------------- secondary: deficit -> loss with persistence controlled
rw2 = rw.sort("region", "w").with_columns(pl.col("attacks").shift(-1).over("region").alias("att_next"),
                                           pl.col("w").shift(-1).over("region").alias("w_next"))
later = np.array([completion_by_w.get(w + 8, np.full(NB * NB, np.nan))[g] for w, g in zip(rw2["w"].to_numpy(), rw2["region"].to_numpy())])
rw2 = rw2.with_columns(pl.Series("dc", later - rw2["completion"].to_numpy())).filter(
    (pl.col("completion") >= 0.5) & pl.col("dc").is_not_nan() & (pl.col("w_next") == pl.col("w") + 1))
yv = rw2["dc"].to_numpy()
ratio = np.log((rw2["repairs"].to_numpy() + 1) / (rw2["attacks"].to_numpy() + 1))
a_now = rw2["attacks"].to_numpy() / rw2["n_px"].to_numpy(); a_next = rw2["att_next"].to_numpy() / rw2["n_px"].to_numpy()
b = np.minimum((rw2["completion"].to_numpy() * 20).astype(int), 19)
def fit2(ix):
    X = np.column_stack([ratio[ix], a_now[ix], a_next[ix]] + [(b[ix] == k).astype(float) for k in np.unique(b)])
    return np.linalg.lstsq(X, yv[ix], rcond=None)[0][:3]
allix = np.arange(len(yv)); co2 = fit2(allix)
regs2 = rw2["region"].to_numpy(); ureg = np.unique(regs2); pos_of = {g: np.nonzero(regs2 == g)[0] for g in ureg}
boot2 = np.array([fit2(np.concatenate([pos_of[g] for g in rng.choice(ureg, len(ureg))])) for _ in range(100)])
ci2 = np.quantile(boot2, [0.025, 0.975], axis=0)
print(f"\nsecondary (n = {len(yv):,}): change in completion over 2 h ~ log repair/attack {co2[0]:+.4f} [{ci2[0,0]:+.4f}, {ci2[1,0]:+.4f}], "
      f"attacks now {co2[1]:+.3f}, attacks next window {co2[2]:+.3f} [{ci2[0,2]:+.3f}, {ci2[1,2]:+.3f}]")
print(f"total {time.time() - T0:.0f}s")
