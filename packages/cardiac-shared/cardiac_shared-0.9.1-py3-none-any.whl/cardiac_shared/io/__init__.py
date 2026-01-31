"""IO modules for cardiac imaging data."""

from cardiac_shared.io.dicom import (
    read_dicom_series,
    get_dicom_metadata,
    extract_dicom_metadata,
    extract_slice_thickness,
    is_thorax_series,
)
from cardiac_shared.io.nifti import load_nifti, save_nifti, get_nifti_info
from cardiac_shared.io.zip_handler import extract_zip, find_dicom_root, get_zip_info
from cardiac_shared.io.preloader import (
    AsyncNiftiPreloader,
    preload_nifti_batch,
)

__all__ = [
    # DICOM
    "read_dicom_series",
    "get_dicom_metadata",
    "extract_dicom_metadata",
    "extract_slice_thickness",
    "is_thorax_series",
    # NIfTI
    "load_nifti",
    "save_nifti",
    "get_nifti_info",
    # ZIP
    "extract_zip",
    "find_dicom_root",
    "get_zip_info",
    # Preloader (v0.5.1)
    "AsyncNiftiPreloader",
    "preload_nifti_batch",
]
