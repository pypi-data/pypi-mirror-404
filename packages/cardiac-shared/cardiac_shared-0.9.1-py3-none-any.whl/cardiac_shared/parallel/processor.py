"""
Parallel Processor Module

Unified parallel processing framework for medical imaging pipelines.

Features:
- Auto worker count detection (based on CPU cores + memory)
- Progress tracking with tqdm
- Error handling and retry logic
- Checkpoint/resume support
- CPU-bound and IO-bound task support
"""

import json
import os
import time
from pathlib import Path
from typing import Callable, List, Any, Optional, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime

# Optional tqdm import
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


@dataclass
class ProcessingResult:
    """Result of processing a single item"""
    item_id: str
    status: str  # 'success', 'failed', 'skipped'
    result: Any = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Checkpoint:
    """Checkpoint data for resume capability"""
    completed: List[str] = field(default_factory=list)
    failed: Dict[str, str] = field(default_factory=dict)
    total: int = 0
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'completed': self.completed,
            'failed': self.failed,
            'total': self.total,
            'last_updated': self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Checkpoint':
        """Create from dictionary"""
        return cls(
            completed=data.get('completed', []),
            failed=data.get('failed', {}),
            total=data.get('total', 0),
            last_updated=data.get('last_updated', datetime.now().isoformat())
        )


