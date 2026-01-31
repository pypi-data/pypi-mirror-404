"""
Cache Management Module

Provides multi-level caching with resume capability for medical imaging pipelines.
"""

import json
from pathlib import Path
from typing import Optional, Dict, Set, Any
from datetime import datetime


class CacheManager:
    """
    Multi-level cache manager for medical imaging pipelines

    Features:
    - Incremental saving after each item
    - Crash-resistant JSON atomic writes
    - Resume from interruption
    - Fast "already processed" lookups

    Example:
        cache = CacheManager("results/cache.json")

        for patient_id in patient_list:
            if cache.is_completed(patient_id):
                continue

            result = process_patient(patient_id)
            cache.mark_completed(patient_id, result)

        cache.save()
    """

    def __init__(self, cache_file: Optional[Path] = None, auto_save: bool = True):
        """
        Initialize cache manager

        Args:
            cache_file: Path to cache file (JSON)
            auto_save: Automatically save after each completion
        """
        self.cache_file = Path(cache_file) if cache_file else None
        self.auto_save = auto_save

        self.completed: Set[str] = set()
        self.failed: Dict[str, str] = {}
        self.results: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }

        # Load existing cache
        self._load()

    def _load(self):
        """Load cache from file if exists"""
        if self.cache_file and self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.completed = set(data.get('completed', []))
                self.failed = data.get('failed', {})
                self.results = data.get('results', {})
                self.metadata = data.get('metadata', self.metadata)
            except Exception:
                pass

    def save(self):
        """Save cache to file"""
        if self.cache_file:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            self.metadata['last_updated'] = datetime.now().isoformat()

            data = {
                'completed': list(self.completed),
                'failed': self.failed,
                'results': self.results,
                'metadata': self.metadata
            }

            # Atomic write
            temp_file = self.cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            temp_file.replace(self.cache_file)

    def is_completed(self, item_id: str) -> bool:
        """Check if item has been completed"""
        return item_id in self.completed

    def mark_completed(self, item_id: str, result: Any = None):
        """Mark item as completed"""
        self.completed.add(item_id)
        if result is not None:
            self.results[item_id] = result
        if item_id in self.failed:
            del self.failed[item_id]
        if self.auto_save:
            self.save()

    def mark_failed(self, item_id: str, error: str):
        """Mark item as failed"""
        self.failed[item_id] = error
        if self.auto_save:
            self.save()

    def get_result(self, item_id: str) -> Optional[Any]:
        """Get cached result for item"""
        return self.results.get(item_id)

    def clear(self):
        """Clear all cache data"""
        self.completed.clear()
        self.failed.clear()
        self.results.clear()
        if self.cache_file and self.cache_file.exists():
            self.cache_file.unlink()

    @property
    def completed_count(self) -> int:
        """Number of completed items"""
        return len(self.completed)

    @property
    def failed_count(self) -> int:
        """Number of failed items"""
        return len(self.failed)


__all__ = ['CacheManager']
