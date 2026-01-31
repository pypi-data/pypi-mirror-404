"""
Unit tests for vertebra module
"""

import pytest
import tempfile
from pathlib import Path
import numpy as np

from cardiac_shared.vertebra import (
    VertebraDetector,
    VertebraInfo,
    VertebraROI,
    VERTEBRAE_ORDER,
    THORACIC_VERTEBRAE,
    LUMBAR_VERTEBRAE,
    parse_vertebrae,
    sort_vertebrae,
    is_valid_vertebra,
)


class TestVertebraInfo:
    """Tests for VertebraInfo class."""

    def test_vertebra_info_creation(self):
        """Test VertebraInfo creation."""
        info = VertebraInfo(name='T12')
        assert info.name == 'T12'
        assert info.level == 'T'
        assert info.number == 12

    def test_vertebra_level(self):
        """Test level property."""
        assert VertebraInfo(name='T12').level == 'T'
        assert VertebraInfo(name='L3').level == 'L'
        assert VertebraInfo(name='C7').level == 'C'
        assert VertebraInfo(name='S1').level == 'S'

    def test_vertebra_number(self):
        """Test number property."""
        assert VertebraInfo(name='T12').number == 12
        assert VertebraInfo(name='L3').number == 3
        assert VertebraInfo(name='T1').number == 1

    def test_is_thoracic(self):
        """Test is_thoracic method."""
        assert VertebraInfo(name='T12').is_thoracic() is True
        assert VertebraInfo(name='L3').is_thoracic() is False

    def test_is_lumbar(self):
        """Test is_lumbar method."""
        assert VertebraInfo(name='L3').is_lumbar() is True
        assert VertebraInfo(name='T12').is_lumbar() is False


class TestVertebraDetector:
    """Tests for VertebraDetector class."""

    def test_extract_vertebra_name(self):
        """Test _extract_vertebra_name method."""
        detector = VertebraDetector()

        # Standard pattern
        assert detector._extract_vertebra_name('vertebrae_T12.nii.gz') == 'T12'
        assert detector._extract_vertebra_name('vertebrae_L3.nii.gz') == 'L3'

        # Alternative pattern
        assert detector._extract_vertebra_name('T12_vertebra.nii.gz') == 'T12'

        # Direct pattern
        assert detector._extract_vertebra_name('T12.nii.gz') == 'T12'

        # Invalid
        assert detector._extract_vertebra_name('random_file.nii.gz') is None

    def test_get_center_slice(self):
        """Test get_center_slice method."""
        detector = VertebraDetector()

        # Create test mask
        mask = np.zeros((100, 50, 50), dtype=np.uint8)
        mask[40:60, 20:30, 20:30] = 1

        center = detector.get_center_slice(mask)
        assert center == 49  # Median of 40-59

    def test_get_slice_range(self):
        """Test get_slice_range method."""
        detector = VertebraDetector()

        mask = np.zeros((100, 50, 50), dtype=np.uint8)
        mask[40:60, 20:30, 20:30] = 1

        start, end = detector.get_slice_range(mask)
        assert start == 40
        assert end == 60

    def test_get_centroid(self):
        """Test get_centroid method."""
        detector = VertebraDetector()

        mask = np.zeros((100, 50, 50), dtype=np.uint8)
        mask[40:60, 20:30, 20:30] = 1

        z, y, x = detector.get_centroid(mask)
        assert 49 < z < 50
        assert 24 < y < 25
        assert 24 < x < 25

    def test_calculate_volume(self):
        """Test calculate_volume method."""
        detector = VertebraDetector()

        mask = np.zeros((10, 10, 10), dtype=np.uint8)
        mask[0:5, 0:5, 0:5] = 1  # 125 voxels

        # With 1mm spacing
        vol = detector.calculate_volume(mask, spacing=(1.0, 1.0, 1.0))
        assert vol == 125.0

        # With 2mm spacing
        vol = detector.calculate_volume(mask, spacing=(2.0, 2.0, 2.0))
        assert vol == 125.0 * 8  # 1000.0

    def test_create_roi(self):
        """Test create_roi method."""
        detector = VertebraDetector()

        mask = np.zeros((100, 50, 50), dtype=np.uint8)
        mask[40:60, 20:30, 20:30] = 1

        roi = detector.create_roi(mask, 'T12', padding_slices=5)

        assert roi.vertebra == 'T12'
        assert roi.center_slice == 49
        assert roi.slice_range == (35, 65)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_sort_vertebrae(self):
        """Test sort_vertebrae function."""
        unsorted = ['L3', 'T12', 'T10', 'L1']
        sorted_list = sort_vertebrae(unsorted)

        assert sorted_list == ['T10', 'T12', 'L1', 'L3']

    def test_is_valid_vertebra(self):
        """Test is_valid_vertebra function."""
        assert is_valid_vertebra('T12') is True
        assert is_valid_vertebra('L3') is True
        assert is_valid_vertebra('C7') is True
        assert is_valid_vertebra('t12') is True  # Case insensitive
        assert is_valid_vertebra('X99') is False


class TestConstants:
    """Tests for module constants."""

    def test_vertebrae_order(self):
        """Test VERTEBRAE_ORDER constant."""
        assert 'T12' in VERTEBRAE_ORDER
        assert 'L3' in VERTEBRAE_ORDER
        assert VERTEBRAE_ORDER.index('T12') < VERTEBRAE_ORDER.index('L1')

    def test_thoracic_vertebrae(self):
        """Test THORACIC_VERTEBRAE constant."""
        assert len(THORACIC_VERTEBRAE) == 12
        assert 'T1' in THORACIC_VERTEBRAE
        assert 'T12' in THORACIC_VERTEBRAE

    def test_lumbar_vertebrae(self):
        """Test LUMBAR_VERTEBRAE constant."""
        assert len(LUMBAR_VERTEBRAE) == 5
        assert 'L1' in LUMBAR_VERTEBRAE
        assert 'L5' in LUMBAR_VERTEBRAE


class TestImports:
    """Test module imports."""

    def test_import_from_main_module(self):
        """Test importing from cardiac_shared."""
        from cardiac_shared import (
            VertebraDetector,
            VertebraInfo,
            VertebraROI,
            parse_vertebrae,
            sort_vertebrae,
            VERTEBRAE_ORDER,
        )

        assert VertebraDetector is not None
        assert VertebraInfo is not None
