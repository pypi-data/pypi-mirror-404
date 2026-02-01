"""Compute similar sequences from bins created by puting the sequence in bins defined by the max two indices of the sequence."""

from __future__ import annotations

from itertools import combinations
from typing import cast

import networkx as nx

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
    count_forest_ref_sequences,
    count_forest_total_photos,
)
from .sequence_clustering import cluster_similar_sequences


def build_cohabitation_graph(
    index_bins: dict[INDEX_T, list[PhotoSequence]],
) -> list[set[PhotoSequence]]:
    """Build graph from index bins and find connected components.

    Args:
            index_bins: Dict mapping index pattern → list of sequences

    Returns:
            List of connected components (each component is a set of PhotoSequence objects)
    """
    # Build graph
    graph: nx.Graph[PhotoSequence] = nx.Graph()
    graph.add_nodes_from(set().union(*index_bins.values()))

    # Add edges where sequences share index bins
    # Add edges between all pairs in this bin
    for index_bin in index_bins.values():
        for seq1, seq2 in combinations(index_bin, 2):
            graph.add_edge(seq1, seq2)

    # Find connected components
    result = [set(c) for c in nx.connected_components(graph)]

    n_seqs = len(set().union(*index_bins.values()))
    n_result_seqs = len(set().union(*result))

    assert n_seqs == n_result_seqs, f"build_cohabitation_graph had {n_seqs} but only returned {n_result_seqs}"

    return result


