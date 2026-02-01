"""Classes and helper functions for processing a bin of photos which have equivalent filename templates.

Bins according to template core (ie the middle section of the filename which varies between files).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any, cast

import pandas as pd

from .comparison_gates import GateName, GateSequence
from .config import CONFIG
from .logger import get_logger
from .models import ReviewType
from .photo_file import ImageData, PhotoFile, pick_exemplar_from_class
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .review_utils import build_sequence_group
from .sequence import (
    INDEX_T,
    PhotoFileSeries,
    PhotoSequence,
    count_forest_ref_photos,
    count_forest_total_photos,
)
from .template import partial_format


class ComputeVersions(
    PipelineStage[
        tuple[str, list[tuple[INDEX_T, PhotoFile]]],  # S: template bin
        PhotoSequence,  # T: work data
        tuple[list[PhotoSequence], dict[str, list[tuple[PhotoSequence, str]]]],  # R: accumulator
    ]
):
    """From a dict of photos binned by filename template, produce a sequence which has detected any part of the filename that is a version."""

    def __init__(self) -> None:
        """Initialize ComputeVersions pipeline stage.

        Configures stage to save results to forest_versions_pkl and identifies
        as "Version Detection" in logs and metadata.

        """
        super().__init__(
            path=CONFIG.paths.forest_versions_pkl,
            stage_name="Version Detection",
        )

        # Store worker argument for port-based execution
        self.args = self.stage_name

        # Create input port for template bins (from ComputeTemplates)
        self.template_bins_i: InputPort[dict[str, list[tuple[INDEX_T, PhotoFile]]]] = InputPort("template_bins")

        # Create output ports - separate ports per downstream consumer (Decision 6)
        # Full tuple output (for backward compatibility or review)
        self.forest_template_bins_o: OutputPort[
            tuple[list[PhotoSequence], dict[str, list[tuple[PhotoSequence, str]]]]
        ] = OutputPort(self, getter=lambda: self.result)

        # Template remainder bins output (for ComputeTemplateSimilarity)
        self.template_remainder_bins_o: OutputPort[dict[str, list[tuple[PhotoSequence, str]]]] = OutputPort(
            self, getter=lambda: self.result[1]
        )

        # Debug counter for tracking accumulate_results calls
        self.accumulate_count = 0

    def prepare(
        self,
    ) -> PrepareResult[
        tuple[str, list[tuple[INDEX_T, PhotoFile]]],
        tuple[list[PhotoSequence], dict[str, list[tuple[PhotoSequence, str]]]],
    ]:
        """Prepare template bins for parallel processing.

        Sorts bins by size (descending) to process largest bins first, improving
        load balancing across worker processes.

        Template bins are read from the input port.

        Returns:
            Tuple of (work_items, accumulator) where:
            - work_items: List of (template_key, photos) tuples sorted by photo count
            - accumulator: Tuple of (forest, bins) where:
              - forest: Empty list for collecting all PhotoSequence objects
              - bins: Defaultdict for collecting (PhotoSequence, prefix) pairs grouped by template_remainder
        """
        # Read from input port to get template bins
        bins: dict[str, list[tuple[INDEX_T, PhotoFile]]] = self.template_bins_i.read()
        # Get reference counts from upstream (for ungrouped photos, ref == total)
        self.ref_photos_init = self.template_bins_i.get_ref_photo_count()
        self.ref_seqs_init = self.template_bins_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (should never change)
        self.total_photos = sum(len(photo_list) for photo_list in bins.values())

        work: list[tuple[str, list[tuple[INDEX_T, PhotoFile]]]] = sorted(bins.items(), key=lambda p: -len(p[1]))

        # ASSERTION: Verify we have exactly one work item per input sequence
        assert len(work) == self.ref_seqs_init, (
            f"Work item count mismatch: have {len(work)} work items but expected {self.ref_seqs_init} from upstream"
        )

        # ASSERTION: Verify all photos accounted for in work items
        photos_in_work = sum(len(photo_list) for _, photo_list in work)
        assert photos_in_work == self.total_photos, (
            f"Lost photos in prepare: started {self.total_photos}, have {photos_in_work} in work items"
        )

        return work, ([], defaultdict(list))

    @classmethod
    def _test_field_as_version_dimension(
        cls,
        df: pd.DataFrame,
        field_idx: str,
        photo_dict: dict[int, PhotoFile],
        compare: Callable[[int, int, ImageData | None, ImageData | None], tuple[bool, float]],
    ) -> bool:
        """Test if a field represents a version dimension.

        Criteria:
        1. No more than MAX_MISMATCHES vs the reference sequence
        2. More hits than misses (a reference photo is considered a hit)

        Args:
            df: DataFrame with photo indices
            field_idx: Field column name to test
            photo_dict: Mapping from photo ID to PhotoFile
            compare: Comparison function accepting optional ImageData for photo similarity

        Returns:
            True if field represents a version dimension
        """
        # OPTIMIZATION: Use dict-based grouping instead of expensive pivot_table
        # Group photos by position (all fields except the one being tested)
        group_cols = [c for c in df.columns if c not in [field_idx, "Index"]]

        # Build position -> {field_value -> [photo_ids]} mapping
        position_photos: dict[tuple[Any, ...], dict[Any, list[int]]] = defaultdict(lambda: defaultdict(list))

        for row in df.itertuples(index=False):
            # Position is the tuple of values for all non-test fields
            position_key = tuple(getattr(row, col) for col in group_cols) if group_cols else ()
            field_value = getattr(row, field_idx)
            photo_id = cast(int, row.Index)
            position_photos[position_key][field_value].append(photo_id)

        # Find positions with multiple field values (potential versions)
        positions_to_check = [
            (pos, field_groups) for pos, field_groups in position_photos.items() if len(field_groups) > 1
        ]

        if not positions_to_check:
            return False

        misses = 0
        hits = 0
        for _position, field_groups in positions_to_check:
            # Collect all photos at this position across all field values
            vset = {pid for photo_list in field_groups.values() for pid in photo_list}
            # Find the exemplar photo
            ex_id = pick_exemplar_from_class(photo_dict, vset)

            # OPTIMIZATION: Create ImageData once for exemplar, reuse across all comparisons
            with photo_dict[ex_id].image_data() as ex_img:
                # Check whether each photo is similar to the exemplar
                # Early break on first mismatch to save comparisons
                matches = True
                for pid in vset:
                    if pid != ex_id:
                        passes, _ = compare(ex_id, pid, ex_img, None)
                        if not passes:
                            matches = False
                            break  # Early exit - no need to check remaining photos

            if not matches:
                misses += 1
                if misses > CONFIG.sequences.MAX_MISMATCHES:
                    return False
            else:
                hits += 1

        return misses < hits

    @classmethod
    def _create_reference_sequence(
        cls,
        df: pd.DataFrame,
        version_columns: list[str],
        photo_dict: dict[int, PhotoFile],
        template_key: str,
    ) -> tuple[PhotoFileSeries, dict[INDEX_T, PhotoFile]]:
        """Create reference sequence by removing version columns.

        Args:
            df: DataFrame with photo indices
            version_columns: List of column names that are version dimensions
            photo_dict: Mapping from photo ID to PhotoFile
            template_key: Original template key

        Returns:
            Tuple of (reference_series, reference_sequence_dict)
        """
        # OPTIMIZATION: Use dict-based grouping instead of pivot + reverse_pivot
        group_columns = [c for c in df.columns[1:] if c not in version_columns]

        # Group photos by position (non-version fields) and pick exemplar for each position
        position_photos: dict[tuple[Any, ...], set[int]] = defaultdict(set)

        for row in df.itertuples(index=False):
            # Position is the tuple of values for all non-version fields
            position_key = tuple(getattr(row, col) for col in group_columns) if group_columns else ()
            photo_id = cast(int, row.Index)
            position_photos[position_key].add(photo_id)

        # Pick exemplar for each position
        ref_seq: dict[INDEX_T, PhotoFile] = {}
        for position, photo_ids in position_photos.items():
            exemplar_id = pick_exemplar_from_class(photo_dict, photo_ids)
            ref_seq[position] = photo_dict[exemplar_id]

        # Remap remaining fields in template
        vcol_remap = {c: f"{{P{i}}}" for i, c in enumerate(group_columns)}
        ref_series = PhotoFileSeries(
            ref_seq,
            name=(partial_format(template_key, dict.fromkeys(version_columns, "V")).format_map(vcol_remap)),
            normal=False,  # Don't remove fields from the template!
        )

        return ref_series, ref_seq

    @classmethod
    def _create_version_sequences(
        cls,
        df: pd.DataFrame,
        version_columns: list[str],
        ref_seq: dict[INDEX_T, PhotoFile],
        photo_dict: dict[int, PhotoFile],
        template_key: str,
        compare: Callable[[int, int], tuple[bool, float]],
    ) -> list[PhotoSequence]:
        """Create individual version sequences.

        Args:
            df: DataFrame with photo indices
            version_columns: List of column names that are version dimensions
            ref_seq: Reference sequence dictionary
            photo_dict: Mapping from photo ID to PhotoFile
            template_key: Original template key
            compare: Comparison function for photo similarity

        Returns:
            List of PhotoSequence objects for each version
        """
        # OPTIMIZATION: Use dict-based grouping instead of pivot + recover_rows
        group_columns = [c for c in df.columns[1:] if c not in version_columns]
        vcol_remap = {c: f"{{P{i}}}" for i, c in enumerate(group_columns)}

        # Group photos by (position, version_values) tuple
        version_photos: dict[tuple[Any, ...], dict[INDEX_T, int]] = defaultdict(dict)

        for row in df.itertuples(index=False):
            # Position is the tuple of values for all non-version fields
            position = tuple(getattr(row, col) for col in group_columns) if group_columns else ()
            # Version values tuple
            version_values = tuple(getattr(row, col) for col in version_columns)
            photo_id = cast(int, row.Index)

            version_photos[version_values][position] = photo_id

        # Create PhotoSequence for each version
        version_sequences = []
        for version_values, position_photo_ids in version_photos.items():
            # Build index_to_photo mapping
            index_to_photo: dict[INDEX_T, PhotoFile] = {pos: photo_dict[pid] for pos, pid in position_photo_ids.items()}

            seq_series = PhotoFileSeries(
                index_to_photo,
                name=partial_format(template_key, dict(zip(version_columns, version_values, strict=False))).format_map(
                    vcol_remap
                ),
                normal=False,
            )

            # Cache similarity scores
            for idx, p in index_to_photo.items():
                exemplar_photo = ref_seq[idx]
                _passes, similarity = compare(p.id, exemplar_photo.id)
                p.cache["SEQUENCE_EXEMPLAR"] = exemplar_photo
                p.cache["SEQUENCE_SIMILARITY"] = similarity

            version_sequences.append(PhotoSequence(seq_series))

        return version_sequences

    @classmethod
    def stage_worker(
        cls, bin_data: tuple[str, list[tuple[INDEX_T, PhotoFile]]], created_by: str
    ) -> WorkerResult[PhotoSequence]:
        """Analyze a template bin for version patterns.

        Worker function that analyzes one template bin to detect version dimensions.
        Tests each field individually to see if it represents a version dimension.

        PhotoSequence construction automatically handles template normalization including:
        - Constant substitution
        - Common prefix folding
        - Variable renumbering
        - Index normalization

        Args:
                bin_data: Tuple of (template_key, list of PhotoFile objects)
                created_by: Process creating this sequence

        Returns:
                PhotoSequence with normalized template components stored as attributes
        """
        template_key, photo_tuples = bin_data
        n_photos: int = len(photo_tuples)

        # Extract normalized template and indices
        whole_sequence: PhotoFileSeries = PhotoFileSeries(dict(photo_tuples), name=template_key)
        template_key = whole_sequence.name
        assert len(whole_sequence) == n_photos

        # Handle bins with < 2 photos (no versions possible)
        if len(photo_tuples) < 2:
            return [], [], PhotoSequence(whole_sequence, created_by=created_by)

        # Setup dataframe and comparison infrastructure
        photo_dict: dict[int, PhotoFile] = {p.id: p for _, p in photo_tuples}
        df = pd.DataFrame([[p.id, *idx] for idx, p in whole_sequence.items()])
        df.columns = ["Index"] + [f"P{i}" for i in range(df.shape[1] - 1)]
        assert n_photos == df.shape[0]

        # Create comparison function with caching
        gates = GateSequence(cast(list[GateName], CONFIG.processing.COMPARISON_GATES))
        simcache: dict[tuple[int, int], tuple[bool, float]] = {}

        def compare(
            x: int,
            y: int,
            x_img: ImageData | None = None,
            y_img: ImageData | None = None,
        ) -> tuple[bool, float]:
            """Memo function to compare two photo ids with optional pre-created ImageData."""
            p = (x, y) if x < y else (y, x)
            if p not in simcache:
                passes, _score, similarity = gates.compare_with_rotation(
                    photo_dict[x],
                    photo_dict[y],
                    ref_img=x_img,
                    cand_img=y_img,
                )
                simcache[p] = (passes, similarity)
            return simcache[p]

        # Test fields from smallest to largest (by unique value count)
        field_sizes: list[tuple[str, int]] = [(field_idx, len(df[field_idx].unique())) for field_idx in df.columns[1:]]
        field_sizes.sort(key=lambda x: x[1])

        # Find version columns by testing each field
        version_columns: list[str] = []
        for field_idx, unique_count in field_sizes:
            # Break if too many unique values (list is sorted by count)
            if unique_count > CONFIG.sequences.MAX_COMPONENT_SIZE:
                break

            if cls._test_field_as_version_dimension(df, field_idx, photo_dict, compare):
                version_columns.append(field_idx)

        # No versions detected - return whole sequence
        if not version_columns:
            return [], [], PhotoSequence(whole_sequence, created_by=created_by)

        # Create reference sequence (removing version dimensions)
        ref_series, ref_seq = cls._create_reference_sequence(df, version_columns, photo_dict, template_key)

        # Create individual version sequences
        version_sequences = cls._create_version_sequences(
            df,
            version_columns,
            ref_seq,
            photo_dict,
            template_key,
            compare,
        )

        # Build final result
        result = PhotoSequence(ref_series, version_sequences, created_by=created_by)
        assert result.n_photos == n_photos, f"Lost photos: expected={n_photos}, achieved={result.n_photos}"

        return [], [build_sequence_group(result)], result

    def accumulate_results(
        self,
        accum: tuple[list[PhotoSequence], dict[str, list[tuple[PhotoSequence, str]]]],
        seq: PhotoSequence,
    ) -> None:
        """Accumulate PhotoSequence results from worker into forest and template remainder bins.

        Groups sequences by their template_remainder attribute,
        and also maintains the complete forest for review.

        Args:
            accum: Tuple of (forest, bins) where:
                - forest: List collecting all PhotoSequence objects
                - bins: Dictionary accumulating (sequence, prefix) pairs by template_remainder
            seq: PhotoSequence from stage_worker with normalized template components
        """
        forest, bins = accum

        # Debug counter
        self.accumulate_count += 1

        # Add to forest (deduplicated by object identity happens in review server)
        forest.append(seq)

        # Add to template remainder bins
        # Extract template components from PhotoSequence attributes
        # template_prefix is the constant prefix before first variable
        # template_remainder is the variable structure (used as grouping key)
        bins[seq.template_remainder].append((seq, seq.reverse_prefix))

    def finalise(self) -> None:
        forest = self.result[0]
        self.ref_photos_final = count_forest_ref_photos(forest)
        # ComputeVersions is the first stage creating PhotoSequences
        # Count top-level sequences (one per input template bin), not children
        # Children are versions detected WITHIN a bin, not separate input sequences
        self.ref_seqs_final = len(forest)

        # ComputeVersions is the FIRST grouping stage - it receives ungrouped photos
        # and creates version groups. Must preserve TOTAL photos, not just references.
        # Downstream stages receive grouped data and track only references.
        photos_final = count_forest_total_photos(forest)
        # Verify we have same number of sequences as input template bins
        seqs_final = len(forest)

        # Debug logging
        get_logger().info(
            f"ComputeVersions finalise: accumulate_results called {self.accumulate_count} times, "
            f"forest has {seqs_final} sequences, expected {self.ref_seqs_init}"
        )

        assert seqs_final == self.ref_seqs_init, (
            f"Sequence count mismatch in {self.stage_name}: "
            f"started with {self.ref_seqs_init} but ended with {seqs_final} "
            f"(accumulate_results was called {self.accumulate_count} times)"
        )
        assert photos_final == self.total_photos, (
            f"Started with {self.total_photos} photos but ended up with {photos_final}"
        )

    def needs_review(self) -> ReviewType:
        """This stage produces sequence groups (version-detected sequences).

        Returns:
            "sequences" to indicate this stage produces reviewable sequence groups
        """
        return "sequences"

    def has_review_data(self) -> bool:
        """Check if there are any version sequence groups to review.

        Returns:
            True if forest has classes (multi-sequence groups), False otherwise
        """
        # Check if stage has run
        if not hasattr(self, "result") or self.result is None:
            return False

        # Check if there are any classes (multi-sequence groups) in the forest
        forest = self.result[0]
        return any(seq.is_class() for seq in forest)

    # Typed result field - tuple of (forest, template_bins)
    result: tuple[list[PhotoSequence], dict[str, list[tuple[PhotoSequence, str]]]]
