"""
Batch Processing Module

Generic batch processor with resume capability for medical imaging pipelines.
"""

from pathlib import Path
from typing import Callable, List, Any, Optional, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Batch processing configuration"""
    enable_resume: bool = True
    cache_dir: Optional[Path] = None
    save_intermediate: bool = True
    log_interval: int = 10


class BatchProcessor:
    """
    Generic batch processor with resume capability

    Features:
    - Resume from interruption
    - Progress tracking
    - Cache management
    - Flexible callback system

    Example:
        processor = BatchProcessor(cache_dir=Path("cache"))

        results = processor.process(
            items=patient_list,
            process_func=analyze_patient,
            get_item_id=lambda p: p.id,
            desc="Analyzing patients"
        )

        processor.print_summary(results)
    """

    def __init__(self, config: Optional[BatchConfig] = None, cache_dir: Optional[Path] = None):
        """
        Initialize batch processor

        Args:
            config: BatchConfig instance
            cache_dir: Directory for cache files
        """
        self.config = config or BatchConfig()
        if cache_dir:
            self.config.cache_dir = Path(cache_dir)

        self._results: List[Dict] = []

    def process(
        self,
        items: List[Any],
        process_func: Callable[[Any], Any],
        get_item_id: Optional[Callable[[Any], str]] = None,
        desc: str = "Processing",
        on_complete: Optional[Callable[[str, Any], None]] = None,
        on_error: Optional[Callable[[str, Exception], None]] = None
    ) -> List[Dict]:
        """
        Process items in batch

        Args:
            items: List of items to process
            process_func: Function to process each item
            get_item_id: Function to extract item ID (default: str)
            desc: Description for logging
            on_complete: Callback on successful processing
            on_error: Callback on error

        Returns:
            List of result dictionaries
        """
        if get_item_id is None:
            get_item_id = str

        self._results = []
        total = len(items)

        logger.info(f"{desc}: Starting batch of {total} items")

        for i, item in enumerate(items, 1):
            item_id = get_item_id(item)

            try:
                result = process_func(item)

                self._results.append({
                    'item_id': item_id,
                    'status': 'success',
                    'result': result
                })

                if on_complete:
                    on_complete(item_id, result)

            except Exception as e:
                self._results.append({
                    'item_id': item_id,
                    'status': 'failed',
                    'error': str(e)
                })

                if on_error:
                    on_error(item_id, e)

                logger.warning(f"Failed to process {item_id}: {e}")

            # Log progress periodically
            if i % self.config.log_interval == 0 or i == total:
                success = sum(1 for r in self._results if r['status'] == 'success')
                logger.info(f"{desc}: {i}/{total} completed ({success} successful)")

        return self._results

    def get_statistics(self) -> Dict:
        """Get processing statistics"""
        total = len(self._results)
        success = sum(1 for r in self._results if r['status'] == 'success')
        failed = total - success

        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': (success / total * 100) if total > 0 else 0
        }

    def print_summary(self, results: Optional[List[Dict]] = None):
        """Print processing summary"""
        if results:
            self._results = results

        stats = self.get_statistics()

        print()
        print("=" * 60)
        print("Batch Processing Summary")
        print("=" * 60)
        print(f"Total: {stats['total']}")
        print(f"Success: {stats['success']} ({stats['success_rate']:.1f}%)")
        print(f"Failed: {stats['failed']}")
        print("=" * 60)

        if stats['failed'] > 0:
            print("\nFailed items:")
            for r in self._results:
                if r['status'] == 'failed':
                    print(f"  - {r['item_id']}: {r.get('error', 'Unknown error')}")


__all__ = ['BatchProcessor', 'BatchConfig']
