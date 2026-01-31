"""
Unit tests for cardiac_shared.preprocessing module
Tests DicomConverter, SharedPreprocessingPipeline, and related functionality
"""

import pytest
import tempfile
from pathlib import Path

# Test imports
from cardiac_shared.preprocessing import (
    DicomConverter,
    ConversionResult,
    convert_dicom_to_nifti,
    SharedPreprocessingPipeline,
    PreprocessingConfig,
    PreprocessingResult,
    create_pipeline,
)


# Check if SimpleITK is available
try:
    import SimpleITK as sitk
    HAS_SIMPLEITK = True
except ImportError:
    HAS_SIMPLEITK = False


class TestConversionResult:
    """Tests for ConversionResult dataclass"""

    def test_success_result(self):
        """Test successful conversion result"""
        result = ConversionResult(
            patient_id="p001",
            success=True,
            output_path=Path("/output/p001.nii.gz"),
            dimensions=[512, 512, 256],
            spacing=[0.7, 0.7, 0.5],
            processing_time=30.5,
            was_cached=False,
        )
        assert result.success is True
        assert result.patient_id == "p001"
        assert result.dimensions == [512, 512, 256]
        assert result.was_cached is False

    def test_failed_result(self):
        """Test failed conversion result"""
        result = ConversionResult(
            patient_id="p001",
            success=False,
            error_message="No DICOM files found",
            processing_time=0.5,
        )
        assert result.success is False
        assert result.error_message == "No DICOM files found"
        assert result.output_path is None

    def test_cached_result(self):
        """Test cached conversion result"""
        result = ConversionResult(
            patient_id="p001",
            success=True,
            output_path=Path("/output/p001.nii.gz"),
            was_cached=True,
            processing_time=0.01,
        )
        assert result.was_cached is True


@pytest.mark.skipif(not HAS_SIMPLEITK, reason="SimpleITK not installed")
class TestDicomConverter:
    """Tests for DicomConverter class (requires SimpleITK)"""

    def test_init_default(self):
        """Test default initialization"""
        converter = DicomConverter()
        assert converter.prefer_thorax is True
        assert converter.min_slices == 50
        assert converter.force_overwrite is False
        assert converter.verbose is True

    def test_init_custom(self):
        """Test custom initialization"""
        converter = DicomConverter(
            prefer_thorax=False,
            min_slices=100,
            force_overwrite=True,
            verbose=False,
        )
        assert converter.prefer_thorax is False
        assert converter.min_slices == 100
        assert converter.force_overwrite is True
        assert converter.verbose is False

    def test_find_existing(self):
        """Test finding existing NIfTI files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            output_dir = Path(tmpdir)
            (output_dir / "p001.nii.gz").touch()

            converter = DicomConverter()

            # Should find existing file
            found = converter.find_existing("p001", output_dir)
            assert found is not None
            assert found.name == "p001.nii.gz"

            # Should not find non-existent
            not_found = converter.find_existing("p999", output_dir)
            assert not_found is None

    def test_convert_patient_no_dicom(self):
        """Test conversion with no DICOM files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            dicom_dir = Path(tmpdir) / "dicom"
            dicom_dir.mkdir()
            output_dir = Path(tmpdir) / "output"

            converter = DicomConverter(verbose=False)
            result = converter.convert_patient(
                patient_id="p001",
                dicom_path=dicom_dir,
                output_dir=output_dir,
            )

            assert result.success is False
            assert "No DICOM" in result.error_message or "not found" in result.error_message.lower()


class TestPreprocessingResult:
    """Tests for PreprocessingResult dataclass"""

    def test_success_result(self):
        """Test successful preprocessing result"""
        result = PreprocessingResult(
            patient_id="p001",
            stage="nifti",
            success=True,
            output_path=Path("/output/p001.nii.gz"),
            was_cached=False,
            processing_time=30.5,
        )
        assert result.success is True
        assert result.stage == "nifti"

    def test_failed_result(self):
        """Test failed preprocessing result"""
        result = PreprocessingResult(
            patient_id="p001",
            stage="totalsegmentator",
            success=False,
            error_message="TotalSegmentator failed",
            processing_time=5.0,
        )
        assert result.success is False
        assert result.error_message == "TotalSegmentator failed"


class TestPreprocessingConfig:
    """Tests for PreprocessingConfig dataclass"""

    def test_default_values(self):
        """Test default configuration"""
        config = PreprocessingConfig()
        assert config.totalsegmentator_task == "total"
        assert config.totalsegmentator_device == "gpu"
        assert config.totalsegmentator_fast is True
        assert config.force_reprocess is False
        assert config.verbose is True
        assert config.gpu_stabilization_time == 2.0

    def test_custom_values(self):
        """Test custom configuration"""
        config = PreprocessingConfig(
            nifti_root=Path("/data/nifti"),
            segmentation_root=Path("/data/seg"),
            totalsegmentator_device="cpu",
            totalsegmentator_fast=False,
            force_reprocess=True,
        )
        assert config.nifti_root == Path("/data/nifti")
        assert config.totalsegmentator_device == "cpu"
        assert config.force_reprocess is True


