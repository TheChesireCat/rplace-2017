import numpy as np, polars as pl, rplace17 as r
h = pl.read_parquet(r.DATA / "pixel_history.parquet"); close = h["t_us"].max()
px = pl.col("x").cast(pl.Int32) * r.SIZE + pl.col("y").cast(pl.Int32)
h = h.with_row_index("i").with_columns(px.alias("pix"))
st = (h.filter(~pl.col("wasted")).sort("pix", "t_us", "i").with_columns(pl.col("t_us").shift(-1).over("pix").fill_null(close).alias("t_end"))
       .with_columns((pl.col("t_end") - pl.col("t_us")).alias("dur")))
sc = st.sort("dur", descending=True).group_by("pix").first().select("pix", pl.col("color").alias("sc"))
first_ok = st.join(sc, on="pix").filter(pl.col("color") == pl.col("sc")).group_by("pix").agg(pl.col("t_us").min().alias("t_build"))
sp = first_ok.filter(pl.col("t_build") >= r.LAUNCH_US).with_columns((pl.col("pix") // r.SIZE).alias("x"), (pl.col("pix") % r.SIZE).alias("y"))
print(f"first-build time (h since launch) quartiles: {np.quantile((sp['t_build'].to_numpy() - r.LAUNCH_US) / 3.6e9, [.25,.5,.75]).round(1)}")
for B in (20, 50):
    sp2 = sp.with_columns(((pl.col("x") // B) * 1000 + pl.col("y") // B).alias("region"))
    T = np.full((r.SIZE, r.SIZE), np.nan); T[sp2["x"].to_numpy(), sp2["y"].to_numpy()] = sp2["t_build"].to_numpy().astype(float)
    Rg = np.full((r.SIZE, r.SIZE), -1); Rg[sp2["x"].to_numpy(), sp2["y"].to_numpy()] = sp2["region"].to_numpy()
    def nb_earlier(T, lag_us=0):
        hit = np.zeros(T.shape, bool)
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            A = np.roll(np.roll(T, dx, 0), dy, 1); RA = np.roll(np.roll(Rg, dx, 0), dy, 1)
            hit |= (RA == Rg) & (A < T) & (A >= T - lag_us) if lag_us else (RA == Rg) & (A < T)
        return hit[~np.isnan(T)].mean()
    # contact growth: a neighbour built within the previous 30 minutes (local, recent growth = a moving front)
    rows = []
    for lag in (0, 30 * 60_000_000):
        real = nb_earlier(T, lag)
        nulls = []
        for s_ in range(3):
            sh = sp2.with_columns(pl.col("t_build").shuffle(seed=s_).over("region").alias("tb"))
            Tn = np.full((r.SIZE, r.SIZE), np.nan); Tn[sh["x"].to_numpy(), sh["y"].to_numpy()] = sh["tb"].to_numpy().astype(float)
            nulls.append(nb_earlier(Tn, lag))
        rows.append((lag, real, np.mean(nulls)))
    print(f"regions {B}x{B}: neighbour built earlier: data {rows[0][1]:.3f} vs shuffle {rows[0][2]:.3f};  neighbour built in the 30 min before: data {rows[1][1]:.3f} vs shuffle {rows[1][2]:.3f}")
    rc = []
    for _, g in sp2.group_by("region"):
        if g.height < 100: continue
        x, y, t = g["x"].to_numpy(), g["y"].to_numpy(), g["t_build"].to_numpy()
        i0 = np.argmin(t); d_ = np.hypot(x - x[i0], y - y[i0])
        rc.append(np.corrcoef(np.argsort(np.argsort(d_)), np.argsort(np.argsort(t)))[0, 1])
    rc = np.array(rc)
    print(f"   rank corr(build time, distance from first-built pixel): median {np.median(rc):.2f}, >0.3 in {np.mean(rc>0.3):.0%}, >0.5 in {np.mean(rc>0.5):.0%} of {len(rc)} regions")
