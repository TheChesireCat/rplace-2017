import numpy as np, polars as pl, rplace17 as r, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy import ndimage
S = "data/scratch/"
lab, TB, SC = np.load(S + "lab.npy"), np.load(S + "tb.npy"), np.load(S + "sc.npy")
sizes = np.bincount(lab.ravel()); sizes[0] = 0
big = np.nonzero(sizes >= 1000)[0]
d = r.load(); live = d.filter(pl.col("t_us") >= r.LAUNCH_US)
rng = np.random.default_rng(0)
# canvas snapshots every 2 hours from +12 h; inside each big domain after 90% of it was built: wrong pixels, their clusters
canvas = np.zeros((r.SIZE, r.SIZE), np.int8)
pre = d.filter(pl.col("t_us") < r.LAUNCH_US); canvas[pre["y"].to_numpy(), pre["x"].to_numpy()] = pre["color"].to_numpy()
t, x, y, c = live["t_us"].to_numpy(), live["x"].to_numpy(), live["y"].to_numpy(), live["color"].to_numpy()
done = 0
t90 = {dl: np.nanquantile(TB[lab == dl], 0.9) for dl in big}
masks = {dl: lab == dl for dl in big}
sing, sing_null, big_cl, big_null, wrong_share = [], [], [], [], []
for hrs in np.arange(12, 72, 2):
    te = r.LAUNCH_US + int(hrs * 3.6e9); k = np.searchsorted(t, te)
    canvas[y[done:k], x[done:k]] = c[done:k]; done = k
    for dl in big:
        if hrs < t90[dl]: continue
        m = masks[dl]; wrong = m & (canvas != SC)
        nw = int(wrong.sum())
        if nw < 5: continue
        wrong_share.append(nw / m.sum())
        cl, n = ndimage.label(wrong); cs = np.bincount(cl.ravel())[1:]
        sing.append((cs == 1).sum() / nw); big_cl.append(cs[cs >= 10].sum() / nw)
        # null: same number of wrong pixels at random positions in the domain
        idx = np.flatnonzero(m.ravel()); pick = rng.choice(idx, nw, replace=False)
        rw = np.zeros(m.size, bool); rw[pick] = True; rw = rw.reshape(m.shape)
        cl0, n0 = ndimage.label(rw); cs0 = np.bincount(cl0.ravel())[1:]
        sing_null.append((cs0 == 1).sum() / nw); big_null.append(cs0[cs0 >= 10].sum() / nw)
print(f"maintenance snapshots (domain x time): {len(sing)}; wrong share of domain pixels: median {np.median(wrong_share):.1%}")
print(f"  wrong pixels that are isolated specks: data {np.median(sing):.0%} (random scatter {np.median(sing_null):.0%})")
print(f"  wrong pixels in clusters of >= 10: data {np.median(big_cl):.0%} (random scatter {np.median(big_null):.0%})")
# figure: build-time maps of four large domains with their outward-growth correlation
order = big[np.argsort(-sizes[big])][:8]
fig, axes = plt.subplots(2, 4, figsize=(16, 8))
rk = lambda a: np.argsort(np.argsort(a))
for ax, dl in zip(axes.ravel(), order):
    yy, xx = np.nonzero(lab == dl); y0, y1, x0, x1 = yy.min(), yy.max() + 1, xx.min(), xx.max() + 1
    crop = np.where(lab[y0:y1, x0:x1] == dl, TB[y0:y1, x0:x1], np.nan)
    t_ = TB[yy, xx]; ok = ~np.isnan(t_); seed = t_[ok] <= np.quantile(t_[ok], 0.02)
    dist = np.hypot(yy[ok] - yy[ok][seed].mean(), xx[ok] - xx[ok][seed].mean())
    rc = np.corrcoef(rk(dist), rk(t_[ok]))[0, 1]
    im = ax.imshow(crop, cmap="viridis"); ax.set_title(f"{sizes[dl]:,} px, colour {SC[yy[0], xx[0]]}; corr {rc:.2f}", fontsize=9); ax.set_axis_off()
    fig.colorbar(im, ax=ax, fraction=0.046)
plt.tight_layout(); plt.savefig(S + "domains_build.png", dpi=80)
