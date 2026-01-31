"""Benchmark utilities."""

from __future__ import annotations

import logging
import random
import time
from collections import defaultdict
from collections.abc import Iterable, Sequence
from itertools import combinations
from pathlib import Path
from typing import Any, cast

# --- Scientific Libraries ---
import matplotlib

# Use non-interactive backend to avoid GUI threading issues
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.stats import ttest_ind
from sklearn.decomposition import PCA
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.preprocessing import StandardScaler

# --- External Project Dependencies (MUST EXIST IN PROJECT) ---
# Replace/confirm these imports match your actual file structure
from .config import CONFIG
from .photo_file import PhotoFile
from .plot_helpers import save_correlation_heatmap, save_histogram_comparison, save_pca_scatter
from .report_builder import ReportBuilder
from .sequence import PhotoFileSeries, PhotoSequence

# ----------------------------
# -----------------------------------------------------------

# Type Aliases
type Pair = tuple[int, int]
type _R = dict[str, dict[Pair, float]]
type _Score = float


# --- Core Utility Functions ---


def _split_large_component(
    comp: set[int], graph: nx.Graph[int], max_size: int, pairs: Sequence[Pair]
) -> list[set[int]]:
    """Splits a large connected component (of pair indices) into smaller pieces using a greedy BFS approach.

    Constrains by unique photo count, not pair count.

    Args:
        comp: Set of pair indices to split
        graph: Graph where nodes are pair indices
        max_size: Maximum unique photos per piece
        pairs: Original pairs array to calculate photo counts

    Returns:
        List of smaller components (sets of pair indices)
    """

    # Helper to count unique photos in a component
    def count_photos(pair_indices: set[int]) -> int:
        return len(unique_ids_from_pairs([pairs[i] for i in pair_indices]))

    if count_photos(comp) <= max_size * 2:
        # Arbitrarily split in half if size is manageable
        comp_list: list[int] = list(comp)
        mid: int = len(comp_list) // 2
        return [set(comp_list[:mid]), set(comp_list[mid:])]

    subgraph: nx.Graph[int] = graph.subgraph(comp)
    pieces: list[set[int]] = []
    remaining: set[int] = set(comp)

    while remaining:
        start_node: int = next(iter(remaining))
        current_piece: set[int] = set()
        queue: list[int] = [start_node]

        # Grow piece up to max_size unique photos using BFS
        while queue and count_photos(current_piece) < max_size:
            node: int = queue.pop(0)
            if node in remaining:
                current_piece.add(node)
                remaining.remove(node)

                # Add neighbors to queue
                neighbor: int
                for neighbor in subgraph.neighbors(node):
                    if neighbor in remaining and neighbor not in queue:
                        queue.append(neighbor)

        pieces.append(current_piece)
    return pieces


def unique_ids_from_pairs(pairs: Iterable[Pair]) -> set[int]:
    """Utility function to collect unique IDs from a list of pairs."""
    u: set[int] = set()
    a: int
    b: int
    for a, b in pairs:
        u.add(a)
        u.add(b)
    return u


