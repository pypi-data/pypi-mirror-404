"""
Multi-Level Progress Tracker

Provides hierarchical progress tracking for long-running medical imaging pipelines.
Displays overall progress, current step, and substeps with time estimation.

Design Principles:
1. Multi-Level - Support overall -> step -> substep hierarchy
2. Time Estimation - Dynamic ETA based on completed work
3. User Friendly - Clear progress visualization, graceful interruption
4. Windows Compatible - ASCII-only characters (no Unicode symbols)
5. Lightweight - Minimal performance overhead
"""

import sys
import time
from typing import Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import threading


@dataclass
class ProgressLevel:
    """Progress tracking for a single level"""
    name: str
    total: int
    current: int = 0
    start_time: Optional[float] = None
    estimated_time_per_item: Optional[float] = None  # seconds

    def __post_init__(self):
        if self.start_time is None:
            self.start_time = time.time()

    @property
    def percentage(self) -> float:
        """Get completion percentage (0-100)"""
        if self.total == 0:
            return 100.0
        return (self.current / self.total) * 100.0

    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return time.time() - self.start_time

    @property
    def average_time_per_item(self) -> Optional[float]:
        """Calculate average time per item based on completed items"""
        if self.current == 0:
            return self.estimated_time_per_item
        return self.elapsed_time / self.current

    @property
    def remaining_time(self) -> Optional[float]:
        """Estimate remaining time in seconds"""
        if self.current == 0:
            if self.estimated_time_per_item is not None:
                return self.estimated_time_per_item * self.total
            return None

        avg_time = self.average_time_per_item
        if avg_time is None:
            return None

        remaining_items = self.total - self.current
        return avg_time * remaining_items

    @property
    def eta(self) -> Optional[datetime]:
        """Estimate completion time"""
        remaining = self.remaining_time
        if remaining is None:
            return None
        return datetime.now() + timedelta(seconds=remaining)


