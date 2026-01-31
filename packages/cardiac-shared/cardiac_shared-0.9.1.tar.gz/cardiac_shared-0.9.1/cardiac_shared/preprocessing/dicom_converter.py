"""
Unified DICOM to NIfTI Converter for cardiac imaging pipelines
Provides standardized conversion with batch tracking and deduplication

This module enables:
- Single patient DICOM->NIfTI conversion
- Batch conversion with manifest tracking
- Automatic deduplication via BatchManager
- Support for ZIP archives
- Multi-series handling

Usage:
    from cardiac_shared.preprocessing import DicomConverter

    # Create converter
    converter = DicomConverter()

    # Convert single patient
    nifti_path, created = converter.convert_patient(
        patient_id="P001234",
        dicom_path=Path("/dicom/P001234"),
        output_dir=Path("/nifti")
    )

    # Convert batch with manifest
    manifest = converter.convert_batch(
        patient_ids=["P001234", "P001235"],
        dicom_root=Path("/dicom"),
        output_dir=Path("/nifti"),
        dataset_id="study_cohort_v1"
    )

Author: Cardiac ML Research Team
Created: 2026-01-03
Version: 0.6.0
"""

import os
import time
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass

# Try importing SimpleITK for conversion
try:
    import SimpleITK as sitk
    HAS_SIMPLEITK = True
except ImportError:
    HAS_SIMPLEITK = False

# Try importing numpy
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Import BatchManager from same package
from cardiac_shared.data.batch_manager import BatchManager, BatchManifest


def _check_simpleitk():
    """Check if SimpleITK is available"""
    if not HAS_SIMPLEITK:
        raise ImportError(
            "SimpleITK is required for DICOM conversion. "
            "Install with: pip install SimpleITK"
        )


@dataclass
class ConversionResult:
    """Result of a DICOM to NIfTI conversion"""
    patient_id: str
    success: bool
    output_path: Optional[Path] = None
    dimensions: Optional[List[int]] = None
    spacing: Optional[List[float]] = None
    processing_time: float = 0.0
    error_message: Optional[str] = None
    was_cached: bool = False


