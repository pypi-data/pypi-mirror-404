"""File hashing utilities for duplicate detection."""

from __future__ import annotations

import hashlib
from pathlib import Path


def file_sha256(path: Path) -> str:
    """Compute SHA256 hash of file contents."""
    # Python 3.11+ streaming helper (zero-copy chunks under the hood)
    with path.open("rb", buffering=0) as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def binary_files_equal(pa: Path, pb: Path, chunk_size: int = 1 << 20) -> bool:
    """Return True iff files `a` and `b` are byte-for-byte identical."""
    sa, sb = pa.stat(), pb.stat()
    if sa.st_size != sb.st_size:
        return False
    with pa.open("rb") as fa, pb.open("rb") as fb:
        while True:
            ca = fa.read(chunk_size)
            cb = fb.read(chunk_size)
            if ca != cb:
                return False
            if not ca:  # reached EOF on both
                return True
