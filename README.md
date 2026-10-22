# r/place 2017 as a complex system

A book that explores Reddit's r/place 2017 placement log bottom up, from single accounts to the whole canvas, with the
code and figures for every step (in the spirit of [d2l.ai](https://d2l.ai)).

**Read it:** https://thechesirecat.github.io/rplace-2017/

## Get the data

The data are not in this repository. Two scripts rebuild them exactly from Reddit's release:

```bash
uv sync                                    # Python environment (https://docs.astral.sh/uv/)
gcloud auth login                          # Google Cloud SDK, for gsutil
export GCS_BILLING_PROJECT=<your-project>  # the bucket is requester-pays: ~1 GB of egress is billed to you
make data
```

1. `scripts/01-fetch.py` downloads `gs://place_data_share/place_tiles.csv` (993 MiB) and checks its SHA-256.
2. `scripts/02-condense.py` writes three parquet files in `data/` (141 MiB together), rebuilds every CSV line from
   them, checks that the rebuilt lines equal the originals byte for byte, and only then deletes the CSV. The record of
   that check, `data/02-parity.json`, is the one data file kept in git.

## Build the book

```bash
make preview    # live preview
make render     # run the chapters, build the site into _site/
make publish    # push the built site to the gh-pages branch
```

Chapter results are cached in `_freeze/` (committed), so the site rebuilds without the data; a chapter re-runs only
when its source changes. Requires [Quarto](https://quarto.org).

## Layout

```
index.qmd, chapters/   the book (Quarto); one chapter per rung of the ladder
src/rplace17/          small helpers the chapters import (load, palette, canvas_at, cooldown_at)
scripts/               01-fetch.py, 02-condense.py: rebuild data/ from Reddit's release
data/                  gitignored, except 02-parity.json
_freeze/               cached chapter results (committed)
prereg/                pre-registrations, committed before the analysis they describe; amendments are added, never edited in
```

## Branches

| Branch | What it holds |
|---|---|
| `main` | the book as published: chapters, helpers, scripts, frozen results |
| `analysis` | work in progress: new chapters and analyses are developed here, then merged into `main` |
| `gh-pages` | the built website, written by `make publish`; never edited by hand |

## Data

The placement log is Reddit's 2017 r/place data release. Account ids in it are hashes; this book refers to accounts
only by small integer ids and never prints the hashes.

## Licence

The code (`src/`, `scripts/`, and the code in the chapters) is under the MIT licence (`LICENSE`). The book's text and
figures are under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Neither covers Reddit's r/place data,
which this repository does not redistribute: `make data` fetches it from Reddit's release.
