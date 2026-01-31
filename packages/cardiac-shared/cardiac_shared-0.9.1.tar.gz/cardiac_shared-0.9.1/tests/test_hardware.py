"""Tests for hardware detection module."""

import pytest


def test_detect_hardware():
    """Test complete hardware detection."""
    from cardiac_shared.hardware import detect_hardware, HardwareInfo

    hw = detect_hardware()

    assert isinstance(hw, HardwareInfo)
    assert hasattr(hw, 'gpu')
    assert hasattr(hw, 'cpu')
    assert hasattr(hw, 'ram')
    assert hasattr(hw, 'environment')


def test_cpu_info():
    """Test CPU detection."""
    from cardiac_shared.hardware import detect_cpu, CPUInfo

    cpu = detect_cpu()

    assert isinstance(cpu, CPUInfo)
    assert cpu.physical_cores >= 1
    assert cpu.logical_cores >= 1
    assert isinstance(cpu.cpu_model, str)


def test_ram_info():
    """Test RAM detection."""
    from cardiac_shared.hardware import detect_ram, RAMInfo

    ram = detect_ram()

    assert isinstance(ram, RAMInfo)
    assert ram.total_gb > 0
    assert ram.available_gb >= 0
    assert 0 <= ram.percent_used <= 100


def test_gpu_info():
    """Test GPU detection (may not have GPU)."""
    from cardiac_shared.hardware import detect_gpu, GPUInfo

    gpu = detect_gpu()

    assert isinstance(gpu, GPUInfo)
    assert isinstance(gpu.available, bool)
    assert isinstance(gpu.device_name, str)


def test_performance_tier():
    """Test performance tier calculation."""
    from cardiac_shared.hardware import detect_hardware

    hw = detect_hardware()

    tier = hw.performance_tier
    assert tier in ["Minimal", "Standard", "Performance", "Professional", "Enterprise"]


def test_cpu_optimizer():
    """Test CPU optimizer."""
    from cardiac_shared.hardware import CPUOptimizer, CPUTier

    optimizer = CPUOptimizer()
    config = optimizer.get_optimal_config()

    assert config.tier in CPUTier
    assert config.num_workers >= 0
    assert config.batch_size >= 1
    assert config.torch_threads >= 1


def test_optimal_config():
    """Test optimal config generation."""
    from cardiac_shared.hardware import detect_hardware, get_optimal_config

    hw = detect_hardware()
    config = get_optimal_config(hw)

    assert 'device' in config
    assert 'num_workers' in config
    assert 'batch_size' in config
    assert config['device'] in ['cpu', 'cuda']
