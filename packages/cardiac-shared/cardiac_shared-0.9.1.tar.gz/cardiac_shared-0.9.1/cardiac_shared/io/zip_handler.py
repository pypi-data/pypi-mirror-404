"""ZIP file handling utilities for medical imaging data.

Provides context managers and utilities for extracting ZIP files
containing DICOM or other medical imaging data.

"""

import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional, Union

# Directories to skip when searching for DICOM files
SKIP_DIRS = {"output", "results", "__pycache__", ".git", ".vscode", "venv", "env"}


@contextmanager
def extract_zip(
    zip_path: Union[str, Path],
    extract_to: Optional[Union[str, Path]] = None,
) -> Generator[Path, None, None]:
    """Context manager for extracting ZIP files.

    Extracts ZIP to a temporary directory (or specified path) and cleans up after.

    Args:
        zip_path: Path to ZIP file
        extract_to: Optional extraction directory (uses temp dir if not specified)

    Yields:
        Path to extracted directory

    Examples:
        >>> with extract_zip("/path/to/data.zip") as extracted:
        ...     dicom_root = find_dicom_root(extracted)
        ...     volume, metadata = read_dicom_series(dicom_root)

    Raises:
        FileNotFoundError: If ZIP file doesn't exist
        zipfile.BadZipFile: If ZIP file is corrupted
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    if extract_to:
        # Use specified directory
        extract_dir = Path(extract_to)
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path, "r") as zf:
            # Test ZIP integrity
            bad_file = zf.testzip()
            if bad_file:
                raise zipfile.BadZipFile(f"Corrupted file in ZIP: {bad_file}")
            zf.extractall(extract_dir)

        yield extract_dir
    else:
        # Use temporary directory (auto-cleanup)
        with tempfile.TemporaryDirectory() as temp_dir:
            extract_dir = Path(temp_dir)

            with zipfile.ZipFile(zip_path, "r") as zf:
                # Test ZIP integrity
                bad_file = zf.testzip()
                if bad_file:
                    raise zipfile.BadZipFile(f"Corrupted file in ZIP: {bad_file}")
                zf.extractall(extract_dir)

            yield extract_dir


def find_dicom_root(extracted_dir: Union[str, Path]) -> Path:
    """Find DICOM root directory after ZIP extraction.

    Handles cases where ZIP contains:
    - Direct DICOM files: patient.zip/001.dcm
    - Subdirectory: patient.zip/DICOM/001.dcm
    - Nested structure: patient.zip/patient_id/series/001.dcm

    Args:
        extracted_dir: Path to extracted ZIP contents

    Returns:
        Path to directory containing DICOM files

    Examples:
        >>> with extract_zip("/path/to/patient.zip") as extracted:
        ...     dicom_root = find_dicom_root(extracted)
        ...     print(f"DICOM files in: {dicom_root}")
    """
    extracted_path = Path(extracted_dir)

    # Check root directory first
    if list(extracted_path.glob("*.dcm")):
        return extracted_path

    # Search for first subdirectory containing DICOM files
    for subdir in extracted_path.iterdir():
        if subdir.is_dir() and subdir.name not in SKIP_DIRS:
            if list(subdir.rglob("*.dcm")):
                # Find the deepest directory with DICOM files
                dcm_files = list(subdir.rglob("*.dcm"))
                if dcm_files:
                    return dcm_files[0].parent

    # Return root if no DICOM found (will fail later with clear error)
    return extracted_path


def list_zip_contents(zip_path: Union[str, Path]) -> List[str]:
    """List contents of a ZIP file without extracting.

    Args:
        zip_path: Path to ZIP file

    Returns:
        List of file paths within the ZIP

    Examples:
        >>> contents = list_zip_contents("/path/to/data.zip")
        >>> dicom_files = [f for f in contents if f.endswith('.dcm')]
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        return zf.namelist()


def get_zip_info(zip_path: Union[str, Path]) -> dict:
    """Get information about a ZIP file.

    Args:
        zip_path: Path to ZIP file

    Returns:
        Dict with file_count, total_size, has_dicom, and file_types

    Examples:
        >>> info = get_zip_info("/path/to/data.zip")
        >>> print(f"Files: {info['file_count']}, DICOM: {info['has_dicom']}")
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f"ZIP file not found: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        file_list = zf.namelist()
        total_size = sum(info.file_size for info in zf.infolist())

        # Categorize file types
        extensions = set()
        for f in file_list:
            if '.' in f:
                ext = f.rsplit('.', 1)[-1].lower()
                extensions.add(ext)

        has_dicom = any(f.endswith('.dcm') for f in file_list)
        has_nifti = any(f.endswith(('.nii', '.nii.gz')) for f in file_list)

        return {
            "file_count": len(file_list),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "has_dicom": has_dicom,
            "has_nifti": has_nifti,
            "file_types": list(extensions),
            "zip_size_mb": zip_path.stat().st_size / (1024 * 1024),
        }
