#!/usr/bin/env python3
"""
scripts/02-condense.py
Condense the r/place 2017 CSV into typed parquet files, prove the parquet holds exactly the CSV's content, and (with
--delete-original) delete the CSV once it does.

Input:  data/raw/place_tiles.csv   columns ts,user_hash,x_coordinate,y_coordinate,color (16,567,567 rows)
Output: data/placements.parquet    t_us (Int64, µs since epoch, UTC), user_id (Int32), x, y (Int16), color (Int8)
                                   sorted by (t_us, user_id, x, y, color); the CSV is not in time order, and its
                                   row order is not kept
        data/users.parquet         user_id -> user_hash (user_id = row of the sorted unique hashes)
        data/palette.parquet       color -> hex, name (the 2017 16-colour palette)
        data/02-parity.json        counts, sizes, and the parity check

Parity: every placement row is turned back into the CSV text (timestamp re-formatted the way the release writes it:
milliseconds with trailing zeros dropped, and no fraction when the milliseconds are 0). The sorted list of these lines
must equal the sorted list of the original data lines, byte for byte. Sorting is needed because the parquet is
re-ordered by time; duplicates are kept on both sides (the CSV has 304 exact duplicate rows).

Known quirks, kept as they are: 3 rows have no coordinates and no colour; coordinates run 0..1000 on a 1000 x 1000
canvas (value 1000 occurs).
"""
import argparse
import hashlib
import json
from pathlib import Path

import polars as pl

# The 2017 palette, in index order, from Reddit's released Place client:
# github.com/reddit-archive/reddit-plugin-place-opensource @ 453892c, reddit_place/public/static/js/place/client.js
# lines 103-119 (DEFAULT_COLOR_PALETTE).
PALETTE = [("#FFFFFF", "white"), ("#E4E4E4", "light grey"), ("#888888", "grey"), ("#222222", "black"),
           ("#FFA7D1", "pink"), ("#E50000", "red"), ("#E59500", "orange"), ("#A06A42", "brown"),
           ("#E5D900", "yellow"), ("#94E044", "lime"), ("#02BE01", "green"), ("#00D3DD", "cyan"),
           ("#0083C7", "blue"), ("#0000EA", "dark blue"), ("#CF6EE4", "magenta"), ("#820080", "purple")]
TS_FORMAT = "%Y-%m-%d %H:%M:%S%.f UTC"
HEADER = "ts,user_hash,x_coordinate,y_coordinate,color"

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="data/raw/place_tiles.csv")
ap.add_argument("--out-dir", default="data")
ap.add_argument("--delete-original", action="store_true", help="delete the CSV if (and only if) parity holds")
args = ap.parse_args()
out = Path(args.out_dir)
out.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- read, as text first (nothing is coerced silently)
raw = pl.read_csv(args.csv, infer_schema=False)
assert raw.columns == HEADER.split(","), raw.columns
print(f"csv rows {raw.height:,}", flush=True)

t_us = raw["ts"].str.to_datetime(TS_FORMAT, time_unit="us", strict=True).dt.timestamp("us")
assert t_us.null_count() == 0
assert (t_us % 1000 == 0).all(), "sub-millisecond timestamps: the re-formatting below would lose them"

hashes = raw["user_hash"].unique().sort()
users = pl.DataFrame({"user_id": pl.Series(range(len(hashes)), dtype=pl.Int32), "user_hash": hashes})
print(f"users {users.height:,}", flush=True)

df = pl.DataFrame({
    "t_us": t_us,
    "user_hash": raw["user_hash"],
    "x": raw["x_coordinate"].cast(pl.Int16, strict=True),
    "y": raw["y_coordinate"].cast(pl.Int16, strict=True),
    "color": raw["color"].cast(pl.Int8, strict=True),
})
# casts are strict, but "007" -> 7 would still pass and break parity; the parity check below catches any such case
df = (df.join(users, on="user_hash", how="left").drop("user_hash")
      .select("t_us", "user_id", "x", "y", "color")
      .sort("t_us", "user_id", "x", "y", "color", nulls_last=True, maintain_order=True))
