"""Download the tutorial 1 raw data (Siemens .dat files, about 7.9 GB) into this folder.

Python counterpart of upstream demo/data_demo/data_8_tutorial_1/downloadData.m: same files, same
Google Drive location. Standard library only. Interrupted downloads resume where they stopped, and
files already complete are skipped.

Usage::

    python demo/data_demo/data_8_tutorial_1/download_data.py            # into this folder
    python demo/data_demo/data_8_tutorial_1/download_data.py --out DIR  # elsewhere
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.request
from pathlib import Path

# (Google Drive file id, file name, size in bytes)
FILES = [
    ("11p1lUw4pcj_xp1kPuKv3LO_cfcyYlnw_", "bodyCoil.dat", 25_224_192),
    ("1dd8I74Hy4Hb97SF-fHBIkrZP_JzwpMa0", "surfaceCoil.dat", 457_097_216),
    ("12sYtd-KfkZYM8IBzg_DGXsxT3n_uHSLf", "brainScan.dat", 7_407_559_168),
]
URL = "https://drive.usercontent.google.com/download?id={}&export=download&confirm=t"
CHUNK = 1 << 20


def _progress(done: int, total: int, t0: float) -> None:
    rate = done / max(time.time() - t0, 1e-9) / 1e6
    sys.stdout.write(f"\r  {done / 1e6:9.1f} / {total / 1e6:.1f} MB  ({rate:5.1f} MB/s)")
    sys.stdout.flush()


def download(file_id: str, dest: Path, size: int) -> None:
    """Download one file, resuming from ``dest.part`` if it exists."""
    if dest.exists() and dest.stat().st_size == size:
        print(f"{dest.name}: already complete, skipped")
        return
    part = dest.with_name(dest.name + ".part")
    start = part.stat().st_size if part.exists() else 0
    print(f"{dest.name}: downloading" + (f" (resuming at {start / 1e6:.1f} MB)" if start else ""))
    req = urllib.request.Request(URL.format(file_id), headers={"User-Agent": "monalisa-python-downloader"})
    if start:
        req.add_header("Range", f"bytes={start}-")
    with urllib.request.urlopen(req, timeout=120) as r:
        if r.headers.get_content_type() == "text/html":
            raise RuntimeError(f"{dest.name}: Google Drive returned a web page instead of the file "
                               "(quota exceeded or link changed); try again later")
        if start and r.status != 206:  # server ignored the range: start over
            start = 0
        m = re.search(r"/(\d+)$", r.headers.get("Content-Range", ""))
        total = int(m.group(1)) if m else start + int(r.headers.get("Content-Length", size - start))
        if total != size:
            raise RuntimeError(f"{dest.name}: expected {size} bytes, the server announces {total}")
        t0, done = time.time(), start
        with open(part, "ab" if start else "wb") as f:
            while chunk := r.read(CHUNK):
                f.write(chunk)
                done += len(chunk)
                _progress(done, total, t0)
    print()
    if part.stat().st_size != size:
        raise RuntimeError(f"{dest.name}: incomplete ({part.stat().st_size} of {size} bytes); "
                           "run the script again to resume")
    part.replace(dest)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent,
                    help="destination folder (default: this folder)")
    args = ap.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    for file_id, name, size in FILES:
        download(file_id, args.out / name, size)
    print(f"All files are in {args.out}")


if __name__ == "__main__":
    main()
