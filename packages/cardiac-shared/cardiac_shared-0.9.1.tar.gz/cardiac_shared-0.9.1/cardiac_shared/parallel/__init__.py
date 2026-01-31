"""
Parallel Processing Module

Provides unified parallel processing framework for medical imaging pipelines.
"""

from cardiac_shared.parallel.processor import (
    ParallelProcessor,
    ProcessingResult,
    Checkpoint,
    parallel_map,
    parallel_map_with_checkpoint,
)

__all__ = [
    'ParallelProcessor',
    'ProcessingResult',
    'Checkpoint',
    'parallel_map',
    'parallel_map_with_checkpoint',
]
