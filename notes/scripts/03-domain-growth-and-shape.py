import numpy as np, polars as pl, rplace17 as r
from scipy import ndimage
h = pl.read_parquet(r.DATA / "pixel_history.parquet"); close = h["t_us"].max()
px = pl.col("x").cast(pl.Int32) * r.SIZE + pl.col("y").cast(pl.Int32)
h = h.with_row_index("i").with_columns(px.alias("pix"))
st = (h.filter(~pl.col("wasted")).sort("pix", "t_us", "i").with_columns(pl.col("t_us").shift(-1).over("pix").fill_null(close).alias("t_end"))
       .with_columns((pl.col("t_end") - pl.col("t_us")).alias("dur")))
sc = st.sort("dur", descending=True).group_by("pix").first().select("pix", pl.col("color").alias("sc"))
fb = st.join(sc, on="pix").filter(pl.col("color") == pl.col("sc")).group_by("pix").agg(pl.col("t_us").min().alias("t_build"))
SC = np.full((r.SIZE, r.SIZE), -1, np.int16); SC[(sc["pix"] % r.SIZE).to_numpy(), (sc["pix"] // r.SIZE).to_numpy()] = sc["sc"].to_numpy()  # [y, x]
TB = np.full((r.SIZE, r.SIZE), np.nan); TB[(fb["pix"] % r.SIZE).to_numpy(), (fb["pix"] // r.SIZE).to_numpy()] = (fb["t_build"].to_numpy() - r.LAUNCH_US) / 3.6e9
# domains: 4-connected patches of one settled colour, excluding white (the background) 
lab = np.zeros(SC.shape, np.int64); nlab = 0
for c in range(1, 16):
    l, n = ndimage.label(SC == c); lab[l > 0] = l[l > 0] + nlab; nlab += n
sizes = np.bincount(lab.ravel()); sizes[0] = 0
big = np.nonzero(sizes >= 1000)[0]
print(f"domains (non-white): {nlab:,}; with >= 1000 px: {len(big)}; covering {sizes[big].sum()/SC.size:.1%} of the canvas")
# 1. outward growth: per big domain, rank corr of build time with distance from the centroid of its earliest 2% pixels
rc, rc_null, compact = [], [], []
rng = np.random.default_rng(0)
for dlab in big:
    yy, xx = np.nonzero(lab == dlab); t = TB[yy, xx]; ok = ~np.isnan(t) & (t >= 0)
    if ok.sum() < 500: continue
    yy, xx, t = yy[ok], xx[ok], t[ok]
    seed = t <= np.quantile(t, 0.02); cy, cx = yy[seed].mean(), xx[seed].mean()
    dist = np.hypot(yy - cy, xx - cx)
    rk = lambda a: np.argsort(np.argsort(a))
    rc.append(np.corrcoef(rk(dist), rk(t))[0, 1])
    tp = rng.permutation(t); seedp = tp <= np.quantile(tp, 0.02)
    distp = np.hypot(yy - yy[seedp].mean(), xx - xx[seedp].mean()); rc_null.append(np.corrcoef(rk(distp), rk(tp))[0, 1])
rc, rc_null = np.array(rc), np.array(rc_null)
print(f"1. outward growth, rank corr(build time, distance from the earliest-built 2%): median {np.median(rc):.2f} (shuffled build times {np.median(rc_null):.2f}); >0.3 in {np.mean(rc>0.3):.0%}, >0.5 in {np.mean(rc>0.5):.0%} of {len(rc)} domains")
# 2. shape-following: |difference in build time| between 4-neighbours, within a domain vs across a domain border (both built)
within, across = [], []
for dy, dx in ((0, 1), (1, 0)):
    A, B = TB[: r.SIZE - dy, : r.SIZE - dx], TB[dy:, dx:]
    LA, LB = lab[: r.SIZE - dy, : r.SIZE - dx], lab[dy:, dx:]
    ok = ~np.isnan(A) & ~np.isnan(B) & (LA > 0) & (LB > 0)
    d = np.abs(A - B)
    within.append(d[ok & (LA == LB)]); across.append(d[ok & (LA != LB)])
within, across = np.concatenate(within), np.concatenate(across)
print(f"2. neighbour build-time difference (h): within a domain median {np.median(within):.2f}, across a domain border median {np.median(across):.2f}; within < 1 h: {np.mean(within<1):.0%}, across < 1 h: {np.mean(across<1):.0%}")
np.save("data/scratch/lab.npy", lab); np.save("data/scratch/tb.npy", TB); np.save("data/scratch/sc.npy", SC)
order = big[np.argsort(-sizes[big])][:12]
for dlab in order[:6]:
    yy, xx = np.nonzero(lab == dlab); c = SC[yy[0], xx[0]]
    print(f"   domain {dlab}: {sizes[dlab]} px, colour {c}, box x {xx.min()}-{xx.max()} y {yy.min()}-{yy.max()}")
