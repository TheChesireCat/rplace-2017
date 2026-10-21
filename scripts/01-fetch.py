#!/usr/bin/env python3
"""
scripts/01-fetch.py
Fetch the r/place 2017 placement log (Reddit data release) from Google Cloud Storage, and check it against the
registered checksum. Never re-pulls: if the file is already on disk with the right checksum, it does nothing.

Input:  gs://place_data_share/place_tiles.csv   (requester-pays bucket: the download is billed to --billing-project,
                                                 ~1 GB of egress per pull)
Output: <out>  (default data/raw/place_tiles.csv; deleted again by 02-condense.py once the parquet matches it)

Needs gsutil (Google Cloud SDK, `gcloud auth login`) and a Google Cloud project you can bill, passed as
--billing-project or the GCS_BILLING_PROJECT environment variable.
"""
import argparse
import hashlib
import os
import subprocess
from pathlib import Path

SOURCE = "gs://place_data_share/place_tiles.csv"
SHA256 = "facbef59866f8cac40b6c495c3e5e74808c5e3872f32f709c7835e8e4271b649"  # pulled 2026-10-21; object dated 2022-03-30
SIZE_BYTES = 1041641746

ap = argparse.ArgumentParser()
ap.add_argument("--billing-project", default=os.environ.get("GCS_BILLING_PROJECT"))
ap.add_argument("--out", default="data/raw/place_tiles.csv")
args = ap.parse_args()
out = Path(args.out)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


if out.exists() and out.stat().st_size == SIZE_BYTES and sha256(out) == SHA256:
    print(f"already on disk with the registered checksum: {out}", flush=True)
else:
    assert args.billing_project, "set GCS_BILLING_PROJECT (or --billing-project) to a Google Cloud project you can bill"
    out.parent.mkdir(parents=True, exist_ok=True)
    print(f"fetching {SOURCE} (billed to {args.billing_project}) -> {out}", flush=True)
    subprocess.run(["gsutil", "-q", "-u", args.billing_project, "cp", SOURCE, str(out)], check=True)
    got = sha256(out)
    assert got == SHA256, f"checksum mismatch: got {got}, registered {SHA256} (source changed? do not use silently)"
    print(f"fetched {out.stat().st_size:,} bytes, checksum matches", flush=True)