def generate_known_different_pairs(
    forest: list[PhotoSequence],
    n_pairs: int,
    seed: int,
) -> list[Pair]:
    """Generate high-quality known-different pairs using forest structure.

    Uses cross-template or distant-sequence sampling.
    """
    known_different: list[Pair] = []

    # 1. Derive template exemplars from the forest
    template_exemplars: dict[str, int] = {}
    for obj in forest:
        # Use hasattr checks to handle polymorphic PhotoSequence objects
        if hasattr(obj, "template_key") and hasattr(obj, "get_reference"):
            template_key = obj.template_key
            reference: PhotoFileSeries = obj.get_reference()

            if template_key and template_key not in template_exemplars and reference:
                first_key = next(iter(reference.keys()), None)
                if first_key is not None:
                    # PhotoFile is expected to have an .id attribute
                    exemplar: PhotoFile = reference[first_key]
                    template_exemplars[template_key] = exemplar.id

    # 2. Group templates by parent directory (assumed from template_key path structure)
    templates_by_parent: defaultdict[Path, list[str]] = defaultdict(list)
    for template_key in template_exemplars:
        parent: Path = Path(template_key).parent
        templates_by_parent[parent].append(template_key)

    # 3. Cross-parent pairing (high confidence negatives)
    for (_p1, t1_list), (_p2, t2_list) in combinations(templates_by_parent.items(), 2):
        for t1 in t1_list[:5]:
            for t2 in t2_list[:5]:
                if t1 in template_exemplars and t2 in template_exemplars:
                    known_different.append((template_exemplars[t1], template_exemplars[t2]))

    # 4. Distant sequence positions (high confidence negatives)
    for obj in forest:
        seq: PhotoFileSeries = obj.get_reference()
        sorted_indices: list[Any] = sorted(seq.index)
        for i in range(min(10, len(sorted_indices) // 2)):
            if i < len(sorted_indices) and -(i + 1) >= -len(sorted_indices):
                known_different.append((seq[sorted_indices[i]].id, seq[sorted_indices[-(i + 1)]].id))

    rng: random.Random = random.Random(seed)
    rng.shuffle(known_different)
    return known_different[:n_pairs]


def generate_benchmark_pairs(
    forest: list[PhotoSequence],
    # Included for consistency, though not directly used
    n_different: int,
    seed: int,
) -> tuple[list[Pair], list[Pair], list[int]]:
    """Generates similar (positive) and known-different (negative) photo pairs.

    Extracts pairs from the forest structure based on sequence relationships.
    """
    # 1. Generate similar (positive) pairs
    positive_pairs: list[Pair] = []
    for obj in forest:
        if hasattr(obj, "get_reference"):
            reference: PhotoFileSeries = obj.get_reference()
            sequences: list[PhotoSequence] = obj.sequences

            for idx, exemplar in reference.items():
                positive_pairs.extend(
                    [
                        (exemplar.id, seq.get_reference()[idx].id)
                        for seq in sequences
                        if idx in seq.get_reference() and exemplar.id != seq.get_reference()[idx].id
                    ]
                )

    # 2. Generate known-different (negative) pairs
    n_diff_limit: int = min(len(positive_pairs), n_different)
    different_pairs: list[Pair] = generate_known_different_pairs(
        forest=forest,
        n_pairs=n_diff_limit,
        seed=seed,
    )

    # 3. Determine unique IDs
    unique_ids: list[int] = sorted(unique_ids_from_pairs(positive_pairs + different_pairs))

    return positive_pairs, different_pairs, unique_ids


def _separate_components_by_size(
    components: list[set[int]],
    max_cluster_size: int,
    pairs: Sequence[Pair],
) -> tuple[list[set[int]], list[set[int]], list[set[int]]]:
    """Separate components into small, medium, and large based on photo count.

    Args:
        components: Connected components (sets of pair indices)
        max_cluster_size: Maximum photos per cluster
        pairs: Original pairs list

    Returns:
        Tuple of (small_components, medium_components, large_components)
        - small: photo_count <= max_cluster_size
        - medium: max_cluster_size < photo_count <= max_cluster_size * 2
        - large: photo_count > max_cluster_size * 2
    """
    small_components: list[set[int]] = []
    medium_components: list[set[int]] = []
    large_components: list[set[int]] = []

    for comp in components:
        photo_count = len(unique_ids_from_pairs([pairs[i] for i in comp]))
        if photo_count <= max_cluster_size:
            small_components.append(comp)
        elif photo_count > max_cluster_size * 2:
            large_components.append(comp)
        else:
            medium_components.append(comp)

    return small_components, medium_components, large_components


def _combine_small_components(
    components: list[set[int]],
    max_cluster_size: int,
    pairs: Sequence[Pair],
) -> list[set[int]]:
    """Greedily combine small components to maximize cluster utilization.

    Uses a two-pointer approach: large components on the left, small on the right.
    Fills each cluster starting with the largest component, then adds smaller ones.

    Args:
        components: Components to combine (assumed pre-sorted by size descending)
        max_cluster_size: Maximum photos per cluster
        pairs: Original pairs list

    Returns:
        List of combined clusters (as sets of pair indices)
    """
    if not components:
        return []

    pair_clusters: list[set[int]] = []
    left_idx: int = 0
    right_idx: int = len(components) - 1

    while left_idx <= right_idx:
        current_cluster: set[int] = set(components[left_idx])
        current_photo_count = len(unique_ids_from_pairs([pairs[i] for i in current_cluster]))
        left_idx += 1

        while right_idx >= left_idx:
            candidate_photo_count = len(unique_ids_from_pairs([pairs[i] for i in components[right_idx]]))
            if current_photo_count + candidate_photo_count <= max_cluster_size:
                current_cluster.update(components[right_idx])
                current_photo_count += candidate_photo_count
                right_idx -= 1
            else:
                break

        pair_clusters.append(current_cluster)

    return pair_clusters


def cluster_pairs_for_scoring(pairs: Sequence[Pair], max_cluster_size: int) -> list[tuple[set[int], list[Pair]]]:
    """Clusters a list of pairs into connected components of limited size.

    Constrains by unique photo count, not pair count, to respect memory limits.

    Args:
        pairs: List of photo ID pairs to cluster
        max_cluster_size: Maximum unique photos per cluster (memory constraint)

    Returns:
        List of (cluster_photos, cluster_pairs) tuples
    """
    # 1. Build graph where nodes are pair indices
    graph: nx.Graph[int] = nx.Graph()
    graph.add_nodes_from(range(len(pairs)))

    # Connect nodes (pairs) that share a photo ID
    for i in range(len(pairs)):
        for j in range(i + 1, len(pairs)):
            if set(pairs[i]) & set(pairs[j]):
                graph.add_edge(i, j)

    # 2. Get initial connected components
    components: list[set[int]] = list(nx.connected_components(graph))

    # 3. Separate and split components by PHOTO count (not pair count)
    small_components, medium_components, large_components = _separate_components_by_size(
        components, max_cluster_size, pairs
    )

    # Split large components into manageable pieces
    split_pieces: list[set[int]] = []
    for comp in large_components:
        pieces: list[set[int]] = _split_large_component(comp, graph, max_cluster_size, pairs)
        split_pieces.extend(pieces)

    # Merge all processable components
    small_components.extend(split_pieces)
    small_components.extend(medium_components)

    # 4. Sort by photo count descending for optimal packing
    small_components.sort(
        key=lambda c: len(unique_ids_from_pairs([pairs[i] for i in c])),
        reverse=True,
    )

    # 5. Greedy combination for final clusters (by PHOTO count)
    pair_clusters = _combine_small_components(small_components, max_cluster_size, pairs)

    # 6. Convert indices to pairs
    result: list[tuple[set[int], list[Pair]]] = []
    for pair_indices in pair_clusters:
        cluster_pairs: list[Pair] = [pairs[i] for i in pair_indices]
        cluster_photos: set[int] = unique_ids_from_pairs(cluster_pairs)
        result.append((cluster_photos, cluster_pairs))

    return result


# --- Analysis Functions ---


def calculate_metrics_at_best_threshold(y_true: NDArray[Any], y_scores: NDArray[Any]) -> dict[str, float]:
    """Calculates metrics by finding the optimal threshold closest to a target FPR.

    Target False Positive Rate (FPR) is 0.01.
    """
    target_fpr = 0.01

    # roc_curve expects positive class to have higher score, which is true for similarity
    fpr, _tpr, thresholds = roc_curve(y_true, y_scores)

    # Find the threshold closest to the target FPR
    diff = fpr - target_fpr
    optimal_idx = np.argmin(np.abs(diff))
    best_threshold = thresholds[optimal_idx]

    y_pred = (y_scores >= best_threshold).astype(int)

    auc = roc_auc_score(y_true, y_scores)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)

    # Confusion matrix values
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    return {
        "auc": float(auc),
        "threshold": float(best_threshold),
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "tpr_at_threshold": float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0,
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "fpr_at_threshold": float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0,
    }


def evaluate_consensus_strategy(df_scores: pd.DataFrame, y_true: NDArray[Any]) -> tuple[str, dict[str, float]]:
    """Evaluates the median consensus strategy."""
    median_scores = cast(NDArray[Any], df_scores.median(axis=1).values)
    metrics = calculate_metrics_at_best_threshold(y_true, median_scores)
    return "Median", metrics


def evaluate_voting_strategy(df_scores: pd.DataFrame, y_true: NDArray[Any]) -> tuple[str, dict[str, float]]:
    """Evaluates a balanced voting strategy using majority vote.

    Finds the best single-method thresholds and applies majority voting.
    """
    method_thresholds = {}
    for method in df_scores.columns:
        method_values = cast(NDArray[Any], df_scores[method].values)
        metrics = calculate_metrics_at_best_threshold(y_true, method_values)
        method_thresholds[method] = metrics["threshold"]

    # Vote for similarity if score >= individual method's optimal threshold
    votes_df = pd.DataFrame()
    for method, threshold in method_thresholds.items():
        method_values = cast(NDArray[Any], df_scores[method].values)
        votes_df[method] = (method_values >= threshold).astype(int)

    # Final score is the mean vote (a value between 0.0 and 1.0)
    voting_scores = cast(NDArray[Any], votes_df.mean(axis=1).values)

    # Use a fixed threshold of 0.5 for the voting mean to get final prediction
    y_pred = (voting_scores >= 0.5).astype(int)

    auc = roc_auc_score(y_true, voting_scores)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)

    return "Majority Vote", {
        "auc": float(auc),
        "threshold": 0.5,
        "f1": float(f1),
        "precision": float(precision),
        "recall": float(recall),
        "tpr_at_threshold": float(recall),
        "tp": int(np.sum((y_true == 1) & (y_pred == 1))),
        "tn": int(np.sum((y_true == 0) & (y_pred == 0))),
        "fp": int(np.sum((y_true == 0) & (y_pred == 1))),
        "fn": int(np.sum((y_true == 1) & (y_pred == 0))),
        "fpr_at_threshold": float(np.sum((y_true == 0) & (y_pred == 1)) / np.sum(y_true == 0)),
    }


