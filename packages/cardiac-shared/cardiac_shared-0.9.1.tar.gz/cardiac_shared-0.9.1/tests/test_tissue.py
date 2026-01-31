"""
Unit tests for tissue module
"""

import pytest
import numpy as np

from cardiac_shared.tissue import (
    TissueClassifier,
    TissueMetrics,
    FilterStats,
    TissueType,
    TISSUE_HU_RANGES,
    MUSCLE_QUALITY_THRESHOLDS,
    filter_tissue,
    get_tissue_hu_range,
    calculate_tissue_area,
)


class TestTissueType:
    """Tests for TissueType enum."""

    def test_tissue_types(self):
        """Test TissueType values."""
        assert TissueType.SKELETAL_MUSCLE.value == 'skeletal_muscle'
        assert TissueType.SAT.value == 'subcutaneous_fat'
        assert TissueType.VAT.value == 'torso_fat'
        assert TissueType.IMAT.value == 'intermuscular_fat'


class TestTissueMetrics:
    """Tests for TissueMetrics class."""

    def test_tissue_metrics_creation(self):
        """Test TissueMetrics creation."""
        metrics = TissueMetrics(
            tissue_type='skeletal_muscle',
            area_mm2=1500.0,
            area_cm2=15.0,
            mean_hu=45.0,
        )

        assert metrics.tissue_type == 'skeletal_muscle'
        assert metrics.area_mm2 == 1500.0
        assert metrics.area_cm2 == 15.0
        assert metrics.mean_hu == 45.0

    def test_tissue_metrics_to_dict(self):
        """Test to_dict method."""
        metrics = TissueMetrics(
            tissue_type='skeletal_muscle',
            area_cm2=15.0,
        )

        d = metrics.to_dict()
        assert d['tissue_type'] == 'skeletal_muscle'
        assert d['area_cm2'] == 15.0


