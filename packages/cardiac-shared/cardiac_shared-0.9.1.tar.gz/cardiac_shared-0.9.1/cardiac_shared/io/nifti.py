"""NIfTI file handling utilities.

Provides simple functions for loading and saving NIfTI files.
"""

from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np

# nibabel is optional - check at runtime
try:
    import nibabel as nib
    HAS_NIBABEL = True
except ImportError:
    HAS_NIBABEL = False


def _check_nibabel():
    """Check if nibabel is available."""
    if not HAS_NIBABEL:
        raise ImportError(
            "nibabel is required for NIfTI operations. "
            "Install with: pip install nibabel"
        )


def load_nifti(file_path: Union[str, Path]) -> Tuple[np.ndarray, Dict]:
    """Load a NIfTI file and return volume data with metadata.

    Args:
        file_path: Path to NIfTI file (.nii or .nii.gz)

    Returns:
        Tuple of (3D/4D numpy array, metadata dict with 'affine', 'header', 'spacing')

    Examples:
        >>> volume, metadata = load_nifti("/path/to/file.nii.gz")
        >>> print(f"Shape: {volume.shape}, Spacing: {metadata['spacing']}")
    """
    _check_nibabel()

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")

    # Load NIfTI file
    img = nib.load(str(file_path))
    volume = img.get_fdata()

    # Extract metadata
    header = img.header
    affine = img.affine

    # Get voxel spacing from header
    spacing = header.get_zooms()[:3]  # First 3 dimensions (x, y, z)

    metadata = {
        "affine": affine,
        "header": header,
        "spacing": tuple(float(s) for s in spacing),
        "shape": volume.shape,
        "dtype": str(volume.dtype),
    }

    return volume, metadata


def save_nifti(
    volume: np.ndarray,
    file_path: Union[str, Path],
    affine: Optional[np.ndarray] = None,
    header: Optional[object] = None,
    spacing: Optional[Tuple[float, float, float]] = None,
) -> Path:
    """Save a numpy array as a NIfTI file.

    Args:
        volume: 3D/4D numpy array to save
        file_path: Output path (.nii or .nii.gz)
        affine: 4x4 affine matrix (optional, uses identity if not provided)
        header: NIfTI header object (optional)
        spacing: Voxel spacing (x, y, z) in mm (optional, only used if header is None)

    Returns:
        Path to saved file

    Examples:
        >>> save_nifti(volume, "/path/to/output.nii.gz", spacing=(1.0, 1.0, 2.5))
    """
    _check_nibabel()

    file_path = Path(file_path)

    # Ensure correct extension
    if not str(file_path).endswith(('.nii', '.nii.gz')):
        file_path = file_path.with_suffix('.nii.gz')

    # Create parent directory if needed
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Use identity affine if not provided
    if affine is None:
        affine = np.eye(4)
        if spacing:
            affine[0, 0] = spacing[0]
            affine[1, 1] = spacing[1]
            affine[2, 2] = spacing[2]

    # Create NIfTI image
    if header is not None:
        img = nib.Nifti1Image(volume.astype(np.float32), affine, header)
    else:
        img = nib.Nifti1Image(volume.astype(np.float32), affine)
        if spacing:
            img.header.set_zooms(spacing)

    # Save
    nib.save(img, str(file_path))

    return file_path


def get_nifti_info(file_path: Union[str, Path]) -> Dict:
    """Get quick information about a NIfTI file without loading full volume.

    Args:
        file_path: Path to NIfTI file

    Returns:
        Dict with shape, spacing, dtype, and file size info

    Examples:
        >>> info = get_nifti_info("/path/to/file.nii.gz")
        >>> print(f"Shape: {info['shape']}, Size: {info['file_size_mb']:.1f} MB")
    """
    _check_nibabel()

    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"NIfTI file not found: {file_path}")

    # Load header only
    img = nib.load(str(file_path))
    header = img.header

    return {
        "shape": tuple(img.shape),
        "spacing": tuple(float(s) for s in header.get_zooms()[:3]),
        "dtype": str(header.get_data_dtype()),
        "file_size_mb": file_path.stat().st_size / (1024 * 1024),
    }
