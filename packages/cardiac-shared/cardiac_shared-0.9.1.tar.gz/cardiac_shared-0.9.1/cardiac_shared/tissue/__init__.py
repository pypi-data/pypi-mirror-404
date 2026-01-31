"""
Tissue Classification Module for Body Composition Analysis

Provides tissue-specific HU filtering and classification.

Usage:
    from cardiac_shared.tissue import (
        TissueClassifier,
        TissueMetrics,
        TISSUE_HU_RANGES,
        filter_tissue,
    )

    # Filter muscle by HU range
    filtered, stats = filter_tissue(ct_array, mask, 'skeletal_muscle')
    print(f"Retention: {stats.retention_pct:.1f}%")

    # Calculate tissue metrics
    classifier = TissueClassifier()
    metrics = classifier.calculate_metrics(ct_array, mask, 'skeletal_muscle', spacing)
    print(f"Area: {metrics.area_cm2:.1f} cm^2")
"""

from .classifier import (
    MUSCLE_QUALITY_THRESHOLDS,
    TISSUE_HU_RANGES,
    FilterStats,
    TissueClassifier,
    TissueMetrics,
    TissueType,
    calculate_tissue_area,
    filter_tissue,
    get_tissue_hu_range,
)

__all__ = [
    # Classes
    'TissueClassifier',
    'TissueMetrics',
    'FilterStats',
    'TissueType',
    # Constants
    'TISSUE_HU_RANGES',
    'MUSCLE_QUALITY_THRESHOLDS',
    # Functions
    'filter_tissue',
    'get_tissue_hu_range',
    'calculate_tissue_area',
]
