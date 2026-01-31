"""
Vertebra Detection and Analysis Module

Provides utilities for vertebra detection, parsing, and ROI calculation.

Usage:
    from cardiac_shared.vertebra import (
        VertebraDetector,
        VertebraInfo,
        parse_vertebrae,
        sort_vertebrae,
    )

    # Find vertebrae in labels directory
    detector = VertebraDetector()
    vertebrae = detector.find_vertebrae('/path/to/labels')

    # Simple parsing
    names = parse_vertebrae('/path/to/labels')
    print(f"Found: {names}")  # ['T10', 'T11', 'T12', 'L1']
"""

from .detector import (
    BODY_COMP_VERTEBRAE,
    LUMBAR_VERTEBRAE,
    THORACIC_VERTEBRAE,
    VERTEBRAE_ORDER,
    VertebraDetector,
    VertebraInfo,
    VertebraROI,
    get_vertebra_file,
    is_valid_vertebra,
    parse_vertebrae,
    sort_vertebrae,
)

__all__ = [
    # Classes
    'VertebraDetector',
    'VertebraInfo',
    'VertebraROI',
    # Constants
    'VERTEBRAE_ORDER',
    'THORACIC_VERTEBRAE',
    'LUMBAR_VERTEBRAE',
    'BODY_COMP_VERTEBRAE',
    # Functions
    'parse_vertebrae',
    'get_vertebra_file',
    'sort_vertebrae',
    'is_valid_vertebra',
]
