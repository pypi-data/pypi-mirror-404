"""Test that all modules can be imported correctly."""

import pytest


def test_import_cardiac_shared():
    """Test main package import."""
    import cardiac_shared
    assert cardiac_shared.__version__ == "0.9.1"


def test_import_io_module():
    """Test IO module imports."""
    from cardiac_shared.io import (
        read_dicom_series,
        get_dicom_metadata,
        extract_slice_thickness,
        is_thorax_series,
        load_nifti,
        save_nifti,
        get_nifti_info,
        extract_zip,
        find_dicom_root,
        get_zip_info,
    )
    # All imports should succeed
    assert callable(read_dicom_series)
    assert callable(load_nifti)
    assert callable(extract_zip)


def test_import_hardware_module():
    """Test hardware module imports."""
    from cardiac_shared.hardware import (
        detect_hardware,
        detect_gpu,
        detect_cpu,
        detect_ram,
        HardwareInfo,
        GPUInfo,
        CPUInfo,
        RAMInfo,
        CPUOptimizer,
        CPUTier,
    )
    assert callable(detect_hardware)
    assert callable(detect_gpu)


def test_import_environment_module():
    """Test environment module imports."""
    from cardiac_shared.environment import (
        detect_runtime,
        detect_colab,
        detect_wsl,
        RuntimeEnvironment,
    )
    assert callable(detect_runtime)
    assert callable(detect_colab)
    assert callable(detect_wsl)


def test_convenience_imports():
    """Test that main convenience imports work."""
    from cardiac_shared import (
        # IO
        read_dicom_series,
        load_nifti,
        extract_zip,
        # Hardware
        detect_hardware,
        CPUOptimizer,
        # Environment
        detect_runtime,
    )
    assert callable(read_dicom_series)
    assert callable(detect_hardware)
    assert callable(detect_runtime)
