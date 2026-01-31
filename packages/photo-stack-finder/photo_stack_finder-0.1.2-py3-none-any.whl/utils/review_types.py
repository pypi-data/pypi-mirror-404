"""Type definitions for review decision persistence."""

from __future__ import annotations

from typing import Literal, TypedDict

# Photo identifier using content hash + path (stable across runs)
PhotoIdentifier = tuple[str, str]  # (sha256, relative_path)


class IdenticalDecision(TypedDict):
    """Decision for an identical group."""

    type: Literal["identical"]
    group_id: str  # SHA256 of sorted photo sha256s
    timestamp: str  # ISO format
    user: str
    action: Literal["keep_all", "keep_exemplar", "delete_all", "custom"]
    kept_photos: list[PhotoIdentifier]  # Photos to keep (empty if keep_all)
    deleted_photos: list[PhotoIdentifier]  # Photos to delete (empty if keep_all)


class SequenceDecision(TypedDict):
    """Decision for a sequence similarity group."""

    type: Literal["sequences"]
    group_id: str  # SHA256 of template + sorted photo sha256s
    timestamp: str  # ISO format
    user: str
    action: Literal["approved", "rejected"]
    sequence_selections: dict[str, bool]  # sequence_name -> included
    deleted_photos: list[PhotoIdentifier]  # Individual photos marked for deletion
    deleted_rows: list[int]  # Row positions marked for deletion
    deleted_sequences: list[int]  # Sequence indices marked for deletion


class ReviewIndexEntry(TypedDict):
    """Entry in the review index (loaded from JSONL)."""

    group_id: str
    decision_type: Literal["identical", "sequences"]
    action: str
    timestamp: str
    user: str


class DeletionIndexEntry(TypedDict):
    """Entry in the deletion index."""

    sha256: str
    path: str
    reason: str  # "identical_group", "sequence_group", "individual"
    group_id: str
    timestamp: str
    user: str
