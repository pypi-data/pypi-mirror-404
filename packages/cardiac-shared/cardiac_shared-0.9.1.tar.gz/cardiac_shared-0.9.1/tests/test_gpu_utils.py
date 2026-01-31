"""Tests for GPU utilities module (v0.5.1)."""

import pytest


class TestGpuStabilizationTime:
    """Tests for get_recommended_gpu_stabilization_time."""

    def test_import(self):
        """Test imports."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time
        assert callable(get_recommended_gpu_stabilization_time)

    def test_rtx_4090(self):
        """Test RTX 4090 returns fast time."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce RTX 4090")
        assert time == 1.0

    def test_rtx_4060(self):
        """Test RTX 4060 returns fast time."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce RTX 4060")
        assert time == 1.5

    def test_rtx_3080(self):
        """Test RTX 3080 returns medium time."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce RTX 3080")
        assert time == 2.0

    def test_rtx_2060(self):
        """Test RTX 2060 returns longer time."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce RTX 2060")
        assert time == 3.5

    def test_gtx_1660_ti(self):
        """Test GTX 1660 Ti returns longer time."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce GTX 1660 Ti")
        assert time == 4.0

    def test_a100(self):
        """Test A100 data center GPU."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA A100-SXM4-80GB")
        assert time == 1.0

    def test_tesla_t4(self):
        """Test Tesla T4."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA Tesla T4")
        assert time == 2.5

    def test_unknown_gpu(self):
        """Test unknown GPU returns default 5.0s."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="Unknown GPU XYZ")
        assert time == 5.0

    def test_none_device_name(self):
        """Test None device name returns default."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name=None)
        assert time == 5.0

    def test_no_args(self):
        """Test no arguments returns default."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time()
        assert time == 5.0

    def test_with_dict_gpu_info(self):
        """Test with dict gpu_info."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        gpu_info = {'device_name': 'NVIDIA GeForce RTX 4060'}
        time = get_recommended_gpu_stabilization_time(gpu_info=gpu_info)
        assert time == 1.5

    def test_with_empty_dict(self):
        """Test with empty dict returns default."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(gpu_info={})
        assert time == 5.0

    def test_return_type(self):
        """Test return type is float."""
        from cardiac_shared.hardware import get_recommended_gpu_stabilization_time

        time = get_recommended_gpu_stabilization_time(device_name="NVIDIA GeForce RTX 4060")
        assert isinstance(time, float)

    def test_range(self):
        """Test all known GPUs return time in valid range."""
        from cardiac_shared.hardware.gpu_utils import GPU_STABILIZATION_TIMES

        for model, time in GPU_STABILIZATION_TIMES.items():
            assert 1.0 <= time <= 5.0, f"GPU {model} has time {time} outside valid range"


class TestGpuPerformanceTier:
    """Tests for get_gpu_performance_tier."""

    def test_import(self):
        """Test imports."""
        from cardiac_shared.hardware import get_gpu_performance_tier
        assert callable(get_gpu_performance_tier)

    def test_high_tier_rtx_4090(self):
        """Test RTX 4090 is high tier."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("NVIDIA GeForce RTX 4090")
        assert tier == 'high'

    def test_medium_tier_rtx_4060(self):
        """Test RTX 4060 is medium tier."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("NVIDIA GeForce RTX 4060")
        assert tier == 'medium'

    def test_low_tier_gtx_1060(self):
        """Test GTX 1060 is low tier."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("NVIDIA GeForce GTX 1060")
        assert tier == 'low'

    def test_unknown_tier(self):
        """Test unknown GPU returns 'unknown'."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("Some Unknown GPU")
        assert tier == 'unknown'

    def test_a100_high_tier(self):
        """Test A100 is high tier."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("NVIDIA A100-SXM4-80GB")
        assert tier == 'high'

    def test_t4_medium_tier(self):
        """Test T4 is medium tier."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        tier = get_gpu_performance_tier("NVIDIA Tesla T4")
        assert tier == 'medium'

    def test_return_values(self):
        """Test all return values are valid."""
        from cardiac_shared.hardware import get_gpu_performance_tier

        test_gpus = [
            "NVIDIA GeForce RTX 4090",
            "NVIDIA GeForce RTX 4060",
            "NVIDIA GeForce GTX 1060",
            "Unknown GPU",
        ]
        valid_tiers = {'high', 'medium', 'low', 'unknown'}

        for gpu in test_gpus:
            tier = get_gpu_performance_tier(gpu)
            assert tier in valid_tiers


class TestGpuStabilizationTimesConstant:
    """Tests for GPU_STABILIZATION_TIMES constant."""

    def test_import(self):
        """Test constant can be imported."""
        from cardiac_shared.hardware import GPU_STABILIZATION_TIMES
        assert isinstance(GPU_STABILIZATION_TIMES, dict)

    def test_has_rtx_40_series(self):
        """Test RTX 40 series is included."""
        from cardiac_shared.hardware import GPU_STABILIZATION_TIMES

        assert '4090' in GPU_STABILIZATION_TIMES
        assert '4080' in GPU_STABILIZATION_TIMES
        assert '4070' in GPU_STABILIZATION_TIMES
        assert '4060' in GPU_STABILIZATION_TIMES

    def test_has_rtx_30_series(self):
        """Test RTX 30 series is included."""
        from cardiac_shared.hardware import GPU_STABILIZATION_TIMES

        assert '3090' in GPU_STABILIZATION_TIMES
        assert '3080' in GPU_STABILIZATION_TIMES
        assert '3070' in GPU_STABILIZATION_TIMES
        assert '3060' in GPU_STABILIZATION_TIMES

    def test_has_data_center_gpus(self):
        """Test data center GPUs are included."""
        from cardiac_shared.hardware import GPU_STABILIZATION_TIMES

        assert 'A100' in GPU_STABILIZATION_TIMES
        assert 'V100' in GPU_STABILIZATION_TIMES
        assert 'T4' in GPU_STABILIZATION_TIMES

    def test_values_are_floats(self):
        """Test all values are floats."""
        from cardiac_shared.hardware import GPU_STABILIZATION_TIMES

        for model, time in GPU_STABILIZATION_TIMES.items():
            assert isinstance(time, (int, float)), f"GPU {model} has non-numeric time"