class ProgressTracker:
    """
    Multi-level progress tracker for medical imaging pipelines

    Supports hierarchical progress visualization:
    - Level 0: Overall progress (all patients)
    - Level 1: Current step (e.g., Stage1, Stage2)
    - Level 2: Substep (e.g., loading data, inference, saving)

    Example Usage:
        # Single-level progress (simple)
        tracker = ProgressTracker()
        tracker.start_overall("Processing Patients", total=100)

        for i, patient_id in enumerate(patient_list):
            process_patient(patient_id)
            tracker.update_overall(i + 1)

        tracker.finish()

        # Multi-level progress (pipeline)
        tracker = ProgressTracker()
        tracker.start_overall("Analysis Pipeline", total=100)

        for i, patient_id in enumerate(patient_list):
            tracker.start_step("Stage 1: Segmentation", total=1)
            segment(patient_id)
            tracker.complete_step()

            tracker.start_step("Stage 2: Metrics", total=5)
            for metric in metrics:
                tracker.update_substep(f"Computing {metric}")
                compute_metric(patient_id, metric)
                tracker.update_step_progress()
            tracker.complete_step()

            tracker.update_overall(i + 1)

        tracker.finish()
    """

    def __init__(
        self,
        show_progress_bar: bool = True,
        bar_width: int = 40,
        update_interval: float = 0.5,
        enable_colors: bool = True
    ):
        """
        Initialize progress tracker

        Args:
            show_progress_bar: Show visual progress bars
            bar_width: Width of progress bar in characters
            update_interval: Minimum time between display updates (seconds)
            enable_colors: Use ANSI colors (works in Windows Terminal)
        """
        self.show_progress_bar = show_progress_bar
        self.bar_width = bar_width
        self.update_interval = update_interval
        self.enable_colors = enable_colors

        # Progress levels
        self.overall: Optional[ProgressLevel] = None
        self.step: Optional[ProgressLevel] = None
        self.substep_message: Optional[str] = None

        # Display state
        self.last_update_time: float = 0
        self.last_display_lines: int = 0

        # Thread safety
        self._lock = threading.Lock()

        # Completion flag
        self._finished = False

    def start_overall(
        self,
        name: str,
        total: int,
        estimated_time_per_item: Optional[float] = None
    ):
        """
        Start overall progress tracking

        Args:
            name: Overall task name
            total: Total number of items
            estimated_time_per_item: Estimated time per item in seconds
        """
        with self._lock:
            self.overall = ProgressLevel(
                name=name,
                total=total,
                estimated_time_per_item=estimated_time_per_item
            )
            self._display()

    def update_overall(self, current: int):
        """
        Update overall progress

        Args:
            current: Current item number (1-based)
        """
        with self._lock:
            if self.overall is None:
                return

            self.overall.current = current
            self._display()

    def start_step(
        self,
        name: str,
        total: int = 1,
        estimated_time_per_item: Optional[float] = None
    ):
        """
        Start step-level progress

        Args:
            name: Step name
            total: Total number of substeps
            estimated_time_per_item: Estimated time per substep
        """
        with self._lock:
            self.step = ProgressLevel(
                name=name,
                total=total,
                estimated_time_per_item=estimated_time_per_item
            )
            self.substep_message = None
            self._display()

    def update_step_progress(self, increment: int = 1):
        """
        Update current step progress

        Args:
            increment: Number of substeps completed
        """
        with self._lock:
            if self.step is None:
                return

            self.step.current += increment
            self._display()

    def update_substep(self, message: str):
        """
        Update substep message

        Args:
            message: Substep description
        """
        with self._lock:
            self.substep_message = message
            self._display()

    def complete_step(self):
        """Mark current step as completed"""
        with self._lock:
            if self.step is not None:
                self.step.current = self.step.total
                self._display()

            # Clear step after brief display
            time.sleep(0.1)
            self.step = None
            self.substep_message = None

    def finish(self, final_message: Optional[str] = None):
        """
        Finish progress tracking and show final summary

        Args:
            final_message: Optional final message to display
        """
        with self._lock:
            self._finished = True

            if self.overall is not None:
                self.overall.current = self.overall.total

            # Clear previous display
            self._clear_display()

            # Show final summary
            if self.overall is not None:
                elapsed = self.overall.elapsed_time
                elapsed_str = self._format_duration(elapsed)

                print(f"\n[OK] {self.overall.name} completed!")
                print(f"     Total items: {self.overall.total}")
                print(f"     Elapsed time: {elapsed_str}")

                if self.overall.total > 0:
                    avg_time = elapsed / self.overall.total
                    avg_str = self._format_duration(avg_time)
                    print(f"     Average time per item: {avg_str}")

            if final_message:
                print(f"\n{final_message}")

            print()

    def _display(self):
        """Display current progress (rate-limited)"""
        if not self.show_progress_bar:
            return

        # Rate limiting
        current_time = time.time()
        if (current_time - self.last_update_time) < self.update_interval:
            return

        self.last_update_time = current_time

        # Clear previous display
        self._clear_display()

        # Build display lines
        lines = []

        # Overall progress
        if self.overall is not None:
            overall_bar = self._render_progress_bar(
                self.overall.current,
                self.overall.total
            )

            remaining = self.overall.remaining_time
            if remaining is not None:
                eta_str = self._format_duration(remaining)
                lines.append(
                    f"{self.overall.name}: {overall_bar} "
                    f"{self.overall.current}/{self.overall.total} "
                    f"(ETA: {eta_str})"
                )
            else:
                lines.append(
                    f"{self.overall.name}: {overall_bar} "
                    f"{self.overall.current}/{self.overall.total}"
                )

        # Step progress
        if self.step is not None:
            step_bar = self._render_progress_bar(
                self.step.current,
                self.step.total
            )

            lines.append(
                f"  {self.step.name}: {step_bar} "
                f"{self.step.current}/{self.step.total}"
            )

        # Substep message
        if self.substep_message is not None:
            lines.append(f"    {self.substep_message}")

        # Display all lines
        for line in lines:
            print(line, file=sys.stderr, flush=True)

        self.last_display_lines = len(lines)

    def _clear_display(self):
        """Clear previous progress display"""
        if self.last_display_lines > 0:
            # Move cursor up and clear lines
            for _ in range(self.last_display_lines):
                sys.stderr.write('\033[F')  # Move up
                sys.stderr.write('\033[K')  # Clear line
            sys.stderr.flush()
            self.last_display_lines = 0

    def _render_progress_bar(self, current: int, total: int) -> str:
        """
        Render ASCII progress bar

        Returns:
            Progress bar string (e.g., "[=====>    ] 50%")
        """
        if total == 0:
            percentage = 100.0
        else:
            percentage = (current / total) * 100.0

        filled_width = int((current / total) * self.bar_width) if total > 0 else self.bar_width
        empty_width = self.bar_width - filled_width

        # Use ASCII characters (Windows-compatible)
        bar = '[' + '=' * filled_width + '>' * min(1, empty_width) + ' ' * max(0, empty_width - 1) + ']'

        return f"{bar} {percentage:5.1f}%"

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration in human-readable format

        Returns:
            Formatted string (e.g., "2h 15m", "45s")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if not self._finished:
            if exc_type is None:
                self.finish()
            else:
                # Error occurred
                self._clear_display()
                print(f"\n[X] Progress interrupted due to error: {exc_val}\n", file=sys.stderr)

        return False


def create_tracker(
    task_name: str,
    total_items: int,
    estimated_time_per_item: Optional[float] = None
) -> ProgressTracker:
    """
    Create and start a progress tracker

    Args:
        task_name: Overall task name
        total_items: Total number of items
        estimated_time_per_item: Estimated time per item in seconds

    Returns:
        ProgressTracker instance (already started)

    Example:
        tracker = create_tracker("Processing", total=100, estimated_time_per_item=60)

        for i, item in enumerate(items):
            process(item)
            tracker.update_overall(i + 1)

        tracker.finish()
    """
    tracker = ProgressTracker()
    tracker.start_overall(task_name, total_items, estimated_time_per_item)
    return tracker
