"""Implementation of perceptual hashing pipeline stage."""

from __future__ import annotations

from collections import defaultdict

import numpy as np

from photo_compare import create_comparison_method

from .config import CONFIG
from .photo_file import load_normalized_pixels
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .sequence import (
    INDEX_T,
    PhotoSequence,
)


def make_defaultdict() -> dict[int, list[INDEX_T]]:
    """Inner helper function needs to be named as lambda : defaultdict(list) does not pickle."""
    return defaultdict(list)


class ComputePerceptualHash(
    PipelineStage[
        tuple[int, INDEX_T, str],  # S: work item
        tuple[int, INDEX_T, bytes],  # T: work data
        dict[bytes, dict[int, list[INDEX_T]]],  # R: accumulator
    ]
):
    def __init__(self) -> None:
        """Initialize the perceptual matching stage."""
        super().__init__(
            path=CONFIG.paths.perceptual_hash_bins_pkl,
            stage_name="Perceptual Hash Calculation",
        )

        # Store worker argument
        self.args = self.stage_name

        # Create input port for forest (from ComputeIndices)
        self.forest_i: InputPort[list[PhotoSequence]] = InputPort("forest")

        # Create output port for perceptual hash bins
        self.perceptual_bins_o: OutputPort[dict[bytes, dict[int, list[INDEX_T]]]] = OutputPort(
            self, getter=lambda: self.result
        )

    def prepare(
        self,
    ) -> PrepareResult[tuple[int, INDEX_T, str], dict[bytes, dict[int, list[INDEX_T]]]]:
        """Prepare perceptual hash work items by reading forest from input port.

        Returns:
            Tuple of (work_items, result_accumulator)
        """
        # Read forest from input port
        forest = self.forest_i.read()
        # Get reference counts from upstream for UI statistics tracking
        self.ref_photos_init = self.forest_i.get_ref_photo_count()
        self.ref_seqs_init = self.forest_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (should never change)
        self.total_photos = sum(seq.n_photos for seq in forest)

        # Create work items from all photos in all sequences
        work: list[tuple[int, INDEX_T, str]] = [
            (seq_idx, idx, str(photo.path))
            for seq_idx, seq in enumerate(forest)
            for idx, photo in seq.get_reference().items()
        ]

        # Initialize result accumulator
        result: dict[bytes, dict[int, list[INDEX_T]]] = defaultdict(make_defaultdict)

        # ASSERTION: Verify work items created for all reference photos
        assert len(work) == sum(len(seq.get_reference()) for seq in forest), (
            f"Work item count mismatch: have {len(work)} work items"
        )

        return work, result

    @classmethod
    def stage_worker(cls, job: tuple[int, INDEX_T, str], _args: str) -> WorkerResult[tuple[int, INDEX_T, bytes]]:
        """Calculate perceptual hash for a photo.

        Normalizes to landscape orientation before calculating hash to ensure
        consistent hash values regardless of portrait/landscape orientation.
        """
        seq_idx, idx, path = job
        cmp = create_comparison_method(CONFIG.sequences.PERCEPTUAL_METHOD)

        # Load with EXIF normalization
        pixels = load_normalized_pixels(path)

        # Additional normalization: rotate portrait to landscape for consistent phash
        # Portrait photos (width < height) are rotated 90° CCW to landscape
        if pixels.shape[1] < pixels.shape[0]:  # width < height
            pixels = np.rot90(pixels, k=1)  # Rotate 90° CCW

        return [], [], (seq_idx, idx, cmp.prepare(pixels))

    def accumulate_results(
        self,
        accum: dict[bytes, dict[int, list[INDEX_T]]],
        job: tuple[int, INDEX_T, bytes],
    ) -> None:
        seq, idx, key = job
        accum[key][seq].append(idx)

    def finalise(self) -> None:
        # Count reference photos across all hash bins
        # The result dict maps hash values -> sequence indices -> photo index lists
        # We sum the length of all photo index lists across all bins
        self.ref_photos_final = sum(len(indices) for bin_dict in self.result.values() for indices in bin_dict.values())
        # Sequence count remains unchanged (this stage just bins existing sequences by hash)
        self.ref_seqs_final = self.ref_seqs_init

        # Invariant: reference photo count should match (this stage doesn't change photos)
        assert self.ref_photos_final == self.ref_photos_init, (
            f"ComputePerceptualHash: reference photo count mismatch - "
            f"started with {self.ref_photos_init}, ended with {self.ref_photos_final}"
        )

    # Typed result field - perceptual hash bins
    result: dict[bytes, dict[int, list[INDEX_T]]]
