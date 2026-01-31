"""
Shared Hardware Detection Module
Hardware detection for Windows/Linux/Colab/WSL
"""

from cardiac_shared.hardware.detector import (
    # Data classes
    GPUInfo,
    CPUInfo,
    RAMInfo,
    EnvironmentInfo,
    HardwareInfo,

    # Detection functions
    detect_gpu,
    detect_cpu,
    detect_ram,
    detect_environment,
    detect_hardware,

    # Utility functions
    print_hardware_summary,
    get_optimal_config,
)

from cardiac_shared.hardware.cpu_optimizer import (
    # CPU Optimization
    CPUTier,
    CPUOptimizationConfig,
    CPUOptimizer,
    get_cpu_optimizer,
    get_optimal_cpu_config,
    apply_cpu_optimizations,
)

from cardiac_shared.hardware.optimizer import (
    # Performance optimization
    PerformanceOptimizer,
    DeviceRecommendation,
    TimeEstimate,
)

from cardiac_shared.hardware.profiles import (
    # GPU Profiles
    GPUProfile,
    GPU_PROFILES,
    estimate_batch_time,
    match_gpu_profile,
    get_all_profiles,
)

from cardiac_shared.hardware.gpu_utils import (
    # GPU utilities (v0.5.1)
    get_recommended_gpu_stabilization_time,
    get_gpu_performance_tier,
    GPU_STABILIZATION_TIMES,
)

# Backward compatibility alias
HardwareDetector = detect_hardware
HardwareProfile = HardwareInfo

__all__ = [
    # Data classes
    'GPUInfo',
    'CPUInfo',
    'RAMInfo',
    'EnvironmentInfo',
    'HardwareInfo',

    # Detection functions
    'detect_gpu',
    'detect_cpu',
    'detect_ram',
    'detect_environment',
    'detect_hardware',

    # Utility functions
    'print_hardware_summary',
    'get_optimal_config',

    # CPU Optimization
    'CPUTier',
    'CPUOptimizationConfig',
    'CPUOptimizer',
    'get_cpu_optimizer',
    'get_optimal_cpu_config',
    'apply_cpu_optimizations',

    # Performance Optimization
    'PerformanceOptimizer',
    'DeviceRecommendation',
    'TimeEstimate',

    # GPU Profiles
    'GPUProfile',
    'GPU_PROFILES',
    'estimate_batch_time',
    'match_gpu_profile',
    'get_all_profiles',

    # Backward compatibility aliases
    'HardwareDetector',
    'HardwareProfile',

    # GPU utilities (v0.5.1)
    'get_recommended_gpu_stabilization_time',
    'get_gpu_performance_tier',
    'GPU_STABILIZATION_TIMES',
]
