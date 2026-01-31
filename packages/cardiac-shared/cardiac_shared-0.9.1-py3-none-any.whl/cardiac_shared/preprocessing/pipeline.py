"""
Shared Preprocessing Pipeline for cardiac imaging modules
Provides unified preprocessing with automatic dependency resolution

This module enables:
- Automatic NIfTI conversion with deduplication
- TotalSegmentator integration with result caching
- Mask discovery and validation
- Cross-module data sharing

Usage:
    from cardiac_shared.preprocessing import SharedPreprocessingPipeline

    # Create pipeline
    pipeline = SharedPreprocessingPipeline(
        nifti_root=Path("/nifti"),
        segmentation_root=Path("/totalsegmentator"),
    )

    # Ensure preprocessing for PCFA
    nifti_path = pipeline.ensure_nifti(patient_id, dataset_id, dicom_path)
    seg_path = pipeline.ensure_totalsegmentator(patient_id, dataset_id)
    heart_mask = pipeline.get_mask(patient_id, dataset_id, "heart")

Author: Cardiac ML Research Team
Created: 2026-01-03
Version: 0.6.0
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass

# Import from same package
from cardiac_shared.data.batch_manager import BatchManager, BatchManifest
from cardiac_shared.preprocessing.dicom_converter import DicomConverter, ConversionResult


@dataclass
class PreprocessingConfig:
    """Configuration for preprocessing pipeline"""
    # NIfTI conversion
    nifti_root: Optional[Path] = None
    dicom_root: Optional[Path] = None

    # TotalSegmentator
    segmentation_root: Optional[Path] = None
    totalsegmentator_task: str = "total"  # "total", "fast", "body"
    totalsegmentator_device: str = "gpu"  # "gpu", "cpu"
    totalsegmentator_fast: bool = True  # Use --fast mode
    totalsegmentator_path: Optional[str] = None  # Custom path to TotalSegmentator executable
    totalsegmentator_roi_subset: Optional[str] = None  # ROI subset (e.g., "heart" for PCFA)
    # v0.6.2: --roi_subset provides 1.5-2x speedup for single-organ tasks

    # Processing options
    force_reprocess: bool = False
    verbose: bool = True

    # GPU stabilization
    gpu_stabilization_time: float = 2.0  # seconds to wait between TotalSegmentator runs

    # v0.6.3: Registry-based auto-discovery
    use_registry: bool = True  # Check IntermediateResultsRegistry for existing results
    registry_config_path: Optional[Path] = None  # Custom registry config path
    fallback_segmentation_paths: Optional[List[Path]] = None  # Additional paths to search


@dataclass
class PreprocessingResult:
    """Result of preprocessing operation"""
    patient_id: str
    stage: str  # "nifti", "totalsegmentator"
    success: bool
    output_path: Optional[Path] = None
    was_cached: bool = False
    processing_time: float = 0.0
    error_message: Optional[str] = None


class SharedPreprocessingPipeline:
    """
    Unified preprocessing pipeline for cardiac imaging modules

    Provides:
    - DICOM to NIfTI conversion with deduplication
    - TotalSegmentator integration with caching
    - Mask discovery and validation
    - Batch processing support

    Designed for use by analysis modules such as:
    - Pericardial fat analysis (requires heart mask)
    - Perivascular fat analysis (requires aorta mask)
    - Vertebra body composition analysis (requires vertebrae masks)
    - Chamber analysis (requires heart mask)

    Example:
        >>> pipeline = SharedPreprocessingPipeline(
        ...     nifti_root=Path("/data/nifti"),
        ...     segmentation_root=Path("/data/totalsegmentator"),
        ... )
        >>>
        >>> # For PCFA
        >>> nifti = pipeline.ensure_nifti("P001234", "study_cohort_v1", dicom_path)
        >>> pipeline.ensure_totalsegmentator("P001234", "study_cohort_v1")
        >>> heart = pipeline.get_mask("P001234", "study_cohort_v1", "heart")
        >>>
        >>> # For VBCA
        >>> vertebrae = pipeline.get_masks("P001234", "study_cohort_v1",
        ...                                 ["vertebrae_T12", "vertebrae_L1", "vertebrae_L2"])
    """

    # Standard TotalSegmentator mask names
    STANDARD_MASKS = {
        # Heart-related
        "heart": "heart.nii.gz",
        "heart_myocardium": "heart_myocardium.nii.gz",
        "heart_atrium_left": "heart_atrium_left.nii.gz",
        "heart_atrium_right": "heart_atrium_right.nii.gz",
        "heart_ventricle_left": "heart_ventricle_left.nii.gz",
        "heart_ventricle_right": "heart_ventricle_right.nii.gz",

        # Aorta
        "aorta": "aorta.nii.gz",

        # Vertebrae
        "vertebrae_T12": "vertebrae_T12.nii.gz",
        "vertebrae_L1": "vertebrae_L1.nii.gz",
        "vertebrae_L2": "vertebrae_L2.nii.gz",
        "vertebrae_L3": "vertebrae_L3.nii.gz",
        "vertebrae_L4": "vertebrae_L4.nii.gz",
        "vertebrae_L5": "vertebrae_L5.nii.gz",

        # Other organs
        "liver": "liver.nii.gz",
        "spleen": "spleen.nii.gz",
        "kidney_left": "kidney_left.nii.gz",
        "kidney_right": "kidney_right.nii.gz",
        "lung_left": "lung_left.nii.gz",
        "lung_right": "lung_right.nii.gz",
    }

    # Analysis module mask requirements (keyed by analysis type abbreviation)
    MODULE_REQUIREMENTS = {
        "pericardial_fat": ["heart"],
        "perivascular_fat": ["aorta"],
        "vertebra_composition": ["vertebrae_T12", "vertebrae_L1", "vertebrae_L2", "vertebrae_L3"],
        "chamber_analysis": ["heart", "heart_atrium_left", "heart_atrium_right",
                            "heart_ventricle_left", "heart_ventricle_right"],
        "liver_fat": ["liver"],
        "kidney_volume": ["kidney_left", "kidney_right"],
    }

    def __init__(
        self,
        nifti_root: Optional[Union[str, Path]] = None,
        segmentation_root: Optional[Union[str, Path]] = None,
        dicom_root: Optional[Union[str, Path]] = None,
        config: Optional[PreprocessingConfig] = None,
    ):
        """
        Initialize SharedPreprocessingPipeline

        Args:
            nifti_root: Root directory for NIfTI files
            segmentation_root: Root directory for TotalSegmentator results
            dicom_root: Root directory for DICOM files
            config: Optional PreprocessingConfig object
        """
        if config:
            self.config = config
        else:
            self.config = PreprocessingConfig(
                nifti_root=Path(nifti_root) if nifti_root else None,
                segmentation_root=Path(segmentation_root) if segmentation_root else None,
                dicom_root=Path(dicom_root) if dicom_root else None,
            )

        # Initialize components
        self._dicom_converter = DicomConverter(
            force_overwrite=self.config.force_reprocess,
            verbose=self.config.verbose,
        )

        # Batch managers for tracking
        self._nifti_managers: Dict[str, BatchManager] = {}
        self._seg_managers: Dict[str, BatchManager] = {}

        # v0.6.3: Initialize registry for auto-discovery
        self._registry = None
        if self.config.use_registry:
            try:
                from cardiac_shared.data.registry import get_registry
                self._registry = get_registry(
                    config_path=self.config.registry_config_path
                )
                self._log("[i] Registry loaded for auto-discovery")
            except Exception as e:
                self._log(f"[!] Could not load registry: {e}")

    def _log(self, message: str) -> None:
        """Print message if verbose"""
        if self.config.verbose:
            print(message)

    def _find_totalsegmentator(self) -> Optional[str]:
        """
        Find TotalSegmentator executable

        Priority:
        1. Custom path from config
        2. Current Python environment (sys.executable)
        3. System PATH

        Returns:
            Path to TotalSegmentator executable, or None if not found
        """
        import sys
        import shutil

        # 1. Custom path from config
        if self.config.totalsegmentator_path:
            custom_path = Path(self.config.totalsegmentator_path)
            if custom_path.exists():
                return str(custom_path)

        # 2. Current Python environment
        python_dir = Path(sys.executable).parent
        possible_paths = [
            python_dir / "TotalSegmentator",      # Linux/WSL
            python_dir / "TotalSegmentator.exe",  # Windows
        ]

        for p in possible_paths:
            if p.exists():
                return str(p)

        # 3. System PATH
        system_cmd = shutil.which("TotalSegmentator")
        if system_cmd:
            return system_cmd

        return None

    def _get_nifti_dir(self, dataset_id: str) -> Path:
        """Get NIfTI directory for dataset"""
        if self.config.nifti_root:
            return self.config.nifti_root / dataset_id
        raise ValueError("nifti_root not configured")

    def _get_segmentation_dir(self, dataset_id: str) -> Path:
        """Get segmentation directory for dataset"""
        if self.config.segmentation_root:
            return self.config.segmentation_root / f"organs_{dataset_id}"
        raise ValueError("segmentation_root not configured")

    def _get_or_load_nifti_manager(self, dataset_id: str) -> BatchManager:
        """Get or create batch manager for NIfTI dataset"""
        if dataset_id not in self._nifti_managers:
            nifti_dir = self._get_nifti_dir(dataset_id)
            manager = BatchManager(output_dir=nifti_dir.parent)

            manifest_path = nifti_dir / "manifest.json"
            if manifest_path.exists():
                manager.load_manifest(manifest_path)
            else:
                manager.create_batch(
                    dataset_id=dataset_id,
                    output_path=nifti_dir,
                    dataset_type="nifti_converted",
                )

            self._nifti_managers[dataset_id] = manager

        return self._nifti_managers[dataset_id]

    def _get_or_load_seg_manager(self, dataset_id: str) -> BatchManager:
        """Get or create batch manager for segmentation dataset"""
        seg_dataset_id = f"organs_{dataset_id}"

        if seg_dataset_id not in self._seg_managers:
            seg_dir = self._get_segmentation_dir(dataset_id)
            manager = BatchManager(output_dir=seg_dir.parent)

            manifest_path = seg_dir / "manifest.json"
            if manifest_path.exists():
                manager.load_manifest(manifest_path)
            else:
                manager.create_batch(
                    dataset_id=seg_dataset_id,
                    output_path=seg_dir,
                    dataset_type="totalsegmentator_masks",
                )

            self._seg_managers[seg_dataset_id] = manager

        return self._seg_managers[seg_dataset_id]

    # =========================================================================
    # NIfTI Conversion
    # =========================================================================

    def ensure_nifti(
        self,
        patient_id: str,
        dataset_id: str,
        dicom_path: Optional[Union[str, Path]] = None,
    ) -> PreprocessingResult:
        """
        Ensure NIfTI file exists for patient, converting if necessary

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier (e.g., "study_cohort_v1")
            dicom_path: Path to DICOM (required if not existing)

        Returns:
            PreprocessingResult with NIfTI path
        """
        start_time = time.time()
        nifti_dir = self._get_nifti_dir(dataset_id)
        nifti_path = nifti_dir / f"{patient_id}.nii.gz"

        # Check if already exists
        if nifti_path.exists() and not self.config.force_reprocess:
            return PreprocessingResult(
                patient_id=patient_id,
                stage="nifti",
                success=True,
                output_path=nifti_path,
                was_cached=True,
                processing_time=time.time() - start_time,
            )

        # Need to convert
        if not dicom_path:
            # Try to find in dicom_root
            if self.config.dicom_root:
                dicom_path = self.config.dicom_root / patient_id
                if not dicom_path.exists():
                    dicom_path = self.config.dicom_root / f"dicom_{patient_id}"

            if not dicom_path or not dicom_path.exists():
                return PreprocessingResult(
                    patient_id=patient_id,
                    stage="nifti",
                    success=False,
                    error_message="DICOM path not provided and not found in dicom_root",
                    processing_time=time.time() - start_time,
                )

        # Convert
        result = self._dicom_converter.convert_patient(
            patient_id=patient_id,
            dicom_path=dicom_path,
            output_dir=nifti_dir,
            dataset_id=dataset_id,
        )

        # Register in batch manager
        manager = self._get_or_load_nifti_manager(dataset_id)
        manager.register_patient(
            dataset_id=dataset_id,
            patient_id=patient_id,
            status="success" if result.success else "failed",
            output_file=result.output_path.name if result.output_path else None,
            dimensions=result.dimensions,
            spacing=result.spacing,
            processing_time_seconds=result.processing_time,
            error_message=result.error_message,
        )

        return PreprocessingResult(
            patient_id=patient_id,
            stage="nifti",
            success=result.success,
            output_path=result.output_path,
            was_cached=result.was_cached,
            processing_time=result.processing_time,
            error_message=result.error_message,
        )

    def get_nifti_path(
        self,
        patient_id: str,
        dataset_id: str,
    ) -> Optional[Path]:
        """
        Get NIfTI path for patient (without conversion)

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier

        Returns:
            Path to NIfTI file if exists, None otherwise
        """
        nifti_dir = self._get_nifti_dir(dataset_id)
        nifti_path = nifti_dir / f"{patient_id}.nii.gz"

        if nifti_path.exists():
            return nifti_path
        return None

    # =========================================================================
    # Registry-based Auto-Discovery (v0.6.3)
    # =========================================================================

    def find_existing_segmentation(
        self,
        patient_id: str,
        dataset_id: str,
        mask_name: str = "heart",
    ) -> Optional[Path]:
        """
        Find existing segmentation from registry or fallback paths

        This method searches for pre-existing TotalSegmentator outputs:
        1. IntermediateResultsRegistry (cross-project discovery)
        2. Fallback paths (configured in PreprocessingConfig)
        3. Local segmentation_root

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier (used for registry key construction)
            mask_name: Mask to verify exists (default: "heart")

        Returns:
            Path to segmentation directory if found, None otherwise

        Example:
            >>> seg_path = pipeline.find_existing_segmentation("P001234", "chd")
            >>> if seg_path:
            ...     heart_mask = seg_path / "heart.nii.gz"
        """
        # Extract cohort from dataset_id (e.g., "chd_pilot_v4" -> "chd")
        cohort = dataset_id.split("_")[0] if "_" in dataset_id else dataset_id

        # 1. Check registry
        if self._registry:
            registry_keys = [
                f"segmentation.totalsegmentator_organs.{cohort}_v2",
                f"segmentation.totalsegmentator_organs.{cohort}_v1",
                f"segmentation.totalsegmentator_organs.{cohort}",
            ]

            for key in registry_keys:
                if self._registry.exists(key):
                    seg_root = self._registry.get_path(key)
                    if seg_root:
                        patient_dir = seg_root / patient_id
                        mask_path = patient_dir / f"{mask_name}.nii.gz"
                        if mask_path.exists():
                            self._log(f"  [Registry] Found: {key}/{patient_id}")
                            return patient_dir

        # 2. Check fallback paths
        if self.config.fallback_segmentation_paths:
            for fallback in self.config.fallback_segmentation_paths:
                if fallback.exists():
                    patient_dir = fallback / patient_id
                    mask_path = patient_dir / f"{mask_name}.nii.gz"
                    if mask_path.exists():
                        self._log(f"  [Fallback] Found: {fallback.name}/{patient_id}")
                        return patient_dir

        # 3. Check local segmentation_root
        if self.config.segmentation_root:
            local_seg_dir = self._get_segmentation_dir(dataset_id)
            patient_dir = local_seg_dir / patient_id
            mask_path = patient_dir / f"{mask_name}.nii.gz"
            if mask_path.exists():
                self._log(f"  [Local] Found: {patient_dir.name}")
                return patient_dir

        return None

    def get_reuse_summary(
        self,
        patient_ids: List[str],
        dataset_id: str,
        mask_name: str = "heart",
    ) -> Dict[str, Any]:
        """
        Get summary of reuse potential for a batch of patients

        Args:
            patient_ids: List of patient IDs to check
            dataset_id: Dataset identifier
            mask_name: Mask to check for

        Returns:
            Summary dictionary with statistics
        """
        reusable = 0
        need_processing = 0
        source_paths = set()

        for patient_id in patient_ids:
            seg_path = self.find_existing_segmentation(patient_id, dataset_id, mask_name)
            if seg_path:
                reusable += 1
                source_paths.add(str(seg_path.parent))
            else:
                need_processing += 1

        return {
            "total": len(patient_ids),
            "reusable": reusable,
            "need_processing": need_processing,
            "reuse_rate": reusable / len(patient_ids) * 100 if patient_ids else 0,
            "source_paths": list(source_paths),
            "estimated_time_saved_hours": reusable * 80 / 3600,  # ~80s per TotalSeg run
        }

    # =========================================================================
    # TotalSegmentator
    # =========================================================================

    def ensure_totalsegmentator(
        self,
        patient_id: str,
        dataset_id: str,
        nifti_path: Optional[Union[str, Path]] = None,
        check_registry: bool = True,
    ) -> PreprocessingResult:
        """
        Ensure TotalSegmentator results exist for patient

        v0.6.3: Now automatically checks IntermediateResultsRegistry for
        existing results from other modules (e.g., VBCA) before running
        TotalSegmentator. This enables cross-project result sharing.

        Search order:
        1. Registry (cross-project discovery)
        2. Fallback paths (configured in config)
        3. Local segmentation_root
        4. Run TotalSegmentator if not found

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            nifti_path: Path to input NIfTI (optional, will look up if not provided)
            check_registry: Whether to check registry for existing results (default: True)

        Returns:
            PreprocessingResult with segmentation directory
        """
        start_time = time.time()
        seg_dir = self._get_segmentation_dir(dataset_id)
        patient_seg_dir = seg_dir / patient_id

        # v0.6.3: Check registry for existing results from other modules
        if check_registry and self.config.use_registry and not self.config.force_reprocess:
            existing_seg = self.find_existing_segmentation(patient_id, dataset_id)
            if existing_seg and existing_seg != patient_seg_dir:
                # Found in registry/fallback - use it
                return PreprocessingResult(
                    patient_id=patient_id,
                    stage="totalsegmentator",
                    success=True,
                    output_path=existing_seg,
                    was_cached=True,
                    processing_time=time.time() - start_time,
                )

        # Check if already exists in local directory
        if patient_seg_dir.exists() and not self.config.force_reprocess:
            # Verify at least heart mask exists
            heart_mask = patient_seg_dir / "heart.nii.gz"
            if heart_mask.exists():
                return PreprocessingResult(
                    patient_id=patient_id,
                    stage="totalsegmentator",
                    success=True,
                    output_path=patient_seg_dir,
                    was_cached=True,
                    processing_time=time.time() - start_time,
                )

        # Get NIfTI path
        if not nifti_path:
            nifti_path = self.get_nifti_path(patient_id, dataset_id)

        if not nifti_path or not Path(nifti_path).exists():
            return PreprocessingResult(
                patient_id=patient_id,
                stage="totalsegmentator",
                success=False,
                error_message="NIfTI file not found. Run ensure_nifti first.",
                processing_time=time.time() - start_time,
            )

        # Run TotalSegmentator
        patient_seg_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Find TotalSegmentator executable
            totalseg_cmd = self._find_totalsegmentator()
            if not totalseg_cmd:
                raise RuntimeError("TotalSegmentator not found. Install with: pip install TotalSegmentator")

            cmd = [
                totalseg_cmd,
                "-i", str(nifti_path),
                "-o", str(patient_seg_dir),
                "--task", self.config.totalsegmentator_task,
            ]

            if self.config.totalsegmentator_fast:
                cmd.append("--fast")

            if self.config.totalsegmentator_roi_subset:
                cmd.extend(["--roi_subset", self.config.totalsegmentator_roi_subset])

            if self.config.totalsegmentator_device == "cpu":
                cmd.extend(["--device", "cpu"])

            self._log(f"  [TotalSeg] Running for {patient_id}...")
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            if process.returncode != 0:
                raise RuntimeError(f"TotalSegmentator failed: {process.stderr}")

            # GPU stabilization wait
            if self.config.totalsegmentator_device == "gpu":
                time.sleep(self.config.gpu_stabilization_time)

            processing_time = time.time() - start_time

            # Register in batch manager
            seg_dataset_id = f"organs_{dataset_id}"
            manager = self._get_or_load_seg_manager(dataset_id)
            manager.register_patient(
                dataset_id=seg_dataset_id,
                patient_id=patient_id,
                status="success",
                output_file=patient_id,
                processing_time_seconds=processing_time,
            )

            self._log(f"  [OK] TotalSegmentator complete: {processing_time:.1f}s")

            return PreprocessingResult(
                patient_id=patient_id,
                stage="totalsegmentator",
                success=True,
                output_path=patient_seg_dir,
                was_cached=False,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            self._log(f"  [X] TotalSegmentator failed: {str(e)}")

            return PreprocessingResult(
                patient_id=patient_id,
                stage="totalsegmentator",
                success=False,
                error_message=str(e),
                processing_time=processing_time,
            )

    # =========================================================================
    # Mask Access
    # =========================================================================

    def get_mask(
        self,
        patient_id: str,
        dataset_id: str,
        mask_name: str,
    ) -> Optional[Path]:
        """
        Get path to specific mask file

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            mask_name: Mask name (e.g., "heart", "aorta", "vertebrae_L1")

        Returns:
            Path to mask file if exists, None otherwise
        """
        seg_dir = self._get_segmentation_dir(dataset_id)
        patient_seg_dir = seg_dir / patient_id

        # Get filename from standard masks or use as-is
        filename = self.STANDARD_MASKS.get(mask_name, f"{mask_name}.nii.gz")
        mask_path = patient_seg_dir / filename

        if mask_path.exists():
            return mask_path
        return None

    def get_masks(
        self,
        patient_id: str,
        dataset_id: str,
        mask_names: List[str],
    ) -> Dict[str, Optional[Path]]:
        """
        Get paths to multiple mask files

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            mask_names: List of mask names

        Returns:
            Dictionary of mask_name -> Path (or None if not found)
        """
        return {
            name: self.get_mask(patient_id, dataset_id, name)
            for name in mask_names
        }

    def get_module_masks(
        self,
        patient_id: str,
        dataset_id: str,
        module: str,
    ) -> Dict[str, Optional[Path]]:
        """
        Get all required masks for a specific module

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            module: Analysis type (e.g., "pericardial_fat", "vertebra_composition")

        Returns:
            Dictionary of mask_name -> Path (or None if not found)
        """
        required_masks = self.MODULE_REQUIREMENTS.get(module, [])
        return self.get_masks(patient_id, dataset_id, required_masks)

    def validate_masks(
        self,
        patient_id: str,
        dataset_id: str,
        mask_names: List[str],
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required masks exist

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            mask_names: List of required mask names

        Returns:
            Tuple of (all_valid, list of missing mask names)
        """
        masks = self.get_masks(patient_id, dataset_id, mask_names)
        missing = [name for name, path in masks.items() if path is None]
        return len(missing) == 0, missing

    def validate_for_module(
        self,
        patient_id: str,
        dataset_id: str,
        module: str,
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all masks required by a module exist

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            module: Analysis type (e.g., "pericardial_fat", "vertebra_composition")

        Returns:
            Tuple of (valid, list of missing mask names)
        """
        required_masks = self.MODULE_REQUIREMENTS.get(module, [])
        return self.validate_masks(patient_id, dataset_id, required_masks)

    # =========================================================================
    # Full Preprocessing
    # =========================================================================

    def preprocess_patient(
        self,
        patient_id: str,
        dataset_id: str,
        dicom_path: Optional[Union[str, Path]] = None,
        run_totalsegmentator: bool = True,
    ) -> Dict[str, PreprocessingResult]:
        """
        Run full preprocessing for a patient

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier
            dicom_path: Path to DICOM (required if NIfTI doesn't exist)
            run_totalsegmentator: Whether to run TotalSegmentator

        Returns:
            Dictionary with results for each stage
        """
        results = {}

        # Stage 1: NIfTI conversion
        nifti_result = self.ensure_nifti(patient_id, dataset_id, dicom_path)
        results["nifti"] = nifti_result

        if not nifti_result.success:
            return results

        # Stage 2: TotalSegmentator (optional)
        if run_totalsegmentator:
            seg_result = self.ensure_totalsegmentator(
                patient_id, dataset_id, nifti_result.output_path
            )
            results["totalsegmentator"] = seg_result

        return results

    def get_preprocessing_status(
        self,
        patient_id: str,
        dataset_id: str,
    ) -> Dict[str, Any]:
        """
        Get preprocessing status for a patient

        Args:
            patient_id: Patient identifier
            dataset_id: Dataset identifier

        Returns:
            Status dictionary
        """
        nifti_path = self.get_nifti_path(patient_id, dataset_id)
        seg_dir = self._get_segmentation_dir(dataset_id) / patient_id

        status = {
            "patient_id": patient_id,
            "dataset_id": dataset_id,
            "nifti": {
                "exists": nifti_path is not None,
                "path": str(nifti_path) if nifti_path else None,
            },
            "totalsegmentator": {
                "exists": seg_dir.exists() if seg_dir else False,
                "path": str(seg_dir) if seg_dir.exists() else None,
            },
            "masks": {},
        }

        # Check key masks
        for mask_name in ["heart", "aorta", "vertebrae_T12", "vertebrae_L1"]:
            mask_path = self.get_mask(patient_id, dataset_id, mask_name)
            status["masks"][mask_name] = mask_path is not None

        return status


# Convenience function
def create_pipeline(
    nifti_root: Union[str, Path],
    segmentation_root: Union[str, Path],
    dicom_root: Optional[Union[str, Path]] = None,
    **kwargs,
) -> SharedPreprocessingPipeline:
    """
    Create a SharedPreprocessingPipeline with common defaults

    Args:
        nifti_root: Root directory for NIfTI files
        segmentation_root: Root directory for TotalSegmentator results
        dicom_root: Optional root directory for DICOM files
        **kwargs: Additional PreprocessingConfig options

    Returns:
        Configured SharedPreprocessingPipeline
    """
    config = PreprocessingConfig(
        nifti_root=Path(nifti_root),
        segmentation_root=Path(segmentation_root),
        dicom_root=Path(dicom_root) if dicom_root else None,
        **kwargs,
    )
    return SharedPreprocessingPipeline(config=config)