class TestTissueClassifier:
    """Tests for TissueClassifier class."""

    def test_get_hu_range(self):
        """Test get_hu_range method."""
        classifier = TissueClassifier()

        # Standard tissue types
        assert classifier.get_hu_range('skeletal_muscle') == (-29, 150)
        assert classifier.get_hu_range('torso_fat') == (-150, -50)

        # Aliases
        assert classifier.get_hu_range('sat') == (-190, -30)
        assert classifier.get_hu_range('vat') == (-150, -50)
        assert classifier.get_hu_range('imat') == (-190, -30)

        # Unknown type
        with pytest.raises(ValueError):
            classifier.get_hu_range('unknown')

    def test_custom_hu_ranges(self):
        """Test custom HU ranges."""
        custom = {'skeletal_muscle': (-30, 100)}
        classifier = TissueClassifier(custom_hu_ranges=custom)

        assert classifier.get_hu_range('skeletal_muscle') == (-30, 100)

    def test_filter_by_hu(self):
        """Test filter_by_hu method."""
        classifier = TissueClassifier()

        # Create test data
        ct_array = np.array([[[50, 200, -100]]])  # Shape (1, 1, 3)
        mask_array = np.array([[[1, 1, 1]]])  # All pixels in mask

        filtered, stats = classifier.filter_by_hu(
            ct_array, mask_array, 'skeletal_muscle'
        )

        # Only 50 HU should pass (-29 to 150)
        assert np.sum(filtered) == 1
        assert stats.original_pixels == 3
        assert stats.filtered_pixels == 1

    def test_filter_by_hu_empty_mask(self):
        """Test filter_by_hu with empty mask."""
        classifier = TissueClassifier()

        ct_array = np.array([[[50, 100]]])
        mask_array = np.array([[[0, 0]]])

        filtered, stats = classifier.filter_by_hu(
            ct_array, mask_array, 'skeletal_muscle'
        )

        assert stats.original_pixels == 0
        assert stats.retention_pct == 0.0

    def test_calculate_metrics(self):
        """Test calculate_metrics method."""
        classifier = TissueClassifier()

        # Create test data: 3x3x3 cube
        ct_array = np.full((3, 3, 3), 40.0)  # 40 HU throughout
        mask_array = np.ones((3, 3, 3), dtype=np.uint8)

        metrics = classifier.calculate_metrics(
            ct_array, mask_array, 'skeletal_muscle',
            spacing=(1.0, 1.0, 1.0)
        )

        assert metrics.tissue_type == 'skeletal_muscle'
        assert metrics.voxel_count == 27  # 3x3x3
        assert metrics.mean_hu == 40.0
        assert metrics.quality_grade == 'Normal'

    def test_calculate_metrics_single_slice(self):
        """Test calculate_metrics for single slice."""
        classifier = TissueClassifier()

        ct_array = np.full((5, 10, 10), 50.0)
        mask_array = np.zeros((5, 10, 10), dtype=np.uint8)
        mask_array[2, 2:8, 2:8] = 1  # 36 pixels in slice 2

        metrics = classifier.calculate_metrics(
            ct_array, mask_array, 'skeletal_muscle',
            spacing=(1.0, 1.0, 1.0),
            slice_idx=2
        )

        assert metrics.pixel_count == 36
        assert metrics.area_mm2 == 36.0
        assert metrics.area_cm2 == 0.36

    def test_classify_muscle_quality(self):
        """Test classify_muscle_quality method."""
        classifier = TissueClassifier()

        assert classifier.classify_muscle_quality(55) == 'Excellent'
        assert classifier.classify_muscle_quality(40) == 'Normal'
        assert classifier.classify_muscle_quality(25) == 'Myosteatosis'


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_tissue_hu_range(self):
        """Test get_tissue_hu_range function."""
        assert get_tissue_hu_range('skeletal_muscle') == (-29, 150)
        assert get_tissue_hu_range('vat') == (-150, -50)

    def test_filter_tissue(self):
        """Test filter_tissue function."""
        ct_array = np.array([[[50, 200]]])
        mask_array = np.array([[[1, 1]]])

        filtered, stats = filter_tissue(ct_array, mask_array, 'skeletal_muscle')

        assert np.sum(filtered) == 1
        assert stats.filtered_pixels == 1

    def test_calculate_tissue_area(self):
        """Test calculate_tissue_area function."""
        mask_array = np.zeros((10, 10, 10), dtype=np.uint8)
        mask_array[5, 2:8, 2:8] = 1  # 36 pixels

        # Test with 1mm spacing
        area = calculate_tissue_area(mask_array, (1.0, 1.0, 1.0), slice_idx=5)
        assert area == 36.0

        # Test with 0.5mm x 0.5mm pixels
        area = calculate_tissue_area(mask_array, (1.0, 0.5, 0.5), slice_idx=5)
        assert area == 9.0  # 36 * 0.25


class TestConstants:
    """Tests for module constants."""

    def test_tissue_hu_ranges(self):
        """Test TISSUE_HU_RANGES constant."""
        assert 'skeletal_muscle' in TISSUE_HU_RANGES
        assert 'torso_fat' in TISSUE_HU_RANGES
        assert 'subcutaneous_fat' in TISSUE_HU_RANGES
        assert 'intermuscular_fat' in TISSUE_HU_RANGES

        assert TISSUE_HU_RANGES['skeletal_muscle']['range'] == (-29, 150)

    def test_muscle_quality_thresholds(self):
        """Test MUSCLE_QUALITY_THRESHOLDS constant."""
        assert MUSCLE_QUALITY_THRESHOLDS['myosteatosis'] == 30
        assert MUSCLE_QUALITY_THRESHOLDS['excellent'] == 50


class TestImports:
    """Test module imports."""

    def test_import_from_main_module(self):
        """Test importing from cardiac_shared."""
        from cardiac_shared import (
            TissueClassifier,
            TissueMetrics,
            FilterStats,
            TISSUE_HU_RANGES,
            filter_tissue,
            get_tissue_hu_range,
        )

        assert TissueClassifier is not None
        assert TISSUE_HU_RANGES is not None
