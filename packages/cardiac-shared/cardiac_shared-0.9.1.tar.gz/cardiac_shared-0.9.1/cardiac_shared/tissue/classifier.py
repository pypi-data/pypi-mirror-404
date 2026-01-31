#!/usr/bin/env python3
"""
Tissue Classification Module for Body Composition Analysis

Provides tissue-specific HU filtering and classification based on
Alberta Protocol 2024 and recent literature (2024-2025).

Tissue Types:
- Skeletal Muscle: -29 to 150 HU (Martin 2013, AWGS 2025)
- SAT (Subcutaneous Fat): -190 to -30 HU (Kvist 1988, Alberta 2024)
- VAT (Visceral Fat): -150 to -50 HU (Alberta Protocol 2024)
- IMAT (Intermuscular Fat): -190 to -30 HU (Goodpaster 2000)

Usage:
    from cardiac_shared.tissue import TissueClassifier, TISSUE_HU_RANGES

    classifier = TissueClassifier()

    # Filter tissue by HU range
    filtered_mask, stats = classifier.filter_by_hu(ct_array, mask, 'skeletal_muscle')

    # Calculate tissue metrics
    metrics = classifier.calculate_metrics(ct_array, mask, spacing)

Version: 1.0.0
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


class TissueType(Enum):
    """Standard tissue types for body composition analysis."""

    SKELETAL_MUSCLE = 'skeletal_muscle'
    SUBCUTANEOUS_FAT = 'subcutaneous_fat'
    VISCERAL_FAT = 'torso_fat'  # TotalSegmentator naming
    INTERMUSCULAR_FAT = 'intermuscular_fat'

    # Aliases
    SAT = 'subcutaneous_fat'
    VAT = 'torso_fat'
    IMAT = 'intermuscular_fat'


# Tissue-specific HU ranges (based on literature)
TISSUE_HU_RANGES: Dict[str, Dict[str, Any]] = {
    'skeletal_muscle': {
        'range': (-29, 150),
        'literature': 'Martin 2013, AWGS 2025',
        'description': 'Total skeletal muscle (includes myosteatosis)',
    },
    'subcutaneous_fat': {
        'range': (-190, -30),
        'literature': 'Kvist 1988, Alberta 2024',
        'description': 'Subcutaneous adipose tissue (broader range for edge effects)',
    },
    'torso_fat': {
        'range': (-150, -50),
        'literature': 'Alberta Protocol 2024',
        'description': 'Visceral adipose tissue (narrower range for higher purity)',
    },
    'intermuscular_fat': {
        'range': (-190, -30),
        'literature': 'Goodpaster 2000',
        'description': 'Intermuscular adipose tissue',
    },
}

# Muscle quality thresholds (Goodpaster 2000)
MUSCLE_QUALITY_THRESHOLDS = {
    'myosteatosis': 30,    # <30 HU indicates myosteatosis
    'normal_lower': 30,    # >=30 HU is normal muscle
    'normal_upper': 150,   # Upper limit for muscle
    'excellent': 50,       # >=50 HU is excellent quality
}


@dataclass
class TissueMetrics:
    """Metrics for a single tissue type."""

    tissue_type: str
    area_mm2: float = 0.0
    area_cm2: float = 0.0
    volume_mm3: float = 0.0
    mean_hu: float = 0.0
    std_hu: float = 0.0
    min_hu: float = 0.0
    max_hu: float = 0.0
    pixel_count: int = 0
    voxel_count: int = 0
    quality_grade: str = ''
    myosteatosis_pct: float = 0.0
    retention_pct: float = 100.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tissue_type': self.tissue_type,
            'area_mm2': self.area_mm2,
            'area_cm2': self.area_cm2,
            'volume_mm3': self.volume_mm3,
            'mean_hu': self.mean_hu,
            'std_hu': self.std_hu,
            'min_hu': self.min_hu,
            'max_hu': self.max_hu,
            'pixel_count': self.pixel_count,
            'voxel_count': self.voxel_count,
            'quality_grade': self.quality_grade,
            'myosteatosis_pct': self.myosteatosis_pct,
            'retention_pct': self.retention_pct,
        }


@dataclass
class FilterStats:
    """Statistics from HU filtering."""

    tissue_type: str
    original_pixels: int
    filtered_pixels: int
    retention_pct: float
    hu_range: Tuple[float, float]
    removed_pixels: int = 0
    mean_hu_before: float = 0.0
    mean_hu_after: float = 0.0


class TissueClassifier:
    """
    Classifies and filters tissues based on HU values.

    Implements tissue-specific HU filtering for body composition analysis
    following Alberta Protocol 2024 and literature standards.
    """

    def __init__(
        self,
        custom_hu_ranges: Optional[Dict[str, Tuple[float, float]]] = None
    ):
        """
        Initialize classifier.

        Args:
            custom_hu_ranges: Optional custom HU ranges to override defaults
        """
        # Deep copy to avoid modifying the original TISSUE_HU_RANGES
        import copy
        self.hu_ranges = copy.deepcopy(TISSUE_HU_RANGES)

        if custom_hu_ranges:
            for tissue, range_tuple in custom_hu_ranges.items():
                if tissue in self.hu_ranges:
                    self.hu_ranges[tissue]['range'] = range_tuple

    def get_hu_range(self, tissue_type: str) -> Tuple[float, float]:
        """
        Get HU range for a tissue type.

        Args:
            tissue_type: Tissue type name

        Returns:
            Tuple of (min_hu, max_hu)

        Raises:
            ValueError: If tissue type unknown
        """
        # Handle aliases
        if tissue_type.lower() == 'sat':
            tissue_type = 'subcutaneous_fat'
        elif tissue_type.lower() == 'vat':
            tissue_type = 'torso_fat'
        elif tissue_type.lower() == 'imat':
            tissue_type = 'intermuscular_fat'

        if tissue_type not in self.hu_ranges:
            available = list(self.hu_ranges.keys())
            raise ValueError(f"Unknown tissue type: {tissue_type}. Available: {available}")

        return self.hu_ranges[tissue_type]['range']

    def filter_by_hu(
        self,
        ct_array: np.ndarray,
        mask_array: np.ndarray,
        tissue_type: str,
        return_stats: bool = True
    ) -> Tuple[np.ndarray, Optional[FilterStats]]:
        """
        Apply HU filtering to a tissue mask.

        Args:
            ct_array: CT image as numpy array
            mask_array: Binary mask as numpy array
            tissue_type: Type of tissue
            return_stats: Whether to return filtering statistics

        Returns:
            Tuple of (filtered_mask, statistics)
        """
        hu_min, hu_max = self.get_hu_range(tissue_type)

        # Get tissue pixels
        tissue_pixels = mask_array > 0
        original_count = int(np.sum(tissue_pixels))

        if original_count == 0:
            stats = FilterStats(
                tissue_type=tissue_type,
                original_pixels=0,
                filtered_pixels=0,
                retention_pct=0.0,
                hu_range=(hu_min, hu_max),
            ) if return_stats else None
            return mask_array.copy(), stats

        # Extract HU values
        hu_values = ct_array[tissue_pixels]
        mean_hu_before = float(np.mean(hu_values))

        # Apply HU filter
        valid_hu_mask = (hu_values >= hu_min) & (hu_values <= hu_max)

        # Create filtered mask
        filtered_array = mask_array.copy()
        filtered_array[tissue_pixels] = valid_hu_mask.astype(mask_array.dtype)

        # Calculate statistics
        filtered_count = int(np.sum(filtered_array > 0))
        retention_pct = (filtered_count / original_count * 100) if original_count > 0 else 0.0

        # Mean HU after filtering
        if filtered_count > 0:
            mean_hu_after = float(np.mean(ct_array[filtered_array > 0]))
        else:
            mean_hu_after = 0.0

        stats = FilterStats(
            tissue_type=tissue_type,
            original_pixels=original_count,
            filtered_pixels=filtered_count,
            retention_pct=retention_pct,
            hu_range=(hu_min, hu_max),
            removed_pixels=original_count - filtered_count,
            mean_hu_before=mean_hu_before,
            mean_hu_after=mean_hu_after,
        ) if return_stats else None

        return filtered_array, stats

    def calculate_metrics(
        self,
        ct_array: np.ndarray,
        mask_array: np.ndarray,
        tissue_type: str,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        slice_idx: Optional[int] = None
    ) -> TissueMetrics:
        """
        Calculate tissue metrics from CT and mask.

        Args:
            ct_array: CT image as numpy array (z, y, x)
            mask_array: Binary mask as numpy array
            tissue_type: Type of tissue for HU filtering
            spacing: Voxel spacing in mm (z, y, x)
            slice_idx: If provided, calculate metrics for single slice only

        Returns:
            TissueMetrics object
        """
        if slice_idx is not None:
            # Single slice analysis
            ct_slice = ct_array[slice_idx]
            mask_slice = mask_array[slice_idx]
            tissue_pixels = mask_slice > 0
            pixel_size = spacing[1] * spacing[2]  # y * x
        else:
            # Full volume analysis
            tissue_pixels = mask_array > 0
            pixel_size = spacing[1] * spacing[2]

        pixel_count = int(np.sum(tissue_pixels))

        if pixel_count == 0:
            return TissueMetrics(tissue_type=tissue_type)

        # Extract HU values
        if slice_idx is not None:
            hu_values = ct_slice[tissue_pixels]
        else:
            hu_values = ct_array[tissue_pixels]

        # Calculate metrics
        area_mm2 = pixel_count * pixel_size
        voxel_volume = spacing[0] * spacing[1] * spacing[2]
        volume_mm3 = pixel_count * voxel_volume if slice_idx is None else 0.0

        # Muscle quality assessment
        quality_grade = ''
        myosteatosis_pct = 0.0

        if tissue_type in ['skeletal_muscle', 'muscle']:
            mean_hu = float(np.mean(hu_values))
            myosteatosis_mask = hu_values < MUSCLE_QUALITY_THRESHOLDS['myosteatosis']
            myosteatosis_pct = float(np.sum(myosteatosis_mask) / len(hu_values) * 100)

            if mean_hu >= MUSCLE_QUALITY_THRESHOLDS['excellent']:
                quality_grade = 'Excellent'
            elif mean_hu >= MUSCLE_QUALITY_THRESHOLDS['normal_lower']:
                quality_grade = 'Normal'
            else:
                quality_grade = 'Myosteatosis'

        return TissueMetrics(
            tissue_type=tissue_type,
            area_mm2=area_mm2,
            area_cm2=area_mm2 / 100,
            volume_mm3=volume_mm3,
            mean_hu=float(np.mean(hu_values)),
            std_hu=float(np.std(hu_values)),
            min_hu=float(np.min(hu_values)),
            max_hu=float(np.max(hu_values)),
            pixel_count=pixel_count,
            voxel_count=pixel_count if slice_idx is None else 0,
            quality_grade=quality_grade,
            myosteatosis_pct=myosteatosis_pct,
        )

    def classify_muscle_quality(self, mean_hu: float) -> str:
        """
        Classify muscle quality based on mean HU.

        Args:
            mean_hu: Mean HU of muscle tissue

        Returns:
            Quality grade string
        """
        if mean_hu >= MUSCLE_QUALITY_THRESHOLDS['excellent']:
            return 'Excellent'
        elif mean_hu >= MUSCLE_QUALITY_THRESHOLDS['normal_lower']:
            return 'Normal'
        else:
            return 'Myosteatosis'


# Convenience functions


def filter_tissue(
    ct_array: np.ndarray,
    mask_array: np.ndarray,
    tissue_type: str
) -> Tuple[np.ndarray, FilterStats]:
    """
    Filter tissue by HU range.

    Args:
        ct_array: CT image array
        mask_array: Binary mask array
        tissue_type: Tissue type name

    Returns:
        Tuple of (filtered_mask, statistics)
    """
    classifier = TissueClassifier()
    return classifier.filter_by_hu(ct_array, mask_array, tissue_type)


def get_tissue_hu_range(tissue_type: str) -> Tuple[float, float]:
    """
    Get HU range for a tissue type.

    Args:
        tissue_type: Tissue type name or alias (sat, vat, imat)

    Returns:
        Tuple of (min_hu, max_hu)
    """
    classifier = TissueClassifier()
    return classifier.get_hu_range(tissue_type)


def calculate_tissue_area(
    mask_array: np.ndarray,
    spacing: Tuple[float, float, float],
    slice_idx: Optional[int] = None
) -> float:
    """
    Calculate tissue area in mm^2.

    Args:
        mask_array: Binary mask array
        spacing: Voxel spacing in mm
        slice_idx: Optional slice index

    Returns:
        Area in mm^2
    """
    if slice_idx is not None:
        pixel_count = np.sum(mask_array[slice_idx] > 0)
    else:
        pixel_count = np.sum(mask_array > 0)

    pixel_size = spacing[1] * spacing[2]
    return float(pixel_count * pixel_size)
