"""
Batch Manager for cardiac imaging pipelines
Provides batch tracking with manifest.json for cross-project data sharing

This module enables:
- Batch creation and tracking with manifest.json
- Deduplication of DICOM->NIfTI conversions
- Consumer tracking for data lineage
- Cross-project data discovery

Usage:
    from cardiac_shared.data import BatchManager, BatchManifest

    # Create batch manager
    manager = BatchManager(output_dir=Path("/path/to/nifti"))

    # Create or load manifest
    manifest = manager.create_batch("study_cohort_v1", source_path="/dicom/chd")

    # Check for existing NIfTI
    existing = manager.find_existing_nifti("P001234", "study_cohort_v1")
    if existing:
        print(f"Reusing existing: {existing}")

    # Register processing result
    manager.register_patient(batch_id, patient_id, output_file, metadata)

    # Register consumer
    manager.register_consumer(batch_id, "analysis_module", "run_001")

Author: Cardiac ML Research Team
Created: 2026-01-03
Version: 0.6.0
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
import socket


@dataclass
class PatientEntry:
    """Individual patient entry in a batch manifest"""
    patient_id: str
    status: str = "pending"  # pending, success, failed, skipped
    output_file: Optional[str] = None
    dimensions: Optional[List[int]] = None
    spacing: Optional[List[float]] = None
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConsumerRecord:
    """Record of a module that consumed this batch"""
    module: str
    batch_id: str
    first_used: str
    last_used: Optional[str] = None
    run_count: int = 1


@dataclass
class BatchManifest:
    """
    Manifest for a batch of processed files

    Stored as manifest.json in the batch output directory
    """
    manifest_version: str = "1.0"
    dataset_id: str = ""
    dataset_type: str = "nifti_converted"

    # Creation info
    created_at: str = ""
    created_by: str = ""
    machine_id: str = ""
    tool: str = ""
    tool_version: str = ""

    # Source info
    source_type: str = "dicom"
    source_path: str = ""
    provider: str = ""
    batch: str = ""

    # Patient data
    patients: Dict[str, PatientEntry] = field(default_factory=dict)

    # Summary stats
    total_patients: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0

    # Consumer tracking
    consumers: List[ConsumerRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            "manifest_version": self.manifest_version,
            "dataset_id": self.dataset_id,
            "dataset_type": self.dataset_type,
            "creation_info": {
                "created_at": self.created_at,
                "created_by": self.created_by,
                "machine_id": self.machine_id,
                "tool": self.tool,
                "tool_version": self.tool_version,
            },
            "source_info": {
                "source_type": self.source_type,
                "source_path": self.source_path,
                "provider": self.provider,
                "batch": self.batch,
            },
            "patients": {
                pid: asdict(entry) for pid, entry in self.patients.items()
            },
            "summary": {
                "total_patients": self.total_patients,
                "successful": self.successful,
                "failed": self.failed,
                "skipped": self.skipped,
            },
            "consumers": [asdict(c) for c in self.consumers],
        }
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BatchManifest':
        """Create from dictionary (loaded from JSON)"""
        manifest = cls()

        manifest.manifest_version = data.get("manifest_version", "1.0")
        manifest.dataset_id = data.get("dataset_id", "")
        manifest.dataset_type = data.get("dataset_type", "nifti_converted")

        # Creation info
        creation = data.get("creation_info", {})
        manifest.created_at = creation.get("created_at", "")
        manifest.created_by = creation.get("created_by", "")
        manifest.machine_id = creation.get("machine_id", "")
        manifest.tool = creation.get("tool", "")
        manifest.tool_version = creation.get("tool_version", "")

        # Source info
        source = data.get("source_info", {})
        manifest.source_type = source.get("source_type", "dicom")
        manifest.source_path = source.get("source_path", "")
        manifest.provider = source.get("provider", "")
        manifest.batch = source.get("batch", "")

        # Patient data
        patients_data = data.get("patients", {})
        for pid, pdata in patients_data.items():
            manifest.patients[pid] = PatientEntry(
                patient_id=pid,
                status=pdata.get("status", "pending"),
                output_file=pdata.get("output_file"),
                dimensions=pdata.get("dimensions"),
                spacing=pdata.get("spacing"),
                processed_at=pdata.get("processed_at"),
                error_message=pdata.get("error_message"),
                processing_time_seconds=pdata.get("processing_time_seconds"),
                metadata=pdata.get("metadata", {}),
            )

        # Summary
        summary = data.get("summary", {})
        manifest.total_patients = summary.get("total_patients", 0)
        manifest.successful = summary.get("successful", 0)
        manifest.failed = summary.get("failed", 0)
        manifest.skipped = summary.get("skipped", 0)

        # Consumers
        consumers_data = data.get("consumers", [])
        for cdata in consumers_data:
            manifest.consumers.append(ConsumerRecord(
                module=cdata.get("module", ""),
                batch_id=cdata.get("batch_id", ""),
                first_used=cdata.get("first_used", ""),
                last_used=cdata.get("last_used"),
                run_count=cdata.get("run_count", 1),
            ))

        return manifest

    def update_summary(self) -> None:
        """Recalculate summary statistics from patient data"""
        self.total_patients = len(self.patients)
        self.successful = sum(1 for p in self.patients.values() if p.status == "success")
        self.failed = sum(1 for p in self.patients.values() if p.status == "failed")
        self.skipped = sum(1 for p in self.patients.values() if p.status == "skipped")


class BatchManager:
    """
    Manager for batch processing with manifest tracking

    Handles:
    - Creating and loading batch manifests
    - Finding existing processed files (deduplication)
    - Registering processing results
    - Tracking data consumers

    Example:
        >>> manager = BatchManager(output_dir=Path("/nifti"))
        >>> manifest = manager.create_batch("study_cohort_v1")
        >>>
        >>> # Check before processing
        >>> existing = manager.find_existing_nifti("P001234", "study_cohort_v1")
        >>> if not existing:
        ...     # Process patient
        ...     manager.register_patient("study_cohort_v1", "P001234",
        ...                              output_file="P001234.nii.gz",
        ...                              dimensions=[512, 512, 512])
    """

    MANIFEST_FILENAME = "manifest.json"

    def __init__(
        self,
        output_dir: Optional[Union[str, Path]] = None,
        auto_save: bool = True,
    ):
        """
        Initialize BatchManager

        Args:
            output_dir: Root directory for batch outputs
            auto_save: Automatically save manifest after changes
        """
        self.output_dir = Path(output_dir) if output_dir else None
        self.auto_save = auto_save
        self._manifests: Dict[str, BatchManifest] = {}
        self._manifest_paths: Dict[str, Path] = {}

    def _get_machine_id(self) -> str:
        """Get machine identifier"""
        try:
            return socket.gethostname()
        except Exception:
            return "unknown"

    def _get_timestamp(self) -> str:
        """Get ISO format timestamp"""
        return datetime.now().isoformat()

    def create_batch(
        self,
        dataset_id: str,
        source_path: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        tool: str = "cardiac-shared",
        tool_version: str = "0.6.0",
        provider: str = "",
        batch: str = "",
        dataset_type: str = "nifti_converted",
    ) -> BatchManifest:
        """
        Create a new batch manifest

        Args:
            dataset_id: Unique batch identifier (e.g., "study_cohort_v1")
            source_path: Path to source data
            output_path: Output directory for this batch
            tool: Processing tool name
            tool_version: Tool version
            provider: Data provider (e.g., "Hospital A")
            batch: Batch name (e.g., "batch1")
            dataset_type: Type of data (e.g., "nifti_converted", "totalsegmentator_masks")

        Returns:
            BatchManifest object
        """
        # Determine output path
        if output_path:
            batch_dir = Path(output_path)
        elif self.output_dir:
            batch_dir = self.output_dir / dataset_id
        else:
            raise ValueError("No output directory specified")

        # Create directory
        batch_dir.mkdir(parents=True, exist_ok=True)

        # Check for existing manifest
        manifest_path = batch_dir / self.MANIFEST_FILENAME
        if manifest_path.exists():
            return self.load_manifest(manifest_path)

        # Create new manifest
        manifest = BatchManifest(
            dataset_id=dataset_id,
            dataset_type=dataset_type,
            created_at=self._get_timestamp(),
            created_by="cardiac-shared.BatchManager",
            machine_id=self._get_machine_id(),
            tool=tool,
            tool_version=tool_version,
            source_type="dicom" if "nifti" in dataset_type else "nifti",
            source_path=str(source_path) if source_path else "",
            provider=provider,
            batch=batch,
        )

        # Store and save
        self._manifests[dataset_id] = manifest
        self._manifest_paths[dataset_id] = manifest_path

        if self.auto_save:
            self.save_manifest(dataset_id)

        return manifest

    def load_manifest(
        self,
        manifest_path: Union[str, Path],
    ) -> BatchManifest:
        """
        Load existing manifest from file

        Args:
            manifest_path: Path to manifest.json

        Returns:
            BatchManifest object
        """
        manifest_path = Path(manifest_path)

        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        manifest = BatchManifest.from_dict(data)

        # Store reference
        self._manifests[manifest.dataset_id] = manifest
        self._manifest_paths[manifest.dataset_id] = manifest_path

        return manifest

    def save_manifest(self, dataset_id: str) -> None:
        """
        Save manifest to disk

        Args:
            dataset_id: Batch identifier
        """
        if dataset_id not in self._manifests:
            raise KeyError(f"Manifest not found: {dataset_id}")

        manifest = self._manifests[dataset_id]
        manifest_path = self._manifest_paths[dataset_id]

        manifest.update_summary()

        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest.to_dict(), f, indent=2, ensure_ascii=False)

    def get_manifest(self, dataset_id: str) -> Optional[BatchManifest]:
        """
        Get manifest by dataset ID

        Args:
            dataset_id: Batch identifier

        Returns:
            BatchManifest or None
        """
        return self._manifests.get(dataset_id)

    def find_existing_nifti(
        self,
        patient_id: str,
        dataset_id: str,
    ) -> Optional[Path]:
        """
        Find existing NIfTI file for a patient (deduplication check)

        Args:
            patient_id: Patient identifier
            dataset_id: Batch identifier

        Returns:
            Path to existing NIfTI file, or None if not found
        """
        manifest = self._manifests.get(dataset_id)
        if not manifest:
            return None

        patient = manifest.patients.get(patient_id)
        if not patient or patient.status != "success":
            return None

        if not patient.output_file:
            return None

        # Get batch directory from manifest path
        manifest_path = self._manifest_paths.get(dataset_id)
        if not manifest_path:
            return None

        output_path = manifest_path.parent / patient.output_file
        if output_path.exists():
            return output_path

        return None

    def register_patient(
        self,
        dataset_id: str,
        patient_id: str,
        status: str = "success",
        output_file: Optional[str] = None,
        dimensions: Optional[List[int]] = None,
        spacing: Optional[List[float]] = None,
        processing_time_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a patient processing result

        Args:
            dataset_id: Batch identifier
            patient_id: Patient identifier
            status: Processing status ("success", "failed", "skipped")
            output_file: Output filename (relative to batch directory)
            dimensions: Volume dimensions [x, y, z]
            spacing: Voxel spacing [x, y, z]
            processing_time_seconds: Processing time
            error_message: Error message if failed
            metadata: Additional metadata
        """
        manifest = self._manifests.get(dataset_id)
        if not manifest:
            raise KeyError(f"Manifest not found: {dataset_id}")

        entry = PatientEntry(
            patient_id=patient_id,
            status=status,
            output_file=output_file,
            dimensions=dimensions,
            spacing=spacing,
            processed_at=self._get_timestamp(),
            error_message=error_message,
            processing_time_seconds=processing_time_seconds,
            metadata=metadata or {},
        )

        manifest.patients[patient_id] = entry

        if self.auto_save:
            self.save_manifest(dataset_id)

    def register_consumer(
        self,
        dataset_id: str,
        module: str,
        batch_id: str,
    ) -> None:
        """
        Register a module that consumed this batch

        Args:
            dataset_id: Batch identifier
            module: Consumer module name (e.g., "pericardial_fat", "vertebra_composition")
            batch_id: Consumer's batch run ID
        """
        manifest = self._manifests.get(dataset_id)
        if not manifest:
            raise KeyError(f"Manifest not found: {dataset_id}")

        timestamp = self._get_timestamp()

        # Check if consumer already exists
        for consumer in manifest.consumers:
            if consumer.module == module:
                consumer.last_used = timestamp
                consumer.run_count += 1
                if self.auto_save:
                    self.save_manifest(dataset_id)
                return

        # Add new consumer
        consumer = ConsumerRecord(
            module=module,
            batch_id=batch_id,
            first_used=timestamp,
        )
        manifest.consumers.append(consumer)

        if self.auto_save:
            self.save_manifest(dataset_id)

    def list_batches(self) -> List[str]:
        """
        List all loaded batch IDs

        Returns:
            List of dataset IDs
        """
        return list(self._manifests.keys())

    def get_batch_summary(self, dataset_id: str) -> Dict[str, Any]:
        """
        Get summary statistics for a batch

        Args:
            dataset_id: Batch identifier

        Returns:
            Summary dictionary
        """
        manifest = self._manifests.get(dataset_id)
        if not manifest:
            return {}

        manifest.update_summary()

        return {
            "dataset_id": manifest.dataset_id,
            "total": manifest.total_patients,
            "successful": manifest.successful,
            "failed": manifest.failed,
            "skipped": manifest.skipped,
            "consumers": len(manifest.consumers),
            "created_at": manifest.created_at,
        }

    def print_summary(self, dataset_id: Optional[str] = None) -> None:
        """
        Print batch summary to console

        Args:
            dataset_id: Optional specific batch ID, or None for all
        """
        if dataset_id:
            batch_ids = [dataset_id] if dataset_id in self._manifests else []
        else:
            batch_ids = list(self._manifests.keys())

        if not batch_ids:
            print("[!] No batches loaded")
            return

        print("=" * 60)
        print("Batch Manager Summary")
        print("=" * 60)

        for bid in batch_ids:
            summary = self.get_batch_summary(bid)
            print(f"\n{bid}:")
            print(f"  Total: {summary['total']}")
            print(f"  Success: {summary['successful']}")
            print(f"  Failed: {summary['failed']}")
            print(f"  Skipped: {summary['skipped']}")
            print(f"  Consumers: {summary['consumers']}")

        print("=" * 60)


# Convenience functions for common operations
def create_nifti_batch(
    dataset_id: str,
    source_path: Union[str, Path],
    output_path: Union[str, Path],
    provider: str = "",
    batch: str = "",
) -> BatchManifest:
    """
    Convenience function to create a NIfTI conversion batch

    Args:
        dataset_id: Batch identifier (e.g., "study_cohort_v1")
        source_path: Path to source DICOM directory
        output_path: Output directory for NIfTI files
        provider: Data provider name
        batch: Batch name

    Returns:
        BatchManifest object
    """
    manager = BatchManager(output_dir=Path(output_path).parent)
    return manager.create_batch(
        dataset_id=dataset_id,
        source_path=str(source_path),
        output_path=output_path,
        dataset_type="nifti_converted",
        provider=provider,
        batch=batch,
    )


def load_batch(manifest_path: Union[str, Path]) -> BatchManifest:
    """
    Convenience function to load a batch manifest

    Args:
        manifest_path: Path to manifest.json

    Returns:
        BatchManifest object
    """
    manager = BatchManager()
    return manager.load_manifest(manifest_path)