def _prepare_benchmark_data(
    final_scores: _R,
    positive_pairs: list[Pair],
    different_pairs: list[Pair],
) -> tuple[pd.DataFrame, NDArray[np.int_]]:
    """Prepare score DataFrame and ground truth labels.

    Args:
        final_scores: Dict mapping method names to pair scores
        positive_pairs: List of similar photo pairs
        different_pairs: List of dissimilar photo pairs

    Returns:
        Tuple of (score_dataframe, y_true_labels)

    Raises:
        ValueError: If no valid pairs remain after dropping NaNs
    """
    all_pairs: list[Pair] = positive_pairs + different_pairs

    score_data = {method: [final_scores[method][pair] for pair in all_pairs] for method in final_scores}
    df_scores = pd.DataFrame(score_data, index=pd.MultiIndex.from_tuples(all_pairs, names=["photo_a", "photo_b"]))
    df_scores = df_scores.dropna()

    if len(df_scores) == 0:
        raise ValueError("No valid pairs remain after dropping NaNs")

    # Align y_true for the pairs that remain (iterate in order to preserve alignment)
    is_positive_mask = [pair in positive_pairs for pair in df_scores.index]
    y_true = np.array(is_positive_mask, dtype=int)

    return df_scores, y_true


def _calculate_method_metrics(
    df_scores: pd.DataFrame,
    y_true: NDArray[np.int_],
) -> tuple[dict[str, dict[str, float]], tuple[str, dict[str, float]], dict[str, dict[str, NDArray[Any]]]]:
    """Calculate performance metrics for each method.

    Args:
        df_scores: DataFrame with method scores
        y_true: Ground truth labels

    Returns:
        Tuple of (method_metrics, best_single_method, plot_data)
    """
    method_metrics: dict[str, dict[str, float]] = {}
    best_single_method: tuple[str, dict[str, float]] = ("", {"f1": -1.0})
    plot_data: dict[str, dict[str, NDArray[Any]]] = {}

    for method in df_scores.columns:
        y_scores: NDArray[Any] = cast(NDArray[Any], df_scores[method].values)

        metrics = calculate_metrics_at_best_threshold(y_true, y_scores)
        method_metrics[method] = metrics

        if metrics["f1"] > best_single_method[1]["f1"]:
            best_single_method = (method, metrics)

        pos_scores = y_scores[y_true == 1]
        neg_scores = y_scores[y_true == 0]
        plot_data[method] = {"pos": pos_scores, "neg": neg_scores}

        # Calculate Effect Size (Cohen's d) and statistical significance
        cohen_d = (np.mean(pos_scores) - np.mean(neg_scores)) / np.sqrt(
            (np.std(pos_scores, ddof=1) ** 2 + np.std(neg_scores, ddof=1) ** 2) / 2
        )
        ttest_result = ttest_ind(pos_scores, neg_scores, equal_var=False)
        method_metrics[method]["cohen_d"] = float(cohen_d)
        method_metrics[method]["p_value"] = float(ttest_result.pvalue)

    return method_metrics, best_single_method, plot_data


