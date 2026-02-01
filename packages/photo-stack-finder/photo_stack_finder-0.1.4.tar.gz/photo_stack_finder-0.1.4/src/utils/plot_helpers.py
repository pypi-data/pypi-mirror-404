"""Plotting utilities for benchmark analysis and visualization.

This module provides standardized plotting functions that encapsulate
matplotlib configuration and boilerplate, ensuring consistent visualization
across the codebase.

All functions save plots directly to files rather than displaying them,
making them suitable for automated analysis pipelines.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray


def save_histogram_comparison(
    pos_data: NDArray[np.float64],
    neg_data: NDArray[np.float64],
    threshold: float,
    method_name: str,
    output_path: Path,
) -> None:
    """Generate and save a histogram comparing similar/dissimilar distributions.

    Creates overlaid histograms showing the distribution of scores for
    similar pairs (pos_data) and dissimilar pairs (neg_data), with a
    vertical line indicating the decision threshold.

    Args:
        pos_data: Scores for similar pairs (positive class)
        neg_data: Scores for dissimilar pairs (negative class)
        threshold: Decision threshold to display as vertical line
        method_name: Name of the comparison method (for plot title)
        output_path: Path where the plot should be saved

    Note:
        Uses 50 bins and 50% transparency for overlapping histograms.
        The plot is saved and closed automatically.
    """
    plt.figure(figsize=(10, 6))
    plt.hist(pos_data, bins=50, alpha=0.5, label="Similar", color="green")
    plt.hist(neg_data, bins=50, alpha=0.5, label="Dissimilar", color="red")
    plt.axvline(threshold, color="black", linestyle="--", label="Threshold")
    plt.xlabel("Score")
    plt.ylabel("Frequency")
    plt.title(f"{method_name} - Score Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def save_correlation_heatmap(
    corr_matrix: pd.DataFrame,
    output_path: Path,
) -> None:
    """Generate and save a correlation heatmap for method comparison.

    Creates a heatmap showing correlation coefficients between different
    comparison methods, using a diverging colormap centered at zero.

    Args:
        corr_matrix: Square correlation matrix (DataFrame with method names as index/columns)
        output_path: Path where the plot should be saved

    Note:
        Uses 'coolwarm' colormap with values clamped to [-1, 1] range.
        Correlation values are annotated on the heatmap.
    """
    plt.figure(figsize=(12, 10))
    plt.imshow(corr_matrix, cmap="coolwarm", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(label="Correlation")
    plt.xticks(range(len(corr_matrix.columns)), list(corr_matrix.columns), rotation=90)
    plt.yticks(range(len(corr_matrix.index)), list(corr_matrix.index))
    plt.title("Method Correlation Matrix")

    # Annotate correlation values
    for i in range(len(corr_matrix.index)):
        for j in range(len(corr_matrix.columns)):
            value = corr_matrix.iloc[i, j]
            plt.text(j, i, f"{value:.2f}", ha="center", va="center", color="black")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def save_pca_scatter(
    x_pca: NDArray[np.float64],
    y_true: NDArray[np.int_],
    explained_variance: list[float],
    output_path: Path,
) -> None:
    """Generate and save a PCA scatter plot with class coloring.

    Creates a 2D scatter plot of the first two principal components,
    with points colored by their true class labels.

    Args:
        x_pca: PCA-transformed coordinates (n_samples x n_components, uses first 2)
        y_true: True class labels (0 for dissimilar, 1 for similar)
        explained_variance: Variance explained by each principal component (uses first 2)
        output_path: Path where the plot should be saved

    Note:
        Axis labels include the percentage of variance explained.
        Similar pairs are shown in green, dissimilar in red.
    """
    plt.figure(figsize=(10, 8))
    for label, color, name in [(1, "green", "Similar"), (0, "red", "Dissimilar")]:
        mask = y_true == label
        plt.scatter(x_pca[mask, 0], x_pca[mask, 1], c=color, label=name, alpha=0.5)

    plt.xlabel(f"PC1 ({explained_variance[0]:.1%} variance)")
    plt.ylabel(f"PC2 ({explained_variance[1]:.1%} variance)")
    plt.title("PCA: Method Scores by True Label")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
