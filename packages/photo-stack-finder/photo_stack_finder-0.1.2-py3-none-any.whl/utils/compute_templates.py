"""Pipeline stage that puts pictures into bins according to the patterns of digits in its filename."""

from __future__ import annotations

import re
from collections import defaultdict

from .config import CONFIG
from .models import ReviewType
from .photo_file import PhotoFile
from .pipeline_stage import PipelineStage, PrepareResult, WorkerResult
from .ports import InputPort, OutputPort
from .sequence import INDEX_T

# FIXME: Incorporate this stage into compute_identical


def extract_template(text: str) -> tuple[str, INDEX_T]:
    """Extract template and digit groups from text.

    Replaces all digit sequences with placeholders {P0}, {P1}, etc.

    Args:
            text: Text to parse (typically filename stem)

    Returns:
            Tuple of (template, list of digit strings)

    Example:
            >>> template, digits = extract_template("IMG_1234_5678")
            >>> print(template)
            IMG_{P0}_{P1}
            >>> print(digits)
            ['1234', '5678']
    """
    digits: list[str] = []

    def repl(m: re.Match[str]) -> str:
        """Replace matched digit sequence with placeholder {PN} and capture digits."""
        digits.append(m.group(0))
        return f"{{P{len(digits) - 1}}}"

    template: str = re.sub(r"\d+", repl, text)
    return template, tuple(digits)


class ComputeTemplates(
    PipelineStage[
        PhotoFile,  # S: work item
        tuple[PhotoFile, str, INDEX_T],  # T: work data
        dict[str, list[tuple[INDEX_T, PhotoFile]]],  # R: accumulator
    ]
):
    def __init__(self) -> None:
        """Initialize template binning stage."""
        super().__init__(
            path=CONFIG.paths.template_bins_pkl,
            stage_name="Filename template binning",
        )

        # Worker args
        self.args = None

        # Create input port for nonidentical photos (from ComputeIdentical)
        self.nonidentical_photos_i: InputPort[list[PhotoFile]] = InputPort("nonidentical")

        # Create output port for template bins
        self.template_bins_o: OutputPort[dict[str, list[tuple[INDEX_T, PhotoFile]]]] = OutputPort(
            self, getter=lambda: self.result
        )

    def prepare(
        self,
    ) -> PrepareResult[PhotoFile, dict[str, list[tuple[INDEX_T, PhotoFile]]]]:
        """Prepare template binning by accessing nonidentical photos from dependency.

        Nonidentical photos are read from the input port.

        Returns:
            Tuple of (work_items, accumulator) where:
            - work_items: Iterator over nonidentical photos
            - accumulator: Empty defaultdict for template bins
        """
        # Read from input port to get nonidentical photos
        photos: list[PhotoFile] = self.nonidentical_photos_i.read()
        # Get reference counts from upstream (for ungrouped photos, ref == total)
        self.ref_photos_init = self.nonidentical_photos_i.get_ref_photo_count()
        self.ref_seqs_init = self.nonidentical_photos_i.get_ref_sequence_count()
        # Count total photos for internal invariant checking (ref == total at this stage)
        self.total_photos = len(photos)

        return photos, defaultdict(list)

    @classmethod
    def stage_worker(cls, photo: PhotoFile, _args: str) -> WorkerResult[tuple[PhotoFile, str, INDEX_T]]:
        """Parse the digits out of the photo filename and prepare to be binned by similar template.

        Work function for parallel processing that takes enumerated file info
        and returns a complete PhotoFile with all core properties (SHA256, dimensions,
        aspect ratio) computed eagerly.

        There is no exception handling in here.  All exceptions should be surfaced to be dealt with by the user.

        Args:
                photo: PhotoFile in which to calculate template patterns.
                _args: Placeholder to match pattern (unused)

        Returns:
                PhotoFile with all core properties computed
        """
        assert photo.path is not None, "Photo path cannot be None in production code"

        template: str
        digits: INDEX_T
        template, digits = extract_template(photo.path.name)

        return [], [], (photo, str(photo.path.with_name(template)), digits)

    def accumulate_results(
        self,
        accum: dict[str, list[tuple[INDEX_T, PhotoFile]]],
        job: tuple[PhotoFile, str, INDEX_T],
    ) -> None:
        photo, template, digits = job
        accum[template].append((digits, photo))

    def finalise(self) -> None:
        self.ref_photos_final = sum(len(b) for b in self.result.values())
        self.ref_seqs_final = len(self.result)

        # Invariant: photo count should be preserved (this stage just bins photos)
        assert self.ref_photos_final == self.total_photos, (
            f"Started with {self.total_photos} photos but ended up with {self.ref_photos_final}"
        )

    def needs_review(self) -> ReviewType:
        return "none"
