"""Distance and similarity utility functions."""

from __future__ import annotations


def hamming_distance(hash1: bytes, hash2: bytes) -> int:
    """Compare any hash-based method using Hamming distance."""
    return sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(hash1, hash2, strict=False))


def hamming_similarity(hash1: bytes, hash2: bytes) -> float:
    """Convert Hamming distance to similarity score (0-1, higher is more similar)."""
    max_distance = len(hash1) * 8
    distance = hamming_distance(hash1, hash2)
    return 1.0 - (distance / max_distance)
