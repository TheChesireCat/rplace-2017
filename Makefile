# make data      fetch the 2017 CSV (requester-pays: set GCS_BILLING_PROJECT), condense to parquet, check parity, delete CSV
# make video     the activity video in media/ (needs ffmpeg)
# make preview   live preview of the book
# make render    run every chapter and build the site into _site/ (re-runs only chapters whose source changed)
# make publish   push the built site to the gh-pages branch
export QUARTO_PYTHON := $(CURDIR)/.venv/bin/python

data: data/02-parity.json
data/02-parity.json: scripts/02-condense.py
	uv run python -u scripts/01-fetch.py --out data/raw/place_tiles.csv
	uv run python -u scripts/02-condense.py --csv data/raw/place_tiles.csv --out-dir data --delete-original

video: media/heatmap-2017.mp4
media/heatmap-2017.mp4: scripts/03-heatmap-video.py
	uv run python -u scripts/03-heatmap-video.py

preview:
	uv run quarto preview
render:
	uv run quarto render
publish:
	uv run quarto publish gh-pages --no-browser --no-prompt

.PHONY: data video preview render publish
