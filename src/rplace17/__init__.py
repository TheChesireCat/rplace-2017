"""
rplace17: small helpers shared by the book's chapters. Everything here is plain polars / numpy, kept short on
purpose so a chapter can show what it does.

    from rplace17 import load, palette, canvas_at
    pl_df = load()                       # all 16,567,567 placements (t_us, user_id, x, y, color)
    rgb   = canvas_at(pl_df, t_us=None)  # the canvas as an H x W x 3 uint8 image (None = after the last placement)
"""
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
SIZE = 1001  # coordinates run 0..1000 inclusive in the release (see chapter 1)


def load(columns=None, lazy=False, drop_missing=True):
    """The placements, sorted by time. drop_missing removes the 3 rows without coordinates."""
    path = DATA / "placements.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} is missing: run `make data` (see the README)")
    q = pl.scan_parquet(path)
    if drop_missing:
        q = q.filter(pl.col("x").is_not_null())
    if columns:
        q = q.select(columns)
    return q if lazy else q.collect()


def palette():
    """The 16 colours as a list of hex strings, in index order."""
    return pl.read_parquet(DATA / "palette.parquet").sort("color")["hex"].to_list()


def palette_rgb():
    return np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in palette()], dtype=np.uint8)


def canvas_at(df, t_us=None):
    """The canvas as an image: the colour of each pixel's last placement at or before t_us. Unplaced pixels are white."""
    if t_us is not None:
        df = df.filter(pl.col("t_us") <= t_us)
    last = df.group_by("x", "y").agg(pl.col("color").last())  # df is time-sorted, so last() is the latest
    idx = np.zeros((SIZE, SIZE), dtype=np.int8)  # colour 0 is white
    idx[last["y"].to_numpy(), last["x"].to_numpy()] = last["color"].to_numpy()
    return palette_rgb()[idx]


def utc(t_us):
    """µs since epoch -> numpy datetime64 (for axis labels)."""
    return np.asarray(t_us, dtype="datetime64[us]")


# ---------------------------------------------------------------- the cooldown, as it was in force (chapter 2)
# The wait between an account's placements was not fixed. Chapter 2 reads it off the log: the 1st percentile of the
# gaps ending in each minute. Each switch matches a commit to Reddit's released Place code
# (github.com/reddit-archive/reddit-plugin-place-opensource, PIXEL_COOLDOWN_SECONDS in reddit_place/controllers.py),
# 2-6 minutes after the commit time. The start times below are when the log shows the new wait in force (UTC, to the
# minute); the values are the committed constants.
LAUNCH = "2017-03-31 17:00"
COOLDOWN_REGIMES = [  # (start, cooldown in seconds, commit); each lasts until the next start
    ("2017-03-31 17:00", 300, "4680dac"),
    ("2017-03-31 21:10", 600, "f9c6728 Increase cooldown to 10 minutes (21:03:58)"),
    ("2017-03-31 22:41", 300, "1b78788 Revert 'Increase cooldown to 10 minutes' (22:38:01)"),
    ("2017-04-01 00:10", 600, "75e3a92 Revert 'Revert ...' (00:05:43)"),
    ("2017-04-01 03:03", 1200, "e8c0e74 Increase cooldown to 20 minutes (02:59:57)"),
    ("2017-04-01 05:00", 900, "ba74693 Decrease cooldown to 15 minutes (04:58:08)"),
    ("2017-04-01 05:27", 603, "5a85e76 Lower to 10 minutes (05:24:39); c50bb72 Up to 10 minutes 3 seconds (05:25:25)"),
    ("2017-04-01 21:30", 300, "0d500f3 Lower cooldown to 5 minutes (21:27:47)"),
]


def _us(s):
    return int(np.datetime64(s.replace(" ", "T"), "us").astype(np.int64))


LAUNCH_US = _us(LAUNCH)


def cooldown_at(t_us):
    """The cooldown (seconds) in force at each time in t_us (array-like of µs)."""
    starts = np.array([_us(s) for s, _, _ in COOLDOWN_REGIMES])
    secs = np.array([c for _, c, _ in COOLDOWN_REGIMES])
    i = np.searchsorted(starts, np.asarray(t_us), side="right") - 1
    return secs[np.clip(i, 0, len(secs) - 1)]