@pytest.mark.skipif(not HAS_SIMPLEITK, reason="SimpleITK not installed")
class TestSharedPreprocessingPipeline:
    """Tests for SharedPreprocessingPipeline (requires SimpleITK)"""

    def test_init_with_paths(self):
        """Test initialization with paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )
            assert pipeline.config.nifti_root == Path(tmpdir) / "nifti"
            assert pipeline.config.segmentation_root == Path(tmpdir) / "seg"

    def test_init_with_config(self):
        """Test initialization with config"""
        config = PreprocessingConfig(
            nifti_root=Path("/data/nifti"),
            segmentation_root=Path("/data/seg"),
            verbose=False,
        )
        pipeline = SharedPreprocessingPipeline(config=config)
        assert pipeline.config.verbose is False

    def test_standard_masks(self):
        """Test standard mask mapping"""
        assert "heart" in SharedPreprocessingPipeline.STANDARD_MASKS
        assert "aorta" in SharedPreprocessingPipeline.STANDARD_MASKS
        assert "vertebrae_T12" in SharedPreprocessingPipeline.STANDARD_MASKS
        assert SharedPreprocessingPipeline.STANDARD_MASKS["heart"] == "heart.nii.gz"

    def test_module_requirements(self):
        """Test module mask requirements"""
        assert "pericardial_fat" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS
        assert "heart" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS["pericardial_fat"]
        assert "perivascular_fat" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS
        assert "aorta" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS["perivascular_fat"]
        assert "vertebra_composition" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS
        assert "vertebrae_T12" in SharedPreprocessingPipeline.MODULE_REQUIREMENTS["vertebra_composition"]

    def test_get_nifti_path(self):
        """Test getting NIfTI path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test directory and file
            nifti_dir = Path(tmpdir) / "nifti" / "test_dataset"
            nifti_dir.mkdir(parents=True)
            (nifti_dir / "p001.nii.gz").touch()

            # Should find existing file
            path = pipeline.get_nifti_path("p001", "test_dataset")
            assert path is not None
            assert path.name == "p001.nii.gz"

            # Should not find non-existent
            path = pipeline.get_nifti_path("p999", "test_dataset")
            assert path is None

    def test_get_mask(self):
        """Test getting mask path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test directory and mask file
            seg_dir = Path(tmpdir) / "seg" / "organs_test_dataset" / "p001"
            seg_dir.mkdir(parents=True)
            (seg_dir / "heart.nii.gz").touch()

            # Should find existing mask
            mask = pipeline.get_mask("p001", "test_dataset", "heart")
            assert mask is not None
            assert mask.name == "heart.nii.gz"

            # Should not find non-existent mask
            mask = pipeline.get_mask("p001", "test_dataset", "aorta")
            assert mask is None

    def test_get_masks(self):
        """Test getting multiple masks"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test directory and mask files
            seg_dir = Path(tmpdir) / "seg" / "organs_test_dataset" / "p001"
            seg_dir.mkdir(parents=True)
            (seg_dir / "heart.nii.gz").touch()
            (seg_dir / "aorta.nii.gz").touch()

            masks = pipeline.get_masks("p001", "test_dataset", ["heart", "aorta", "liver"])
            assert masks["heart"] is not None
            assert masks["aorta"] is not None
            assert masks["liver"] is None

    def test_validate_masks(self):
        """Test mask validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test directory and mask files
            seg_dir = Path(tmpdir) / "seg" / "organs_test_dataset" / "p001"
            seg_dir.mkdir(parents=True)
            (seg_dir / "heart.nii.gz").touch()

            # Should pass with only heart
            valid, missing = pipeline.validate_masks("p001", "test_dataset", ["heart"])
            assert valid is True
            assert len(missing) == 0

            # Should fail with missing masks
            valid, missing = pipeline.validate_masks("p001", "test_dataset", ["heart", "aorta"])
            assert valid is False
            assert "aorta" in missing

    def test_get_module_masks(self):
        """Test getting masks for specific module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            masks = pipeline.get_module_masks("p001", "test_dataset", "pericardial_fat")
            assert "heart" in masks

    def test_validate_for_module(self):
        """Test validation for specific module"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test directory and heart mask
            seg_dir = Path(tmpdir) / "seg" / "organs_test_dataset" / "p001"
            seg_dir.mkdir(parents=True)
            (seg_dir / "heart.nii.gz").touch()

            # Pericardial fat should pass (only needs heart)
            valid, missing = pipeline.validate_for_module("p001", "test_dataset", "pericardial_fat")
            assert valid is True

            # Perivascular fat should fail (needs aorta)
            valid, missing = pipeline.validate_for_module("p001", "test_dataset", "perivascular_fat")
            assert valid is False
            assert "aorta" in missing

    def test_get_preprocessing_status(self):
        """Test getting preprocessing status"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = SharedPreprocessingPipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
            )

            # Create test files
            nifti_dir = Path(tmpdir) / "nifti" / "test_dataset"
            nifti_dir.mkdir(parents=True)
            (nifti_dir / "p001.nii.gz").touch()

            seg_dir = Path(tmpdir) / "seg" / "organs_test_dataset" / "p001"
            seg_dir.mkdir(parents=True)
            (seg_dir / "heart.nii.gz").touch()

            status = pipeline.get_preprocessing_status("p001", "test_dataset")
            assert status["nifti"]["exists"] is True
            assert status["totalsegmentator"]["exists"] is True
            assert status["masks"]["heart"] is True
            assert status["masks"]["aorta"] is False


class TestCreatePipeline:
    """Tests for create_pipeline convenience function"""

    @pytest.mark.skipif(not HAS_SIMPLEITK, reason="SimpleITK not installed")
    def test_create_pipeline(self):
        """Test create_pipeline function"""
        with tempfile.TemporaryDirectory() as tmpdir:
            pipeline = create_pipeline(
                nifti_root=Path(tmpdir) / "nifti",
                segmentation_root=Path(tmpdir) / "seg",
                verbose=False,
            )
            assert pipeline.config.nifti_root == Path(tmpdir) / "nifti"
            assert pipeline.config.verbose is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
