"""DICOM file handling utilities."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

# pydicom is optional - check at runtime
try:
    import pydicom
    HAS_PYDICOM = True
except ImportError:
    HAS_PYDICOM = False


def _check_pydicom():
    """Check if pydicom is available."""
    if not HAS_PYDICOM:
        raise ImportError(
            "pydicom is required for DICOM operations. "
            "Install with: pip install pydicom"
        )


def read_dicom_series(dicom_dir: Union[str, Path]) -> Tuple[np.ndarray, Dict]:
    """Read DICOM series from directory.

    Args:
        dicom_dir: Path to directory containing DICOM files

    Returns:
        Tuple of (3D numpy array, metadata dict)

    Examples:
        >>> volume, metadata = read_dicom_series(Path("/path/to/dicom"))
        >>> print(f"Shape: {volume.shape}, Spacing: {metadata['spacing']}")
    """
    _check_pydicom()

    dicom_dir = Path(dicom_dir)

    # Find DICOM files (with or without .dcm extension)
    dicom_files = sorted(list(dicom_dir.glob("*.dcm")))
    if not dicom_files:
        # Try files without extension (common in some DICOM exports)
        all_files = [f for f in dicom_dir.iterdir() if f.is_file()]
        dicom_files = []
        for f in all_files:
            try:
                pydicom.dcmread(f, stop_before_pixels=True)
                dicom_files.append(f)
            except Exception:
                continue
        dicom_files = sorted(dicom_files)

    if not dicom_files:
        raise ValueError(f"No DICOM files found in {dicom_dir}")

    # Read first file for metadata
    ds = pydicom.dcmread(dicom_files[0])

    # Extract metadata
    metadata = get_dicom_metadata(ds)

    # Read all slices and sort by position if available
    slices_data = []
    for dcm_file in dicom_files:
        ds = pydicom.dcmread(dcm_file)
        position = getattr(ds, 'ImagePositionPatient', [0, 0, 0])
        z_position = float(position[2]) if position else 0
        slices_data.append((z_position, ds.pixel_array))

    # Sort by z position
    slices_data.sort(key=lambda x: x[0])
    slices = [s[1] for s in slices_data]

    volume = np.stack(slices, axis=-1)

    return volume, metadata


def extract_slice_thickness(ds) -> Optional[float]:
    """Extract slice thickness from DICOM dataset.

    Args:
        ds: pydicom Dataset

    Returns:
        Slice thickness in mm

    Examples:
        >>> ds = pydicom.dcmread("image.dcm")
        >>> thickness = extract_slice_thickness(ds)
        >>> print(f"Slice thickness: {thickness:.2f} mm")
    """
    # Try multiple DICOM tags
    if hasattr(ds, "SliceThickness"):
        return float(ds.SliceThickness)
    elif hasattr(ds, "SpacingBetweenSlices"):
        return float(ds.SpacingBetweenSlices)
    elif hasattr(ds, "PixelSpacing") and len(ds.PixelSpacing) > 2:
        return float(ds.PixelSpacing[2])
    else:
        return None


def get_dicom_metadata(ds) -> Dict:
    """Extract comprehensive metadata from DICOM dataset.

    Args:
        ds: pydicom Dataset

    Returns:
        Dictionary with metadata fields

    Examples:
        >>> ds = pydicom.dcmread("image.dcm")
        >>> metadata = get_dicom_metadata(ds)
        >>> print(f"Manufacturer: {metadata['manufacturer']}")
    """
    metadata = {
        "patient_id": getattr(ds, "PatientID", "Unknown"),
        "study_id": getattr(ds, "StudyInstanceUID", "Unknown"),
        "series_id": getattr(ds, "SeriesInstanceUID", "Unknown"),
        "series_description": getattr(ds, "SeriesDescription", "Unknown"),
        "modality": getattr(ds, "Modality", "Unknown"),
        "manufacturer": getattr(ds, "Manufacturer", "Unknown"),
        "manufacturer_model": getattr(ds, "ManufacturerModelName", "Unknown"),
        "slice_thickness": extract_slice_thickness(ds),
        "pixel_spacing": (
            tuple(map(float, ds.PixelSpacing)) if hasattr(ds, "PixelSpacing") else None
        ),
        "kvp": float(ds.KVP) if hasattr(ds, "KVP") else None,
        "exposure": float(ds.Exposure) if hasattr(ds, "Exposure") else None,
        "rows": int(ds.Rows) if hasattr(ds, "Rows") else None,
        "columns": int(ds.Columns) if hasattr(ds, "Columns") else None,
    }

    return metadata


def extract_dicom_metadata(ds) -> Dict:
    """Extract essential DICOM metadata (alias for backward compatibility)."""
    return get_dicom_metadata(ds)


def is_thorax_series(series_description: str) -> bool:
    """Check if series is thorax/chest CT.

    Args:
        series_description: DICOM SeriesDescription field

    Returns:
        True if thorax series, False otherwise

    Examples:
        >>> is_thorax_series("THORAX 1.0 B31f")
        True
        >>> is_thorax_series("ABDOMEN")
        False
    """
    keywords = [
        "thorax",
        "chest",
        "lung",
        "cardiac",
    ]

    desc_lower = series_description.lower()
    return any(keyword in desc_lower for keyword in keywords)