def table(df):
    """Show a small polars DataFrame as a Markdown table (no truncation), for the book."""
    from IPython.display import Markdown
    cols = df.columns
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    lines += ["| " + " | ".join(str(v) for v in row) + " |" for row in df.iter_rows()]
    return Markdown("\n".join(lines))


# ---------------------------------------------------------------- the cooldown switches (chapter 3; prereg/03-*)
# Six independent switches after amendment 1: 05:00 (20 -> 15 min) and 05:27 (15 -> 10 min) are merged into one, and
# the 15-minute stretch between them is not used. Each: (before-window end s_before, after-window start reference
# s_after, new cooldown in s, direction: +1 tighten / -1 loosen).
SWITCHES = [
    ("2017-03-31 21:10", "2017-03-31 21:10", 600, +1),
    ("2017-03-31 22:41", "2017-03-31 22:41", 300, -1),
    ("2017-04-01 00:10", "2017-04-01 00:10", 600, +1),
    ("2017-04-01 03:03", "2017-04-01 03:03", 1200, +1),
    ("2017-04-01 05:00", "2017-04-01 05:27", 603, -1),
    ("2017-04-01 21:30", "2017-04-01 21:30", 300, -1),
]
# Placebo: the same clock times inside the stable five-minute period (prereg: 48 h later; the last one 24 h later,
# since 48 h would fall after the close), same windows and directions.
PLACEBO = [
    ("2017-04-02 21:10", "2017-04-02 21:10", 600, +1),
    ("2017-04-02 22:41", "2017-04-02 22:41", 300, -1),
    ("2017-04-03 00:10", "2017-04-03 00:10", 600, +1),
    ("2017-04-03 03:03", "2017-04-03 03:03", 1200, +1),
    ("2017-04-03 05:00", "2017-04-03 05:27", 603, -1),
    ("2017-04-02 21:30", "2017-04-02 21:30", 300, -1),
]


def switch_windows(switches=None, W_min=20):
    """One row per (switch, side): window start and end in µs. side is 'pre2' [s-2W, s-W), 'before' [s-W, s) or
    'after' [s+delta, s+delta+W), with delta = the new cooldown."""
    W = W_min * 60_000_000
    rows = []
    for k, (sb, sa, new_c, direction) in enumerate(switches or SWITCHES, start=1):
        b, a = _us(sb), _us(sa) + new_c * 1_000_000
        for side, lo, hi in (("pre2", b - 2 * W, b - W), ("before", b - W, b), ("after", a, a + W)):
            rows.append({"k": k, "side": side, "lo": lo, "hi": hi, "direction": direction, "new_cooldown": new_c})
    return pl.DataFrame(rows)


def sign_flip_p(delta, direction):
    """Exact two-sided sign-flip p for T = sum(direction * delta) (prereg/03-*): under H0 each delta is symmetric
    about 0, so all 2^n sign assignments are equally likely."""
    import itertools
    x = np.asarray(direction, float) * np.asarray(delta, float)
    T = x.sum()
    Ts = np.array([np.dot(s, np.abs(x)) for s in itertools.product((-1, 1), repeat=len(x))])
    return T, float(np.mean(np.abs(Ts) >= abs(T) - 1e-12))


def pixel_history(df):
    """Per placement, what it did to its pixel (chapter 3; definitions in prereg/03-*). The canvas starts white, and
    that initial white counts as the pixel's first colour state.
      wasted       repaints the pixel's current colour
      first        the first placement ever on the pixel
      overwrite    not wasted, not first, and the pixel's last placement was by a different account
      undo         not wasted, and restores the colour the pixel had before its current colour (A-B-A);
                   null when the pixel has had fewer than two colour states
    Uses the whole log, including the pre-launch placements, so a pixel's state is right at every time."""
    px = pl.col("x").cast(pl.Int32) * SIZE + pl.col("y").cast(pl.Int32)
    h = (df.with_row_index("i").with_columns(px.alias("pix"))
           .sort("pix", "t_us", "i")
           .with_columns(pl.col("color").shift(1).over("pix").fill_null(0).alias("prev_color"),
                         pl.col("user_id").shift(1).over("pix").alias("prev_user")))
    h = h.with_columns((pl.col("color") == pl.col("prev_color")).alias("wasted"),
                       pl.col("prev_user").is_null().alias("first"))
    h = h.with_columns((~pl.col("wasted") & ~pl.col("first") & (pl.col("prev_user") != pl.col("user_id"))).alias("overwrite"))
    # colour before the current one: the prev_color of the placement that created the current state
    changes = (h.filter(~pl.col("wasted"))
                .with_columns(pl.col("prev_color").shift(1).over("pix").alias("before_current"))
                .select("i", (pl.col("color") == pl.col("before_current")).alias("undo")))
    return h.join(changes, on="i", how="left").sort("i").drop("i", "pix")