assert df["user_id"].null_count() == 0
assert df.filter(pl.col("color").is_not_null())["color"].is_between(0, len(PALETTE) - 1).all()

palette = pl.DataFrame({"color": pl.Series(range(len(PALETTE)), dtype=pl.Int8),
                        "hex": [h for h, _ in PALETTE], "name": [n for _, n in PALETTE]})

files = {"placements": out / "placements.parquet", "users": out / "users.parquet", "palette": out / "palette.parquet"}
df.write_parquet(files["placements"], compression="zstd", compression_level=19, statistics=True)
users.write_parquet(files["users"], compression="zstd", compression_level=19)
palette.write_parquet(files["palette"], compression="zstd")
for k, p in files.items():
    print(f"wrote {p} ({p.stat().st_size / 2**20:,.1f} MiB)", flush=True)

# ---------------------------------------------------------------- parity: rebuild the CSV text from the files on disk
back = pl.read_parquet(files["placements"]).join(pl.read_parquet(files["users"]), on="user_id", how="left")
ms = ((pl.col("t_us") // 1000) % 1000).cast(pl.Utf8).str.zfill(3).str.strip_chars_end("0")
ts_text = (pl.from_epoch(pl.col("t_us"), time_unit="us").dt.strftime("%Y-%m-%d %H:%M:%S")
           + pl.when(ms == "").then(pl.lit("")).otherwise("." + ms) + pl.lit(" UTC"))
txt = lambda c: pl.col(c).cast(pl.Utf8).fill_null("")  # noqa: E731
rebuilt = back.select(pl.concat_str([ts_text, pl.col("user_hash"), txt("x"), txt("y"), txt("color")], separator=",")
                      .alias("line"))["line"].sort()

# the original lines, read as raw text (no CSV parsing), minus the header
lines = pl.read_csv(args.csv, has_header=False, separator="\x1f", quote_char=None, infer_schema=False,
                    new_columns=["line"])["line"]
assert lines[0] == HEADER, lines[0]
lines = lines.slice(1).str.strip_chars_end("\r").sort()


def digest(s):
    h = hashlib.sha256()
    for chunk in s.to_frame().iter_slices(1_000_000):
        h.update(("\n".join(chunk["line"].to_list()) + "\n").encode())
    return h.hexdigest()


same_len = rebuilt.len() == lines.len()
mismatch = int((rebuilt != lines).sum()) if same_len else None
parity = same_len and mismatch == 0
sha_csv, sha_parquet = digest(lines), digest(rebuilt)
parity = parity and sha_csv == sha_parquet
print(f"parity: {parity} (rows {lines.len():,} vs {rebuilt.len():,}; mismatched sorted lines {mismatch})", flush=True)

csv_bytes = Path(args.csv).stat().st_size
parquet_bytes = sum(p.stat().st_size for p in files.values())
summary = {
    "rows": df.height, "users": users.height,
    "rows_without_coordinates": int(df["x"].null_count()), "exact_duplicate_rows": int(raw.height - raw.unique().height),
    "t_first_us": int(df["t_us"].min()), "t_last_us": int(df["t_us"].max()),
    "x_range": [int(df["x"].min()), int(df["x"].max())], "y_range": [int(df["y"].min()), int(df["y"].max())],
    "csv_bytes": csv_bytes, "parquet_bytes": {k: p.stat().st_size for k, p in files.items()},
    "compression_ratio": round(csv_bytes / parquet_bytes, 2),
    "parity": {"holds": parity, "rows_csv": lines.len(), "rows_parquet": rebuilt.len(), "mismatched_sorted_lines": mismatch,
               "sha256_sorted_lines_csv": sha_csv, "sha256_sorted_lines_parquet": sha_parquet},
    "original_deleted": False,
}
write = lambda: (out / "02-parity.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")  # noqa: E731
write()  # the record exists before anything is deleted
assert parity, "parquet does not reproduce the CSV; keeping the CSV"
if args.delete_original:
    Path(args.csv).unlink()
    summary["original_deleted"] = True
    write()
    print(f"deleted {args.csv} (re-fetch with scripts/01-fetch.py)", flush=True)
print(json.dumps(summary, indent=1), flush=True)
