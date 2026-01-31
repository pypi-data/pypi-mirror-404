"""
Asynchronous NIfTI Preloader

Background preloading of NIfTI files to eliminate I/O wait times
during batch processing. Added in v0.5.1.

Features:
- Background thread preloading
- LRU memory cache (configurable size)
- Thread-safe operations
- Automatic resource cleanup

Usage:
    >>> from cardiac_shared.io import AsyncNiftiPreloader
    >>> preloader = AsyncNiftiPreloader(max_cache_size=2)
    >>> preloader.start(file_list)
    >>> for f in file_list:
    ...     data = preloader.get(f)  # From cache or wait
    ...     process(data)  # Next file loading in background
    >>> preloader.stop()
"""

import logging
import threading
import time
from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Check for nibabel
try:
    import nibabel as nib
    HAS_NIBABEL = True
except ImportError:
    HAS_NIBABEL = False


class AsyncNiftiPreloader:
    """
    Asynchronous NIfTI file preloader.

    Preloads NIfTI files in a background thread while the main thread
    processes the current file. Uses an LRU cache to manage memory.

    Attributes:
        max_cache_size: Maximum number of files to keep in cache
        timeout: Maximum time to wait for a file to load (seconds)

    Example:
        >>> preloader = AsyncNiftiPreloader(max_cache_size=2)
        >>> files = ["/path/to/file1.nii.gz", "/path/to/file2.nii.gz", ...]
        >>> preloader.start(files)
        >>> for f in files:
        ...     volume, metadata = preloader.get(f)
        ...     # Process volume...
        >>> preloader.stop()
    """

    def __init__(
        self,
        max_cache_size: int = 2,
        timeout: float = 300.0,
        load_metadata: bool = True
    ):
        """
        Initialize the preloader.

        Args:
            max_cache_size: Maximum files to cache (default: 2)
            timeout: Timeout for loading a single file in seconds (default: 300)
            load_metadata: Whether to include metadata in cache (default: True)
        """
        if not HAS_NIBABEL:
            raise ImportError(
                "nibabel is required for NIfTI preloading. "
                "Install with: pip install nibabel"
            )

        self.max_cache_size = max_cache_size
        self.timeout = timeout
        self.load_metadata = load_metadata

        # Thread-safe cache (LRU via OrderedDict)
        self._cache: OrderedDict = OrderedDict()
        self._cache_lock = threading.Lock()

        # File queue
        self._queue: List[str] = []
        self._queue_lock = threading.Lock()
        self._queue_index = 0

        # Background thread
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._file_ready = threading.Condition()

        # Statistics
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'files_preloaded': 0,
            'total_load_time': 0.0,
        }
        self._stats_lock = threading.Lock()

    def start(self, file_list: List[Union[str, Path]]) -> None:
        """
        Start preloading files.

        Args:
            file_list: List of NIfTI file paths to preload

        Example:
            >>> preloader.start(["/path/to/file1.nii.gz", "/path/to/file2.nii.gz"])
        """
        # Convert to strings and validate
        with self._queue_lock:
            self._queue = [str(f) for f in file_list]
            self._queue_index = 0

        # Clear previous state
        with self._cache_lock:
            self._cache.clear()

        self._stop_event.clear()

        # Start background thread
        self._thread = threading.Thread(target=self._preload_worker, daemon=True)
        self._thread.start()

        logger.info(f"[Preloader] Started with {len(file_list)} files, cache_size={self.max_cache_size}")

    def stop(self) -> Dict:
        """
        Stop preloading and return statistics.

        Returns:
            Dict with preloader statistics

        Example:
            >>> stats = preloader.stop()
            >>> print(f"Cache hits: {stats['cache_hits']}")
        """
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            # Wake up the worker thread
            with self._file_ready:
                self._file_ready.notify_all()
            self._thread.join(timeout=2.0)

        # Clear cache to free memory
        with self._cache_lock:
            self._cache.clear()

        with self._stats_lock:
            stats = dict(self._stats)

        logger.info(f"[Preloader] Stopped. Stats: {stats}")
        return stats

    def get(
        self,
        file_path: Union[str, Path],
        blocking: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Get a preloaded NIfTI file.

        If the file is in cache, returns immediately (cache hit).
        Otherwise, waits for the preloader or loads synchronously.

        Args:
            file_path: Path to NIfTI file
            blocking: Wait for file if not in cache (default: True)

        Returns:
            Tuple of (volume array, metadata dict)

        Raises:
            TimeoutError: If blocking=True and file not available within timeout
            FileNotFoundError: If file does not exist

        Example:
            >>> volume, metadata = preloader.get("/path/to/file.nii.gz")
        """
        file_key = str(file_path)

        # Check cache first
        with self._cache_lock:
            if file_key in self._cache:
                # Move to end (LRU)
                self._cache.move_to_end(file_key)
                with self._stats_lock:
                    self._stats['cache_hits'] += 1
                logger.debug(f"[Preloader] Cache HIT: {Path(file_key).name}")
                return self._cache[file_key]

        # Cache miss
        with self._stats_lock:
            self._stats['cache_misses'] += 1

        if blocking:
            # Wait for the file to be preloaded (with timeout)
            start_time = time.time()
            while True:
                with self._cache_lock:
                    if file_key in self._cache:
                        self._cache.move_to_end(file_key)
                        return self._cache[file_key]

                if time.time() - start_time > self.timeout:
                    # Timeout - load synchronously
                    logger.warning(f"[Preloader] Timeout waiting for {Path(file_key).name}, loading sync")
                    return self._load_file(file_key)

                # Wait briefly
                time.sleep(0.1)
        else:
            # Non-blocking: load synchronously
            logger.debug(f"[Preloader] Cache MISS, loading sync: {Path(file_key).name}")
            return self._load_file(file_key)

    def prefetch(self, file_path: Union[str, Path]) -> None:
        """
        Request a specific file to be preloaded next.

        Useful when the processing order is known ahead of time.

        Args:
            file_path: Path to prefetch
        """
        file_key = str(file_path)

        with self._queue_lock:
            if file_key in self._queue:
                idx = self._queue.index(file_key)
                if idx > self._queue_index:
                    # Move to next position
                    self._queue.remove(file_key)
                    self._queue.insert(self._queue_index, file_key)

    def _preload_worker(self) -> None:
        """Background worker thread for preloading files."""
        while not self._stop_event.is_set():
            # Get next file to preload
            file_to_load = None

            with self._queue_lock:
                # Find next file not in cache
                while self._queue_index < len(self._queue):
                    candidate = self._queue[self._queue_index]
                    with self._cache_lock:
                        if candidate not in self._cache:
                            file_to_load = candidate
                            self._queue_index += 1
                            break
                    self._queue_index += 1

            if file_to_load is None:
                # No more files to preload
                time.sleep(0.1)
                continue

            # Load the file
            try:
                start_time = time.time()
                volume, metadata = self._load_file(file_to_load)
                load_time = time.time() - start_time

                # Add to cache
                with self._cache_lock:
                    self._cache[file_to_load] = (volume, metadata)

                    # Enforce cache size limit (LRU eviction)
                    while len(self._cache) > self.max_cache_size:
                        evicted = self._cache.popitem(last=False)
                        logger.debug(f"[Preloader] Evicted from cache: {Path(evicted[0]).name}")

                with self._stats_lock:
                    self._stats['files_preloaded'] += 1
                    self._stats['total_load_time'] += load_time

                logger.debug(f"[Preloader] Preloaded: {Path(file_to_load).name} ({load_time:.2f}s)")

            except Exception as e:
                logger.error(f"[Preloader] Failed to preload {file_to_load}: {e}")

    def _load_file(self, file_path: str) -> Tuple[np.ndarray, Dict]:
        """
        Load a NIfTI file synchronously.

        Args:
            file_path: Path to NIfTI file

        Returns:
            Tuple of (volume array, metadata dict)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"NIfTI file not found: {file_path}")

        img = nib.load(str(path))
        volume = img.get_fdata()

        metadata = {}
        if self.load_metadata:
            header = img.header
            metadata = {
                "affine": img.affine,
                "header": header,
                "spacing": tuple(float(s) for s in header.get_zooms()[:3]),
                "shape": volume.shape,
                "dtype": str(volume.dtype),
            }

        return volume, metadata

    @property
    def cache_size(self) -> int:
        """Current number of files in cache."""
        with self._cache_lock:
            return len(self._cache)

    @property
    def stats(self) -> Dict:
        """Get current statistics."""
        with self._stats_lock:
            return dict(self._stats)

    def is_cached(self, file_path: Union[str, Path]) -> bool:
        """Check if a file is in the cache."""
        with self._cache_lock:
            return str(file_path) in self._cache

    def clear_cache(self) -> None:
        """Clear the cache to free memory."""
        with self._cache_lock:
            self._cache.clear()
        logger.debug("[Preloader] Cache cleared")


