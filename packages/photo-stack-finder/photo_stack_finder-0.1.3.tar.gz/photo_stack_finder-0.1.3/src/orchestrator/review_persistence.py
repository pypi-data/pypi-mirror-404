"""Functions for persisting and loading review decisions."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from utils.review_types import (
    DeletionIndexEntry,
    IdenticalDecision,
    PhotoIdentifier,
    ReviewIndexEntry,
    SequenceDecision,
)


def append_decision_to_log(decision: IdenticalDecision | SequenceDecision, work_dir: Path) -> None:
    """Append a review decision to the JSONL log.

    Args:
        decision: Decision object (IdenticalDecision or SequenceDecision)
        work_dir: Work directory containing the log file
    """
    log_path: Path = work_dir / "review_decisions.jsonl"

    # Ensure work directory exists
    work_dir.mkdir(parents=True, exist_ok=True)

    # Append decision as JSON line
    with log_path.open("a", encoding="utf-8") as f:
        json.dump(decision, f, ensure_ascii=False)
        f.write("\n")


def build_review_index(work_dir: Path) -> dict[str, Any]:
    """Build in-memory indices from JSONL log and generate CSV files.

    Reads review_decisions.jsonl and creates:
    - review_index_identical.csv: identical group decisions
    - review_index_sequences.csv: sequence group decisions
    - review_index_deletions.csv: individual photo deletions

    Args:
        work_dir: Work directory containing the log file

    Returns:
        Dictionary with 'identical', 'sequences', and 'deletions' indices
    """
    log_path: Path = work_dir / "review_decisions.jsonl"

    if not log_path.exists():
        # No decisions yet, return empty indices
        return {"identical": {}, "sequences": {}, "deletions": {}}

    # Parse JSONL log
    identical_index: dict[str, ReviewIndexEntry] = {}
    sequences_index: dict[str, ReviewIndexEntry] = {}
    deletions_index: dict[PhotoIdentifier, DeletionIndexEntry] = {}

    with log_path.open(encoding="utf-8") as f:
        for _line_num, raw_line in enumerate(f, 1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                decision: dict[str, Any] = json.loads(line)
                decision_type: str | None = decision.get("type")

                if decision_type == "identical":
                    # Index identical group decision
                    group_id: str = decision["group_id"]
                    identical_index[group_id] = {
                        "group_id": group_id,
                        "decision_type": "identical",
                        "action": decision["action"],
                        "timestamp": decision["timestamp"],
                        "user": decision["user"],
                    }

                    # Index deletions
                    deleted_photos: list[tuple[str, str]] = decision.get("deleted_photos", [])
                    sha256: str
                    path: str
                    for sha256, path in deleted_photos:
                        deletions_index[(sha256, path)] = {
                            "sha256": sha256,
                            "path": path,
                            "reason": "identical_group",
                            "group_id": group_id,
                            "timestamp": decision["timestamp"],
                            "user": decision["user"],
                        }

                elif decision_type == "sequences":
                    # Index sequence group decision
                    seq_group_id: str = decision["group_id"]
                    sequences_index[seq_group_id] = {
                        "group_id": seq_group_id,
                        "decision_type": "sequences",
                        "action": decision["action"],
                        "timestamp": decision["timestamp"],
                        "user": decision["user"],
                    }

                    # Index deletions
                    seq_deleted_photos: list[tuple[str, str]] = decision.get("deleted_photos", [])
                    seq_sha256: str
                    seq_path: str
                    for seq_sha256, seq_path in seq_deleted_photos:
                        deletions_index[(seq_sha256, seq_path)] = {
                            "sha256": seq_sha256,
                            "path": seq_path,
                            "reason": "sequence_group",
                            "group_id": seq_group_id,
                            "timestamp": decision["timestamp"],
                            "user": decision["user"],
                        }

            except json.JSONDecodeError:
                continue

    # Write CSV indices
    _write_csv_index(
        work_dir / "review_index_identical.csv",
        identical_index.values(),
        ["group_id", "decision_type", "action", "timestamp", "user"],
    )

    _write_csv_index(
        work_dir / "review_index_sequences.csv",
        sequences_index.values(),
        ["group_id", "decision_type", "action", "timestamp", "user"],
    )

    _write_csv_index(
        work_dir / "review_index_deletions.csv",
        deletions_index.values(),
        ["sha256", "path", "reason", "group_id", "timestamp", "user"],
    )

    return {
        "identical": identical_index,
        "sequences": sequences_index,
        "deletions": deletions_index,
    }


def _write_csv_index(path: Path, rows: list[dict[str, Any]] | Any, fieldnames: list[str]) -> None:
    """Write index data to CSV file.

    Args:
        path: Output CSV file path
        rows: Iterable of dictionaries to write
        fieldnames: CSV column names
    """
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