class DicomConverter:
    """
    Unified DICOM to NIfTI converter with batch tracking

    Features:
    - Single patient conversion
    - Batch conversion with manifest tracking
    - Automatic deduplication (skip existing)
    - ZIP archive support
    - Progress callback support
    - Multi-series selection

    Example:
        >>> converter = DicomConverter()
        >>>
        >>> # Single patient
        >>> result = converter.convert_patient("P001234", dicom_path, output_dir)
        >>> if result.success:
        ...     print(f"Saved to: {result.output_path}")
        >>>
        >>> # Batch with manifest
        >>> manifest = converter.convert_batch(
        ...     patient_ids=["P001234", "P001235"],
        ...     dicom_root=Path("/dicom"),
        ...     output_dir=Path("/nifti"),
        ...     dataset_id="study_cohort_v1"
        ... )
    """

    DEFAULT_TOOL = "SimpleITK"
    DEFAULT_TOOL_VERSION = "2.3.1"

    def __init__(
        self,
        prefer_thorax: bool = True,
        min_slices: int = 50,
        force_overwrite: bool = False,
        verbose: bool = True,
    ):
        """
        Initialize DicomConverter

        Args:
            prefer_thorax: Prefer thorax/chest series when multiple available
            min_slices: Minimum number of slices for valid series
            force_overwrite: Overwrite existing NIfTI files
            verbose: Print progress messages
        """
        _check_simpleitk()

        self.prefer_thorax = prefer_thorax
        self.min_slices = min_slices
        self.force_overwrite = force_overwrite
        self.verbose = verbose

        self._batch_manager: Optional[BatchManager] = None

    def _log(self, message: str) -> None:
        """Print message if verbose"""
        if self.verbose:
            print(message)

    def _find_dicom_dir(self, path: Path) -> Optional[Path]:
        """
        Find DICOM directory from path (handles nested structures)

        Args:
            path: Starting path

        Returns:
            Path to directory containing DICOM files
        """
        # Check if path itself contains DICOM files
        if path.is_dir():
            dcm_files = list(path.glob("*.dcm"))
            if dcm_files:
                return path

            # Check for files without extension (common DICOM pattern)
            for f in path.iterdir():
                if f.is_file() and not f.suffix:
                    try:
                        sitk.ReadImage(str(f))
                        return path
                    except Exception:
                        continue

            # Search subdirectories (up to 3 levels)
            for subdir in path.rglob("*"):
                if subdir.is_dir():
                    dcm_files = list(subdir.glob("*.dcm"))
                    if dcm_files:
                        return subdir

        return None

    def _find_best_series(self, dicom_dir: Path) -> Optional[str]:
        """
        Find best DICOM series in directory

        Args:
            dicom_dir: Directory containing DICOM files

        Returns:
            Series ID of best series, or None
        """
        reader = sitk.ImageSeriesReader()
        series_ids = reader.GetGDCMSeriesIDs(str(dicom_dir))

        if not series_ids:
            return None

        best_series = None
        best_score = -1

        for series_id in series_ids:
            file_names = reader.GetGDCMSeriesFileNames(str(dicom_dir), series_id)
            n_slices = len(file_names)

            if n_slices < self.min_slices:
                continue

            # Score: prefer more slices
            score = n_slices

            # Bonus for thorax series
            if self.prefer_thorax and file_names:
                try:
                    reader_test = sitk.ImageFileReader()
                    reader_test.SetFileName(file_names[0])
                    reader_test.LoadPrivateTagsOn()
                    reader_test.ReadImageInformation()

                    desc = reader_test.GetMetaData("0008|103e") if reader_test.HasMetaDataKey("0008|103e") else ""
                    if any(kw in desc.lower() for kw in ["thorax", "chest", "lung", "cardiac"]):
                        score += 1000
                except Exception:
                    pass

            if score > best_score:
                best_score = score
                best_series = series_id

        return best_series

    def _extract_zip(self, zip_path: Path, extract_dir: Path) -> Path:
        """
        Extract ZIP archive to temporary directory

        Args:
            zip_path: Path to ZIP file
            extract_dir: Directory to extract to

        Returns:
            Path to extracted directory
        """
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(extract_dir)

        # Find DICOM directory in extracted content
        dicom_dir = self._find_dicom_dir(extract_dir)
        if not dicom_dir:
            dicom_dir = extract_dir

        return dicom_dir

    def convert_patient(
        self,
        patient_id: str,
        dicom_path: Union[str, Path],
        output_dir: Union[str, Path],
        output_filename: Optional[str] = None,
        dataset_id: Optional[str] = None,
    ) -> ConversionResult:
        """
        Convert single patient DICOM to NIfTI

        Args:
            patient_id: Patient identifier
            dicom_path: Path to DICOM directory or ZIP file
            output_dir: Output directory for NIfTI
            output_filename: Custom output filename (default: {patient_id}.nii.gz)
            dataset_id: Optional batch ID for deduplication check

        Returns:
            ConversionResult with conversion details
        """
        start_time = time.time()
        dicom_path = Path(dicom_path)
        output_dir = Path(output_dir)

        # Determine output filename
        if output_filename is None:
            output_filename = f"{patient_id}.nii.gz"
        output_path = output_dir / output_filename

        # Check for existing file (deduplication)
        if not self.force_overwrite:
            # Check via batch manager if available
            if dataset_id and self._batch_manager:
                existing = self._batch_manager.find_existing_nifti(patient_id, dataset_id)
                if existing:
                    self._log(f"  [CACHE] {patient_id}: Reusing existing {existing.name}")
                    return ConversionResult(
                        patient_id=patient_id,
                        success=True,
                        output_path=existing,
                        was_cached=True,
                        processing_time=time.time() - start_time,
                    )

            # Check output path directly
            if output_path.exists():
                self._log(f"  [SKIP] {patient_id}: Already exists")
                return ConversionResult(
                    patient_id=patient_id,
                    success=True,
                    output_path=output_path,
                    was_cached=True,
                    processing_time=time.time() - start_time,
                )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_dir = None
        try:
            # Handle ZIP files
            if dicom_path.suffix.lower() == '.zip' or str(dicom_path).endswith('.zip'):
                temp_dir = tempfile.mkdtemp(prefix=f"dicom_{patient_id}_")
                dicom_dir = self._extract_zip(dicom_path, Path(temp_dir))
            elif dicom_path.is_file():
                # Single file - assume it's in a directory
                dicom_dir = dicom_path.parent
            else:
                dicom_dir = self._find_dicom_dir(dicom_path)

            if not dicom_dir:
                raise ValueError(f"No DICOM files found in {dicom_path}")

            # Find best series
            series_id = self._find_best_series(dicom_dir)
            if not series_id:
                raise ValueError(f"No valid DICOM series found (min {self.min_slices} slices)")

            # Read DICOM series
            reader = sitk.ImageSeriesReader()
            file_names = reader.GetGDCMSeriesFileNames(str(dicom_dir), series_id)
            reader.SetFileNames(file_names)
            reader.MetaDataDictionaryArrayUpdateOn()
            reader.LoadPrivateTagsOn()

            image = reader.Execute()

            # Get dimensions and spacing
            dimensions = list(image.GetSize())
            spacing = list(image.GetSpacing())

            # Write NIfTI
            sitk.WriteImage(image, str(output_path), True)  # True = compress

            processing_time = time.time() - start_time
            self._log(f"  [OK] {patient_id}: {dimensions[2]} slices, {processing_time:.1f}s")

            return ConversionResult(
                patient_id=patient_id,
                success=True,
                output_path=output_path,
                dimensions=dimensions,
                spacing=spacing,
                processing_time=processing_time,
                was_cached=False,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self._log(f"  [X] {patient_id}: {str(e)}")

            return ConversionResult(
                patient_id=patient_id,
                success=False,
                error_message=str(e),
                processing_time=processing_time,
            )

        finally:
            # Cleanup temp directory
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def convert_batch(
        self,
        patient_ids: List[str],
        dicom_root: Union[str, Path],
        output_dir: Union[str, Path],
        dataset_id: str,
        provider: str = "",
        batch: str = "",
        dicom_pattern: str = "{patient_id}",
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> BatchManifest:
        """
        Convert batch of patients with manifest tracking

        Args:
            patient_ids: List of patient identifiers
            dicom_root: Root directory containing patient DICOM folders
            output_dir: Output directory for NIfTI files
            dataset_id: Batch identifier (e.g., "study_cohort_v1")
            provider: Data provider name
            batch: Batch name
            dicom_pattern: Pattern to find DICOM folder (default: "{patient_id}")
            progress_callback: Optional callback(current, total, patient_id)

        Returns:
            BatchManifest with all results
        """
        dicom_root = Path(dicom_root)
        output_dir = Path(output_dir)

        self._log(f"[i] Starting batch conversion: {dataset_id}")
        self._log(f"    Source: {dicom_root}")
        self._log(f"    Output: {output_dir}")
        self._log(f"    Patients: {len(patient_ids)}")

        # Create batch manager and manifest
        self._batch_manager = BatchManager(output_dir=output_dir.parent, auto_save=False)
        manifest = self._batch_manager.create_batch(
            dataset_id=dataset_id,
            source_path=str(dicom_root),
            output_path=output_dir,
            tool=self.DEFAULT_TOOL,
            tool_version=self.DEFAULT_TOOL_VERSION,
            provider=provider,
            batch=batch,
            dataset_type="nifti_converted",
        )

        # Process each patient
        total = len(patient_ids)
        for idx, patient_id in enumerate(patient_ids, 1):
            # Find DICOM path
            dicom_folder = dicom_pattern.format(patient_id=patient_id)
            dicom_path = dicom_root / dicom_folder

            # Try with common patterns if not found
            if not dicom_path.exists():
                # Try dicom_{patient_id}
                dicom_path = dicom_root / f"dicom_{patient_id}"
            if not dicom_path.exists():
                # Try {patient_id}.zip
                dicom_path = dicom_root / f"{patient_id}.zip"
            if not dicom_path.exists():
                # Try searching for ZIP files
                zip_files = list(dicom_root.glob(f"*{patient_id}*.zip"))
                if zip_files:
                    dicom_path = zip_files[0]

            # Progress callback
            if progress_callback:
                progress_callback(idx, total, patient_id)

            # Convert
            result = self.convert_patient(
                patient_id=patient_id,
                dicom_path=dicom_path,
                output_dir=output_dir,
                dataset_id=dataset_id,
            )

            # Register result
            self._batch_manager.register_patient(
                dataset_id=dataset_id,
                patient_id=patient_id,
                status="success" if result.success else "failed",
                output_file=result.output_path.name if result.output_path else None,
                dimensions=result.dimensions,
                spacing=result.spacing,
                processing_time_seconds=result.processing_time,
                error_message=result.error_message,
                metadata={"was_cached": result.was_cached},
            )

        # Save manifest
        self._batch_manager.save_manifest(dataset_id)

        # Print summary
        manifest.update_summary()
        self._log(f"\n[i] Batch conversion complete:")
        self._log(f"    Total: {manifest.total_patients}")
        self._log(f"    Success: {manifest.successful}")
        self._log(f"    Failed: {manifest.failed}")

        return manifest

    def find_existing(
        self,
        patient_id: str,
        output_dir: Union[str, Path],
    ) -> Optional[Path]:
        """
        Find existing NIfTI file for patient

        Args:
            patient_id: Patient identifier
            output_dir: Output directory to search

        Returns:
            Path to existing file, or None
        """
        output_dir = Path(output_dir)

        # Check standard naming patterns
        patterns = [
            f"{patient_id}.nii.gz",
            f"{patient_id}.nii",
            f"dicom_{patient_id}.nii.gz",
        ]

        for pattern in patterns:
            path = output_dir / pattern
            if path.exists():
                return path

        return None


# Convenience functions
def convert_dicom_to_nifti(
    dicom_path: Union[str, Path],
    output_path: Union[str, Path],
    patient_id: Optional[str] = None,
) -> ConversionResult:
    """
    Simple DICOM to NIfTI conversion

    Args:
        dicom_path: Path to DICOM directory or ZIP
        output_path: Output NIfTI file path
        patient_id: Optional patient ID (inferred from path if not provided)

    Returns:
        ConversionResult
    """
    dicom_path = Path(dicom_path)
    output_path = Path(output_path)

    if patient_id is None:
        patient_id = dicom_path.stem

    converter = DicomConverter(verbose=False)
    return converter.convert_patient(
        patient_id=patient_id,
        dicom_path=dicom_path,
        output_dir=output_path.parent,
        output_filename=output_path.name,
    )
