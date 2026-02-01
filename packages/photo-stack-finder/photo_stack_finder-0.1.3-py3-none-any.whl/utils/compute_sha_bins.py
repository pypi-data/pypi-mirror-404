from __future__ import annotations

import mimetypes
import os
from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from photo_compare import file_sha256

from .config import CONFIG
from .photo_file import PhotoFile
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import OutputPort


class ComputeShaBins(PipelineStage[tuple[int, tuple[Path, str]], tuple[PhotoFile, str], dict[str, list[PhotoFile]]]):
    """Pipeline stage that walks source directory and bins photos by SHA256 hash.

    Creates PhotoFile objects with minimal core properties (path, mime, size_bytes)
    computed from file metadata only - NO image opening! SHA256 is computed from
    file contents and used for binning, then discarded. All image-derived properties
    (pixels, dimensions, EXIF) are computed lazily when first accessed.
    """

    def __init__(self, source_path: Path) -> None:
        """Initialize SHA256 binning stage.

        Args:
            source_path: Root directory to scan for images
        """
        super().__init__(
            path=CONFIG.paths.sha_bins_pkl,
            stage_name="Directory Walk",
        )
        # Store input
        self.source_path = source_path
        self.args = source_path

        # Create output ports
        self.sha_bins_o: OutputPort[dict[str, list[PhotoFile]]] = OutputPort(self, getter=lambda: self.result)
        self.photofiles_o: OutputPort[dict[int, PhotoFile]] = OutputPort(self, getter=lambda: self.photofiles)

    def prepare(
        self,
    ) -> PrepareResult[tuple[int, tuple[Path, str]], dict[str, list[PhotoFile]]]:
        """Prepare source directory for processing.

        Walks directory tree lazily to find image files and creates work items.

        Returns:
            Tuple of (enumerated file paths, empty SHA256 bins accumulator)
        """
        self.ref_photos_init = None
        self.ref_seqs_init = None

        # Use stored source_path
        path = self.source_path

        def walk_image_files(root: Path) -> Iterator[tuple[Path, str]]:
            """Walk directory tree and yield image file paths with mime types.

            Args:
                    root: Root directory to walk

            Yields:
                    Tuples of (file_path, mime_subtype) for each image file
                    Example: (Path("/photos/img.jpg"), "jpeg")
            """
            dp: str
            fns: list[str]
            for dp, _, fns in os.walk(root):
                fn: str
                for fn in fns:
                    mime: str | None
                    mime, _ = mimetypes.guess_type(fn)
                    if mime is not None and mime.startswith("image/"):
                        p: Path = Path(dp) / fn
                        yield p, mime.removeprefix("image/")

        return enumerate(walk_image_files(path)), defaultdict(list)

    @classmethod
    def stage_worker(cls, param: tuple[int, tuple[Path, str]], _args: str) -> WorkerResult[tuple[PhotoFile, str]]:
        """Create PhotoFile with core file properties and compute SHA256.

        Work function for parallel processing that takes enumerated file info
        and returns a PhotoFile with core file properties (no image opening!).
        SHA256 is computed and returned separately for binning.

        Pixels, dimensions, and all image-derived properties are computed lazily
        when first accessed.

        There is no exception handling in here.  All exceptions should be surfaced to be dealt with by the user.

        Args:
                param: (photo_id, (path, mime)) tuple
                _args: Placeholder to match pattern

        Returns:
                (PhotoFile with core properties, SHA256 hash) tuple
        """
        photo_id: int
        path: Path
        mime: str
        photo_id, (path, mime) = param

        # Compute SHA256 (file I/O only, no image opening)
        sha256_hash: str = file_sha256(path)

        # Get file size
        size_bytes: int = path.stat().st_size

        # Create PhotoFile with core file properties only
        # No image opening! Pixels/dimensions computed lazily when accessed
        photo = PhotoFile(
            path=path,
            mime=mime,
            size_bytes=size_bytes,
            file_id=photo_id,
        )

        # Return PhotoFile and SHA256 separately (SHA256 used for binning only)
        return (
            [],
            [],
            (photo, sha256_hash),
        )

    def accumulate_results(self, result: dict[str, list[PhotoFile]], job: tuple[PhotoFile, str]) -> None:
        """Add PhotoFile to appropriate SHA256 bin.

        Args:
            result: Dictionary mapping SHA256 hash to list of PhotoFile objects
            job: Tuple of (PhotoFile, sha256) from stage_worker
        """
        photo, sha256 = job
        result[sha256].append(photo)

    def finalise(self) -> None:
        self.ref_photos_final = sum(len(b) for b in self.result.values())
        self.ref_seqs_final = None

    @property
    def photofiles(self) -> dict[int, PhotoFile]:
        """Property that returns the photofile dictionary mapping id to structure."""
        return {p.id: p for b in self.result.values() for p in b}
