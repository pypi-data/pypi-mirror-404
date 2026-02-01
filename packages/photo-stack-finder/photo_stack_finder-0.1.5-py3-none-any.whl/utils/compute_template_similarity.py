"""Template similarity detection for photo sequences.

This module identifies sequences that share common template structures,
where templates differ only in their constant (non-variable) prefixes or suffixes.
This indicates they likely represent photos from the same event or location.

Example:
    Templates like "Summer2024_{P0}.jpg" and "Vacation2024_{P0}.jpg"
    share the template remainder "_{P0}.jpg" and would be grouped together.
"""

from __future__ import annotations

from collections import defaultdict
from heapq import nlargest
from os.path import commonprefix
from typing import cast

from .comparison_gates import GateName, GateSequence
from .config import CONFIG
from .logger import get_logger
from .models import ReviewType
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .sequence import (
    INDEX_T,
    PhotoSequence,
    count_forest_ref_photos,
    count_forest_total_photos,
)
from .sequence_clustering import cluster_similar_sequences

# ==================== Phase 2: Large Bin Subdivision ====================


# Note: The iterative subdivision algorithm has been integrated directly into
# ComputeTemplateSimilarity.prepare() method, replacing the previous recursive
# subdivide_large_bin() and find_longest_common_suffix() functions.