OUTCOMES = {  # name -> (numerator flag, denominator mask), per prereg/03-* and amendment 1
    "overwrite": ("overwrite", ~pl.col("wasted") & ~pl.col("first")),       # primary
    "wasted": ("wasted", pl.lit(True)),
    "undo": ("undo", ~pl.col("wasted") & pl.col("undo").is_not_null()),
}


def window_outcomes(h, windows, accounts=None):
    """Per (switch k, side) window: placements, accounts, and per-account numerators/denominators for each outcome.
    accounts: optional {k: set of user_ids} to restrict each switch to the same people."""
    out = []
    for row in windows.iter_rows(named=True):
        w = h.filter(pl.col("t_us").is_between(row["lo"], row["hi"], closed="left"))
        if accounts is not None:
            w = w.filter(pl.col("user_id").is_in(list(accounts[row["k"]])))
        per = w.group_by("user_id").agg(
            [pl.len().alias("n")] +
            [x for name, (num, den) in OUTCOMES.items()
             for x in ((pl.col(num) & den).sum().alias(f"{name}_num"), den.sum().alias(f"{name}_den"))])
        out.append({**row, "per_account": per, "placements": w.height, "accounts": per.height})
    return out


def share(per, name):
    return per[f"{name}_num"].sum() / max(per[f"{name}_den"].sum(), 1)


def boot_delta(before, after, name, B=1000, seed=0):
    """95% interval for share(after) - share(before), resampling accounts within each window."""
    rng = np.random.default_rng(seed)
    nb, db = before[f"{name}_num"].to_numpy(), before[f"{name}_den"].to_numpy()
    na, da = after[f"{name}_num"].to_numpy(), after[f"{name}_den"].to_numpy()
    ds = []
    for _ in range(B):
        i, j = rng.integers(len(nb), size=len(nb)), rng.integers(len(na), size=len(na))
        ds.append(na[j].sum() / da[j].sum() - nb[i].sum() / db[i].sum())
    return np.quantile(ds, [0.025, 0.975])


def kaplan_meier(duration, event):
    """Kaplan-Meier survival: returns (times, S(t)) at each distinct event time. event = False means censored."""
    duration, event = np.asarray(duration, float), np.asarray(event, bool)
    order = np.argsort(duration, kind="stable")
    duration, event = duration[order], event[order]
    times, first_idx, counts = np.unique(duration, return_index=True, return_counts=True)
    at_risk = len(duration) - first_idx
    deaths = np.add.reduceat(event.astype(np.int64), first_idx)
    keep = deaths > 0
    return times[keep], np.cumprod(1 - deaths[keep] / at_risk[keep])


def with_timing(h):
    """Add to a pixel_history() frame: t_end, when the colour state a non-wasted placement set was next changed (null if
    never), and t_next_own, the placing account's next placement anywhere (null if none). Used for the mechanical
    prediction in chapter 3."""
    px = pl.col("x").cast(pl.Int32) * SIZE + pl.col("y").cast(pl.Int32)
    h = h.with_row_index("_i").with_columns(px.alias("_pix"))
    ends = (h.filter(~pl.col("wasted")).sort("_pix", "t_us", "_i")
              .with_columns(pl.col("t_us").shift(-1).over("_pix").alias("t_end")).select("_i", "t_end"))
    h = h.join(ends, on="_i", how="left")
    h = (h.sort("user_id", "t_us", "_i").with_columns(pl.col("t_us").shift(-1).over("user_id").alias("t_next_own"))
          .sort("_i"))
    return h.drop("_i", "_pix")


def own_and_intact(w):
    """For one window of with_timing() rows: own-pixel colour changes (count, of colour changes after the first), and
    the share of colour states set in the window that were still intact at the placer's next placement."""
    cc = w.filter(~pl.col("wasted") & ~pl.col("first"))
    s = w.filter(~pl.col("wasted") & pl.col("t_next_own").is_not_null())
    intact = (s["t_end"].is_null() | (s["t_end"] > s["t_next_own"])).mean()
    return int((~cc["overwrite"]).sum()), cc.height, float(intact)
