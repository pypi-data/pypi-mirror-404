"""
Slice Thickness Detection Module.

Automatically detects CT slice thickness from DICOM metadata, NIfTI headers,
or computes it from slice positions when metadata is unavailable.

Example:
    >>> from cardiac_shared.preprocessing import ThicknessDetector, ThicknessInfo
    >>> detector = ThicknessDetector()
    >>> info = detector.detect_from_dicom(dicom_series)
    >>> print(f"Detected: {info.thickness}mm ({info.category})")

    >>> # Or use convenience function
    >>> from cardiac_shared.preprocessing import detect_thickness
    >>> info = detect_thickness(dicom_datasets=dicom_series)
"""

from typing import List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ThicknessSource(Enum):
    """Source of thickness information."""
    DICOM_METADATA = "dicom_metadata"
    NIFTI_HEADER = "nifti_header"
    Z_SPACING = "z_spacing"
    MANUAL = "manual"
    UNKNOWN = "unknown"


class ThicknessCategory(Enum):
    """CT slice thickness categories for clinical classification."""
    THIN = "thin"        # <= 1.5mm
    MEDIUM = "medium"    # 1.5-2.5mm  
    THICK = "thick"      # > 2.5mm
    UNKNOWN = "unknown"


@dataclass
class ThicknessInfo:
    """
    Container for slice thickness information.
    
    Attributes:
        thickness: Slice thickness in mm
        source: How the thickness was determined
        confidence: Confidence score (0.0 to 1.0)
        z_spacing: Actual z-spacing if different from thickness
    """
    thickness: float  # in mm
    source: ThicknessSource
    confidence: float  # 0.0 to 1.0
    z_spacing: Optional[float] = None

    @property
    def is_thin(self) -> bool:
        """Check if this is thin-slice CT (<=1.5mm)."""
        return self.thickness <= 1.5

    @property
    def is_medium(self) -> bool:
        """Check if this is medium-slice CT (1.5-2.5mm)."""
        return 1.5 < self.thickness <= 2.5

    @property
    def is_thick(self) -> bool:
        """Check if this is thick-slice CT (>2.5mm)."""
        return self.thickness > 2.5

    @property
    def category(self) -> ThicknessCategory:
        """Get thickness category."""
        if self.is_thin:
            return ThicknessCategory.THIN
        elif self.is_medium:
            return ThicknessCategory.MEDIUM
        elif self.is_thick:
            return ThicknessCategory.THICK
        return ThicknessCategory.UNKNOWN

    @property
    def category_str(self) -> str:
        """Get thickness category as string."""
        return self.category.value

    @property
    def resolution_ratio(self) -> float:
        """Calculate resolution ratio relative to 1.0mm baseline."""
        return self.thickness / 1.0

    def is_compatible_with(self, target_thickness: float, tolerance: float = 0.5) -> bool:
        """Check if thickness is compatible with target (within tolerance)."""
        return abs(self.thickness - target_thickness) <= tolerance

    def __str__(self) -> str:
        return f"ThicknessInfo({self.thickness:.2f}mm, {self.category_str}, source={self.source.value}, conf={self.confidence:.2f})"

    def __repr__(self) -> str:
        return self.__str__()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'thickness': self.thickness,
            'source': self.source.value,
            'confidence': self.confidence,
            'z_spacing': self.z_spacing,
            'category': self.category_str,
            'is_thin': self.is_thin,
            'is_medium': self.is_medium,
            'is_thick': self.is_thick,
        }