class ComputeTemplateSimilarity(
    PipelineStage[
        tuple[str, list[tuple[PhotoSequence, str]]],  # S: template bin
        list[tuple[list[INDEX_T], PhotoSequence]],  # T: work data
        tuple[list[PhotoSequence], dict[INDEX_T, list[PhotoSequence]]],  # R: accumulator
    ]
):
    """Pipeline stage for processing template similarity bins.

    This stage takes template bins (sequences grouped by template remainder)
    and processes each bin to create new PhotoSequence objects that group
    similar sequences together. Outputs index bins.

    Similar to ComputeIndices, but operates on template-based bins instead of
    index-based bins from version detection.
    """

    def __init__(self) -> None:
        """Initialize the template similarity stage."""
        super().__init__(
            path=CONFIG.paths.forest_template_similarity_pkl,
            stage_name="Template Similarity",
        )

        # Store worker argument for port-based execution
        self.args = self.stage_name

        # Create input port for template bins (from ComputeVersions)
        self.template_bins_i: InputPort[dict[str, list[tuple[PhotoSequence, str]]]] = InputPort("template_bins")

        # Create output ports - separate ports per downstream consumer (Decision 6)
        # Full tuple output (for backward compatibility or review)
        self.forest_bins_o: OutputPort[tuple[list[PhotoSequence], dict[INDEX_T, list[PhotoSequence]]]] = OutputPort(
            self, getter=lambda: self.result
        )

        # Index bins output (for ComputeIndices)
        self.index_bins_o: OutputPort[dict[INDEX_T, list[PhotoSequence]]] = OutputPort(
            self, getter=lambda: self.result[1]
        )

    def _extract_common_prefix_and_update(
        self,
        template_remainder: str,
        bin_items: list[tuple[PhotoSequence, str]],
    ) -> tuple[str, list[tuple[PhotoSequence, str]]]:
        """Extract common prefix from bin items and update template remainder.

        Args:
            template_remainder: Current template remainder key
            bin_items: List of (sequence, prefix) pairs

        Returns:
            Tuple of (updated_template_remainder, updated_bin_items)
        """
        prefixes = [prefix for _, prefix in bin_items]
        common_prefix = commonprefix(prefixes)

        if common_prefix:
            # Add reversed prefix to template key
            template_remainder = common_prefix[::-1] + template_remainder
            bin_items = [(s, p[len(common_prefix) :]) for s, p in bin_items]

        return template_remainder, bin_items

    def _subdivide_by_first_char(
        self,
        bin_items: list[tuple[PhotoSequence, str]],
        template_remainder: str,
    ) -> dict[str, list[tuple[PhotoSequence, str]]]:
        """Subdivide bin items by first character of remaining prefix.

        Args:
            bin_items: List of (sequence, prefix) pairs to subdivide
            template_remainder: Current template remainder key (for logging)

        Returns:
            Dict mapping first character to list of bin items
        """
        char_bins: dict[str, list[tuple[PhotoSequence, str]]] = defaultdict(list)
        for seq, new_prefix in bin_items:
            # Use first character as bin key (empty string if prefix is empty)
            first_char = new_prefix[0] if new_prefix else ""
            char_bins[first_char].append((seq, new_prefix))
        return char_bins

    def _log_subdivision_statistics(
        self,
        total_subdivisions: int,
        largest_input_bin: int,
        largest_output_bin: int,
        processable_bins: list[tuple[str, list[tuple[PhotoSequence, str]]]],
        skipped_sequences: list[PhotoSequence],
        template_bins: dict[str, list[tuple[PhotoSequence, str]]],
        max_size: int,
    ) -> None:
        """Log subdivision and processing statistics.

        Args:
            total_subdivisions: Number of original large bins subdivided
            largest_input_bin: Size of largest bin before subdivision
            largest_output_bin: Size of largest bin after subdivision
            processable_bins: List of bins ready for processing
            skipped_sequences: Sequences skipped due to being singletons
            template_bins: Original template bins (for count comparison)
            max_size: Maximum allowed bin size
        """
        bin_sizes = [len(bin_items) for _, bin_items in processable_bins]
        min_bin_size = min(bin_sizes) if bin_sizes else 0
        max_bin_size = max(bin_sizes) if bin_sizes else 0

        get_logger().info(
            f"Processing {len(processable_bins)} template bins, "
            f"skipped {len(skipped_sequences)} singleton sequences from "
            f"{len(template_bins) - len(processable_bins) - total_subdivisions} bins"
        )

        if bin_sizes:
            avg_bin_size = sum(bin_sizes) / len(bin_sizes)
            get_logger().info(
                f"  All bins within limits: {min_bin_size}-{max_bin_size} sequences "
                f"(avg: {avg_bin_size:.1f}, limit: {max_size})"
            )

        if total_subdivisions > 0:
            get_logger().info(
                f"  Subdivision: {total_subdivisions} large bins (max input: {largest_input_bin}) "
                f"-> {len(processable_bins)} processable bins (max output: {largest_output_bin}, limit: {max_size})"
            )

        if skipped_sequences:
            get_logger().info(
                f"  Added {len(skipped_sequences)} skipped sequences directly to output (ensuring no data loss)"
            )

    def _validate_subdivision_results(
        self,
        processable_bins: list[tuple[str, list[tuple[PhotoSequence, str]]]],
        skipped_sequences: list[PhotoSequence],
        max_size: int,
    ) -> None:
        """Validate subdivision results and ensure all sequences accounted for.

        Args:
            processable_bins: List of bins ready for processing
            skipped_sequences: Sequences skipped due to being singletons
            max_size: Maximum allowed bin size

        Raises:
            AssertionError: If validation fails
        """
        # Verify all reference sequences accounted for
        processable_ref_seqs = sum(len(bin_items) for _, bin_items in processable_bins)
        skipped_ref_seqs = len(skipped_sequences)
        total_ref_seqs = processable_ref_seqs + skipped_ref_seqs
        assert total_ref_seqs == self.ref_seqs_init, (
            f"Lost ref seqs in subdivision: started {self.ref_seqs_init}, "
            f"have {total_ref_seqs} ({processable_ref_seqs} processable + {skipped_ref_seqs} skipped)"
        )
        assert self.total_seqs_init == sum(s.n_seqs for s in skipped_sequences) + sum(
            s.n_seqs for _, lpss in processable_bins for s, _ in lpss
        )

        # Validate all processable bins are within size limit
        bin_sizes = [len(bin_items) for _, bin_items in processable_bins]
        if bin_sizes:
            max_bin_size = max(bin_sizes)
            assert max_bin_size <= max_size, f"Subdivision failed: max bin size {max_bin_size} exceeds limit {max_size}"

    def _initialize_from_input(
        self,
        template_bins: dict[str, list[tuple[PhotoSequence, str]]],
    ) -> None:
        """Initialize counters and validate input from template bins port.

        Args:
            template_bins: Template bins read from input port

        Raises:
            AssertionError: If reference sequence counts don't match
        """
        self.ref_photos_init = self.template_bins_i.get_ref_photo_count()
        self.ref_seqs_init = self.template_bins_i.get_ref_sequence_count()
        self.total_photos = sum(seq.n_photos for bin_items in template_bins.values() for seq, _ in bin_items)
        n_bin_seqs: int = sum(len(bin_items) for bin_items in template_bins.values())
        assert self.ref_seqs_init == n_bin_seqs
        self.total_seqs_init = sum(s.n_seqs for bin_items in template_bins.values() for s, _ in bin_items)

    def _finalize_and_validate(
        self,
        forest: list[PhotoSequence],
        processable_bins: list[tuple[str, list[tuple[PhotoSequence, str]]]],
    ) -> None:
        """Perform final validation checks on processed results.

        Args:
            forest: List of sequences in forest
            processable_bins: List of bins ready for processing

        Raises:
            AssertionError: If photo or sequence counts don't match
        """
        # Verify all reference sequences accounted for
        assert self.ref_seqs_init == len(forest) + sum(len(ss) for _, ss in processable_bins)

        # Verify all photos accounted for
        photos_in_forest = sum(seq.n_photos for seq in forest)
        photos_in_bins = sum(seq.n_photos for _, bin_items in processable_bins for seq, _ in bin_items)
        total_photos = photos_in_forest + photos_in_bins
        assert total_photos == self.total_photos, (
            f"Lost photos in prepare: started {self.total_photos}, have {total_photos} "
            f"({photos_in_forest} in forest + {photos_in_bins} in bins)"
        )

    def prepare(
        self,
    ) -> PrepareResult[
        tuple[str, list[tuple[PhotoSequence, str]]],
        tuple[list[PhotoSequence], dict[INDEX_T, list[PhotoSequence]]],
    ]:
        """Prepare template bins for processing with iterative subdivision.

        Uses an iterative worklist algorithm to subdivide large bins by extracting
        common prefixes and splitting on first character. This replaces the previous
        recursive approach with a simpler, more maintainable implementation.

        Algorithm:
            1. Start with template bins in worklist
            2. For each bin:
               - Extract common prefix from all prefix strings
               - Move common prefix (reversed) to template remainder key
               - If bin is small enough (<= max_size), add to processable bins
               - Otherwise, split by first character and add sub-bins back to worklist
            3. Continue until worklist is empty

        Template bins are read from the input port.

        Returns:
            Tuple of (processable_bins, accumulator) where:
                - processable_bins: List of (template_remainder, bin) pairs to process
                - accumulator: Tuple of (forest, bins) with skipped sequences already added
        """
        # Read from input port and initialize counters
        template_bins: dict[str, list[tuple[PhotoSequence, str]]] = self.template_bins_i.read()
        self._initialize_from_input(template_bins)

        max_size = CONFIG.sequences.MAX_COMPONENT_SIZE

        # Initialize results and tracking
        forest: list[PhotoSequence] = []
        bins: dict[INDEX_T, list[PhotoSequence]] = defaultdict(list)
        processable_bins: list[tuple[str, list[tuple[PhotoSequence, str]]]] = []
        skipped_sequences: list[PhotoSequence] = []

        # Subdivision statistics
        total_subdivisions = 0
        total_sub_bins_created = 0
        largest_input_bin = 0
        largest_output_bin = 0
        original_large_bins_seen: set[str] = set()

        # Iterative worklist for subdivision
        worklist: list[tuple[str, list[tuple[PhotoSequence, str]]]] = list(template_bins.items())

        while worklist:
            try:
                template_remainder, bin_items = worklist.pop()
                bin_size = len(bin_items)

                # Skip singleton bins
                if bin_size < 2:
                    skipped_sequences.extend([seq for seq, _ in bin_items])
                    continue

                # Extract common prefix and update template remainder
                template_remainder, bin_items = self._extract_common_prefix_and_update(template_remainder, bin_items)

                # Check if bin is small enough to process
                if bin_size <= max_size:
                    processable_bins.append((template_remainder, bin_items))
                    largest_output_bin = max(largest_output_bin, bin_size)
                    continue

                # Bin is too large - subdivide it
                if template_remainder in template_bins and template_remainder not in original_large_bins_seen:
                    get_logger().info(f"Subdividing large bin '{template_remainder}' with {bin_size} sequences")
                    original_large_bins_seen.add(template_remainder)
                    total_subdivisions += 1
                    largest_input_bin = max(largest_input_bin, bin_size)

                # Split by first character of remaining prefix
                char_bins = self._subdivide_by_first_char(bin_items, template_remainder)

                # Check if we made progress
                if len(char_bins) == 1:
                    # No progress - skip these sequences
                    get_logger().warning(
                        f"Cannot subdivide bin '{template_remainder}' with {bin_size} items "
                        f"(all prefixes identical). Skipping (exceeds limit of {max_size})."
                    )
                    skipped_sequences.extend([bi[0] for bi in bin_items])
                else:
                    # Made progress - add sub-bins back to worklist
                    for _char, char_bin_items in char_bins.items():
                        worklist.append((template_remainder, char_bin_items))
                        total_sub_bins_created += 1
            finally:
                # Invariant checks
                assert self.ref_seqs_init == sum(len(ss) for _, ss in worklist) + len(skipped_sequences) + sum(
                    len(ss) for _, ss in processable_bins
                )
                assert self.total_seqs_init == sum(s.n_seqs for _, lpss in worklist for s, _ in lpss) + sum(
                    s.n_seqs for s in skipped_sequences
                ) + sum(s.n_seqs for _, lpss in processable_bins for s, _ in lpss)

        # Validate subdivision results
        self._validate_subdivision_results(processable_bins, skipped_sequences, max_size)

        # Add skipped singleton sequences to forest and bins
        for seq in skipped_sequences:
            forest.append(seq)
            position_keys = nlargest(2, seq.series.index)
            for key in position_keys:
                bins[key].append(seq)

        # Sort by total photo count (descending) for better progress tracking
        processable_bins.sort(key=lambda x: -sum(seq.n_ref_photos for seq, _prefix in x[1]))

        # Log summary statistics
        self._log_subdivision_statistics(
            total_subdivisions,
            largest_input_bin,
            largest_output_bin,
            processable_bins,
            skipped_sequences,
            template_bins,
            max_size,
        )

        # Final validation
        self._finalize_and_validate(forest, processable_bins)

        return processable_bins, (forest, bins)

    @classmethod
    def stage_worker(
        cls, bin_item: tuple[str, list[tuple[PhotoSequence, str]]], created_by: str
    ) -> WorkerResult[list[tuple[list[INDEX_T], PhotoSequence]]]:
        # FIXME: This docstring should document what is here without reference to other stages
        """Process one template bin to create grouped PhotoSequence objects.

        Similar to ComputeIndices.stage_worker, but operates on template-grouped
        sequences instead of index-grouped sequences.

        Args:
            bin_item: Tuple of (template_remainder, list of (sequence, prefix) pairs)
            created_by: Label for how similarity was detected (e.g., "Template Similarity")

        Returns:
            List of (position_keys, PhotoSequence) tuples for accumulation into index bins
        """
        _template_remainder, seq_prefix_pairs = bin_item

        # Extract just the sequences (discard prefixes for now - phase 2 will use them)
        sequences = [seq for seq, _prefix in seq_prefix_pairs]
        total_seqs = sum(s.n_seqs for s in sequences)

        # ASSERTION: Count input photos (atomic invariant)
        input_photos: int = sum(seq.n_photos for seq in sequences)

        # Use configured gate sequence
        gates = GateSequence(cast(list[GateName], CONFIG.processing.COMPARISON_GATES))

        # Use common clustering algorithm
        result_sequences, new_sequences = cluster_similar_sequences(
            sequences,
            gates,
            created_by,
        )

        # Wrap with position keys for index bin accumulation
        result_classes: list[tuple[list[INDEX_T], PhotoSequence]] = []
        for result_seq in result_sequences:
            # Get top 2 position keys from the result sequence
            position_keys = nlargest(2, result_seq.series.index)
            result_classes.append((position_keys, result_seq))

        # ASSERTION: Verify all photos preserved
        output_photos = sum(seq.n_photos for _, seq in result_classes)
        assert output_photos == input_photos, (
            f"Lost photos in stage_worker: started {input_photos}, ended {output_photos}"
        )
        assert total_seqs == sum(seq.n_seqs for _, seq in result_classes)

        return [], new_sequences, result_classes

    def accumulate_results(
        self,
        accum: tuple[list[PhotoSequence], dict[INDEX_T, list[PhotoSequence]]],
        job: list[tuple[list[INDEX_T], PhotoSequence]],
    ) -> None:
        """Accumulate PhotoSequence results from worker into forest and index bins.

        Adds each PhotoSequence to the forest and to multiple index bins based on
        its position keys, enabling finding overlapping sequences.

        Args:
            accum: Tuple of (forest, bins) where:
                - forest: List collecting all PhotoSequence objects
                - bins: Dictionary accumulating sequences by position key
            job: Results from stage_worker - list of (position_keys, sequence) tuples
        """
        forest, bins = accum
        for position_keys, seq in job:
            forest.append(seq)
            for key in position_keys:
                bins[key].append(seq)

    def finalise(self) -> None:
        forest, _ = self.result
        self.ref_photos_final = count_forest_ref_photos(forest)
        self.ref_seqs_final = len(forest)

        # Count total photos to ensure no photos lost (invariant check)
        photos_final = count_forest_total_photos(forest)
        assert photos_final == self.total_photos, (
            f"Started with {self.total_photos} photos but ended up with {photos_final}"
        )
        assert sum(s.n_seqs for s in forest) == self.total_seqs_init

    def needs_review(self) -> ReviewType:
        """This stage produces sequence groups (template similarity sequences).

        Returns:
            "sequences" to indicate this stage produces reviewable sequence groups
        """
        return "sequences"

    def has_review_data(self) -> bool:
        """Check if there are any template similarity sequence groups to review.

        Returns:
            True if forest has classes (multi-sequence groups), False otherwise
        """
        # Check if stage has run
        if not hasattr(self, "result") or self.result is None:
            return False

        # Check if there are any classes (multi-sequence groups) in the forest
        forest = self.result[0]
        return any(seq.is_class() for seq in forest)

    # Typed result field - tuple of (forest, index_bins)
    result: tuple[list[PhotoSequence], dict[INDEX_T, list[PhotoSequence]]]
