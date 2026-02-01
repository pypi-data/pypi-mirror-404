"""Utilities for building review data structures from pipeline outputs.

This module contains functions to transform pipeline stage outputs into
the format expected by the review interface.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .models import (
    IdenticalGroup,
    IdenticalPhoto,
    SequenceGroup,
    SequenceInfo,
    SequencePhoto,
    SequenceRow,
)
from .photo_file import (
    PhotoFile,
)
from .sequence import (
    INDEX_T,
    PhotoFileSeries,
    PhotoSequence,
)


def build_identical_group(eq_class: list[PhotoFile], exemplar_id: int) -> IdenticalGroup:
    """Create review data structure from a list of identical photos."""
    # Create stable group_id from sorted photo IDs
    photo_ids: list[int] = sorted([pf.id for pf in eq_class])
    group_id: str = hashlib.sha256("".join(str(id) for id in photo_ids).encode()).hexdigest()

    photos: list[IdenticalPhoto] = []
    for pf in eq_class:
        # Get canonical dimensions (may trigger rotation detection if not cached)
        with pf.image_data() as img:
            width = img.get_width()
            height = img.get_height()

        # Production code: path should never be None
        assert pf.path is not None, f"Photo {pf.id} has None path in production code"

        photos.append(
            IdenticalPhoto(
                id=pf.id,
                path=str(pf.path),
                filename=pf.path.name,
                is_exemplar="IDENTICAL" in pf.cache,
                file_size=pf.size_bytes,
                width=width,
                height=height,
            )
        )

    return IdenticalGroup(
        group_id=group_id,
        exemplar_id=exemplar_id,
        photos=photos,
        is_identical=True,
        confidence="high",
    )


def build_sequence_group(obj: PhotoSequence) -> SequenceGroup:
    # Convert to DataFrame
    df = obj.to_dataframe()

    # Filter rows with only 0-1 photos (no conflicts to review)
    photo_counts = df.notna().sum(axis=1)
    filtered = df[photo_counts >= 2].copy()
    filtered.attrs = df.attrs.copy()
    df = filtered

    # Verify we have rows to review (if not, matching/alignment failed)
    assert len(df) != 0, (
        f"SequenceGroup has no reviewable rows after filtering. "
        f"This indicates sequences were matched but index alignment failed to produce overlapping positions. "
        f"Reference: {df.attrs.get('reference_name', 'unknown')}, "
        f"Created by: {df.attrs.get('created_by', 'unknown')}, "
        f"Sequences: {len(df.columns)}, "
        f"Columns: {list(df.columns)}"
    )

    # Sort by min similarity (least reliable first)
    min_sims = df.apply(row_min_similarity, axis=1)
    sorted_df = df.iloc[min_sims.argsort()].copy()
    sorted_df.attrs = df.attrs.copy()

    # Get min similarity, defaulting to 1.0 if series is empty or contains NaN
    # (prevents NaN from breaking JSON serialization in UI)
    min_val = min_sims.min()
    sorted_df.attrs["min_similarity"] = 1.0 if (min_sims.empty or pd.isna(min_val)) else float(min_val)
    df = sorted_df

    # Get reference for exemplar detection
    reference, _version_seqs = obj.flatten()

    # Convert to SequenceGroup model
    return _dataframe_to_group_dict(df, reference)


def row_min_similarity(row: pd.Series[Any]) -> float:
    """Get min similarity across non-exemplar photos in row."""
    similarities: list[float] = []
    for photo in row.dropna():
        score = photo.cache.get("SEQUENCE_SIMILARITY")
        # Skip exemplars (have None) and validate score is not NaN (prevents JSON serialization errors in UI)
        if score is not None and not math.isnan(score):
            similarities.append(score)
    return min(similarities) if similarities else 1.0


def _dataframe_to_group_dict(df: pd.DataFrame, reference: PhotoFileSeries) -> SequenceGroup:
    """Convert DataFrame to SequenceGroup model.

    Args:
        df: Sorted DataFrame with PhotoFile|None values
        reference: Reference sequence for exemplar detection

    Returns:
        SequenceGroup model for review interface

    Raises:
        KeyError: If a non-exemplar photo is missing SEQUENCE_SIMILARITY cache value

    Note:
        All stages providing sequence review data MUST compute similarity scores.
        Non-exemplar photos must have SEQUENCE_SIMILARITY set by the stage's comparison logic.
    """
    # Generate stable group_id from photo IDs (SHA256 no longer stored in PhotoFile)
    reference_name = str(reference.name)
    photo_ids = sorted([photo.id for col in df.columns for photo in df[col].dropna()])
    group_content = reference_name + "".join(str(id) for id in photo_ids)
    group_id = hashlib.sha256(group_content.encode()).hexdigest()

    # Build sequences list
    sequences: list[SequenceInfo] = []
    for seq_name in df.columns:
        seq_path = Path(str(seq_name))
        sequences.append(
            SequenceInfo(
                name=str(seq_name),
                parent_dir=(str(seq_path.parent) if str(seq_path.parent) != "." else df.attrs.get("parent_dir", "")),
                template_name=seq_path.name,
            )
        )

    # Build rows list using iterrows() to avoid index access issues
    rows: list[SequenceRow] = []
    for row_idx, (position_key, row_data) in enumerate(df.iterrows()):
        # position_key from pandas is Hashable, but we know it's INDEX_T for PhotoSequence DataFrames
        # Assert type for mypy - PhotoSequence DataFrames always have tuple indices
        assert isinstance(position_key, tuple), f"Expected tuple index, got {type(position_key)}"
        index_key: INDEX_T = position_key
        photos: list[SequencePhoto | None] = []

        for seq_idx, seq_name in enumerate(df.columns):
            photo_or_none = row_data[seq_name]

            # Handle potential Series by extracting scalar value
            value = photo_or_none.iloc[0] if isinstance(photo_or_none, pd.Series) else photo_or_none

            # Check if we have a valid PhotoFile (check PhotoFile first for type narrowing)
            if isinstance(value, PhotoFile):
                photo = value
                ref_photo: PhotoFile | None = reference.get(index_key)
                is_exemplar = ref_photo is not None and photo.id == ref_photo.id

                # Exemplar photos: None (no self-comparison needed)
                # Non-exemplar photos: MUST have similarity score - raises KeyError if missing
                # This catches pipeline bugs where stages provide review data without computing similarity
                similarity_score = None if is_exemplar else photo.cache["SEQUENCE_SIMILARITY"]

                # Extract all metadata from PhotoFile (no lazy loading needed)
                # WORKAROUND: Handle test fixtures where path=None for anonymization
                # In production, path is never None, but test fixtures need this
                filename = photo.path.name if photo.path is not None else f"test_photo_{photo.id}.jpg"

                # Get canonical dimensions (may trigger rotation detection if not cached)
                # For test fixtures with path=None, use placeholder values
                if photo.path is not None:
                    with photo.image_data() as img:
                        width = img.get_width()
                        height = img.get_height()
                else:
                    # Test fixture: estimate dimensions from pixels assuming square
                    width = int(math.sqrt(photo.pixels))
                    height = int(math.sqrt(photo.pixels))

                photos.append(
                    SequencePhoto(
                        id=photo.id,
                        filename=filename,
                        sequence_index=seq_idx,
                        is_exemplar=is_exemplar,
                        similarity_score=similarity_score,
                        attention_test=False,
                        file_size=photo.size_bytes,
                        width=width,
                        height=height,
                    )
                )
            else:
                # Value is None or NaN - represent as missing
                photos.append(None)

        rows.append(SequenceRow(position_key=index_key, row_index=row_idx, photos=photos))

    return SequenceGroup(
        group_id=group_id,
        template_name=df.attrs.get("template_name", Path(reference_name).name),
        parent_dir=df.attrs.get("parent_dir", str(Path(reference_name).parent)),
        created_by=df.attrs.get("created_by", ""),
        min_similarity=df.attrs.get("min_similarity", 1.0),
        sequences=sequences,
        rows=rows,
    )