# Convenience function for simple use cases
def preload_nifti_batch(
    file_list: List[Union[str, Path]],
    process_func: callable,
    max_cache_size: int = 2
) -> List:
    """
    Process a batch of NIfTI files with preloading.

    Convenience function that handles preloader lifecycle automatically.

    Args:
        file_list: List of NIfTI file paths
        process_func: Function that takes (volume, metadata, file_path) and returns result
        max_cache_size: Cache size for preloader (default: 2)

    Returns:
        List of results from process_func

    Example:
        >>> def process(vol, meta, path):
        ...     return vol.mean()
        >>> results = preload_nifti_batch(files, process)
    """
    preloader = AsyncNiftiPreloader(max_cache_size=max_cache_size)
    preloader.start(file_list)

    results = []
    try:
        for file_path in file_list:
            volume, metadata = preloader.get(file_path)
            result = process_func(volume, metadata, file_path)
            results.append(result)
    finally:
        preloader.stop()

    return results


if __name__ == "__main__":
    # Test code
    print("AsyncNiftiPreloader Test")
    print("=" * 60)

    # Simple functionality test (requires actual NIfTI files)
    preloader = AsyncNiftiPreloader(max_cache_size=2)
    print(f"[OK] Preloader initialized")
    print(f"     Cache size: {preloader.cache_size}")
    print(f"     Stats: {preloader.stats}")
