import numpy as np, polars as pl, rplace17 as r
h = pl.read_parquet(r.DATA / "pixel_history.parquet"); close = h["t_us"].max()
px = pl.col("x").cast(pl.Int32) * r.SIZE + pl.col("y").cast(pl.Int32)
h = h.with_row_index("i").with_columns(px.alias("pix"))
# each pixel's settled colour = its longest-held colour state, and when it began
st = (h.filter(~pl.col("wasted")).sort("pix", "t_us", "i")
       .with_columns(pl.col("t_us").shift(-1).over("pix").fill_null(close).alias("t_end"))
       .with_columns((pl.col("t_end") - pl.col("t_us")).alias("dur")))
settled = st.sort("dur", descending=True).group_by("pix").first().select("pix", pl.col("color").alias("sc"), pl.col("t_us").alias("t_settle"))
L = (h.filter(pl.col("t_us") >= r.LAUNCH_US).join(settled, on="pix")
       .with_columns(((pl.col("x") // 20) * 100 + pl.col("y") // 20).alias("region"),
                     ((pl.col("t_us") - r.LAUNCH_US) // 900_000_000).alias("w"),
                     pl.when(pl.col("wasted")).then(pl.lit("reinforce"))
                       .when((pl.col("color") == pl.col("sc")) & (pl.col("prev_color") != pl.col("sc")) & (pl.col("undo") == True)).then(pl.lit("repair"))
                       .when(pl.col("color") == pl.col("sc")).then(pl.lit("build"))
                       .when(pl.col("prev_color") == pl.col("sc")).then(pl.lit("attack"))
                       .otherwise(pl.lit("other")).alias("kind")))
print(L.group_by("kind").len().with_columns((pl.col("len")/pl.col("len").sum()).round(3)).sort("kind"))
# completion per region-window: share of region pixels showing their settled colour at window end (approx: pixel correct if its state set before then is sc)
# compute via state intervals: for each state, mark correct=(color==sc); per region, completion(t) = sum over pixels of correct at t / pixels
stc = st.join(settled, on="pix").with_columns((pl.col("color") == pl.col("sc")).alias("ok"), ((pl.col("x") // 20) * 100 + pl.col("y") // 20).alias("region"))
W = int((close - r.LAUNCH_US) // 900_000_000) + 1
grid_t = r.LAUNCH_US + (np.arange(W) + 1) * 900_000_000
ok = stc.filter(pl.col("ok"))
s0, s1 = ok["t_us"].to_numpy(), ok["t_end"].to_numpy(); reg = ok["region"].to_numpy()
ureg, ri = np.unique(reg, return_inverse=True)
npx = stc.group_by("region").agg(pl.col("pix").n_unique().alias("n")).sort("region")
npx_map = dict(zip(npx["region"].to_list(), npx["n"].to_list()))
C = np.zeros((len(ureg), W))
a = np.searchsorted(grid_t, s0, side="left"); b = np.searchsorted(grid_t, s1, side="left")   # windows whose end lies in [s0, s1)
for k in range(len(s0)):
    if b[k] > a[k]: C[ri[k], a[k]:b[k]] += 1
C = C / np.array([npx_map[u] for u in ureg])[:, None]
# composition per region-window
comp = L.group_by("region", "w", "kind").len().pivot(on="kind", index=["region", "w"], values="len").fill_null(0)
kinds = ["build", "attack", "repair", "reinforce", "other"]
comp = comp.with_columns(pl.sum_horizontal(kinds).alias("n")).filter(pl.col("n") >= 20)
reg_index = {u: i for i, u in enumerate(ureg)}
comp = comp.with_columns(pl.Series("completion", [C[reg_index[g], w] if w < W else np.nan for g, w in zip(comp["region"], comp["w"])]))
# (a) wasted (reinforce) share and build share by completion
comp = comp.with_columns(*[(pl.col(k) / pl.col("n")).alias(f"{k}_s") for k in kinds])
print("\nby completion of the region (share of its pixels showing their settled colour):")
print(comp.with_columns((pl.col("completion") * 10).floor().clip(0, 9).alias("c10")).group_by("c10").agg(pl.len().alias("windows"), *[pl.col(f"{k}_s").mean().round(3) for k in kinds]).sort("c10"))
# (b) align on each region's own t50 (first window completion >= 0.5) vs calendar
t50 = {u: int(np.argmax(C[i] >= 0.5)) if (C[i] >= 0.5).any() else None for i, u in enumerate(ureg)}
comp = comp.with_columns(pl.Series("t50", [t50[g] for g in comp["region"]], dtype=pl.Int64)).drop_nulls("t50").with_columns((pl.col("w") - pl.col("t50")).alias("rel"))
print("\nregions reaching 50% completion:", sum(v is not None for v in t50.values()), "of", len(ureg), "| t50 (hours) quartiles", np.quantile([v/4 for v in t50.values() if v is not None], [.25,.5,.75]))
rel = comp.filter(pl.col("rel").is_between(-16, 32)).group_by(((pl.col("rel") // 4)).alias("h")).agg(pl.len().alias("windows"), *[pl.col(f"{k}_s").mean().round(3) for k in kinds]).sort("h")
print("\naligned on own t50 (hours):"); print(rel)
# (1) labour per pixel vs completion
comp_l = comp.with_columns((pl.col("n") / pl.Series([npx_map[g] for g in comp["region"]])).alias("per_px"))
print("\nplacements per region pixel per 15 min, by completion:")
print(comp_l.with_columns((pl.col("completion") * 10).floor().clip(0, 9).alias("c10")).group_by("c10").agg(pl.col("per_px").median().round(3).alias("median"), pl.col("per_px").mean().round(3).alias("mean")).sort("c10"))
# (2) region-specific lifecycle: permute t50 across regions
rng = np.random.default_rng(0)
def peak_profile(df):
    p = df.filter(pl.col("rel").is_between(-16, 32)).group_by((pl.col("rel") // 4).alias("h")).agg(pl.col("build_s").mean(), pl.col("reinforce_s").mean()).sort("h")
    b = dict(zip(p["h"].to_list(), p["build_s"].to_list())); rf = dict(zip(p["h"].to_list(), p["reinforce_s"].to_list()))
    return b.get(-1, np.nan) - b.get(4, np.nan), rf.get(4, np.nan) - rf.get(-1, np.nan)
real = peak_profile(comp)
regs = list(t50.keys()); vals = [t50[g] for g in regs]
null = []
for _ in range(20):
    perm = dict(zip(regs, rng.permutation(vals)))
    c2 = comp.with_columns(pl.Series("t50p", [perm[g] for g in comp["region"]], dtype=pl.Int64)).drop_nulls("t50p").with_columns((pl.col("w") - pl.col("t50p")).alias("rel"))
    null.append(peak_profile(c2))
null = np.array(null)
print(f"\nbuild drop (-1h minus +4h) and reinforce rise (+4h minus -1h): own t50 {np.round(real,3)}; permuted t50 mean {null.mean(0).round(3)}, max {null.max(0).round(3)}")
# (3) fronts: share of pixels whose 4-neighbour (same region) settled earlier, vs shuffle within region
sp = settled.with_columns((pl.col("pix") // r.SIZE).alias("x"), (pl.col("pix") % r.SIZE).alias("y")).with_columns(((pl.col("x") // 20) * 100 + pl.col("y") // 20).alias("region"))
T = np.full((r.SIZE, r.SIZE), np.nan); T[sp["x"].to_numpy(), sp["y"].to_numpy()] = sp["t_settle"].to_numpy().astype(float)
Rg = np.full((r.SIZE, r.SIZE), -1); Rg[sp["x"].to_numpy(), sp["y"].to_numpy()] = sp["region"].to_numpy()
def neighbour_earlier(T):
    cnt = tot = 0
    hit = np.zeros(T.shape, bool)
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        A = np.roll(np.roll(T, dx, 0), dy, 1); RA = np.roll(np.roll(Rg, dx, 0), dy, 1)
        hit |= (RA == Rg) & (A < T)
    valid = ~np.isnan(T)
    return hit[valid].mean()
real_f = neighbour_earlier(T)
# within-region shuffle of settle times
nulls = []
for s_ in range(5):
    Tn = T.copy()
    shuffled = sp.with_columns(pl.col("t_settle").shuffle(seed=s_).over("region").alias("ts"))
    Tn[shuffled["x"].to_numpy(), shuffled["y"].to_numpy()] = shuffled["ts"].to_numpy().astype(float)
    nulls.append(neighbour_earlier(Tn))
print(f"pixels with an earlier-settled neighbour in their region: data {real_f:.3f}, within-region shuffle {np.mean(nulls):.3f}")
# front speed proxy: correlation between settle time and distance from the region's first-settled pixel
rows = []
for reg_id, g in sp.filter(pl.col("t_settle") > r.LAUNCH_US).group_by("region"):
    if g.height < 200: continue
    x, y, t = g["x"].to_numpy(), g["y"].to_numpy(), g["t_settle"].to_numpy()
    i0 = np.argmin(t); dist = np.hypot(x - x[i0], y - y[i0])
    rows.append(stats.spearmanr(dist, t).statistic if False else np.corrcoef(np.argsort(np.argsort(dist)), np.argsort(np.argsort(t)))[0,1])
rows = np.array(rows)
print(f"rank correlation of settle time with distance from the first-settled pixel, per region: median {np.median(rows):.2f}, share > 0.3 {np.mean(rows>0.3):.0%}, share < -0.1 {np.mean(rows<-0.1):.0%} (n={len(rows)})")

# ---- defence margin: do repair deficits precede losses? (exploratory)
cw = comp_l.sort("region", "w")
# completion two hours later
cw = cw.with_columns(pl.Series("c_later", [C[reg_index[g], w + 8] if w + 8 < W else np.nan for g, w in zip(cw["region"], cw["w"])]))
m = cw.filter((pl.col("completion") >= 0.7) & pl.col("c_later").is_not_nan() & (pl.col("attack") >= 5))
m = m.with_columns((pl.col("repair") / pl.col("attack")).alias("ratio"), (pl.col("c_later") - pl.col("completion")).alias("dc"),
                   ((pl.col("repair") + pl.col("reinforce")) / pl.col("n")).alias("spare_plus_repair"))
print(f"\nmaintenance windows (completion >= 0.7, >= 5 attacks): {m.height:,}")
print(m.with_columns(pl.col("ratio").cut([0.5, 0.8, 1.0, 1.25, 2.0]).alias("repair/attack")).group_by("repair/attack")
       .agg(pl.len().alias("windows"), pl.col("dc").mean().round(4).alias("mean change in completion, next 2 h"), (pl.col("dc") < -0.1).mean().round(3).alias("P(lose > 10 points)")).sort("repair/attack"))
print("balance: overall repairs / attacks in maintenance windows:", round(m["repair"].sum() / m["attack"].sum(), 3))
