#!/usr/bin/env python3
"""
scripts/03-heatmap-video.py
An activity video of the 2017 canvas: where people placed, where colours changed, and what the canvas looked like,
in a sliding window, side by side. Adapted from the 2023 project's 03-activity-heatmap-video.py (same log1p counts and
fixed colour scale), with a sliding window, a conflict panel, and the cooldown in force shown under the frames.

Input:  data/placements.parquet (via rplace17.load)
Output: media/heatmap-2017.mp4

Choices (all here, so they can be changed in one place):
  WINDOW_MIN  placements counted in the last 15 minutes (1 to 3 cooldown cycles)
  STEP_MIN    one frame every 5 minutes
  BIN         pixels binned 2 x 2 (sums), so single placements do not flicker as isolated dots
  colour      inferno, log1p(count), one fixed scale per panel for the whole video (99.5th percentile of non-zero
              bins), so frames are comparable: a dim frame means less activity, not a rescaled one
  cooldown    the strip under the frames shows the wait in force; in the 10- and 20-minute periods everyone could
              place 2-4 times less, so those frames are dimmer for that reason alone
"""
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np
import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import rplace17 as r  # noqa: E402

WINDOW_MIN, STEP_MIN, BIN, FPS = 15, 5, 2, 24
OUT = Path("media/heatmap-2017.mp4")

d = r.load()
d = d.with_columns(r.pixel_history(d)["wasted"]).filter(pl.col("t_us") >= r.LAUNCH_US)   # same row order as load()
t = d["t_us"].to_numpy()
x, y = d["x"].to_numpy().astype(np.int64), d["y"].to_numpy().astype(np.int64)
changed = ~d["wasted"].to_numpy()
n_bins = (r.SIZE + BIN - 1) // BIN
cell = (y // BIN) * n_bins + (x // BIN)

starts = np.arange(r.LAUNCH_US, t.max() - WINDOW_MIN * 60e6, STEP_MIN * 60e6).astype(np.int64)
lo = np.searchsorted(t, starts)
hi = np.searchsorted(t, starts + WINDOW_MIN * 60_000_000)
print(f"{len(starts)} frames, {len(starts) / FPS:.0f} s at {FPS} fps", flush=True)

def counts(mask_lo_hi):
    a, b, m = mask_lo_hi
    c = cell[a:b] if m is None else cell[a:b][m[a:b]]
    return np.bincount(c, minlength=n_bins * n_bins).reshape(n_bins, n_bins)

# fixed scales from a sample of frames
def nonzero(a):
    return a[a > 0]
sample = np.linspace(0, len(starts) - 1, 60).astype(int)
vmax_all = np.log1p(np.percentile(np.concatenate([nonzero(counts((lo[i], hi[i], None))) for i in sample]), 99.5))
vmax_chg = np.log1p(np.percentile(np.concatenate([nonzero(counts((lo[i], hi[i], changed))) for i in sample]), 99.5))

# canvas frames: incremental, one placement at a time in time order
palette = r.palette_rgb()
canvas_idx = np.zeros((r.SIZE, r.SIZE), dtype=np.int8)
pre = r.load().filter(pl.col("t_us") < r.LAUNCH_US)                # the pre-launch state
canvas_idx[pre["y"].to_numpy(), pre["x"].to_numpy()] = pre["color"].to_numpy()
cols = d["color"].to_numpy()
done = 0

OUT.parent.mkdir(exist_ok=True)
fig = plt.figure(figsize=(15, 5.6), dpi=100, facecolor="black")
axs = [fig.add_axes([0.005 + i * 0.333, 0.12, 0.325, 0.76]) for i in range(3)]
strip = fig.add_axes([0.03, 0.04, 0.94, 0.05], facecolor="black")
for ax, title in zip(axs, ("all placements, last 15 min", "colour changes, last 15 min", "the canvas")):
    ax.set_axis_off(); ax.set_title(title, color="white", fontsize=11)
im_all = axs[0].imshow(np.zeros((n_bins, n_bins)), cmap="inferno", vmin=0, vmax=vmax_all, interpolation="none")
im_chg = axs[1].imshow(np.zeros((n_bins, n_bins)), cmap="inferno", vmin=0, vmax=vmax_chg, interpolation="none")
im_can = axs[2].imshow(palette[canvas_idx], interpolation="none")
grid = np.arange(r.LAUNCH_US, t.max(), 60_000_000)
strip.step((grid - r.LAUNCH_US) / 3.6e9, r.cooldown_at(grid) / 60, where="post", color="white", lw=1)
strip.set_xlim(0, (t.max() - r.LAUNCH_US) / 3.6e9); strip.set_ylim(0, 22)
strip.tick_params(colors="white", labelsize=8); strip.set_yticks([5, 10, 20])
for sp in strip.spines.values():
    sp.set_color("grey")
strip.set_xlabel("hours since launch (line: cooldown in minutes)", color="white", fontsize=8)
marker = strip.axvline(0, color="tab:orange", lw=2)
label = fig.text(0.5, 0.955, "", color="white", ha="center", fontsize=13)

writer = animation.FFMpegWriter(fps=FPS, codec="h264", extra_args=["-crf", "26", "-preset", "slow", "-pix_fmt", "yuv420p"])
with writer.saving(fig, str(OUT), dpi=100):
    for i, s0 in enumerate(starts):
        end = hi[i]
        canvas_idx[y[done:end], x[done:end]] = cols[done:end]       # advance the canvas to the end of the window
        done = end
        im_all.set_data(np.log1p(counts((lo[i], hi[i], None))))
        im_chg.set_data(np.log1p(counts((lo[i], hi[i], changed))))
        im_can.set_data(palette[canvas_idx])
        marker.set_xdata([(s0 + WINDOW_MIN * 60e6 - r.LAUNCH_US) / 3.6e9] * 2)
        label.set_text(np.datetime64(int(s0 + WINDOW_MIN * 60e6), "us").astype("datetime64[m]").astype(str).replace("T", " ")
                       + f" UTC   (cooldown {r.cooldown_at([s0 + WINDOW_MIN * 60_000_000])[0] // 60} min)")
        writer.grab_frame()
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(starts)}", flush=True)
plt.close(fig)
print(f"wrote {OUT} ({OUT.stat().st_size / 2**20:.1f} MiB)")