class ThicknessDetector:
    """
    Automatic CT slice thickness detector.
    
    Supports multiple detection methods:
    1. DICOM SliceThickness metadata
    2. Z-spacing calculation from ImagePositionPatient
    3. NIfTI header z-spacing
    4. Manual specification
    
    Example:
        >>> detector = ThicknessDetector()
        >>> info = detector.detect_from_dicom(dicom_series)
        >>> print(f"Detected thickness: {info.thickness}mm")
        
        >>> # From NIfTI file
        >>> info = detector.detect_from_nifti('/path/to/file.nii.gz')
    """
    
    # Standard slice thicknesses for validation
    STANDARD_THICKNESSES = [0.5, 0.625, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 5.0]
    TOLERANCE = 0.1  # mm tolerance for standard thickness matching
    
    # Thickness ranges for filtering
    THIN_RANGE = (0.0, 1.5)
    MEDIUM_RANGE = (1.5, 2.5)
    THICK_RANGE = (2.5, 10.0)

    def __init__(self, default_thickness: float = 5.0):
        """
        Initialize the thickness detector.
        
        Args:
            default_thickness: Default thickness to use when detection fails (mm)
        """
        self.default_thickness = default_thickness

    def detect_from_dicom(
        self,
        dicom_datasets: List,
        prefer_z_spacing: bool = False
    ) -> ThicknessInfo:
        """
        Detect slice thickness from DICOM datasets.
        
        Args:
            dicom_datasets: List of pydicom Dataset objects
            prefer_z_spacing: If True, prefer z-spacing calculation over metadata
            
        Returns:
            ThicknessInfo with detected thickness and metadata
        """
        if not dicom_datasets:
            logger.warning("Empty DICOM series provided")
            return ThicknessInfo(
                thickness=self.default_thickness,
                source=ThicknessSource.UNKNOWN,
                confidence=0.0
            )
        
        # Try both methods
        metadata_thickness = self._get_from_dicom_metadata(dicom_datasets[0])
        z_spacing = self._calculate_z_spacing(dicom_datasets)
        
        # Decide which to use
        if prefer_z_spacing and z_spacing is not None:
            return ThicknessInfo(
                thickness=z_spacing,
                source=ThicknessSource.Z_SPACING,
                confidence=self._calculate_confidence(z_spacing, len(dicom_datasets)),
                z_spacing=z_spacing
            )
        
        if metadata_thickness is not None:
            confidence = 0.95 if self._is_standard_thickness(metadata_thickness) else 0.85
            return ThicknessInfo(
                thickness=metadata_thickness,
                source=ThicknessSource.DICOM_METADATA,
                confidence=confidence,
                z_spacing=z_spacing
            )
        
        if z_spacing is not None:
            return ThicknessInfo(
                thickness=z_spacing,
                source=ThicknessSource.Z_SPACING,
                confidence=self._calculate_confidence(z_spacing, len(dicom_datasets)),
                z_spacing=z_spacing
            )
        
        # Fallback to default
        logger.warning(f"Could not detect thickness, using default: {self.default_thickness}mm")
        return ThicknessInfo(
            thickness=self.default_thickness,
            source=ThicknessSource.UNKNOWN,
            confidence=0.0
        )

    def detect_from_nifti(
        self,
        nifti_path: Union[str, Path],
        use_sitk: bool = True
    ) -> ThicknessInfo:
        """
        Detect slice thickness from NIfTI file header.
        
        Args:
            nifti_path: Path to NIfTI file
            use_sitk: Use SimpleITK (True) or nibabel (False)
            
        Returns:
            ThicknessInfo with detected thickness
        """
        nifti_path = Path(nifti_path)
        
        if not nifti_path.exists():
            logger.warning(f"NIfTI file not found: {nifti_path}")
            return ThicknessInfo(
                thickness=self.default_thickness,
                source=ThicknessSource.UNKNOWN,
                confidence=0.0
            )
        
        try:
            if use_sitk:
                import SimpleITK as sitk
                img = sitk.ReadImage(str(nifti_path))
                spacing = img.GetSpacing()
                z_spacing = spacing[2]  # z is typically the third dimension
            else:
                import nibabel as nib
                img = nib.load(str(nifti_path))
                z_spacing = abs(img.header.get_zooms()[2])
            
            confidence = 0.9 if self._is_standard_thickness(z_spacing) else 0.8
            
            return ThicknessInfo(
                thickness=z_spacing,
                source=ThicknessSource.NIFTI_HEADER,
                confidence=confidence,
                z_spacing=z_spacing
            )
            
        except Exception as e:
            logger.warning(f"Failed to read NIfTI header: {e}")
            return ThicknessInfo(
                thickness=self.default_thickness,
                source=ThicknessSource.UNKNOWN,
                confidence=0.0
            )

    def detect_from_array(
        self,
        volume: np.ndarray,
        voxel_spacing: Tuple[float, float, float]
    ) -> ThicknessInfo:
        """
        Detect slice thickness from numpy array with known voxel spacing.
        
        Args:
            volume: 3D numpy array
            voxel_spacing: Tuple of (x_spacing, y_spacing, z_spacing) in mm
            
        Returns:
            ThicknessInfo with detected thickness
        """
        z_spacing = voxel_spacing[2]
        
        return ThicknessInfo(
            thickness=z_spacing,
            source=ThicknessSource.Z_SPACING,
            confidence=0.9,
            z_spacing=z_spacing
        )

    def set_manual(self, thickness: float) -> ThicknessInfo:
        """
        Manually specify slice thickness.
        
        Args:
            thickness: Slice thickness in mm
            
        Returns:
            ThicknessInfo with manual thickness
        """
        return ThicknessInfo(
            thickness=thickness,
            source=ThicknessSource.MANUAL,
            confidence=1.0
        )

    def _get_from_dicom_metadata(self, dicom_ds) -> Optional[float]:
        """Extract slice thickness from DICOM metadata."""
        # Try SliceThickness tag
        if hasattr(dicom_ds, 'SliceThickness'):
            try:
                return float(dicom_ds.SliceThickness)
            except (ValueError, TypeError):
                pass
        
        # Try SpacingBetweenSlices as fallback
        if hasattr(dicom_ds, 'SpacingBetweenSlices'):
            try:
                return float(dicom_ds.SpacingBetweenSlices)
            except (ValueError, TypeError):
                pass
        
        return None

    def _calculate_z_spacing(self, dicom_datasets: List) -> Optional[float]:
        """Calculate z-spacing from slice positions."""
        if len(dicom_datasets) < 2:
            return None
        
        z_positions = []
        for ds in dicom_datasets:
            if hasattr(ds, 'ImagePositionPatient'):
                try:
                    z_pos = float(ds.ImagePositionPatient[2])
                    z_positions.append(z_pos)
                except (IndexError, TypeError, ValueError):
                    continue
        
        if len(z_positions) < 2:
            return None
        
        # Sort and calculate spacing
        z_positions = sorted(z_positions)
        spacings = np.diff(z_positions)
        
        # Use median to handle potential outliers
        z_spacing = abs(np.median(spacings))
        
        # Validate spacing is reasonable (0.1mm to 10mm)
        if 0.1 <= z_spacing <= 10.0:
            return z_spacing
        
        return None

    def _is_standard_thickness(self, thickness: float) -> bool:
        """Check if thickness matches a standard value."""
        for std in self.STANDARD_THICKNESSES:
            if abs(thickness - std) <= self.TOLERANCE:
                return True
        return False

    def _calculate_confidence(self, z_spacing: float, num_slices: int) -> float:
        """Calculate confidence based on z-spacing and number of slices."""
        # More slices = higher confidence
        slice_confidence = min(1.0, num_slices / 100)
        
        # Standard thickness = higher confidence
        std_confidence = 0.9 if self._is_standard_thickness(z_spacing) else 0.7
        
        return slice_confidence * std_confidence

    def validate_thickness(self, info: ThicknessInfo) -> Tuple[bool, str]:
        """
        Validate detected thickness for processing.
        
        Args:
            info: ThicknessInfo to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if info.thickness < 0.5:
            return False, f"Thickness {info.thickness}mm is too thin for reliable processing"
        
        if info.thickness > 10.0:
            return False, f"Thickness {info.thickness}mm is too thick for processing"
        
        if info.confidence < 0.5:
            return True, f"Warning: Low confidence ({info.confidence:.2f}) in thickness detection"
        
        return True, "Thickness validated successfully"

    @staticmethod
    def classify_thickness(thickness: float) -> ThicknessCategory:
        """
        Classify thickness value into category.
        
        Args:
            thickness: Thickness in mm
            
        Returns:
            ThicknessCategory enum value
        """
        if thickness <= 1.5:
            return ThicknessCategory.THIN
        elif thickness <= 2.5:
            return ThicknessCategory.MEDIUM
        else:
            return ThicknessCategory.THICK

    @staticmethod
    def is_in_range(thickness: float, target: float, tolerance: float = 0.5) -> bool:
        """
        Check if thickness is within range of target.
        
        Args:
            thickness: Actual thickness
            target: Target thickness
            tolerance: Allowed tolerance (+/- mm)
            
        Returns:
            True if within range
        """
        return abs(thickness - target) <= tolerance


# Convenience function
def detect_thickness(
    dicom_datasets: Optional[List] = None,
    nifti_path: Optional[Union[str, Path]] = None,
    volume: Optional[np.ndarray] = None,
    voxel_spacing: Optional[Tuple[float, float, float]] = None,
    manual_thickness: Optional[float] = None,
    default_thickness: float = 5.0
) -> ThicknessInfo:
    """
    Convenience function to detect slice thickness.
    
    Args:
        dicom_datasets: List of DICOM datasets (priority 2)
        nifti_path: Path to NIfTI file (priority 3)
        volume: 3D numpy array (priority 4)
        voxel_spacing: Voxel spacing tuple (required with volume)
        manual_thickness: Manual override (priority 1 - highest)
        default_thickness: Default if detection fails
        
    Returns:
        ThicknessInfo with detected thickness
        
    Example:
        >>> info = detect_thickness(dicom_datasets=series)
        >>> info = detect_thickness(nifti_path='/path/to/file.nii.gz')
        >>> info = detect_thickness(manual_thickness=2.0)
    """
    detector = ThicknessDetector(default_thickness=default_thickness)
    
    if manual_thickness is not None:
        return detector.set_manual(manual_thickness)
    
    if dicom_datasets is not None:
        return detector.detect_from_dicom(dicom_datasets)
    
    if nifti_path is not None:
        return detector.detect_from_nifti(nifti_path)
    
    if volume is not None and voxel_spacing is not None:
        return detector.detect_from_array(volume, voxel_spacing)
    
    raise ValueError("Must provide either dicom_datasets, nifti_path, (volume + voxel_spacing), or manual_thickness")


# Export all public classes and functions
__all__ = [
    'ThicknessSource',
    'ThicknessCategory',
    'ThicknessInfo',
    'ThicknessDetector',
    'detect_thickness',
]
