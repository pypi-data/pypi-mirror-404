"""Implementation of perceptual matching pipeline stage."""

from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import cast

import networkx as nx

from .comparison_gates import GateName, GateSequence
from .config import CONFIG
from .logger import get_logger
from .models import ReviewType, SequenceGroup
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .sequence import (
    INDEX_T,
    PhotoSequence,
    count_forest_ref_photos,
    count_forest_ref_sequences,
    count_forest_total_photos,
    predict_exemplar_sequence,
)
from .sequence_clustering import cluster_similar_sequences


class ComputePerceptualMatch(
    PipelineStage[
        list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]],  # S: component
        list[PhotoSequence],  # T: merged sequences
        list[PhotoSequence],  # R: result forest
    ]
):
    def __init__(self) -> None:
        """Initialize the perceptual matching stage."""
        super().__init__(
            path=CONFIG.paths.forest_final_pkl,
            stage_name="Perceptual Matching",
        )

        # Store worker argument
        self.args = self.stage_name  # Standard args attribute for run()

        # Create input port for forest (from ComputeIndices)
        self.forest_i: InputPort[list[PhotoSequence]] = InputPort("forest")

        # Create input port for perceptual bins (from ComputePerceptualHash)
        self.perceptual_bins_i: InputPort[dict[bytes, dict[int, list[INDEX_T]]]] = InputPort("perceptual_bins")

        # Create output port for final forest
        self.final_forest_o: OutputPort[list[PhotoSequence]] = OutputPort(self, getter=lambda: self.result)

    def prepare(
        self,
    ) -> PrepareResult[list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]], list[PhotoSequence]]:
        """Extract index bins, build graph, and return processable components.

        Reads forest and bins from input ports, builds connection graph,
        and filters components by size.

        Returns:
            Tuple of (processable_components, skipped_sequences)
        """
        # Read from input ports
        forest = self.forest_i.read()
        # Get reference counts from upstream for UI statistics tracking
        self.ref_photos_init = self.forest_i.get_ref_photo_count()
        self.ref_seqs_init = self.forest_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (should never change)
        self.total_photos = sum(seq.n_photos for seq in forest)
        perceptual_bins = self.perceptual_bins_i.read()

        # Within each bin, calculate the number of connections between sequences and the best index mapping with its value
        connections: dict[tuple[int, int], list[tuple[list[INDEX_T], list[INDEX_T]]]] = defaultdict(list)
        associations: dict[int, list[tuple[INDEX_T, bytes]]] = defaultdict(list)
        k: bytes
        hbin: dict[int, list[INDEX_T]]
        for k, hbin in perceptual_bins.items():
            # label each index of the sequence with its hash
            s: int
            idces: list[INDEX_T]
            for s, idces in hbin.items():
                associations[s].extend([(idx, k) for idx in idces])
            # add the pair of index lists that are matched to the pair of sequences
            for (s1, hb1), (s2, hb2) in combinations(sorted(hbin.items()), 2):
                connections[(s1, s2)].append((hb1, hb2))

        # Form connection graph along with index mappings and get components of connected sequences
        graph: nx.Graph[int] = nx.Graph()
        graph.add_nodes_from(range(len(forest)))
        for (s1, s2), idx_pairs in connections.items():
            # If the sequences match for at least half their points then test them for equality
            if sum([min(len(idces1), len(idces2)) for idces1, idces2 in idx_pairs]) >= 0.5 * min(
                len(forest[s1].get_reference()), len(forest[s2].get_reference())
            ):
                graph.add_edge(s1, s2)

        components: list[list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]]] = [
            [(forest[i], associations[i]) for i in c] for c in nx.connected_components(graph)
        ]

        # Filter components by size
        max_size = CONFIG.sequences.MAX_COMPONENT_SIZE
        processable_components: list[list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]]] = sorted(
            [c for c in components if 2 <= len(c) <= max_size],
            key=lambda c: -sum([seq.n_ref_photos for seq, _ in c]),
        )
        skipped_components: list[list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]]] = [
            c for c in components if len(c) > max_size or len(c) < 2
        ]

        # Flatten skipped components into result sequences
        results: list[PhotoSequence] = [seq for comp in skipped_components for seq, _ in comp]

        # Calculate skip statistics
        num_singletons = sum(1 for c in skipped_components if len(c) < 2)
        num_oversized = sum(1 for c in skipped_components if len(c) > max_size)

        get_logger().info(
            f"There are {len(processable_components)} perceptual components with an average of {float(sum([len(c) for c in processable_components])) / float(len(processable_components)) if processable_components else 0} sequences"
        )
        get_logger().info(
            f"Skipped {len(skipped_components)} components ({num_singletons} singletons, {num_oversized} oversized), "
            f"total sequences is {sum([len(c) for c in processable_components])} in {len(processable_components)} sets"
        )

        n_photos_processable = sum(seq.n_photos for component in processable_components for seq, _ in component)
        n_photos_skipped = sum(seq.n_photos for seq in results)

        assert self.total_photos == n_photos_processable + n_photos_skipped, (
            f"ComputePerceptualMatch._prepare_with_bins lost photos, expected {self.total_photos}, got {n_photos_processable} + {n_photos_skipped}"
        )

        return processable_components, results

    @classmethod
    def stage_worker(
        cls,
        bin_data: list[tuple[PhotoSequence, list[tuple[INDEX_T, bytes]]]],
        created_by: str,
    ) -> WorkerResult[list[PhotoSequence]]:
        # ASSERTION: Count input photos (atomic invariant)
        input_photos: int = sum(seq.n_photos for seq, _ in bin_data)

        gates = GateSequence(cast(list[GateName], CONFIG.processing.COMPARISON_GATES))

        # Keep sequences and their hash associations
        seq_with_hashes: list[tuple[PhotoSequence, dict[INDEX_T, bytes]]] = [
            (seq, dict(hashes)) for seq, hashes in bin_data
        ]

        result_sequences: list[PhotoSequence] = []
        review_groups: list[SequenceGroup] = []

        # Iteratively find clusters of similar sequences
        while seq_with_hashes:
            # Extract just sequences for exemplar prediction
            sequences = [seq for seq, _hashes in seq_with_hashes]

            # Pick best exemplar from remaining sequences
            exemplar_seq_obj = predict_exemplar_sequence(sequences)
            exemplar_idx = sequences.index(exemplar_seq_obj)
            seq_with_hashes[exemplar_idx][1]

            remaining_with_hashes = [
                (seq, hashes) for i, (seq, hashes) in enumerate(seq_with_hashes) if i != exemplar_idx
            ]

            # Use common clustering algorithm
            cluster_results, cluster_reviews = cluster_similar_sequences(
                [exemplar_seq_obj] + [seq for seq, _ in remaining_with_hashes],
                gates,
                created_by,
            )

            result_sequences.extend(cluster_results)
            review_groups.extend(cluster_reviews)

            # Remove all processed sequences from pool (they're now in cluster_results)
            # Note: cluster_results contains NEW PhotoSequence objects, so we track input sequences instead
            input_sequences = {exemplar_seq_obj} | {seq for seq, _ in remaining_with_hashes}
            seq_with_hashes = [(seq, hashes) for seq, hashes in seq_with_hashes if seq not in input_sequences]

        # ASSERTION: Verify all photos preserved
        output_photos = sum(seq.n_photos for seq in result_sequences)
        assert output_photos == input_photos, (
            f"Lost photos in stage_worker: started {input_photos}, ended {output_photos}"
        )

        return [], review_groups, result_sequences

    def accumulate_results(
        self,
        accum: list[PhotoSequence],
        job: list[PhotoSequence],
    ) -> None:
        accum.extend(job)

    def finalise(self) -> None:
        self.ref_photos_final = count_forest_ref_photos(self.result)
        self.ref_seqs_final = len(self.result)

        # Count total photos to ensure no photos lost (invariant check)
        photos_final = count_forest_total_photos(self.result)
        seqs_final = count_forest_ref_sequences(self.result)

        if seqs_final != self.ref_seqs_init:
            get_logger().warning(
                f"Sequence count mismatch in {self.stage_name}: "
                f"started with {self.ref_seqs_init} but ended with {seqs_final}"
            )

        assert photos_final == self.total_photos, (
            f"Started with {self.total_photos} photos and ended up with {photos_final}"
        )

    def needs_review(self) -> ReviewType:
        """This stage produces sequence groups (similar photo sequences).

        Returns:
            "sequences" to indicate this stage produces reviewable sequence groups
        """
        return "sequences"

    def has_review_data(self) -> bool:
        """Check if there are any sequence groups to review.

        Returns:
            True if forest has classes (multi-sequence groups), False otherwise
        """
        # Check if stage has run
        if not hasattr(self, "result") or self.result is None:
            return False

        # Check if there are any classes (multi-sequence groups)
        return any(seq.is_class() for seq in self.result)

    # Typed result field - just the forest
    result: list[PhotoSequence]
