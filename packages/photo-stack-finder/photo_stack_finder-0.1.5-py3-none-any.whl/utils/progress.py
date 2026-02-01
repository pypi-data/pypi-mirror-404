"""Progress tracking with in-place updates for cleaner logs."""

from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class ProgressInfo:
    """Complete progress information, pre-formatted for UI display.

    All formatting happens in the backend - frontend just displays values.
    """

    # Raw values (for programmatic use if needed)
    fraction_complete: float  # 0.0 to 1.0
    current_count: int  # Current item count
    total_count: int | None  # Total item count (None if unknown)
    rate: float | None  # Items per second
    eta_seconds: float | None  # Estimated seconds remaining

    # Formatted strings (ready for direct display in HTML)
    percentage_display: str  # "73%"
    progress_bar_width: str  # "73%" (CSS width property)
    status_message: str  # "Processing photos"
    items_display: str | None  # "11,123 / 15,234" or None
    rate_display: str | None  # "1,250 items/sec" or None
    eta_display: str | None  # "3 seconds" or "2 minutes" or "1h 23m"
    stage_display: str  # "Compute Identical"


def _format_time(seconds: float) -> str:
    """Format time in seconds to human-readable format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string like "2d3h45s" or "1h30s" or "45s"
    """
    if seconds < 60:
        return f"{seconds:.0f}s"

    days: int = int(seconds // 86400)
    remaining: float = seconds % 86400
    hours: int = int(remaining // 3600)
    remaining = remaining % 3600
    minutes: int = int(remaining // 60)
    secs: int = int(remaining % 60)

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:  # Always show seconds if nothing else to show
        parts.append(f"{secs}s")

    return "".join(parts)


def _format_completion_time(eta_seconds: float) -> str:
    """Format estimated completion time as a timestamp.

    Args:
        eta_seconds: Estimated seconds remaining until completion

    Returns:
        Formatted string like "14:35:20" for same-day or "tomorrow 09:30" for next day
    """
    completion: datetime = datetime.now() + timedelta(seconds=eta_seconds)
    now: datetime = datetime.now()

    # Check if completion is tomorrow or later
    if completion.date() > now.date():
        days_diff: int = (completion.date() - now.date()).days
        if days_diff == 1:
            return f"tomorrow {completion.strftime('%H:%M')}"
        return f"in {days_diff} days at {completion.strftime('%H:%M')}"

    # Same day - just show time
    return completion.strftime("%H:%M:%S")


def format_seconds_weighted(total_seconds: float) -> str:
    """Formats a number of seconds into DDDdHHhMMmSS.ffs.

    Omits leading zero-value fields.
    """
    if total_seconds < 0:
        return "-" + format_seconds_weighted(-total_seconds)

    # 1. Separate whole seconds and fractional seconds
    whole_seconds = int(total_seconds)
    fractional_seconds = total_seconds - whole_seconds

    # 2. Convert whole seconds to Days, Hours, Minutes, Seconds
    days = whole_seconds // (24 * 3600)
    whole_seconds %= 24 * 3600

    hours = whole_seconds // 3600
    whole_seconds %= 3600

    minutes = whole_seconds // 60
    seconds = whole_seconds % 60

    # 3. Build the components list (Days, Hours, Minutes, Seconds)
    components = []

    if days > 0:
        components.append(f"{days}d")

    if hours > 0 or (days > 0 and (minutes > 0 or seconds > 0 or fractional_seconds > 0)):
        # Include hours if non-zero, OR if days are present and there's any time after hours.
        components.append(f"{hours}h")

    if minutes > 0 or (hours > 0 and (seconds > 0 or fractional_seconds > 0)):
        # Include minutes if non-zero, OR if hours are present and there's any time after minutes.
        components.append(f"{minutes}m")

    # 4. Handle the Seconds and Fractional part

    # The seconds and fractional part must always be included,
    # unless the entire duration is 0.0.
    if not components and seconds == 0 and fractional_seconds == 0:
        return "0s"  # Special case for exact zero

    # The Seconds part is built using the combined whole and fractional seconds
    # which ensures the correct two decimal places.
    # Note: We must use the 'seconds' variable and add the fractional part back
    # to avoid issues with floating point arithmetic accumulating large errors
    # if we simply calculated total_seconds % 60.

    formatted_seconds = seconds + fractional_seconds

    # Check if a higher-order component (d, h, m) was printed.
    # If not, the seconds field is the leading field and should not be zero-padded.
    # The format is S.ffs (no padding) or SS.ffs (padding if it follows another field)

    if components:
        # Pad with 0 to ensure two digits if it follows an hour or minute field
        # e.g., '1h05.12s', not '1h5.12s'
        components.append(f"{formatted_seconds:05.2f}s")
    else:
        # This is the leading field, so no mandatory padding on the integer part
        # The formatting will be "S.ffs" or "SS.ffs"
        components.append(f"{formatted_seconds:.2f}s")

    # 5. Combine and return
    return "".join(components).replace(
        ":", ""
    )  # Remove potential colons from hour/minute formatting if using a different approach


class ProgressTracker:
    """Track progress with in-place console updates.

    Updates the same line repeatedly to avoid cluttering logs with progress messages.
    Falls back to periodic line updates if terminal doesn't support in-place updates.
    """

    def __init__(
        self,
        description: str,
        total: int | None = None,
        update_interval: float = 0.5,
    ):
        """Initialize progress tracker.

        Args:
            description: Description of what's being tracked (e.g., "Processing photos")
            total: Expected total count (if known). If None, shows count without percentage.
            update_interval: Minimum seconds between display updates (default 0.5s)
        """
        self.description = description
        self.total = total
        self.update_interval = update_interval

        self.current = 0
        self.last_update_time = 0.0
        self.start_time = time.time()
        self.last_displayed_message = ""

        # Final metrics (set when finish() is called)
        self.elapsed_seconds: float | None = None
        self.final_rate: float | None = None  # items per second

        # Thread safety for concurrent access from UI polling
        self._lock = threading.Lock()

        # Always use carriage return for in-place updates
        self.supports_inplace = True

    def update(self, increment: int = 1) -> None:
        """Update progress by incrementing the counter.

        Args:
            increment: Amount to add to current count (default 1)
        """
        with self._lock:
            self.current += increment
            now: float = time.time()

            # Only update display if enough time has passed
            if now - self.last_update_time >= self.update_interval:
                self._display()
                self.last_update_time = now

    def set(self, value: int) -> None:
        """Set progress to a specific value.

        Args:
            value: Absolute count value
        """
        with self._lock:
            self.current = value
            now: float = time.time()

            if now - self.last_update_time >= self.update_interval:
                self._display()
                self.last_update_time = now

    def set_status(self, status: str) -> None:
        """Update status message without changing count.

        Useful for showing status during finalize/save operations.

        Args:
            status: New status message (e.g., "Finalizing results...", "Saving to cache...")
        """
        with self._lock:
            self.description = status
            self._display()
            self.last_update_time = time.time()

    def finish(self, message: str | None = None) -> None:
        """Finish progress tracking and print final message.

        Stores final elapsed time and throughput for later access.

        Args:
            message: Optional custom completion message. If None, uses default format.
        """
        elapsed: float = time.time() - self.start_time

        # Store final metrics for web UI
        self.elapsed_seconds = elapsed
        self.final_rate = self.current / elapsed if elapsed > 0 and self.current > 0 else None

        if message is None:
            elapsed_s: str = format_seconds_weighted(elapsed)
            if self.total is not None:
                message = f"{self.description}: {self.current}/{self.total} ({elapsed_s})"
            else:
                message = f"{self.description}: {self.current} ({elapsed_s})"

        # Clear the line and print final message
        if self.supports_inplace and self.last_displayed_message:
            sys.stderr.write("\r" + " " * len(self.last_displayed_message) + "\r")
        sys.stderr.write(message + "\n")
        sys.stderr.flush()
        self.last_displayed_message = ""

    def _display(self) -> None:
        """Display current progress."""
        elapsed: float = time.time() - self.start_time

        # Build progress message
        message: str
        if self.total is not None:
            percentage: float = (self.current / self.total * 100) if self.total > 0 else 0
            rate: float = self.current / elapsed if elapsed > 0 else 0
            eta: float = (self.total - self.current) / rate if rate > 0 else 0

            message = (
                f"{self.description}: {self.current}/{self.total} "
                f"({percentage:.1f}%, {rate:.1f}/s, finishes {_format_completion_time(eta)})"
            )
        else:
            rate_simple: float = self.current / elapsed if elapsed > 0 else 0
            message = f"{self.description}: {self.current} ({rate_simple:.1f}/s)"

        # Display with carriage return for in-place update, or newline if not supported
        if self.supports_inplace:
            # Pad with spaces to clear any previous longer message
            if len(message) < len(self.last_displayed_message):
                message = message + " " * (len(self.last_displayed_message) - len(message))
            sys.stderr.write("\r" + message)
            sys.stderr.flush()
        else:
            # No in-place support, print new line
            sys.stderr.write(message + "\n")
            sys.stderr.flush()

        self.last_displayed_message = message

    def get_snapshot(self) -> ProgressInfo:
        """Get formatted progress snapshot (for UI polling).

        Thread-safe method that returns complete progress information
        with all values pre-formatted for display.

        Returns:
            ProgressInfo with all fields formatted for UI display
        """
        with self._lock:
            # Calculate raw metrics
            elapsed = time.time() - self.start_time
            items_per_second = self.current / elapsed if elapsed > 0 else None

            # Calculate ETA if we have total and rate
            eta_seconds = None
            if self.total and items_per_second and items_per_second > 0:
                remaining = self.total - self.current
                eta_seconds = remaining / items_per_second

            # Calculate completion fraction
            if self.total and self.total > 0:
                fraction = min(1.0, self.current / self.total)
            else:
                fraction = 0.0

            percentage = int(fraction * 100)

            # Format everything for display (backend does all formatting)
            return ProgressInfo(
                # Raw values
                fraction_complete=fraction,
                current_count=self.current,
                total_count=self.total,
                rate=items_per_second,
                eta_seconds=eta_seconds,
                # Formatted strings
                percentage_display=f"{percentage}%",
                progress_bar_width=f"{percentage}%",
                status_message=self.description,
                items_display=self._format_items(self.current, self.total),
                rate_display=self._format_rate(items_per_second),
                eta_display=self._format_eta(eta_seconds),
                stage_display=self.description.replace("_", " ").title(),
            )

    @staticmethod
    def _format_items(current: int, total: int | None) -> str | None:
        """Format item counts: '11,123 / 15,234'.

        Args:
            current: Current item count
            total: Total item count (or None if unknown)

        Returns:
            Formatted string or None if current is 0
        """
        if current == 0:
            return None
        if total is None:
            return f"{current:,} items processed"
        return f"{current:,} / {total:,}"

    @staticmethod
    def _format_rate(items_per_second: float | None) -> str | None:
        """Format processing rate: '1,250 items/sec'.

        Args:
            items_per_second: Processing rate in items per second

        Returns:
            Formatted string or None if rate is too low/unknown
        """
        if items_per_second is None or items_per_second < 0.1:
            return None
        return f"{items_per_second:,.0f} items/sec"

    @staticmethod
    def _format_eta(seconds: float | None) -> str | None:
        """Format estimated time remaining: '3 seconds', '2 minutes', '1h 23m'.

        Args:
            seconds: Estimated seconds remaining

        Returns:
            Formatted string or None if ETA unknown or less than 1 second
        """
        if seconds is None or seconds < 1:
            return None

        if seconds < 60:
            return f"{int(seconds)} second{'s' if int(seconds) != 1 else ''}"
        if seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        if minutes > 0:
            return f"{hours}h {minutes}m"
        return f"{hours} hour{'s' if hours != 1 else ''}"

    def __enter__(self) -> ProgressTracker:
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        """Context manager exit - finish progress tracking."""
        if exc_type is None:
            self.finish()
        else:
            # Error occurred, still clean up display
            self.finish(f"{self.description}: Failed at {self.current}")
