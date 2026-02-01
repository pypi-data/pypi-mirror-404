"""Sequence clustering algorithm for photo deduplication pipeline.

This module provides the core clustering algorithm used by multiple pipeline stages
(ComputeIndices, ComputeTemplateSimilarity, ComputePerceptualMatch) to group similar
photo sequences.

The algorithm:
1. Picks best exemplar from remaining sequences
2. Compares candidates against exemplar reference (with optional precheck)
3. Merges similar sequences, updating reference
4. Backfills similarity scores with ImageData reuse optimization

This module can import from both sequence.py (data structures) and review_utils.py
(review data builders) without creating circular dependencies.
"""

from __future__ import annotations

from collections import defaultdict

from .comparison_gates import GateSequence
from .models import SequenceGroup
from .photo_file import PhotoFile
from .review_utils import build_sequence_group
from .sequence import (
    INDEX_T,
    PhotoFileSeries,
    PhotoSequence,
    extend_reference_sequence,
    predict_exemplar_sequence,
)


def cluster_similar_sequences(
    sequences: list[PhotoSequence],
    gates: GateSequence,
    created_by: str,
) -> tuple[list[PhotoSequence], list[SequenceGroup]]:
    """Core sequence clustering algorithm used by multiple pipeline stages.

    Iteratively clusters sequences by:
    1. Picking best exemplar from remaining sequences
    2. Comparing candidates against exemplar reference
    3. Merging similar sequences, updating reference
    4. Backfilling similarity scores with ImageData reuse optimization

    This function extracts the common clustering pattern used by ComputeIndices,
    ComputeTemplateSimilarity, and ComputePerceptualMatch stages.

    When clustering PhotoSequences that are already classes (from previous stages),
    comparison uses each sequence's reference (via get_reference()), not flattened
    leaf photos. This respects the hierarchical abstraction.

    Args:
        sequences: Sequences to cluster (may be singletons or classes)
        gates: Comparison gates for similarity checking
        created_by: Label for merged sequences

    Returns:
        Tuple of (clustered_sequences, review_groups)

    Example:
        >>> # ComputeIndices usage
        >>> results, reviews = cluster_similar_sequences(
        ...     list(component), gates, "ComputeIndices"
        ... )
    """
    result_sequences: list[PhotoSequence] = []
    review_groups: list[SequenceGroup] = []
    remaining: list[PhotoSequence] = list(sequences)

    while remaining:
        # Pick best exemplar from remaining sequences
        exemplar_seq_obj: PhotoSequence = predict_exemplar_sequence(remaining)
        remaining.remove(exemplar_seq_obj)

        # Use predicted exemplar's reference
        reference: PhotoFileSeries = exemplar_seq_obj.get_reference().copy()

        # Start similar_sequences list
        similar_sequences: list[PhotoSequence] = []

        # Compare remaining sequences against reference
        for candidate_seq_obj in remaining:
            candidate_ref: PhotoFileSeries = candidate_seq_obj.get_reference()

            # Attempt merge
            new_ref: PhotoFileSeries | None = extend_reference_sequence(gates, reference, candidate_ref)

            if new_ref is None:
                continue  # Doesn't match - skip

            reference = new_ref

            # Accept sequence
            similar_sequences.append(candidate_seq_obj)

        # Remove accepted sequences from remaining
        for seq_obj in similar_sequences:
            remaining.remove(seq_obj)
        similar_sequences.append(exemplar_seq_obj)

        # Create PhotoSequence if we have multiple sequences
        if len(similar_sequences) > 1:
            # Backfill missing similarities (for indices not in original reference)
            # OPTIMIZATION: Transpose loops to reuse exemplar ImageData across sequences
            photos_by_idx: dict[INDEX_T, list[PhotoFile]] = defaultdict(list)
            for seq in similar_sequences:
                for seq_idx, photo in seq.get_reference().items():
                    photos_by_idx[seq_idx].append(photo)

            # Process by seq_idx (allows exemplar ImageData reuse)
            for seq_idx, photos in photos_by_idx.items():
                exemplar: PhotoFile = reference[seq_idx]

                # Create ImageData once for exemplar, reuse across all sequence photos at this index
                with exemplar.image_data() as ex_img:
                    for photo in photos:
                        if photo.id == exemplar.id:
                            continue

                        similarity: float
                        _passes, _scores, similarity = gates.compare_with_rotation(
                            exemplar, photo, short_circuit=True, ref_img=ex_img, cand_img=None
                        )
                        photo.cache["SEQUENCE_SIMILARITY"] = similarity
                        photo.cache["SEQUENCE_EXEMPLAR"] = exemplar

            result_seq = PhotoSequence(reference, similar_sequences, created_by=created_by)
            result_sequences.append(result_seq)

            # Build review group if we merged multiple sequences
            # Uses direct sub-sequence count (not flattened) to respect hierarchy
            if len(result_seq.sequences) > 1:
                review_groups.append(build_sequence_group(result_seq))
        elif len(similar_sequences) == 1:
            # Only exemplar - keep as-is (no review group for singleton)
            result_sequences.append(exemplar_seq_obj)

    return result_sequences, review_groups
