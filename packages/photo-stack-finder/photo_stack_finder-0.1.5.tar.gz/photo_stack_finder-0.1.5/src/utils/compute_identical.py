"""Pipeline stage that consumes SHA256 bins and outputs groups of identical files and a list of unique exemplar files."""

from __future__ import annotations

import random

from .config import CONFIG
from .models import IdenticalGroup, ReviewType
from .photo_file import PhotoFile, pick_exemplar_from_class
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .review_utils import build_identical_group


class ComputeIdentical(PipelineStage[list[PhotoFile], list[PhotoFile], list[PhotoFile]]):
    # FIXME : Add docstring
    # TODO: Update to incorporate digit parsing and output template bins
    # Typed result field - populated after run() completes
    # Full tuple: (identical_classes, nonidentical_exemplars)
    result: list[PhotoFile]

    def __init__(self) -> None:
        """Initialize identical files detection stage."""
        super().__init__(
            path=CONFIG.paths.identical_pkl,
            stage_name="Byte-identical detection",
        )

        # Worker args
        self.args = None

        # Create input port for SHA bins (from ComputeShaBins)
        self.sha_bins_i: InputPort[dict[str, list[PhotoFile]]] = InputPort("sha_bins")

        # Create output ports
        # - nonidentical_o: for next stage (templates)
        self.nonidentical_o: OutputPort[list[PhotoFile]] = OutputPort(self, getter=lambda: self.result)

    def prepare(
        self,
    ) -> PrepareResult[list[PhotoFile], list[PhotoFile]]:
        """Prepare identical file detection by splitting bins into work items.

        Reads SHA bins from input port and prepares work items for parallel processing.

        Returns:
            Tuple of (work_items, accumulator) where:
            - work_items: List of bins with multiple photos (potential duplicates)
            - accumulator: nonidentical_photos
        """
        # Read SHA bins from input port
        sha_bins: dict[str, list[PhotoFile]] = self.sha_bins_i.read()
        # Get reference counts from upstream (for photos without sequences, ref == total)
        self.ref_photos_init = self.sha_bins_i.get_ref_photo_count()
        self.ref_seqs_init = self.sha_bins_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (ref == total at this stage)
        self.total_photos = sum(len(b) for b in sha_bins.values())

        multiple_bins: list[list[PhotoFile]] = [b for b in sha_bins.values() if len(b) > 1]
        singleton_bins: list[list[PhotoFile]] = [b for b in sha_bins.values() if len(b) == 1]
        exemplars: list[PhotoFile] = [x for b in singleton_bins for x in b]

        return multiple_bins, exemplars

    def finalise(self) -> None:
        self.ref_photos_final = len(self.result)
        self.ref_seqs_final = None
        # Count total photos to ensure no photos lost (invariant check)
        photos_final: int = (
            sum(len(cl.photos) for cl in self.identical_review_result)
            - len(self.identical_review_result)
            + self.ref_photos_final
        )

        assert photos_final == self.total_photos, (
            f"ComputeIdentical started with {self.total_photos} photos and ended up with {photos_final}"
        )

    @classmethod
    def stage_worker(cls, photo_list: list[PhotoFile], _args: str) -> WorkerResult[list[PhotoFile]]:
        """Process one SHA bin to find byte-identical files.

        Creates both review data (IdenticalGroups) and working data (classes/exemplars)
        from a single SHA bin.

        Args:
            photo_list: Photos from one SHA256 bin
            _args: Stage name (unused, required to match PipelineStage interface)

        Returns:
            Tuple of (review_data, work_data) where:
            - review_data: (list[IdenticalGroup], dict[int, PhotoFile]) for review UI
            - work_data: (list[list[PhotoFile]], list[PhotoFile]) for pipeline flow
        """
        # Singleton bins are filtered out by prepare()
        assert len(photo_list) >= 2

        groups: list[IdenticalGroup] = []
        exemplars: list[PhotoFile] = []

        # Build dict and set for pick_exemplar_from_class
        photos_dict: dict[int, PhotoFile] = {pf.id: pf for pf in photo_list}
        remaining_ids: set[int] = set(photos_dict.keys())

        # Process bin until empty
        while remaining_ids:
            # Pick exemplar from remaining files
            exemplar_id: int = pick_exemplar_from_class(photos_dict, remaining_ids)
            exemplar: PhotoFile = photos_dict[exemplar_id]

            # Create new equivalence class starting with exemplar
            eq_class: list[PhotoFile] = [exemplar]
            remaining_ids.remove(exemplar_id)

            # Read exemplar once into memory for comparison against all candidates
            assert exemplar.path is not None, "Exemplar path cannot be None in production code"
            with exemplar.path.open("rb") as f:
                exemplar_data: bytes = f.read()

            # Compare exemplar against all remaining files
            to_remove: set[int] = set()
            photo_id: int
            for photo_id in remaining_ids:
                candidate: PhotoFile = photos_dict[photo_id]
                assert candidate.path is not None, "Candidate path cannot be None in production code"

                # Read candidate and compare (exemplar already in memory)
                with candidate.path.open("rb") as f:
                    candidate_data: bytes = f.read()

                if exemplar_data == candidate_data:
                    # Mark as identical to exemplar
                    candidate.cache["IDENTICAL"] = exemplar
                    eq_class.append(candidate)
                    to_remove.add(photo_id)

            # Remove matched files from remaining
            remaining_ids -= to_remove

            if len(eq_class) > 1:
                groups.append(build_identical_group(eq_class, exemplar_id))
            exemplars.append(exemplar)

        # Shuffle the groups to see something more inteeresting at review time.
        random.shuffle(groups)

        return groups, [], exemplars

    def accumulate_results(
        self,
        accum: list[PhotoFile],
        job: list[PhotoFile],
    ) -> None:
        # FIXME: Add docstring
        accum.extend(job)

    def needs_review(self) -> ReviewType:
        """This stage produces photo groups (byte-identical duplicates).

        Returns:
            "photos" to indicate this stage produces reviewable photo groups
        """
        return "photos"

    def has_review_data(self) -> bool:
        """Check if there are any identical photo groups to review.

        Returns:
            True if there are identical photo groups with 2+ photos, False otherwise
        """
        # Check if there are any classes with duplicates (2+ photos)
        return len(self.identical_review_result) > 0