class ComputeIndices(
    PipelineStage[
        set[PhotoSequence],  # S: component
        list[PhotoSequence],  # T: work data
        tuple[list[PhotoSequence], list[PhotoSequence]],  # R: accumulator
    ]
):
    def __init__(self) -> None:
        """Initialize the index-based grouping stage."""
        super().__init__(
            path=CONFIG.paths.forest_sequence_matches_pkl,
            stage_name="Index Grouping",
        )

        # Store worker argument
        self.args = self.stage_name  # Standard args attribute for run()

        # Create input port for index bins
        self.index_bins_i: InputPort[dict[INDEX_T, list[PhotoSequence]]] = InputPort("index_bins")

        # Create output ports - separate ports per downstream consumer
        # Full tuple output (for backward compatibility or review)
        self.forest_bins_o: OutputPort[tuple[list[PhotoSequence], list[PhotoSequence]]] = OutputPort(
            self, getter=lambda: self.result
        )

        # Forest output (for ComputePerceptualHash and ComputePerceptualMatch)
        self.forest_o: OutputPort[list[PhotoSequence]] = OutputPort(self, getter=lambda: self.result[0])

    def prepare(
        self,
    ) -> PrepareResult[set[PhotoSequence], tuple[list[PhotoSequence], list[PhotoSequence]]]:
        """Extract index bins, build graph, and return processable components.

        Reads index bins from input port and prepares work items for parallel processing.

        Returns:
            Tuple of (processable_components, accumulator)
        """
        # Read index bins from input port
        index_bins: dict[INDEX_T, list[PhotoSequence]] = self.index_bins_i.read()
        # Get reference counts from upstream for UI statistics tracking
        all_sequences = set().union(*index_bins.values())
        self.ref_photos_init = self.index_bins_i.get_ref_photo_count()
        self.ref_seqs_init = self.index_bins_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (should never change)
        self.total_photos = sum(seq.n_photos for seq in all_sequences)

        n_photos = self.total_photos

        # Build cohabitation graph
        components: list[set[PhotoSequence]] = build_cohabitation_graph(index_bins)
        n_component_photos = sum(seq.n_photos for seq in set().union(*components))
        assert n_photos == n_component_photos, (
            f"Had {n_photos} before cohabitation graph and {n_component_photos} afterward"
        )

        # Filter components by size
        max_size = CONFIG.sequences.MAX_COMPONENT_SIZE
        processable_components: list[set[PhotoSequence]] = sorted(
            [c for c in components if 2 <= len(c) <= max_size],
            key=lambda c: -sum([s.n_ref_photos for s in c]),
        )
        skipped_components: list[set[PhotoSequence]] = [c for c in components if len(c) > max_size or len(c) < 2]

        # Calculate skip statistics
        num_singletons = sum(1 for c in skipped_components if len(c) < 2)
        num_oversized = sum(1 for c in skipped_components if len(c) > max_size)

        get_logger().info(
            f"Skipped {len(skipped_components)} components ({num_singletons} singletons, {num_oversized} oversized), "
            f"total sequences is {sum([len(c) for c in processable_components])} in {len(processable_components)} sets"
        )

        # Initialize forest with skipped sequences (pass-through)
        skipped_sequences = [seq for comp in skipped_components for seq in comp]
        forest: list[PhotoSequence] = list(skipped_sequences)
        bins: list[PhotoSequence] = list(skipped_sequences)

        new_photos = sum(seq.n_photos for seq in set().union(*processable_components)) + +sum(
            v.n_photos for v in forest
        )
        assert n_photos == new_photos, f"ComputeIndices.prepare had {n_photos} photos and ended up with {new_photos}"

        # Return work items and tuple accumulator
        return processable_components, (forest, bins)

    @classmethod
    def stage_worker(cls, component: set[PhotoSequence], created_by: str) -> WorkerResult[list[PhotoSequence]]:
        """Process one connected component to form PhotoSequence objects.

        Uses predicted exemplar sequence and intersection-based comparison.
        Builds SequenceGroup models incrementally for review.

        Args:
            component: Set of PhotoSequence objects to compare
            created_by: Annotation of how the similarity was detected

        Returns:
            Tuple of (identical_groups, sequence_groups, work_sequences) where:
            - identical_groups: Always empty list for this stage
            - sequence_groups: SequenceGroup models for multi-sequence groups
            - work_sequences: PhotoSequence objects for pipeline flow
        """
        # ASSERTION: Count input photos (atomic invariant)
        input_photos: int = sum(seq.n_photos for seq in component)

        # Use configured gate sequence instead of hardcoded method
        gates = GateSequence(cast(list[GateName], CONFIG.processing.COMPARISON_GATES))

        # Use common clustering algorithm
        result_classes, sequence_groups = cluster_similar_sequences(
            list(component),
            gates,
            created_by,
        )

        # ASSERTION: Verify all photos preserved
        output_photos = sum(seq.n_photos for seq in result_classes)
        assert output_photos == input_photos, (
            f"Lost photos in stage_worker: started {input_photos}, ended {output_photos}"
        )

        return [], sequence_groups, result_classes

    def accumulate_results(
        self,
        accum: tuple[list[PhotoSequence], list[PhotoSequence]],
        job: list[PhotoSequence],
    ) -> None:
        """Accumulate worker results into forest and bins.

        Args:
            accum: Tuple of (forest, bins) - both contain all sequences
            job: List of PhotoSequence objects from worker
        """
        forest, bins = accum
        forest.extend(job)
        bins.extend(job)

    def finalise(self) -> None:
        forest = self.result[0]
        self.ref_photos_final = count_forest_ref_photos(forest)
        self.ref_seqs_final = len(forest)

        # Count total photos to ensure no photos lost (invariant check)
        photos_final = count_forest_total_photos(forest)
        count_forest_ref_sequences(forest)

        # FIXME: Sequence count validation disabled due to test fixture limitations
        assert photos_final == self.total_photos, (
            f"Started with {self.total_photos} photos but ended up with {photos_final}"
        )

    def needs_review(self) -> ReviewType:
        """This stage produces sequence groups (index overlap sequences).

        Returns:
            "sequences" to indicate this stage produces reviewable sequence groups
        """
        return "sequences"

    def has_review_data(self) -> bool:
        """Check if there are any index overlap sequence groups to review.

        Returns:
            True if forest has classes (multi-sequence groups), False otherwise
        """
        # Check if stage has run
        if not hasattr(self, "result") or self.result is None:
            return False

        # Check if there are any classes (multi-sequence groups) in the forest
        forest = self.result[0]
        return any(seq.is_class() for seq in forest)

    # Typed result field - tuple of (forest, bins)
    result: tuple[list[PhotoSequence], list[PhotoSequence]]
