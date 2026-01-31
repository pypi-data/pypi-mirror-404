"""
Unit tests for cardiac_shared.data.batch_manager module
Tests BatchManager, BatchManifest, and related functionality
"""

import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from cardiac_shared.data.batch_manager import (
    BatchManager,
    BatchManifest,
    PatientEntry,
    ConsumerRecord,
    create_nifti_batch,
    load_batch,
)


class TestPatientEntry:
    """Tests for PatientEntry dataclass"""

    def test_default_values(self):
        """Test default values"""
        entry = PatientEntry(patient_id="test123")
        assert entry.patient_id == "test123"
        assert entry.status == "pending"
        assert entry.output_file is None
        assert entry.dimensions is None
        assert entry.spacing is None
        assert entry.metadata == {}

    def test_custom_values(self):
        """Test custom values"""
        entry = PatientEntry(
            patient_id="test456",
            status="success",
            output_file="test456.nii.gz",
            dimensions=[512, 512, 256],
            spacing=[0.7, 0.7, 0.5],
            processing_time_seconds=30.5,
        )
        assert entry.status == "success"
        assert entry.dimensions == [512, 512, 256]
        assert entry.processing_time_seconds == 30.5


class TestConsumerRecord:
    """Tests for ConsumerRecord dataclass"""

    def test_default_values(self):
        """Test default values"""
        consumer = ConsumerRecord(
            module="pericardial_fat",
            batch_id="analysis_run_001",
            first_used="2026-01-03T10:00:00",
        )
        assert consumer.module == "pericardial_fat"
        assert consumer.run_count == 1
        assert consumer.last_used is None


class TestBatchManifest:
    """Tests for BatchManifest class"""

    def test_default_values(self):
        """Test default manifest creation"""
        manifest = BatchManifest()
        assert manifest.manifest_version == "1.0"
        assert manifest.dataset_type == "nifti_converted"
        assert manifest.total_patients == 0

    def test_to_dict(self):
        """Test manifest serialization to dict"""
        manifest = BatchManifest(
            dataset_id="test_batch",
            created_at="2026-01-03T10:00:00",
            created_by="test",
            machine_id="testmachine",
        )
        manifest.patients["p001"] = PatientEntry(
            patient_id="p001",
            status="success",
            output_file="p001.nii.gz",
        )

        data = manifest.to_dict()
        assert data["dataset_id"] == "test_batch"
        assert "creation_info" in data
        assert data["creation_info"]["created_at"] == "2026-01-03T10:00:00"
        assert "p001" in data["patients"]

    def test_from_dict(self):
        """Test manifest deserialization from dict"""
        data = {
            "manifest_version": "1.0",
            "dataset_id": "test_batch",
            "dataset_type": "nifti_converted",
            "creation_info": {
                "created_at": "2026-01-03T10:00:00",
                "created_by": "test",
                "machine_id": "testmachine",
                "tool": "SimpleITK",
                "tool_version": "2.3.1",
            },
            "source_info": {
                "source_type": "dicom",
                "source_path": "/data/dicom",
                "provider": "Dr. Test",
                "batch": "batch1",
            },
            "patients": {
                "p001": {
                    "patient_id": "p001",
                    "status": "success",
                    "output_file": "p001.nii.gz",
                }
            },
            "summary": {
                "total_patients": 1,
                "successful": 1,
                "failed": 0,
                "skipped": 0,
            },
            "consumers": [
                {
                    "module": "pericardial_fat",
                    "batch_id": "pcfa_001",
                    "first_used": "2026-01-03T11:00:00",
                    "run_count": 1,
                }
            ],
        }

        manifest = BatchManifest.from_dict(data)
        assert manifest.dataset_id == "test_batch"
        assert manifest.source_path == "/data/dicom"
        assert len(manifest.patients) == 1
        assert manifest.patients["p001"].status == "success"
        assert len(manifest.consumers) == 1

    def test_update_summary(self):
        """Test summary recalculation"""
        manifest = BatchManifest()
        manifest.patients["p001"] = PatientEntry(patient_id="p001", status="success")
        manifest.patients["p002"] = PatientEntry(patient_id="p002", status="success")
        manifest.patients["p003"] = PatientEntry(patient_id="p003", status="failed")
        manifest.patients["p004"] = PatientEntry(patient_id="p004", status="skipped")

        manifest.update_summary()
        assert manifest.total_patients == 4
        assert manifest.successful == 2
        assert manifest.failed == 1
        assert manifest.skipped == 1


