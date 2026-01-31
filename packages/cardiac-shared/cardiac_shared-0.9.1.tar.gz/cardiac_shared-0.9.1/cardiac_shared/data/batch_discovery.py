"""
Batch Discovery Module for cardiac imaging pipelines
Provides automatic discovery and selection of processing batches

This module enables:
- Automatic discovery of all batches in a directory (by manifest.json)
- Version/batch selection at runtime
- Cross-batch patient lookup
- Batch comparison and validation

Usage:
    from cardiac_shared.data import BatchDiscovery

    # Discover all TotalSegmentator batches
    discovery = BatchDiscovery(root_dir="/data/totalsegmentator")

    # List all available batches
    batches = discovery.list_batches()
    # Output: ['organs_cohort_v1', 'organs_cohort_v2', 'organs_normal_v1']

    # Get batch info
    info = discovery.get_batch_info('organs_cohort_v2')
    print(f"Created: {info['created_at']}, Patients: {info['total']}")

    # Find patient across all batches
    results = discovery.find_patient('P001234')
    # Output: [{'batch': 'organs_cohort_v2', 'status': 'success', 'path': ...}]

    # Select a specific batch for processing
    batch = discovery.select_batch('organs_cohort_v2')
    heart_mask = batch.get_mask('P001234', 'heart')

Author: Cardiac ML Research Team
Created: 2026-01-04
Version: 0.6.4
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field


@dataclass
class BatchInfo:
    """Information about a discovered batch"""
    batch_id: str
    path: Path
    dataset_type: str = "unknown"
    created_at: Optional[str] = None
    created_by: Optional[str] = None
    machine_id: Optional[str] = None
    tool: Optional[str] = None
    tool_version: Optional[str] = None
    total_patients: int = 0
    successful: int = 0
    failed: int = 0
    patients: List[str] = field(default_factory=list)
    has_manifest: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "path": str(self.path),
            "dataset_type": self.dataset_type,
            "created_at": self.created_at,
            "created_by": self.created_by,
            "machine_id": self.machine_id,
            "tool": self.tool,
            "tool_version": self.tool_version,
            "total_patients": self.total_patients,
            "successful": self.successful,
            "failed": self.failed,
            "patient_count": len(self.patients),
            "has_manifest": self.has_manifest,
        }


@dataclass
class PatientBatchRecord:
    """Record of a patient found in a batch"""
    patient_id: str
    batch_id: str
    batch_path: Path
    status: str = "unknown"
    output_file: Optional[str] = None
    processed_at: Optional[str] = None

    @property
    def patient_path(self) -> Path:
        """Get full path to patient directory"""
        return self.batch_path / self.patient_id


class BatchDiscovery:
    """
    Batch Discovery - Find and manage multiple processing batches

    This class provides intelligent batch discovery and selection:
    1. Scans directories for manifest.json files
    2. Maintains an index of all discovered batches
    3. Allows runtime selection of specific batches
    4. Supports cross-batch patient lookup

    Example:
        >>> discovery = BatchDiscovery("/data/totalsegmentator")
        >>>
        >>> # List all batches
        >>> for batch in discovery.list_batches():
        ...     info = discovery.get_batch_info(batch)
        ...     print(f"{batch}: {info['total_patients']} patients")
        >>>
        >>> # Select latest batch for CHD
        >>> batch = discovery.select_latest_batch(prefix="organs_cohort")
        >>>
        >>> # Find patient in any batch
        >>> results = discovery.find_patient("P001234")
        >>> if results:
        ...     latest = results[-1]  # Most recent
        ...     heart_mask = latest.patient_path / "heart.nii.gz"
    """

    MANIFEST_FILENAME = "manifest.json"

    def __init__(
        self,
        root_dir: Optional[Union[str, Path]] = None,
        scan_depth: int = 2,
        auto_scan: bool = True,
    ):
        """
        Initialize BatchDiscovery

        Args:
            root_dir: Root directory to scan for batches
            scan_depth: How deep to scan for manifest files (default: 2)
            auto_scan: Automatically scan on initialization (default: True)
        """
        self.root_dir = Path(root_dir) if root_dir else None
        self.scan_depth = scan_depth
        self._batches: Dict[str, BatchInfo] = {}
        self._patient_index: Dict[str, List[PatientBatchRecord]] = {}

        if auto_scan and self.root_dir and self.root_dir.exists():
            self.scan()

    def scan(self, root_dir: Optional[Union[str, Path]] = None) -> int:
        """
        Scan directory for batches

        Args:
            root_dir: Optional override for root directory

        Returns:
            Number of batches discovered
        """
        scan_dir = Path(root_dir) if root_dir else self.root_dir
        if not scan_dir or not scan_dir.exists():
            return 0

        self._batches.clear()
        self._patient_index.clear()

        # Find all manifest files
        manifest_paths = self._find_manifests(scan_dir, self.scan_depth)

        for manifest_path in manifest_paths:
            batch_info = self._load_batch_info(manifest_path)
            if batch_info:
                self._batches[batch_info.batch_id] = batch_info
                self._index_patients(batch_info)

        return len(self._batches)

    def _find_manifests(self, root: Path, depth: int) -> List[Path]:
        """Find all manifest.json files within depth"""
        manifests = []

        if depth <= 0:
            return manifests

        try:
            for item in root.iterdir():
                if item.is_file() and item.name == self.MANIFEST_FILENAME:
                    manifests.append(item)
                elif item.is_dir() and depth > 1:
                    manifests.extend(self._find_manifests(item, depth - 1))
        except PermissionError:
            pass

        return manifests

    def _load_batch_info(self, manifest_path: Path) -> Optional[BatchInfo]:
        """Load batch info from manifest file"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            batch_path = manifest_path.parent
            batch_id = data.get("dataset_id", batch_path.name)

            # Get creation info
            creation = data.get("creation_info", {})

            # Get summary
            summary = data.get("summary", {})

            # Get patient list
            patients_data = data.get("patients", {})
            patients = list(patients_data.keys())

            return BatchInfo(
                batch_id=batch_id,
                path=batch_path,
                dataset_type=data.get("dataset_type", "unknown"),
                created_at=creation.get("created_at"),
                created_by=creation.get("created_by"),
                machine_id=creation.get("machine_id"),
                tool=creation.get("tool"),
                tool_version=creation.get("tool_version"),
                total_patients=summary.get("total_patients", len(patients)),
                successful=summary.get("successful", 0),
                failed=summary.get("failed", 0),
                patients=patients,
                has_manifest=True,
            )

        except Exception as e:
            print(f"[!] Failed to load manifest {manifest_path}: {e}")
            return None

    def _index_patients(self, batch_info: BatchInfo) -> None:
        """Index patients from a batch for quick lookup"""
        # Try to load full manifest for patient details
        manifest_path = batch_info.path / self.MANIFEST_FILENAME
        patients_data = {}

        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            patients_data = data.get("patients", {})
        except:
            pass

        for patient_id in batch_info.patients:
            patient_info = patients_data.get(patient_id, {})

            record = PatientBatchRecord(
                patient_id=patient_id,
                batch_id=batch_info.batch_id,
                batch_path=batch_info.path,
                status=patient_info.get("status", "unknown"),
                output_file=patient_info.get("output_file"),
                processed_at=patient_info.get("processed_at"),
            )

            if patient_id not in self._patient_index:
                self._patient_index[patient_id] = []
            self._patient_index[patient_id].append(record)

    # =========================================================================
    # Query Methods
    # =========================================================================

    def list_batches(
        self,
        prefix: Optional[str] = None,
        sort_by: str = "created_at",
    ) -> List[str]:
        """
        List all discovered batch IDs

        Args:
            prefix: Optional prefix filter (e.g., "organs_cohort")
            sort_by: Sort key ("created_at", "batch_id", "total_patients")

        Returns:
            List of batch IDs
        """
        batches = list(self._batches.keys())

        if prefix:
            batches = [b for b in batches if b.startswith(prefix)]

        if sort_by == "created_at":
            batches.sort(key=lambda b: self._batches[b].created_at or "", reverse=True)
        elif sort_by == "total_patients":
            batches.sort(key=lambda b: self._batches[b].total_patients, reverse=True)
        else:
            batches.sort()

        return batches

    def get_batch_info(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed info for a batch

        Args:
            batch_id: Batch identifier

        Returns:
            Batch info dictionary or None
        """
        batch = self._batches.get(batch_id)
        if batch:
            return batch.to_dict()
        return None

    def get_batch(self, batch_id: str) -> Optional[BatchInfo]:
        """
        Get BatchInfo object for a batch

        Args:
            batch_id: Batch identifier

        Returns:
            BatchInfo object or None
        """
        return self._batches.get(batch_id)

    def find_patient(
        self,
        patient_id: str,
        batch_prefix: Optional[str] = None,
    ) -> List[PatientBatchRecord]:
        """
        Find a patient across all batches

        Args:
            patient_id: Patient identifier
            batch_prefix: Optional batch prefix filter

        Returns:
            List of PatientBatchRecord (sorted by processed_at, newest first)
        """
        records = self._patient_index.get(patient_id, [])

        if batch_prefix:
            records = [r for r in records if r.batch_id.startswith(batch_prefix)]

        # Sort by processed_at (newest first)
        records.sort(key=lambda r: r.processed_at or "", reverse=True)

        return records

    def select_latest_batch(
        self,
        prefix: Optional[str] = None,
        require_success_count: int = 0,
    ) -> Optional[BatchInfo]:
        """
        Select the latest batch matching criteria

        Args:
            prefix: Batch ID prefix filter
            require_success_count: Minimum successful patients required

        Returns:
            BatchInfo for the latest matching batch, or None
        """
        batches = self.list_batches(prefix=prefix, sort_by="created_at")

        for batch_id in batches:
            batch = self._batches[batch_id]
            if batch.successful >= require_success_count:
                return batch

        return None

    def select_batch_for_patient(
        self,
        patient_id: str,
        prefer_latest: bool = True,
        require_success: bool = True,
    ) -> Optional[PatientBatchRecord]:
        """
        Select the best batch for a specific patient

        Args:
            patient_id: Patient identifier
            prefer_latest: Prefer the most recent batch
            require_success: Only consider successful processing

        Returns:
            PatientBatchRecord for the best match, or None
        """
        records = self.find_patient(patient_id)

        if require_success:
            records = [r for r in records if r.status == "success"]

        if not records:
            return None

        if prefer_latest:
            return records[0]  # Already sorted newest first

        return records[-1]  # Oldest

    # =========================================================================
    # Batch Comparison
    # =========================================================================

    def compare_batches(
        self,
        batch_id_a: str,
        batch_id_b: str,
    ) -> Dict[str, Any]:
        """
        Compare two batches

        Args:
            batch_id_a: First batch ID
            batch_id_b: Second batch ID

        Returns:
            Comparison dictionary
        """
        batch_a = self._batches.get(batch_id_a)
        batch_b = self._batches.get(batch_id_b)

        if not batch_a or not batch_b:
            return {"error": "One or both batches not found"}

        patients_a = set(batch_a.patients)
        patients_b = set(batch_b.patients)

        return {
            "batch_a": batch_id_a,
            "batch_b": batch_id_b,
            "patients_a": len(patients_a),
            "patients_b": len(patients_b),
            "common": len(patients_a & patients_b),
            "only_in_a": len(patients_a - patients_b),
            "only_in_b": len(patients_b - patients_a),
            "created_a": batch_a.created_at,
            "created_b": batch_b.created_at,
        }

    def get_patient_coverage(
        self,
        patient_ids: List[str],
        batch_prefix: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check how many patients are covered by existing batches

        Args:
            patient_ids: List of patient IDs to check
            batch_prefix: Optional batch prefix filter

        Returns:
            Coverage summary
        """
        covered = []
        not_covered = []
        coverage_details = {}

        for patient_id in patient_ids:
            records = self.find_patient(patient_id, batch_prefix)
            successful = [r for r in records if r.status == "success"]

            if successful:
                covered.append(patient_id)
                coverage_details[patient_id] = {
                    "batches": [r.batch_id for r in successful],
                    "latest": successful[0].batch_id,
                }
            else:
                not_covered.append(patient_id)

        return {
            "total": len(patient_ids),
            "covered": len(covered),
            "not_covered": len(not_covered),
            "coverage_rate": len(covered) / len(patient_ids) * 100 if patient_ids else 0,
            "covered_patients": covered,
            "not_covered_patients": not_covered,
            "details": coverage_details,
        }

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def print_summary(self) -> None:
        """Print summary of all discovered batches"""
        print("=" * 70)
        print("Batch Discovery Summary")
        print("=" * 70)
        print(f"Root: {self.root_dir}")
        print(f"Batches: {len(self._batches)}")
        print(f"Indexed patients: {len(self._patient_index)}")
        print("-" * 70)

        for batch_id in self.list_batches(sort_by="created_at"):
            batch = self._batches[batch_id]
            created = batch.created_at[:10] if batch.created_at else "N/A"
            print(f"  [{batch_id}]")
            print(f"    Created: {created}, Patients: {batch.total_patients}, "
                  f"Success: {batch.successful}")
            print(f"    Path: {batch.path}")

        print("=" * 70)

    def add_batch_directory(
        self,
        batch_path: Union[str, Path],
        batch_id: Optional[str] = None,
    ) -> Optional[BatchInfo]:
        """
        Manually add a batch directory (even without manifest)

        Args:
            batch_path: Path to batch directory
            batch_id: Optional batch ID (defaults to directory name)

        Returns:
            BatchInfo for the added batch
        """
        batch_path = Path(batch_path)
        if not batch_path.exists():
            return None

        batch_id = batch_id or batch_path.name
        manifest_path = batch_path / self.MANIFEST_FILENAME

        if manifest_path.exists():
            batch_info = self._load_batch_info(manifest_path)
        else:
            # Create batch info from directory contents
            patients = []
            for item in batch_path.iterdir():
                if item.is_dir():
                    # Check if it looks like a patient directory
                    if any((item / f).exists() for f in ["heart.nii.gz", "aorta.nii.gz"]):
                        patients.append(item.name)

            batch_info = BatchInfo(
                batch_id=batch_id,
                path=batch_path,
                dataset_type="totalsegmentator_masks",
                total_patients=len(patients),
                successful=len(patients),  # Assume all successful if no manifest
                patients=patients,
                has_manifest=False,
            )

        if batch_info:
            self._batches[batch_info.batch_id] = batch_info
            self._index_patients(batch_info)

        return batch_info


# Convenience function
def discover_batches(
    root_dir: Union[str, Path],
    prefix: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function to discover and list batches

    Args:
        root_dir: Root directory to scan
        prefix: Optional batch ID prefix filter

    Returns:
        List of batch info dictionaries
    """
    discovery = BatchDiscovery(root_dir)
    batch_ids = discovery.list_batches(prefix=prefix)
    return [discovery.get_batch_info(bid) for bid in batch_ids]