def _analyze_method_correlations(
    df_scores: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Analyze correlations between methods.

    Args:
        df_scores: DataFrame with method scores

    Returns:
        Tuple of (correlation_matrix, independence_scores)
    """
    corr_matrix = df_scores.corr(method="pearson")

    # Remove diagonal (self-correlation)
    for method in corr_matrix.columns:
        corr_matrix.loc[method, method] = np.nan

    # Calculate independence (lower correlation = more independent)
    independent_methods = corr_matrix.abs().mean(axis=1).sort_values().to_dict()

    return corr_matrix, independent_methods


def _generate_visualizations(
    df_scores: pd.DataFrame,
    y_true: NDArray[np.int_],
    method_metrics: dict[str, dict[str, float]],
    plot_data: dict[str, dict[str, NDArray[Any]]],
    corr_matrix: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Generate all benchmark visualization plots.

    Args:
        df_scores: DataFrame with method scores
        y_true: Ground truth labels
        method_metrics: Metrics for each method
        plot_data: Positive/negative score distributions
        corr_matrix: Method correlation matrix
        output_dir: Directory to save plots
    """
    plt.style.use("ggplot")

    # Distribution histograms for each method
    for method in df_scores.columns:
        save_histogram_comparison(
            pos_data=plot_data[method]["pos"],
            neg_data=plot_data[method]["neg"],
            threshold=method_metrics[method]["threshold"],
            method_name=method,
            output_path=output_dir / f"distribution_{method}.png",
        )

    # Correlation heatmap
    save_correlation_heatmap(
        corr_matrix=corr_matrix.fillna(0),
        output_path=output_dir / "correlation_heatmap.png",
    )

    # PCA dimensionality reduction (with graceful fallback)
    try:
        scaler = StandardScaler()
        x_scaled = scaler.fit_transform(df_scores.values)
        pca = PCA(n_components=min(len(df_scores.columns), 3))
        x_pca = pca.fit_transform(x_scaled)

        save_pca_scatter(
            x_pca=x_pca,
            y_true=y_true,
            explained_variance=pca.explained_variance_ratio_.tolist(),
            output_path=output_dir / "pca_plot.png",
        )
    except Exception as e:
        logging.warning(f"PCA failed: {e}")


def _evaluate_ensemble_strategies(
    df_scores: pd.DataFrame,
    y_true: NDArray[np.int_],
) -> tuple[tuple[str, dict[str, float]], tuple[str, dict[str, float]]]:
    """Evaluate consensus and voting ensemble strategies.

    Args:
        df_scores: DataFrame with method scores
        y_true: Ground truth labels

    Returns:
        Tuple of (best_consensus, best_voting)
    """
    best_consensus: tuple[str, dict[str, float]] = evaluate_consensus_strategy(df_scores, y_true)
    best_voting: tuple[str, dict[str, float]] = evaluate_voting_strategy(df_scores, y_true)
    return best_consensus, best_voting


def _generate_analysis_report(
    method_metrics: dict[str, dict[str, float]],
    best_single_method: tuple[str, dict[str, float]],
    best_voting: tuple[str, dict[str, float]],
    best_consensus: tuple[str, dict[str, float]],
    independent_methods: dict[str, float],
    n_rows: int,
    y_true: NDArray[np.int_],
) -> str:
    """Generate formatted analysis report using ReportBuilder.

    Args:
        method_metrics: Performance metrics for each method
        best_single_method: Best performing single method
        best_voting: Best voting ensemble strategy
        best_consensus: Best consensus ensemble strategy
        independent_methods: Method independence scores
        n_rows: Total number of pairs scored
        y_true: Ground truth labels

    Returns:
        Formatted report string
    """
    sorted_methods = sorted(method_metrics.items(), key=lambda item: item[1].get("f1", -1.0), reverse=True)

    report = (
        ReportBuilder()
        .add_title("PHOTO BENCHMARK ANALYSIS REPORT")
        .add_text(f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        .add_text(f"Total Pairs Scored: {n_rows} (Similar: {np.sum(y_true == 1)}, Dissimilar: {np.sum(y_true == 0)})")
        .add_section("1. INDIVIDUAL METHOD PERFORMANCE")
    )

    # Add metrics for each method
    for method, metrics in sorted_methods:
        report.add_text(f"Method: {method}")
        report.add_text(f"  AUC: {metrics['auc']:.4f}")
        report.add_text(f"  Optimal Threshold (at 1% FPR target): {metrics['threshold']:.4f}")
        report.add_text(f"  F1 Score: {metrics['f1']:.4f}")
        report.add_text(f"  Precision: {metrics['precision']:.4f}")
        report.add_text(f"  Recall/TPR: {metrics['recall']:.4f}")
        report.add_text(f"  Effect Size (Cohen's d): {metrics.get('cohen_d', 'N/A'):.3f}")
        report.add_blank_line()

    # Add recommendations
    report.add_section("2. RECOMMENDATIONS")
    report.add_text("Option A: Best Single Method (highest performance)")
    report.add_text(f"  Use {best_single_method[0]} with threshold > {best_single_method[1]['threshold']:.4f}")
    report.add_text(
        f"  Performance: F1={best_single_method[1]['f1']:.4f}, "
        f"Precision={best_single_method[1]['precision']:.4f}, "
        f"Recall={best_single_method[1]['recall']:.4f}"
    )
    report.add_blank_line()

    report.add_text("Option B: Voting Strategy (balanced ensemble)")
    report.add_text(f"  Use {best_voting[0]}")
    report.add_text(
        f"  Performance: F1={best_voting[1]['f1']:.4f}, "
        f"Precision={best_voting[1]['precision']:.4f}, "
        f"Recall={best_voting[1]['recall']:.4f}"
    )
    report.add_blank_line()

    report.add_text("Option C: Consensus Median (most robust ensemble)")
    report.add_text(f"  Use median score > {best_consensus[1]['threshold']:.4f}")
    report.add_text(
        f"  Performance: F1={best_consensus[1]['f1']:.4f}, "
        f"Precision={best_consensus[1]['precision']:.4f}, "
        f"Recall={best_consensus[1]['recall']:.4f}"
    )
    report.add_blank_line()

    # Add independence analysis
    report.add_section("3. METHOD INDEPENDENCE (for ensemble)")
    report.add_text("Most independent methods (lowest average absolute correlation):")
    for method, avg_corr_val in independent_methods.items():
        report.add_text(f"  • {method}: avg |r|={avg_corr_val:.3f}")

    return report.build()


def _analyze_cascades(
    df_scores: pd.DataFrame,
    y_true: NDArray[np.int_],
    method_metrics: dict[str, dict[str, float]],
    output_dir: Path,
) -> None:
    """Test specific cascade combinations and save results.

    Args:
        df_scores: DataFrame with method scores
        y_true: Ground truth labels
        method_metrics: Performance metrics for each method
        output_dir: Directory to save results
    """
    # Only run if all required methods are present
    if not all(method in df_scores.columns for method in ["dhash", "ssim", "sift"]):
        logging.info("Skipping cascade analysis - required methods (dhash, ssim, sift) not all present")
        return

    cascade_results = []

    # Test: dhash only
    dhash_only = df_scores["dhash"] > method_metrics["dhash"]["threshold"]
    cascade_results.append(
        {
            "cascade": "dhash_only",
            "f1": f1_score(y_true, dhash_only),
            "precision": precision_score(y_true, dhash_only),
            "recall": recall_score(y_true, dhash_only),
        }
    )

    # Test: dhash → ssim (current cascade)
    dhash_pass = df_scores["dhash"] > method_metrics["dhash"]["threshold"]
    ssim_pass = df_scores["ssim"] > method_metrics["ssim"]["threshold"]
    current_cascade = dhash_pass & ssim_pass
    cascade_results.append(
        {
            "cascade": "dhash_AND_ssim",
            "f1": f1_score(y_true, current_cascade),
            "precision": precision_score(y_true, current_cascade),
            "recall": recall_score(y_true, current_cascade),
        }
    )

    # Test: dhash → sift (independent cascade)
    sift_pass = df_scores["sift"] > method_metrics["sift"]["threshold"]
    independent_cascade = dhash_pass & sift_pass
    cascade_results.append(
        {
            "cascade": "dhash_AND_sift",
            "f1": f1_score(y_true, independent_cascade),
            "precision": precision_score(y_true, independent_cascade),
            "recall": recall_score(y_true, independent_cascade),
        }
    )

    # Save cascade analysis
    df_cascade = pd.DataFrame(cascade_results)
    df_cascade.to_csv(output_dir / CONFIG.paths.CASCADE_COMPARISON, index=False)
    logging.info(f"Cascade comparison saved to {output_dir / CONFIG.paths.CASCADE_COMPARISON}")


def post_analysis(
    final_scores: _R,
    positive_pairs: list[Pair],
    different_pairs: list[Pair],
    output_dir: Path,
) -> None:
    """Performs the full benchmark analysis and generates reports.

    Includes metrics calculation, correlation analysis, ensemble evaluation, plotting, and report generation.
    """
    logging.info("Starting post-analysis phase.")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Prepare data
    try:
        df_scores, y_true = _prepare_benchmark_data(final_scores, positive_pairs, different_pairs)
    except ValueError as e:
        logging.error(f"Data preparation failed: {e}. Aborting analysis.")
        return

    # Save pair-level scores and ground truth for outlier analysis
    df_scores.to_csv(output_dir / CONFIG.paths.PAIR_SCORES)
    pair_ground_truth = pd.DataFrame(
        {
            "photo_a": [pair[0] for pair in df_scores.index],
            "photo_b": [pair[1] for pair in df_scores.index],
            "ground_truth": ["similar" if is_pos else "dissimilar" for is_pos in (y_true == 1)],
        }
    )
    pair_ground_truth.to_csv(output_dir / CONFIG.paths.PAIR_GROUND_TRUTH, index=False)
    logging.info(
        f"Saved {len(df_scores)} pair-level scores to {CONFIG.paths.PAIR_SCORES} and {CONFIG.paths.PAIR_GROUND_TRUTH}"
    )

    # 2. Calculate individual method metrics
    method_metrics, best_single_method, plot_data = _calculate_method_metrics(df_scores, y_true)

    # 3. Analyze correlations and independence
    corr_matrix, independent_methods = _analyze_method_correlations(df_scores)

    # 4. Evaluate ensemble strategies
    best_consensus, best_voting = _evaluate_ensemble_strategies(df_scores, y_true)

    # 5. Generate visualizations
    _generate_visualizations(df_scores, y_true, method_metrics, plot_data, corr_matrix, output_dir)

    # 6. Generate analysis report
    report_text = _generate_analysis_report(
        method_metrics,
        best_single_method,
        best_voting,
        best_consensus,
        independent_methods,
        len(df_scores),
        y_true,
    )
    report_file = output_dir / CONFIG.paths.ANALYSIS_RECOMMENDATIONS
    report_file.write_text(report_text, encoding="utf-8")

    # 7. Analyze cascade combinations
    _analyze_cascades(df_scores, y_true, method_metrics, output_dir)

    # 8. Save derived data to CSV
    df_metrics = pd.DataFrame(method_metrics).T
    df_metrics.to_csv(output_dir / CONFIG.paths.METHOD_METRICS)
    corr_matrix.to_csv(output_dir / CONFIG.paths.METHOD_CORRELATIONS)

    logging.info(f"Analysis complete. Report written to {report_file}")