class TestBatchManager:
    """Tests for BatchManager class"""

    def test_init(self):
        """Test manager initialization"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            assert manager.output_dir == Path(tmpdir)
            assert manager.auto_save is True

    def test_create_batch(self):
        """Test batch creation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manifest = manager.create_batch(
                dataset_id="test_batch",
                source_path="/data/dicom",
                provider="Dr. Test",
            )

            assert manifest.dataset_id == "test_batch"
            assert manifest.source_path == "/data/dicom"
            assert manifest.provider == "Dr. Test"

            # Check manifest file exists
            manifest_path = Path(tmpdir) / "test_batch" / "manifest.json"
            assert manifest_path.exists()

    def test_load_manifest(self):
        """Test manifest loading"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest file
            batch_dir = Path(tmpdir) / "test_batch"
            batch_dir.mkdir()
            manifest_path = batch_dir / "manifest.json"

            data = {
                "manifest_version": "1.0",
                "dataset_id": "test_batch",
                "dataset_type": "nifti_converted",
                "creation_info": {
                    "created_at": "2026-01-03",
                    "created_by": "test",
                    "machine_id": "test",
                    "tool": "test",
                    "tool_version": "1.0",
                },
                "source_info": {},
                "patients": {},
                "summary": {"total_patients": 0, "successful": 0, "failed": 0, "skipped": 0},
                "consumers": [],
            }
            with open(manifest_path, 'w') as f:
                json.dump(data, f)

            manager = BatchManager(output_dir=tmpdir)
            manifest = manager.load_manifest(manifest_path)

            assert manifest.dataset_id == "test_batch"

    def test_register_patient(self):
        """Test patient registration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manager.create_batch("test_batch")

            manager.register_patient(
                dataset_id="test_batch",
                patient_id="p001",
                status="success",
                output_file="p001.nii.gz",
                dimensions=[512, 512, 256],
                spacing=[0.7, 0.7, 0.5],
            )

            manifest = manager.get_manifest("test_batch")
            assert "p001" in manifest.patients
            assert manifest.patients["p001"].status == "success"
            assert manifest.patients["p001"].dimensions == [512, 512, 256]

    def test_find_existing_nifti(self):
        """Test finding existing NIfTI file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manager.create_batch("test_batch")

            # Create fake NIfTI file
            batch_dir = Path(tmpdir) / "test_batch"
            nifti_file = batch_dir / "p001.nii.gz"
            nifti_file.touch()

            # Register patient
            manager.register_patient(
                dataset_id="test_batch",
                patient_id="p001",
                status="success",
                output_file="p001.nii.gz",
            )

            # Should find existing file
            existing = manager.find_existing_nifti("p001", "test_batch")
            assert existing is not None
            assert existing.name == "p001.nii.gz"

            # Should not find non-existent patient
            not_found = manager.find_existing_nifti("p999", "test_batch")
            assert not_found is None

    def test_register_consumer(self):
        """Test consumer registration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manager.create_batch("test_batch")

            manager.register_consumer("test_batch", "pericardial_fat", "analysis_run_001")

            manifest = manager.get_manifest("test_batch")
            assert len(manifest.consumers) == 1
            assert manifest.consumers[0].module == "pericardial_fat"

            # Register same consumer again - should increment count
            manager.register_consumer("test_batch", "pericardial_fat", "analysis_run_002")
            assert manifest.consumers[0].run_count == 2

    def test_list_batches(self):
        """Test listing batches"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manager.create_batch("batch1")
            manager.create_batch("batch2")

            batches = manager.list_batches()
            assert "batch1" in batches
            assert "batch2" in batches

    def test_get_batch_summary(self):
        """Test getting batch summary"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BatchManager(output_dir=tmpdir)
            manager.create_batch("test_batch")

            manager.register_patient("test_batch", "p001", status="success")
            manager.register_patient("test_batch", "p002", status="failed")

            summary = manager.get_batch_summary("test_batch")
            assert summary["total"] == 2
            assert summary["successful"] == 1
            assert summary["failed"] == 1


class TestConvenienceFunctions:
    """Tests for module-level convenience functions"""

    def test_create_nifti_batch(self):
        """Test create_nifti_batch function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            manifest = create_nifti_batch(
                dataset_id="test_batch",
                source_path="/data/dicom",
                output_path=Path(tmpdir) / "test_batch",
                provider="Dr. Test",
            )

            assert manifest.dataset_id == "test_batch"
            assert manifest.dataset_type == "nifti_converted"

    def test_load_batch(self):
        """Test load_batch function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create manifest
            batch_dir = Path(tmpdir) / "test_batch"
            batch_dir.mkdir()
            manifest_path = batch_dir / "manifest.json"

            data = {
                "manifest_version": "1.0",
                "dataset_id": "test_batch",
                "dataset_type": "nifti_converted",
                "creation_info": {},
                "source_info": {},
                "patients": {},
                "summary": {"total_patients": 0, "successful": 0, "failed": 0, "skipped": 0},
                "consumers": [],
            }
            with open(manifest_path, 'w') as f:
                json.dump(data, f)

            manifest = load_batch(manifest_path)
            assert manifest.dataset_id == "test_batch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
