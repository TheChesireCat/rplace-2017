#!/usr/bin/env python3
"""
notes/scripts/06-capacity-hinge.py
Amendment 1 to prereg/05-capacity.md: the hinge test. Reads data/scratch/05-region-windows.parquet (from 05-capacity-test.py).
"""
import os, numpy as np, polars as pl
src = open("notes/scripts/05-capacity-test.py").read().split("# ---------------------------------------------------------------- the data")[0]
ns = {}; exec(src.replace("pos, neg = fit(simulate(True)), fit(simulate(False, n=5_000))", "").replace('print(f"positive control', '#').replace('print(f"negative control', '#'), ns)
def hinge(df):
    y = df["wasted_share"].to_numpy(); z = np.log(df["L"].to_numpy() / (df["W"].to_numpy() + 1))
    b = np.minimum((df["completion"].to_numpy() * 20).astype(int), 19)
    X = np.column_stack([np.minimum(z, 0), np.maximum(z, 0), np.log(df["A"].to_numpy())] + [(b == k).astype(float) for k in np.unique(b)])
    co = np.linalg.lstsq(X, y, rcond=None)[0]
    return co[0], co[1], co[1] - co[0]
ns["rng"] = np.random.default_rng(0)
pos = hinge(ns["simulate"](True))
negs = []
for s in (10, 11, 12):
    ns["rng"] = np.random.default_rng(s); negs.append(hinge(ns["simulate"](False, n=4000)))
print(f"positive control (capacity): below {pos[0]:+.3f}, above {pos[1]:+.3f}, H {pos[2]:+.3f}")
for s, n_ in zip((10, 11, 12), negs): print(f"negative control seed {s}: below {n_[0]:+.3f}, above {n_[1]:+.3f}, H {n_[2]:+.3f}")
rw = pl.read_parquet(os.environ.get("OUT", "data/scratch/05-region-windows.parquet"))
use = rw.filter((pl.col("L") >= 20) & (pl.col("completion") >= 0.5))
a, b, H = hinge(use)
rng = np.random.default_rng(0); regs = use["region"].unique().to_numpy(); by = {k: g for (k,), g in use.group_by("region")}
boot = np.array([hinge(pl.concat([by[k] for k in rng.choice(regs, len(regs))])) for _ in range(200)])
lo, hi = np.quantile(boot[:, 2], [0.025, 0.975]); hmax = max(n_[2] for n_ in negs)
print(f"data: slope below {a:+.4f}, above {b:+.4f}, H {H:+.4f} [{lo:+.4f}, {hi:+.4f}]; largest random-targeting H {hmax:+.4f}")
ok_pos = pos[2] > 0
print("verdict:", "not informative (positive control failed)" if not ok_pos else ("spare capacity SUPPORTED" if lo > 0 and lo > hmax else "spare capacity NOT supported"))
