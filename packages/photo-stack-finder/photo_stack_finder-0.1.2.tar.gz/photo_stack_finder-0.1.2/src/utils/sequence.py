"""Sequence data structures for photo deduplication pipeline.

This module provides dict-based data structures that replace pandas for type safety
and pickle reliability, while maintaining minimal pandas usage for specific algorithms.

Core Types:
    INDEX_T: Type alias for tuple[str, ...], used as multi-field index keys
    PhotoFileSeries: dict[INDEX_T, PhotoFile] with template name and pd.Series-like API
    PhotoSequence: Hierarchical forest structure containing reference + similar sequences

Key Features:
    - Strong typing via dict inheritance (mypy strict compatible)
    - Template canonicalization with variable renaming
    - Index prefix folding and constant substitution
    - Efficient alignment algorithms for sequence comparison

Example Usage:
    >>> # Create a PhotoFileSeries from indexed photos
    >>> photos = {
    ...     ("IMG", "001"): PhotoFile(...),
    ...     ("IMG", "002"): PhotoFile(...),
    ... }
    >>> series = PhotoFileSeries(photos, name="prefix_{P0}_{P1}.jpg")
    >>> series.name  # Template after normalization
    'prefix_IMG_{P0}.jpg'
    >>> series.index  # Returns list[tuple[str, ...]]
    [("001",), ("002",)]

    >>> # Create a PhotoSequence (similarity class)
    >>> seq = PhotoSequence(series, sequences=[...], created_by="Perceptual Matching")
    >>> seq.is_class()  # True if has sub-sequences
    True
    >>> df = seq.to_dataframe()  # Convert to human-readable pandas DataFrame

Architecture:
    The forest structure represents hierarchical similarity:
    - PhotoSequence contains either:
        * A singleton (series only, no sequences)
        * A class (reference series + list of similar PhotoSequences)
    - Flattening produces reference + all leaf sequences for processing
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from os.path import commonprefix
from typing import Literal, TypeVar

import numpy as np
import numpy.typing as npt
import pandas as pd

from .comparison_gates import GateSequence
from .config import CONFIG
from .photo_file import PhotoFile

# Type alias for multi-field index keys used in PhotoFileSeries
# Each tuple element represents a field extracted from the filename pattern
# Example: ("IMG", "001", "2024") for template "prefix_{P0}_{P1}_{P2}.jpg"
# Variable-length tuple allows different sequences to have different numbers of fields
INDEX_T = tuple[str, ...]


class PhotoFileSeries(dict[INDEX_T, PhotoFile]):
    """Simple dict of PhotoFile with a name and other attributes to make it look enough like a pd.Series."""

    @staticmethod
    def _substitute_index_prefixes(series: dict[INDEX_T, PhotoFile], name: str) -> tuple[dict[INDEX_T, PhotoFile], str]:
        """Substitute common index prefixes and constants into template.

        Analyzes index fields to:
        1. Substitute constant fields (same value everywhere)
        2. Fold common prefixes of varying fields into the template

        Renumber variables so that they match up with the index tuples.

        Args:
            series: Simple PhotoFile series
            name: Template string with variable placeholders

        Returns:
            Tuple of (updated_template, kept_fields, prefixes_to_strip):
                - updated_template: Template with substitutions applied
                - new_indices: index list with constants removed and common prefixes removed

        """
        # Find common prefixes, remove them from index fields and build substitution map for template
        fmt_dict: dict[str, str] = {}
        strip_list: list[int] = []
        new_num: int = 0
        for field_idx, vals in enumerate(zip(*series.keys(), strict=True)):
            valist = list(vals)
            valset = set(vals)
            # Find common prefix across all indices
            prefs: str = commonprefix(valist)

            if len(valset) <= 1:
                fmt_dict[f"P{field_idx}"] = prefs
                strip_list.append(-1)
            else:
                fmt_dict[f"P{field_idx}"] = f"{prefs}{{P{new_num}}}"
                strip_list.append(len(prefs))
                new_num += 1

        # Apply substitutions to template
        substituted_template: str = name.format_map(fmt_dict)

        new_series = {
            tuple(idx[s:] for s, idx in zip(strip_list, idces, strict=False) if s >= 0): p
            for idces, p in series.items()
        }

        return new_series, substituted_template

    def __init__(self, data: dict[INDEX_T, PhotoFile], *, name: str, normal: bool = True):
        cls = self.__class__
        new_data, new_name = cls._substitute_index_prefixes(data, name) if normal else (data, name)
        super().__init__(new_data)
        self.name = new_name

    @property
    def index(self) -> list[INDEX_T]:
        """Make this look as much like a pd.Series as we need to."""
        return list(self.keys())

    def copy(self) -> PhotoFileSeries:
        """Make this look as much like a pd.Series as we need to."""
        # We don't want to call __init__ directly as we don't want to rerun the normalization.
        new_instance = self.__class__.__new__(self.__class__)
        dict.__init__(new_instance, self)  # Copy the internal dict structure
        new_instance.name = self.name  # Copy the name attribute
        return new_instance


# ==================== Template Processing Functions ====================


class VariableMapper(dict[str, str]):
    """Dict subclass that auto-assigns sequential variable names.

    When a variable placeholder like {P3} is accessed for the first time,
    it's automatically mapped to {P0}, {P1}, etc. in sequence.

    This allows template canonicalization where {P1}_{P3}.jpg becomes {P0}_{P1}.jpg.

    Attributes:
        num: Counter for next variable number to assign
    """

    def __init__(self) -> None:
        """Initialize with counter at 0 and no first position."""
        super().__init__()
        self.num: int = 0

    def __missing__(self, key: str) -> str:
        """Auto-assign sequential variable name when key not found.

        Adds non-printing characters around the variable so we can split later.

        Args:
            key: Original variable name (e.g., "P3")

        Returns:
            Canonicalized variable name (e.g., "{P0}")
        """
        result = f"\x1e{{P{self.num}}}\x1e"
        self[key] = result
        self.num += 1
        return result


def split_template(template: str) -> tuple[str, str, str]:
    """Takes a template, canonicalises the variable names and splits into the core which starts at the first variable and ends at the end of the last variable, the prefix before the core and the suffix after the core.  If there are no variables, the core is the entire template and the prefix/suffix are empty strings.

    Args:
        template: template to split

    Returns:
        template core, template prefix, template suffix

    """
    parts = re.split("\x1e", template.format_map(VariableMapper()))
    if len(parts) == 1:  # No variables found
        return template, "", ""
    return "".join(parts[1:-1]), parts[0], parts[-1]


# ==================== Index Processing Functions ====================


class PhotoSequence:
    """Class for photo sequences.

    series is a reference series with the union of indices and exemplar photo for all the sequences
    sequences is empty if there is nothing in the similarity class
    """

    def __init__(
        self,
        series: PhotoFileSeries,
        sequences: list[PhotoSequence] | None = None,
        created_by: str = "",
    ):
        """Initialize PhotoSequence with comprehensive template and index normalization.

        Performs multi-stage normalization to create a canonical representation:
        1. Substitute constants and common prefixes into template
        2. Strip constant fields and common prefixes from indices
        3. Renumber variables sequentially ({P0}, {P1}, ...) via split_template
        4. Split into prefix, remainder, suffix

        Template prefix is stored REVERSED for efficient commonprefix operations during
        subdivision (enables finding common suffixes via string reversal).

        Args:
                series: PhotoFileSeries representing the union/reference sequence
                sequences: List of PhotoFileSeries representing similar sequences
                created_by: Optional string indicating which stage created this class
                           (e.g., "Version Detection", "Index Overlap")
        """
        # Extract and process template from series name
        # Substitute common index prefixes and constants into template
        self.series = series

        # Extract constant prefix and suffix and split series.name (this also renumbers variables)
        self.template_remainder, self.template_prefix, self.template_suffix = split_template(self.series.name)

        # reverse this to help with rebinning large pattern bins
        self.reverse_prefix: str = self.template_prefix[::-1]

        self.sequences: list[PhotoSequence] = [] if sequences is None else sequences
        self.created_by: str = created_by

    @property
    def name(self) -> str:
        """Get the name of the reference sequence."""
        return self.series.name

    def get_reference(self) -> PhotoFileSeries:
        """Get the reference sequence for this object.

        Returns:
                PhotoFileSeries with index=position keys, values=PhotoFile objects
        """
        return self.series

    def is_class(self) -> bool:
        """Check if this is a class or a singleton.

        Returns:
                True if class, False if singleton
        """
        return len(self.sequences) != 0

    def flatten(self) -> tuple[PhotoFileSeries, list[PhotoFileSeries]]:
        """Flatten the hierarchical structure of the sequence.

        Returns:
                the reference series, the list of all leaf sequences that make up the class.
        """
        # Base case: if this is a singleton (leaf), return self in the result list
        if len(self.sequences) == 0:
            return self.series, [self.series]

        # Recursive case: collect all leaf sequences from children
        result: list[PhotoFileSeries] = []
        for s in self.sequences:
            _, ss = s.flatten()
            result.extend(ss)

        return self.series, result

    def __len__(self) -> int:
        """Return number of photos in sequence.

        Returns:
            Number of photos in sequence.
        """
        return len(self.series)

    def to_dataframe(self) -> pd.DataFrame:
        """Convert this PhotoSequence to DataFrame representation.

        Creates a DataFrame where:
        - Rows = position keys (union of all sequence indices)
        - Columns = sequence names
        - Values = PhotoFile | None (None for gaps where photo doesn't exist)

        This provides a natural 2D representation for sequence alignment, making
        it easy to iterate over positions and compare photos across sequences.

        For singleton sequences, returns a single-column DataFrame.

        Returns:
            DataFrame with position keys as index, sequence names as columns,
            PhotoFile|None as values
        """
        # Handle singleton (single sequence) - return single-column DataFrame
        if not self.is_class():
            df = pd.DataFrame({str(self.series.name): self.series})
            df.index.name = "position_key"
            df.attrs = {
                "reference_name": str(self.series.name),
                "created_by": self.created_by,
            }
            return df

        # Handle class (multiple sequences)
        reference: PhotoFileSeries
        version_seqs: list[PhotoFileSeries]
        reference, version_seqs = self.flatten()

        # Build DataFrame - pandas handles index union and gap filling automatically
        all_indices = sorted(set().union(*(seq.index for seq in version_seqs)))
        data = {str(seq.name): seq for seq in version_seqs}
        df = pd.DataFrame(data, index=all_indices)
        df.index.name = "position_key"

        # Store reference info in attrs for downstream use
        df.attrs = {
            "reference_name": str(reference.name),
            "created_by": self.created_by,
        }

        return df

    @property
    def n_ref_photos(self) -> int:
        """Number of reference photos in the series."""
        return len(self.series)

    @property
    def n_photos(self) -> int:
        """Total number of photos in the series."""
        if self.sequences:
            return sum(seq.n_photos for seq in self.sequences)
        return len(self.series)

    @property
    def n_seqs(self) -> int:
        """Total number of sequences in the tree.

        Returns:
            Total number of sequences in the tree.
        """
        return max(1, sum(s.n_seqs for s in self.sequences))


def predict_exemplar_sequence(sequences: list[PhotoSequence]) -> PhotoSequence:
    """Predict which sequence will provide the most reference exemplars.

    Strategy: For each index, find ALL "best" photos (highest quality).
    Give each sequence a point for each index where it has a best photo.
    The sequence with the most points is the exemplar sequence.

    Args:
            sequences: List of sequences to analyze

    Returns:
            Predicted exemplar sequence
    """
    seq_refs: list[PhotoFileSeries] = [seq.get_reference() for seq in sequences]

    photos_at_idx: dict[INDEX_T, list[PhotoFile]] = defaultdict(list)
    for seq in seq_refs:
        for idx_key, photo in seq.items():
            photos_at_idx[idx_key].append(photo)

    # For each index, find which sequences have best photos
    sequence_best_count: dict[int, int] = defaultdict(int)

    best_pixels: dict[INDEX_T, int] = {}
    best_size: dict[INDEX_T, int] = {}
    for idx, photos in photos_at_idx.items():
        # Find best quality (ignoring path/id tiebreakers)
        # Quality is (pixels, size_bytes) tuple
        best_quality: PhotoFile = max(photos, key=lambda p: (p.pixels, p.size_bytes))
        best_pixels[idx] = best_quality.pixels
        best_size[idx] = best_quality.size_bytes

    for i, ref in enumerate(seq_refs):
        for idx_key, p in ref.items():
            if p.pixels == best_pixels[idx_key] and p.size_bytes == best_size[idx_key]:
                sequence_best_count[i] += 1

    # Return sequence with most points
    # If tie, use sequence name as tiebreaker for stability (convert None to empty string)
    exemplar_idx: int = min(
        range(len(sequences)),
        key=lambda i: (
            -sequence_best_count[i],
            sequences[i].get_reference().name,
        ),
    )
    exemplar_seq: PhotoSequence = sequences[exemplar_idx]
    return exemplar_seq


def count_forest_ref_sequences(forest: list[PhotoSequence]) -> int:
    """Count reference sequences in a forest.

    For each PhotoSequence in the forest:
    - If it has children (is a group), count the children (the reference sequences that were grouped)
    - If it's a singleton (no children), count it as 1 (the sequence itself is the reference)

    This correctly handles the distinction between:
    - Container count: len(forest) - number of top-level PhotoSequence objects
    - Reference sequence count: the actual number of reference sequences represented

    Args:
        forest: List of PhotoSequence objects

    Returns:
        Total number of reference sequences in the forest
    """
    return sum(len(s.sequences) if s.sequences else 1 for s in forest)


def count_forest_ref_photos(forest: list[PhotoSequence]) -> int:
    """Count reference photos in a forest.

    Counts only the reference photos (exemplars) across all sequences,
    not including duplicate photos that have been identified.

    Args:
        forest: List of PhotoSequence objects

    Returns:
        Total number of reference photos across all sequences
    """
    return sum(s.n_ref_photos for s in forest)


def count_forest_total_photos(forest: list[PhotoSequence]) -> int:
    """Count total photos (including duplicates) in a forest.

    Counts all photos recursively, including:
    - Reference photos (exemplars)
    - Duplicate photos in version sequences
    - Photos in nested groups

    Args:
        forest: List of PhotoSequence objects

    Returns:
        Total number of all photos (references + duplicates) across all sequences
    """
    return sum(s.n_photos for s in forest)


# Type variable for element keys (e.g., int, str)
K = TypeVar("K", bound=int | str)

# Type for the alignment path: list of (index_x, index_y) tuples.
# -1 indicates a gap/omission.
COL_ALIGN_T = list[tuple[int, int]]

# Literal type for the alignment commands (moves): 0=Skip X, 1=Skip Y, 2=Match XY.
CMD_T = Literal[0, 1, 2]


def _align_columns(df_fields_list: list[pd.DataFrame]) -> tuple[int, COL_ALIGN_T]:
    """Orchestrates the column alignment DP, setting up initial costs and counters.

    Uses dynamic programming to find the optimal alignment of columns (fields) between
    two sequences, minimizing the cost of row deletions needed to make aligned columns
    have compatible value distributions.

    The algorithm explores three types of moves at each step:
    1. Skip field in X (insert gap in Y alignment)
    2. Skip field in Y (insert gap in X alignment)
    3. Match/align fields from both X and Y

    Args:
        df_fields_list: List of two DataFrames representing the normalized field values [X, Y].

    Returns:
        Tuple of (minimum_cost, optimal_alignment_path).
    """
    # Pre-processing: Convert each column (field) into a Counter of value frequencies
    # Pandas Series is iterable, so Counter can count values directly (no need for .to_dict())
    # Store as list to avoid x_/y_ duplication
    field_counts_list: list[list[Counter[int]]] = [
        [Counter(col_series) for _, col_series in df.items()] for df in df_fields_list
    ]
    field_lengths: list[int] = [len(counts) for counts in field_counts_list]

    # Initial limit is total number of rows (a safe upper bound for total deletions)
    pruning_limit: int = sum(field_lengths)

    # The recursive function is now nested and private to align_columns
    def align_columns_aux(
        field_indices: tuple[int, int],
        accumulated_cost: tuple[int, int],
        alignment_path_trace: COL_ALIGN_T,
        pruning_limit: int,
    ) -> tuple[int, COL_ALIGN_T]:
        """Recursive auxiliary function for column alignment using Dynamic Programming.

        This function is a closure and accesses the following variables from the
        enclosing '_align_columns' scope:
        field_counts_list, field_lengths.

        Args:
            field_indices: Current field index pointers (x_field_index, y_field_index).
            accumulated_cost: Accumulated cost of required row deletions: (x_deletions, y_deletions).
            alignment_path_trace: Current best alignment path trace.
            pruning_limit: abort if cost exceeds this value.

        Returns:
            Tuple of (minimum_accumulated_cost, optimal_path).
        """
        x_field_index, y_field_index = field_indices
        x_acc_cost, y_acc_cost = accumulated_cost
        total_acc_cost = sum(accumulated_cost)

        # Pruning: If accumulated cost exceeds the current best limit, stop this path.
        # This avoids exploring branches that cannot possibly improve the solution.
        if total_acc_cost > pruning_limit:
            return total_acc_cost, alignment_path_trace

        # Base case: Both sequences of fields are exhausted.
        if all(idx == length for idx, length in zip(field_indices, field_lengths, strict=True)):
            return total_acc_cost, alignment_path_trace

        # Stores the three possible moves and their new incremental costs
        possible_moves: list[tuple[CMD_T, tuple[int, int]]] = []

        # --- 1 & 2. Skip moves (symmetric for X and Y) ---
        # Skipping a field means treating it as a constant/gap in the alignment.
        # Cost is the number of rows we'd need to delete to make the field constant
        # (i.e., keep only the most common value).
        indices: list[int] = [x_field_index, y_field_index]
        costs: list[int] = [x_acc_cost, y_acc_cost]

        for i, (field_idx, field_len, field_counts, acc_cost) in enumerate(
            zip(indices, field_lengths, field_counts_list, costs, strict=True)
        ):
            if field_idx < field_len:
                current_counts = field_counts[field_idx]
                # Cost to simplify: delete all rows except those with the most common value
                cost_to_simplify = sum(current_counts.values()) - current_counts.most_common(1)[0][1]
                # Use max() because we track the maximum deletions needed across any single field
                skip_cost = max(acc_cost, cost_to_simplify)
                cost_tuple = (skip_cost, 0) if i == 0 else (0, skip_cost)
                move_cmd: CMD_T = 0 if i == 0 else 1
                possible_moves.append((move_cmd, cost_tuple))

        # --- 3. Move: Match X and Y Fields ---
        # Matching fields means aligning them. Cost is the deletions needed to make
        # their value distributions compatible (Counter subtraction gives the difference).
        if all(idx < length for idx, length in zip(indices, field_lengths, strict=True)):
            x_counts, y_counts = field_counts_list
            # Deletions needed: positive values from Counter subtraction indicate excess
            req_deletions_in_y = sum((y_counts[y_field_index] - x_counts[x_field_index]).values())
            req_deletions_in_x = sum((x_counts[x_field_index] - y_counts[y_field_index]).values())

            match_x_new_cost = max(x_acc_cost, req_deletions_in_x)
            match_y_new_cost = max(y_acc_cost, req_deletions_in_y)

            possible_moves.append((2, (match_x_new_cost, match_y_new_cost)))

        # Sort moves by total incremental cost to try the most promising option first
        # (greedy heuristic for pruning efficiency)
        possible_moves = sorted(possible_moves, key=lambda cmd_cost: sum(cmd_cost[1]))

        # Local, private function to execute the next step in the DP
        def align_columns_next(prog: tuple[CMD_T, tuple[int, int]], pruning_limit: int) -> tuple[int, COL_ALIGN_T]:
            """Executes the recursive call for a given command/cost combination."""
            cmd, (x_new_cost, y_new_cost) = prog

            new_accumulated_cost = (x_acc_cost + x_new_cost, y_acc_cost + y_new_cost)

            match cmd:
                case 0:
                    # Skip X (Gap in Y): Advance X pointer, leave Y unchanged
                    return align_columns_aux(
                        (x_field_index + 1, y_field_index),
                        new_accumulated_cost,
                        [*alignment_path_trace, (x_field_index, -1)],
                        pruning_limit,
                    )
                case 1:
                    # Skip Y (Gap in X): Advance Y pointer, leave X unchanged
                    return align_columns_aux(
                        (x_field_index, y_field_index + 1),
                        new_accumulated_cost,
                        [*alignment_path_trace, (-1, y_field_index)],
                        pruning_limit,
                    )
                case 2:
                    # Match/Mismatch Move: Advance both pointers (align these fields)
                    return align_columns_aux(
                        (x_field_index + 1, y_field_index + 1),
                        new_accumulated_cost,
                        [*alignment_path_trace, (x_field_index, y_field_index)],
                        pruning_limit,
                    )

        # Execute the best plan option first (lowest incremental cost)
        best_move = possible_moves[0]
        min_cost_found, alignment_path_trace = align_columns_next(best_move, pruning_limit)

        # Check remaining options, pruning paths that already exceed the current best cost
        for current_move in possible_moves[1:]:
            current_cost, current_path_trace = align_columns_next(current_move, min_cost_found)
            if current_cost < min_cost_found:
                min_cost_found, alignment_path_trace = current_cost, current_path_trace

        return min_cost_found, alignment_path_trace

    # Start the recursive DP alignment from the beginning of both sequences
    return align_columns_aux(
        field_indices=(0, 0),
        accumulated_cost=(0, 0),
        alignment_path_trace=[],
        pruning_limit=pruning_limit,
    )


def _get_constant_value_for_skipped_column(
    col_idx: int,
    df_fields: pd.DataFrame,
    row_tuples: list[tuple[int, ...]],
    rows_in_both: set[tuple[int, ...]],
    series_name: str,
    skip_idx: int,
) -> int:
    """Get constant value from a column if all matched rows have the same value.

    Args:
        col_idx: Column index in df_fields to check
        df_fields: DataFrame with field values
        row_tuples: List of row tuples from matched columns
        rows_in_both: Set of rows that exist in both series
        series_name: Name of series for error messages ("series_x" or "series_y")
        skip_idx: Skip index for error messages

    Returns:
        The constant integer value found in all matched rows

    Raises:
        ValueError: If matched rows have multiple different values
    """
    matched_indices: list[int] = [i for i, row_tuple in enumerate(row_tuples) if row_tuple in rows_in_both]
    matched_indices_array: npt.NDArray[np.intp] = np.array(matched_indices)
    values_at_col: pd.Series[int] = df_fields[col_idx].iloc[matched_indices_array]
    unique_values: npt.NDArray[np.intp] = values_at_col.unique()
    if len(unique_values) == 1:
        return int(unique_values[0])
    raise ValueError(
        f"Cannot fill skipped column {skip_idx} in {series_name}: "
        f"has multiple values {unique_values.tolist()} in matched rows"
    )


def _merge_sequences(
    gates: GateSequence,
    ref_list: list[tuple[INDEX_T, PhotoFile]],
    seq_list: list[tuple[INDEX_T, PhotoFile]],
) -> tuple[list[tuple[INDEX_T, PhotoFile]], dict[PhotoFile, tuple[int, float]], int, int, int]:
    """Merge two sorted sequences with similarity checking.

    Merges reference and sequence lists by comparing photos at matching indices.
    Performs early termination if too many mismatches are found.

    Early Termination Logic (Optimistic Accounting):
        hit_count tracks the OPTIMISTIC number of remaining successful matches we expect.
        It starts at intersection_size (assume all overlaps will pass) and decrements when:
        - A comparison FAILS (optimistic assumption was wrong)
        - A ref index has nothing to compare with (ridx < sidx: lose potential match)

        hit_count does NOT decrement when a comparison PASSES (optimistic assumption confirmed).

        miss_count tracks actual comparison failures, incrementing only when gates.compare() fails.

        Early termination triggers when: miss_count >= min(hit_count, MAX_MISMATCHES + 1)
        This means: "Even if all remaining optimistic matches succeed, we still have too many failures."

        CRITICAL: Only terminate when miss_count > 0 to avoid false positives when hit_count
        reaches 0 naturally (all potential matches processed successfully).

    Args:
        gates: Gate sequence for comparing photos
        ref_list: Sorted reference sequence (reverse order for efficient pop)
        seq_list: Sorted candidate sequence (reverse order for efficient pop)

    Returns:
        Tuple of:
        - new_ref: Merged sequence with all indices
        - sim: Similarity scores for overlapping photos
        - hit_count: Remaining expected hits (optimistic)
        - miss_count: Count of failed comparisons
        - overlap_count: Number of indices that overlapped

    Note:
        Returns early termination flag via overlap_count < 0 when mismatch threshold exceeded
    """
    new_ref: list[tuple[INDEX_T, PhotoFile]] = []

    # Initialize hit_count to intersection size to ensure early termination
    # works correctly when sequences have minimal overlap
    ref_indices = {idx for idx, _ in ref_list}
    seq_indices = {idx for idx, _ in seq_list}
    intersection = ref_indices & seq_indices
    hit_count: int = len(intersection)
    miss_count: int = 0
    overlap_count: int = 0
    sim: dict[PhotoFile, tuple[int, float]] = {}
    early_termination = False

    while ref_list and seq_list and not early_termination:
        ridx, rpic = ref_list[-1]
        sidx, spic = seq_list[-1]

        if ridx < sidx:
            new_ref.append(ref_list.pop())
            hit_count -= 1
            # Only terminate early if we've had actual mismatches
            if miss_count > 0 and miss_count >= min(hit_count, CONFIG.sequences.MAX_MISMATCHES + 1):
                early_termination = True
        elif sidx < ridx:
            new_ref.append(seq_list.pop())
        else:
            # Indices match - this is an overlap
            overlap_count += 1
            passes, _scores, final_score = gates.compare_with_rotation(rpic, spic, short_circuit=True)
            sim[spic] = (rpic.id, final_score)

            if not passes:
                # Comparison failed: decrement optimistic hit_count and increment miss_count
                hit_count -= 1
                miss_count += 1
                # Check early termination: can we still succeed given remaining potential matches?
                if miss_count >= min(hit_count, CONFIG.sequences.MAX_MISMATCHES + 1):
                    early_termination = True

            new_ref.append(ref_list.pop())
            seq_list.pop()

    # Signal early termination via negative overlap_count
    if early_termination:
        overlap_count = -1

    new_ref.extend(ref_list)
    new_ref.extend(seq_list)

    return new_ref, sim, hit_count, miss_count, overlap_count


def _validate_merged_indices(
    ref: PhotoFileSeries,
    seq: PhotoFileSeries,
    result: PhotoFileSeries,
    new_ref: list[tuple[INDEX_T, PhotoFile]],
) -> None:
    """Validate that merged sequence contains all indices from both inputs.

    This assertion catches bugs where indices get corrupted during merge.

    Args:
        ref: Original reference sequence
        seq: Original candidate sequence
        result: Merged sequence result
        new_ref: Raw list used to construct result (for debugging)

    Raises:
        AssertionError: If any indices are missing from the result
    """
    ref_indices = set(ref.keys())
    seq_indices = set(seq.keys())
    result_indices = set(result.keys())

    missing_from_ref = ref_indices - result_indices
    missing_from_seq = seq_indices - result_indices

    if missing_from_ref or missing_from_seq:
        error_msg = "extend_reference_sequence corrupted indices during merge:\n"
        error_msg += f"  Original ref indices: {sorted(ref_indices)}\n"
        error_msg += f"  Original seq indices: {sorted(seq_indices)}\n"
        error_msg += f"  Result indices: {sorted(result_indices)}\n"
        if missing_from_ref:
            error_msg += f"  Missing from ref: {sorted(missing_from_ref)}\n"
        if missing_from_seq:
            error_msg += f"  Missing from seq: {sorted(missing_from_seq)}\n"
        error_msg += f"  new_ref={new_ref}"
        raise AssertionError(error_msg)


def extend_reference_sequence(
    gates: GateSequence, ref: PhotoFileSeries, seq: PhotoFileSeries
) -> PhotoFileSeries | None:
    """Extend a reference sequence with a new sequence comparison.

    Uses the configured gate sequence from CONFIG.processing.COMPARISON_GATES
    to determine if sequences are similar. Gates handle caching and thresholding.

    Arguments:
        gates: sequence of gates for comparing photos
        ref: reference sequence
        seq: candidate similar sequence

    Returns:
        Updated photo series and a dictionary of comparison scores for all compared points.
        Returns (None, scores) if sequences are not similar enough.
    """
    # Sort in reverse so we can traverse from the ends of the lists using O(1) pop() rather than O(n) pop(0)
    ref_list: list[tuple[INDEX_T, PhotoFile]] = [
        (k, v) for k, v in sorted(ref.items(), key=lambda sp: sp[0], reverse=True)
    ]
    seq_list: list[tuple[INDEX_T, PhotoFile]] = [
        (k, v) for k, v in sorted(seq.items(), key=lambda sp: sp[0], reverse=True)
    ]

    # Track overlap to ensure minimum index overlap
    min_sequence_length: int = min(len(ref_list), len(seq_list))

    # Merge sequences with similarity checking
    new_ref, sim, _hit_count, _miss_count, overlap_count = _merge_sequences(gates, ref_list, seq_list)

    # Check for early termination (signaled by negative overlap_count)
    if overlap_count < 0:
        return None

    # Validate minimum overlap requirement
    # Require at least 50% of shorter sequence's indices to overlap
    min_overlap_required: int = max(1, min_sequence_length // 2)
    if overlap_count < min_overlap_required:
        return None

    # Store similarity scores in photo cache
    for spic, (ex, score) in sim.items():
        spic.cache["SEQUENCE_EXEMPLAR"] = ex
        spic.cache["SEQUENCE_SIMILARITY"] = score

    # Construct Series from separate indices and values for proper type inference
    # Preserve name from reference series
    result = PhotoFileSeries(dict(new_ref), name=ref.name, normal=False)

    # Validate that merged sequence contains all indices from both inputs
    _validate_merged_indices(ref, seq, result, new_ref)

    return result



# Moved to sequence_clustering.py to avoid circular import with review_utils
# Import from sequence_clustering instead: from .sequence_clustering import cluster_similar_sequences
