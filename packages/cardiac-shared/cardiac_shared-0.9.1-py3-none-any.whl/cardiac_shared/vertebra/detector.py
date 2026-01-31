#!/usr/bin/env python3
"""
Vertebra Detection and Analysis Module

Provides utilities for vertebra detection, parsing, and ROI calculation
for body composition analysis.

Usage:
    from cardiac_shared.vertebra import VertebraDetector, parse_vertebrae

    # Parse vertebrae from label files
    vertebrae = parse_vertebrae(labels_dir)
    print(f"Found vertebrae: {vertebrae}")

    # Get vertebra center slice
    detector = VertebraDetector()
    center_slice = detector.get_center_slice(vertebra_mask)

Version: 1.0.0
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np


# Standard vertebrae order (cranial to caudal)
VERTEBRAE_ORDER = [
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7',  # Cervical
    'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12',  # Thoracic
    'L1', 'L2', 'L3', 'L4', 'L5',  # Lumbar
    'S1',  # Sacral (first sacral vertebra)
]

# Vertebrae commonly used for body composition analysis
THORACIC_VERTEBRAE = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12']
LUMBAR_VERTEBRAE = ['L1', 'L2', 'L3', 'L4', 'L5']
BODY_COMP_VERTEBRAE = ['T12', 'L3']  # Most common for body composition


@dataclass
class VertebraInfo:
    """Information about a detected vertebra."""

    name: str
    file_path: Optional[Path] = None
    center_slice: Optional[int] = None
    z_range: Optional[Tuple[int, int]] = None
    volume_mm3: Optional[float] = None
    centroid: Optional[Tuple[float, float, float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def level(self) -> str:
        """Return vertebra level (e.g., 'T' for T12, 'L' for L3)."""
        if self.name and len(self.name) > 0:
            return self.name[0]
        return ''

    @property
    def number(self) -> int:
        """Return vertebra number (e.g., 12 for T12, 3 for L3)."""
        match = re.search(r'(\d+)', self.name)
        if match:
            return int(match.group(1))
        return 0

    def is_thoracic(self) -> bool:
        """Check if vertebra is thoracic."""
        return self.level == 'T'

    def is_lumbar(self) -> bool:
        """Check if vertebra is lumbar."""
        return self.level == 'L'


@dataclass
class VertebraROI:
    """Region of interest around a vertebra."""

    vertebra: str
    center_slice: int
    slice_range: Tuple[int, int]
    mask: Optional[np.ndarray] = None

    @property
    def num_slices(self) -> int:
        """Return number of slices in ROI."""
        return self.slice_range[1] - self.slice_range[0]


class VertebraDetector:
    """
    Detects and analyzes vertebrae from segmentation masks.

    Works with TotalSegmentator output format where vertebrae are
    saved as individual files (vertebrae_T12.nii.gz, etc.).
    """

    def __init__(self, file_pattern: str = "vertebrae_{}.nii.gz"):
        """
        Initialize detector.

        Args:
            file_pattern: Pattern for vertebra files. {} is replaced with vertebra name.
        """
        self.file_pattern = file_pattern

    def find_vertebrae(self, labels_dir: Union[str, Path]) -> List[VertebraInfo]:
        """
        Find all vertebra files in a directory.

        Args:
            labels_dir: Directory containing vertebra label files

        Returns:
            List of VertebraInfo objects, sorted cranial to caudal
        """
        labels_dir = Path(labels_dir)
        if not labels_dir.exists():
            return []

        vertebrae = []

        # Try common patterns
        patterns = [
            'vertebrae_*.nii.gz',
            'vertebra_*.nii.gz',
            '*_vertebra_*.nii.gz',
        ]

        for pattern in patterns:
            for file_path in labels_dir.glob(pattern):
                name = self._extract_vertebra_name(file_path.name)
                if name:
                    vertebrae.append(VertebraInfo(
                        name=name,
                        file_path=file_path,
                    ))

        # Sort by anatomical order
        return self._sort_vertebrae(vertebrae)

    def _extract_vertebra_name(self, filename: str) -> Optional[str]:
        """Extract vertebra name from filename."""
        # Pattern: vertebrae_T12.nii.gz -> T12
        match = re.search(r'vertebrae?_([CTLS]\d+)', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Pattern: T12_vertebra.nii.gz -> T12
        match = re.search(r'([CTLS]\d+)_vertebrae?', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        # Direct pattern: T12.nii.gz
        match = re.search(r'^([CTLS]\d+)\.nii', filename, re.IGNORECASE)
        if match:
            return match.group(1).upper()

        return None

    def _sort_vertebrae(self, vertebrae: List[VertebraInfo]) -> List[VertebraInfo]:
        """Sort vertebrae from cranial to caudal."""
        def sort_key(v: VertebraInfo) -> int:
            try:
                return VERTEBRAE_ORDER.index(v.name)
            except ValueError:
                return 999  # Unknown vertebrae at end
        return sorted(vertebrae, key=sort_key)

    def get_center_slice(
        self,
        mask: np.ndarray,
        axis: int = 0
    ) -> int:
        """
        Calculate the center slice of a vertebra mask.

        Args:
            mask: 3D binary mask array
            axis: Axis to calculate center along (default 0 = axial/z)

        Returns:
            Center slice index
        """
        if mask is None or mask.size == 0:
            return 0

        # Find slices containing the mask
        slices_with_mask = np.where(np.any(mask, axis=tuple(i for i in range(3) if i != axis)))[0]

        if len(slices_with_mask) == 0:
            return 0

        # Return middle slice
        return int(np.median(slices_with_mask))

    def get_slice_range(
        self,
        mask: np.ndarray,
        axis: int = 0
    ) -> Tuple[int, int]:
        """
        Get the slice range containing the vertebra.

        Args:
            mask: 3D binary mask array
            axis: Axis to calculate range along

        Returns:
            Tuple of (start_slice, end_slice)
        """
        if mask is None or mask.size == 0:
            return (0, 0)

        slices_with_mask = np.where(np.any(mask, axis=tuple(i for i in range(3) if i != axis)))[0]

        if len(slices_with_mask) == 0:
            return (0, 0)

        return (int(slices_with_mask.min()), int(slices_with_mask.max()) + 1)

    def get_centroid(self, mask: np.ndarray) -> Tuple[float, float, float]:
        """
        Calculate the centroid of a vertebra mask.

        Args:
            mask: 3D binary mask array

        Returns:
            Tuple of (z, y, x) centroid coordinates
        """
        if mask is None or mask.size == 0:
            return (0.0, 0.0, 0.0)

        indices = np.where(mask > 0)
        if len(indices[0]) == 0:
            return (0.0, 0.0, 0.0)

        return (
            float(np.mean(indices[0])),
            float(np.mean(indices[1])),
            float(np.mean(indices[2])),
        )

    def calculate_volume(
        self,
        mask: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> float:
        """
        Calculate volume of vertebra mask in mm^3.

        Args:
            mask: 3D binary mask array
            spacing: Voxel spacing (z, y, x) in mm

        Returns:
            Volume in mm^3
        """
        if mask is None or mask.size == 0:
            return 0.0

        voxel_count = np.sum(mask > 0)
        voxel_volume = spacing[0] * spacing[1] * spacing[2]

        return float(voxel_count * voxel_volume)

    def analyze_vertebra(
        self,
        mask: np.ndarray,
        name: str,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        file_path: Optional[Path] = None
    ) -> VertebraInfo:
        """
        Perform full analysis of a vertebra mask.

        Args:
            mask: 3D binary mask array
            name: Vertebra name (e.g., 'T12')
            spacing: Voxel spacing in mm
            file_path: Path to the mask file

        Returns:
            VertebraInfo with all calculated properties
        """
        z_range = self.get_slice_range(mask)
        center_slice = self.get_center_slice(mask)
        centroid = self.get_centroid(mask)
        volume = self.calculate_volume(mask, spacing)

        return VertebraInfo(
            name=name,
            file_path=file_path,
            center_slice=center_slice,
            z_range=z_range,
            volume_mm3=volume,
            centroid=centroid,
        )

    def create_roi(
        self,
        mask: np.ndarray,
        vertebra: str,
        padding_slices: int = 0
    ) -> VertebraROI:
        """
        Create a region of interest around a vertebra.

        Args:
            mask: 3D binary mask array
            vertebra: Vertebra name
            padding_slices: Additional slices to include above/below

        Returns:
            VertebraROI object
        """
        center = self.get_center_slice(mask)
        z_range = self.get_slice_range(mask)

        # Apply padding
        padded_range = (
            max(0, z_range[0] - padding_slices),
            min(mask.shape[0], z_range[1] + padding_slices)
        )

        return VertebraROI(
            vertebra=vertebra,
            center_slice=center,
            slice_range=padded_range,
            mask=mask,
        )


# Convenience functions


def parse_vertebrae(labels_dir: Union[str, Path]) -> List[str]:
    """
    Parse vertebra names from a labels directory.

    Args:
        labels_dir: Directory containing vertebra label files

    Returns:
        List of vertebra names (e.g., ['T10', 'T11', 'T12', 'L1'])
    """
    detector = VertebraDetector()
    vertebrae = detector.find_vertebrae(labels_dir)
    return [v.name for v in vertebrae]


def get_vertebra_file(
    labels_dir: Union[str, Path],
    vertebra: str,
    pattern: str = "vertebrae_{}.nii.gz"
) -> Optional[Path]:
    """
    Get the file path for a specific vertebra.

    Args:
        labels_dir: Directory containing vertebra label files
        vertebra: Vertebra name (e.g., 'T12')
        pattern: File pattern ({} is replaced with vertebra name)

    Returns:
        Path to vertebra file or None if not found
    """
    labels_dir = Path(labels_dir)
    file_path = labels_dir / pattern.format(vertebra)

    if file_path.exists():
        return file_path

    # Try case-insensitive search
    for f in labels_dir.glob(f"*{vertebra}*"):
        if f.suffix == '.gz' or f.suffix == '.nii':
            return f

    return None


def sort_vertebrae(vertebrae: List[str]) -> List[str]:
    """
    Sort vertebrae from cranial to caudal.

    Args:
        vertebrae: List of vertebra names

    Returns:
        Sorted list
    """
    def sort_key(name: str) -> int:
        try:
            return VERTEBRAE_ORDER.index(name.upper())
        except ValueError:
            return 999
    return sorted(vertebrae, key=sort_key)


def is_valid_vertebra(name: str) -> bool:
    """
    Check if a vertebra name is valid.

    Args:
        name: Vertebra name

    Returns:
        True if valid
    """
    return name.upper() in VERTEBRAE_ORDER