class ParallelProcessor:
    """
    Unified parallel processing framework

    Handles:
    - Automatic worker count optimization
    - Progress tracking with tqdm
    - Checkpoint/resume support
    - Error handling and retry
    - CPU-bound and IO-bound tasks

    Example:
        >>> processor = ParallelProcessor(max_workers=4)
        >>> results = processor.map(process_func, items, desc="Processing")
        >>>
        >>> # With checkpoint support
        >>> processor = ParallelProcessor(checkpoint_file='checkpoint.json')
        >>> results = processor.map_with_checkpoint(process_func, items)
    """

    def __init__(self,
                 max_workers: Optional[int] = None,
                 checkpoint_file: Optional[Path] = None,
                 use_threads: bool = False,
                 retry_failed: int = 0):
        """
        Initialize parallel processor

        Args:
            max_workers: Maximum number of parallel workers
                        If None, auto-detect from hardware
            checkpoint_file: Path to checkpoint file for resume support
            use_threads: Use ThreadPoolExecutor instead of ProcessPoolExecutor
                        (useful for IO-bound tasks)
            retry_failed: Number of times to retry failed items (default: 0)
        """
        self.max_workers = max_workers or self._auto_detect_workers()
        self.checkpoint_file = Path(checkpoint_file) if checkpoint_file else None
        self.use_threads = use_threads
        self.retry_failed = retry_failed

        # Load checkpoint if exists
        self.checkpoint = self._load_checkpoint()

    def _auto_detect_workers(self) -> int:
        """
        Auto-detect optimal worker count based on system resources

        Returns:
            Optimal number of workers
        """
        try:
            from cardiac_shared.hardware import detect_hardware

            hw = detect_hardware()
            physical_cores = hw.cpu.physical_cores

            # Use 60-80% of physical cores
            optimal_workers = max(2, int(physical_cores * 0.75))

            # Check memory constraint
            available_gb = hw.ram.available_gb
            memory_per_worker = 2.0  # Assume 2GB per worker
            max_workers_memory = int(available_gb / memory_per_worker)

            # Take minimum to avoid memory issues
            final_workers = min(optimal_workers, max_workers_memory)

            return max(2, final_workers)  # At least 2 workers

        except Exception:
            # Fallback to CPU count
            cpu_count = os.cpu_count() or 4
            return max(2, int(cpu_count * 0.75))

    def _load_checkpoint(self) -> Checkpoint:
        """Load checkpoint from file if exists"""
        if self.checkpoint_file and self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Checkpoint.from_dict(data)
            except Exception:
                return Checkpoint()
        return Checkpoint()

    def _save_checkpoint(self):
        """Save checkpoint to file"""
        if self.checkpoint_file:
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            self.checkpoint.last_updated = datetime.now().isoformat()

            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(self.checkpoint.to_dict(), f, indent=2)

    def _should_skip(self, item_id: str) -> bool:
        """Check if item should be skipped (already completed)"""
        return item_id in self.checkpoint.completed

    def map(self,
            func: Callable,
            items: List[Any],
            desc: str = "Processing",
            unit: str = "items",
            show_progress: bool = True) -> List[ProcessingResult]:
        """
        Process items in parallel with progress tracking

        Args:
            func: Function to apply to each item
                 Should take one argument and return result
            items: List of items to process
            desc: Description for progress bar
            unit: Unit name for progress bar (e.g., "cases", "files")
            show_progress: Show progress bar

        Returns:
            List of ProcessingResult objects
        """
        results = []

        # Choose executor type
        ExecutorClass = ThreadPoolExecutor if self.use_threads else ProcessPoolExecutor

        with ExecutorClass(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(func, item): item
                for item in items
            }

            # Process results with progress bar
            pbar = None
            if show_progress and HAS_TQDM:
                pbar = tqdm(total=len(items), desc=desc, unit=unit)

            for future in as_completed(future_to_item):
                item = future_to_item[future]

                try:
                    result = future.result()
                    results.append(ProcessingResult(
                        item_id=str(item),
                        status='success',
                        result=result
                    ))
                except Exception as e:
                    results.append(ProcessingResult(
                        item_id=str(item),
                        status='failed',
                        error=str(e)
                    ))

                if pbar:
                    pbar.update(1)

            if pbar:
                pbar.close()

        return results

    def map_with_checkpoint(self,
                           func: Callable,
                           items: List[Any],
                           desc: str = "Processing",
                           unit: str = "items",
                           get_item_id: Optional[Callable] = None) -> List[ProcessingResult]:
        """
        Process items with checkpoint/resume support

        Args:
            func: Function to process each item
            items: List of items to process
            desc: Description for progress bar
            unit: Unit name for progress bar
            get_item_id: Optional function to extract item ID
                        Default: str(item)

        Returns:
            List of ProcessingResult objects
        """
        if get_item_id is None:
            get_item_id = str

        # Filter out already completed items
        items_to_process = [
            item for item in items
            if get_item_id(item) not in self.checkpoint.completed
        ]

        skipped_count = len(items) - len(items_to_process)

        if skipped_count > 0:
            print(f"[i] Resuming from checkpoint: {skipped_count} items already completed")
            print(f"[i] Processing remaining {len(items_to_process)} items")

        self.checkpoint.total = len(items)

        results = []

        # Choose executor type
        ExecutorClass = ThreadPoolExecutor if self.use_threads else ProcessPoolExecutor

        with ExecutorClass(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_item = {}
            for item in items_to_process:
                future = executor.submit(self._process_with_timing, func, item)
                future_to_item[future] = item

            # Process results with progress bar
            pbar = None
            if HAS_TQDM:
                pbar = tqdm(
                    total=len(items),
                    initial=skipped_count,
                    desc=desc,
                    unit=unit
                )

            for future in as_completed(future_to_item):
                item = future_to_item[future]
                item_id = get_item_id(item)

                try:
                    result, duration = future.result()

                    proc_result = ProcessingResult(
                        item_id=item_id,
                        status='success',
                        result=result,
                        duration_seconds=duration
                    )
                    results.append(proc_result)

                    # Update checkpoint
                    self.checkpoint.completed.append(item_id)
                    if item_id in self.checkpoint.failed:
                        del self.checkpoint.failed[item_id]

                except Exception as e:
                    proc_result = ProcessingResult(
                        item_id=item_id,
                        status='failed',
                        error=str(e)
                    )
                    results.append(proc_result)

                    # Update checkpoint
                    self.checkpoint.failed[item_id] = str(e)

                # Save checkpoint periodically (every 10 items)
                if len(results) % 10 == 0:
                    self._save_checkpoint()

                if pbar:
                    pbar.update(1)
                    # Update progress bar postfix with stats
                    success_count = sum(1 for r in results if r.status == 'success')
                    failed_count = sum(1 for r in results if r.status == 'failed')
                    pbar.set_postfix({
                        'success': success_count,
                        'failed': failed_count
                    })

            if pbar:
                pbar.close()

        # Final checkpoint save
        self._save_checkpoint()

        return results

    def _process_with_timing(self, func: Callable, item: Any) -> Tuple[Any, float]:
        """
        Process item and measure duration

        Returns:
            Tuple of (result, duration_seconds)
        """
        start_time = time.time()
        result = func(item)
        duration = time.time() - start_time
        return result, duration

    def get_statistics(self, results: List[ProcessingResult]) -> Dict:
        """
        Calculate statistics from processing results

        Args:
            results: List of ProcessingResult objects

        Returns:
            Dictionary with statistics
        """
        total = len(results)
        success = sum(1 for r in results if r.status == 'success')
        failed = sum(1 for r in results if r.status == 'failed')
        skipped = sum(1 for r in results if r.status == 'skipped')

        durations = [r.duration_seconds for r in results if r.duration_seconds > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            'total': total,
            'success': success,
            'failed': failed,
            'skipped': skipped,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'average_duration_seconds': avg_duration,
            'total_duration_seconds': sum(durations),
        }

    def print_summary(self, results: List[ProcessingResult]):
        """
        Print processing summary

        Args:
            results: List of ProcessingResult objects
        """
        stats = self.get_statistics(results)

        print()
        print("=" * 70)
        print("Processing Summary")
        print("=" * 70)
        print(f"Total items: {stats['total']}")
        print(f"  Success: {stats['success']} ({stats['success_rate']:.1f}%)")
        print(f"  Failed: {stats['failed']}")
        if stats['skipped'] > 0:
            print(f"  Skipped: {stats['skipped']}")
        print()
        print(f"Average time per item: {stats['average_duration_seconds']:.2f} seconds")
        print(f"Total processing time: {stats['total_duration_seconds'] / 60:.1f} minutes")
        print("=" * 70)
        print()

        # Show failed items if any
        if stats['failed'] > 0:
            print("Failed items:")
            for result in results:
                if result.status == 'failed':
                    print(f"  - {result.item_id}: {result.error}")
            print()


# Convenience functions
def parallel_map(func: Callable,
                items: List[Any],
                max_workers: Optional[int] = None,
                desc: str = "Processing",
                use_threads: bool = False) -> List[ProcessingResult]:
    """
    Quick parallel map without checkpoint support

    Args:
        func: Function to apply
        items: Items to process
        max_workers: Number of workers (auto-detect if None)
        desc: Progress bar description
        use_threads: Use threads instead of processes

    Returns:
        List of ProcessingResult objects
    """
    processor = ParallelProcessor(
        max_workers=max_workers,
        use_threads=use_threads
    )
    return processor.map(func, items, desc=desc)


def parallel_map_with_checkpoint(func: Callable,
                                 items: List[Any],
                                 checkpoint_file: Path,
                                 max_workers: Optional[int] = None,
                                 desc: str = "Processing",
                                 get_item_id: Optional[Callable] = None) -> List[ProcessingResult]:
    """
    Quick parallel map with checkpoint/resume support

    Args:
        func: Function to apply
        items: Items to process
        checkpoint_file: Path to checkpoint file
        max_workers: Number of workers (auto-detect if None)
        desc: Progress bar description
        get_item_id: Function to extract item ID

    Returns:
        List of ProcessingResult objects
    """
    processor = ParallelProcessor(
        max_workers=max_workers,
        checkpoint_file=checkpoint_file
    )
    return processor.map_with_checkpoint(
        func, items, desc=desc, get_item_id=get_item_id
    )
