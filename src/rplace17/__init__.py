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


# ---------------------------------------------------------------- the cooldown, as it was in force (derived in chapter 2)
# The wait between an account's placements was not fixed: chapter 2 reads it off the log (the 1st percentile of
# gaps ending in each 10-minute window). Boundaries are to the nearest 10 minutes, UTC.
LAUNCH = "2017-03-31 17:00"
COOLDOWN_REGIMES = [  # (start, cooldown in seconds); each lasts until the next start
    ("2017-03-31 17:00", 300),
    ("2017-03-31 21:10", 600),
    ("2017-03-31 22:40", 300),
    ("2017-04-01 00:10", 600),
    ("2017-04-01 03:10", 1200),
    ("2017-04-01 05:30", 600),
    ("2017-04-01 21:30", 300),
]


def _us(s):
    return int(np.datetime64(s.replace(" ", "T"), "us").astype(np.int64))


LAUNCH_US = _us(LAUNCH)


def cooldown_at(t_us):
    """The cooldown (seconds) in force at each time in t_us (array-like of µs)."""
    starts = np.array([_us(s) for s, _ in COOLDOWN_REGIMES])
    secs = np.array([c for _, c in COOLDOWN_REGIMES])
    i = np.searchsorted(starts, np.asarray(t_us), side="right") - 1
    return secs[np.clip(i, 0, len(secs) - 1)]
