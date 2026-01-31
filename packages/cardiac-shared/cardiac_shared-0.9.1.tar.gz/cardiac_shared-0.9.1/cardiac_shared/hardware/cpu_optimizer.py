"""
CPU Optimizer Module

Provides CPU-specific optimizations for hospital deployment scenarios
where GPU may not be available. Critical component for medical institutions
running AI inference on CPU-only machines.

Key Features:
- CPU performance tier detection (Minimal -> Professional)
- DataLoader optimization (num_workers, batch_size, prefetch)
- Inference optimization (thread control, memory management)
- Hospital CPU presets (typical 8-core, 16GB configurations)
"""

import os
import psutil
import platform
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class CPUTier(Enum):
    """CPU performance tiers based on core count and capabilities"""
    MINIMAL = "Minimal"          # 2-4 cores, basic hospital workstation
    STANDARD = "Standard"        # 4-8 cores, typical hospital workstation
    PERFORMANCE = "Performance"  # 8-16 cores, high-end hospital workstation
    PROFESSIONAL = "Professional"  # 16-32 cores, workstation/server
    ENTERPRISE = "Enterprise"    # 32+ cores, server-grade hardware


@dataclass
class CPUOptimizationConfig:
    """CPU optimization configuration for inference"""

    # Performance tier
    tier: CPUTier

    # DataLoader settings
    num_workers: int
    batch_size: int
    prefetch_factor: int
    pin_memory: bool

    # Inference settings
    torch_threads: int
    enable_mkldnn: bool

    # Memory management
    max_memory_usage_gb: float
    enable_memory_efficient_mode: bool

    # Expected performance
    expected_time_per_patient_sec: Tuple[int, int]  # (min, max)

    # Description
    description: str


class CPUOptimizer:
    """
    CPU performance optimizer for medical imaging inference

    Optimizes PyTorch inference for CPU-only environments commonly found in hospitals.
    Provides automatic configuration based on available hardware resources.
    """

    # Performance tier thresholds
    TIER_THRESHOLDS = {
        CPUTier.MINIMAL: (2, 4),      # 2-4 cores
        CPUTier.STANDARD: (4, 8),     # 4-8 cores
        CPUTier.PERFORMANCE: (8, 16),  # 8-16 cores
        CPUTier.PROFESSIONAL: (16, 32),  # 16-32 cores
        CPUTier.ENTERPRISE: (32, float('inf'))  # 32+ cores
    }

    def __init__(self):
        """Initialize CPU optimizer"""
        self.cpu_count = psutil.cpu_count(logical=False)  # Physical cores
        self.cpu_count_logical = psutil.cpu_count(logical=True)
        self.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        self.cpu_freq = self._get_cpu_frequency()
        self.platform = platform.system()

    def _get_cpu_frequency(self) -> float:
        """Get CPU frequency in GHz"""
        try:
            freq = psutil.cpu_freq()
            if freq:
                return freq.max / 1000.0  # Convert MHz to GHz
        except:
            pass
        return 0.0

    def detect_cpu_tier(self) -> CPUTier:
        """
        Detect CPU performance tier based on core count

        Returns:
            CPUTier enum value
        """
        for tier, (min_cores, max_cores) in self.TIER_THRESHOLDS.items():
            if min_cores <= self.cpu_count < max_cores:
                return tier

        # Fallback to minimal if detection fails
        return CPUTier.MINIMAL

    def get_optimal_config(self,
                          tier: Optional[CPUTier] = None,
                          available_memory_gb: Optional[float] = None) -> CPUOptimizationConfig:
        """
        Get optimal CPU configuration for inference

        Args:
            tier: CPU performance tier (auto-detected if None)
            available_memory_gb: Available memory in GB (auto-detected if None)

        Returns:
            CPUOptimizationConfig with optimized settings
        """
        if tier is None:
            tier = self.detect_cpu_tier()

        if available_memory_gb is None:
            available_memory_gb = self.total_memory_gb

        # Get base configuration for tier
        config = self._get_tier_config(tier, available_memory_gb)

        # Apply memory constraints
        config = self._apply_memory_constraints(config, available_memory_gb)

        return config

    def _get_tier_config(self, tier: CPUTier, memory_gb: float) -> CPUOptimizationConfig:
        """Get base configuration for a specific CPU tier"""
        configs = {
            CPUTier.MINIMAL: CPUOptimizationConfig(
                tier=tier,
                num_workers=0,
                batch_size=1,
                prefetch_factor=2,
                pin_memory=False,
                torch_threads=2,
                enable_mkldnn=True,
                max_memory_usage_gb=min(4.0, memory_gb * 0.6),
                enable_memory_efficient_mode=True,
                expected_time_per_patient_sec=(120, 180),
                description="Basic hospital workstation (2-4 cores) - Conservative settings"
            ),

            CPUTier.STANDARD: CPUOptimizationConfig(
                tier=tier,
                num_workers=2,
                batch_size=2,
                prefetch_factor=2,
                pin_memory=False,
                torch_threads=4,
                enable_mkldnn=True,
                max_memory_usage_gb=min(8.0, memory_gb * 0.7),
                enable_memory_efficient_mode=True,
                expected_time_per_patient_sec=(40, 60),
                description="Typical hospital workstation (4-8 cores) - Balanced performance"
            ),

            CPUTier.PERFORMANCE: CPUOptimizationConfig(
                tier=tier,
                num_workers=4,
                batch_size=4,
                prefetch_factor=2,
                pin_memory=False,
                torch_threads=8,
                enable_mkldnn=True,
                max_memory_usage_gb=min(16.0, memory_gb * 0.75),
                enable_memory_efficient_mode=False,
                expected_time_per_patient_sec=(20, 30),
                description="High-end hospital workstation (8-16 cores) - Optimized for speed"
            ),

            CPUTier.PROFESSIONAL: CPUOptimizationConfig(
                tier=tier,
                num_workers=8,
                batch_size=4,
                prefetch_factor=3,
                pin_memory=False,
                torch_threads=16,
                enable_mkldnn=True,
                max_memory_usage_gb=min(32.0, memory_gb * 0.8),
                enable_memory_efficient_mode=False,
                expected_time_per_patient_sec=(15, 25),
                description="Workstation/Server (16-32 cores) - Maximum CPU throughput"
            ),

            CPUTier.ENTERPRISE: CPUOptimizationConfig(
                tier=tier,
                num_workers=16,
                batch_size=8,
                prefetch_factor=4,
                pin_memory=False,
                torch_threads=32,
                enable_mkldnn=True,
                max_memory_usage_gb=min(64.0, memory_gb * 0.8),
                enable_memory_efficient_mode=False,
                expected_time_per_patient_sec=(10, 15),
                description="Server-grade hardware (32+ cores) - Maximum throughput"
            ),
        }

        return configs.get(tier, configs[CPUTier.MINIMAL])

    def _apply_memory_constraints(self,
                                  config: CPUOptimizationConfig,
                                  available_memory_gb: float) -> CPUOptimizationConfig:
        """Apply memory constraints to prevent OOM"""
        if available_memory_gb < 8:
            config.batch_size = min(config.batch_size, 1)
            config.num_workers = min(config.num_workers, 1)
            config.enable_memory_efficient_mode = True
        elif available_memory_gb < 16:
            config.batch_size = min(config.batch_size, 2)
            config.num_workers = min(config.num_workers, 2)

        config.max_memory_usage_gb = min(
            config.max_memory_usage_gb,
            available_memory_gb * 0.7
        )

        return config

    def apply_torch_optimizations(self, config: CPUOptimizationConfig):
        """
        Apply PyTorch CPU optimizations

        Args:
            config: CPU optimization configuration
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError("PyTorch not available, cannot apply optimizations")

        # Set number of threads for PyTorch operations
        torch.set_num_threads(config.torch_threads)

        # Enable MKL-DNN optimizations if available
        if config.enable_mkldnn and hasattr(torch.backends, 'mkldnn'):
            if torch.backends.mkldnn.is_available():
                torch.backends.mkldnn.enabled = True

        # Disable gradient computation (inference only)
        torch.set_grad_enabled(False)

    def get_dataloader_kwargs(self, config: CPUOptimizationConfig) -> Dict:
        """
        Get PyTorch DataLoader keyword arguments

        Args:
            config: CPU optimization configuration

        Returns:
            Dictionary of DataLoader kwargs
        """
        kwargs = {
            'num_workers': config.num_workers,
            'batch_size': config.batch_size,
            'pin_memory': config.pin_memory,
        }

        if config.num_workers > 0:
            kwargs['prefetch_factor'] = config.prefetch_factor

        return kwargs

    def get_system_info(self) -> Dict:
        """Get system information for diagnostics"""
        return {
            'platform': self.platform,
            'cpu_count_physical': self.cpu_count,
            'cpu_count_logical': self.cpu_count_logical,
            'cpu_freq_ghz': self.cpu_freq,
            'total_memory_gb': self.total_memory_gb,
            'available_memory_gb': psutil.virtual_memory().available / (1024**3),
            'cpu_tier': self.detect_cpu_tier().value,
        }

    def estimate_processing_time(self,
                                 num_patients: int,
                                 config: Optional[CPUOptimizationConfig] = None) -> Dict:
        """
        Estimate total processing time for a dataset

        Args:
            num_patients: Number of patients to process
            config: CPU optimization configuration (auto-detected if None)

        Returns:
            Dictionary with time estimates
        """
        if config is None:
            config = self.get_optimal_config()

        min_time_sec = num_patients * config.expected_time_per_patient_sec[0]
        max_time_sec = num_patients * config.expected_time_per_patient_sec[1]
        avg_time_sec = (min_time_sec + max_time_sec) / 2

        return {
            'num_patients': num_patients,
            'min_time_sec': min_time_sec,
            'max_time_sec': max_time_sec,
            'avg_time_sec': avg_time_sec,
            'min_time_str': self._format_time(min_time_sec),
            'max_time_str': self._format_time(max_time_sec),
            'avg_time_str': self._format_time(avg_time_sec),
        }

    def _format_time(self, seconds: float) -> str:
        """Format seconds into human-readable string"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds/60)}m {int(seconds%60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"

    def print_optimization_report(self, config: Optional[CPUOptimizationConfig] = None):
        """Print optimization report to console"""
        if config is None:
            config = self.get_optimal_config()

        system_info = self.get_system_info()

        print("=" * 70)
        print("CPU OPTIMIZATION REPORT")
        print("=" * 70)
        print()
        print("System Information:")
        print(f"  Platform: {system_info['platform']}")
        print(f"  CPU Cores: {system_info['cpu_count_physical']} physical, " +
              f"{system_info['cpu_count_logical']} logical")
        if system_info['cpu_freq_ghz'] > 0:
            print(f"  CPU Frequency: {system_info['cpu_freq_ghz']:.2f} GHz")
        print(f"  Total Memory: {system_info['total_memory_gb']:.1f} GB")
        print(f"  Available Memory: {system_info['available_memory_gb']:.1f} GB")
        print()
        print("Performance Tier:")
        print(f"  Tier: {config.tier.value}")
        print(f"  Description: {config.description}")
        print()
        print("Optimized Settings:")
        print(f"  DataLoader Workers: {config.num_workers}")
        print(f"  Batch Size: {config.batch_size}")
        print(f"  PyTorch Threads: {config.torch_threads}")
        print(f"  Memory Limit: {config.max_memory_usage_gb:.1f} GB")
        print(f"  MKL-DNN: {'Enabled' if config.enable_mkldnn else 'Disabled'}")
        print()
        print("Expected Performance:")
        min_t, max_t = config.expected_time_per_patient_sec
        print(f"  Time per Patient: {min_t}-{max_t} seconds")

        for num_patients in [10, 50, 100, 500]:
            est = self.estimate_processing_time(num_patients, config)
            print(f"  {num_patients} patients: {est['min_time_str']} - {est['max_time_str']}")

        print("=" * 70)


# Convenience functions

def get_cpu_optimizer() -> CPUOptimizer:
    """Get CPU optimizer instance"""
    return CPUOptimizer()


def get_optimal_cpu_config(tier: Optional[CPUTier] = None) -> CPUOptimizationConfig:
    """
    Get optimal CPU configuration (convenience function)

    Args:
        tier: CPU performance tier (auto-detected if None)

    Returns:
        CPUOptimizationConfig
    """
    optimizer = CPUOptimizer()
    return optimizer.get_optimal_config(tier=tier)


def apply_cpu_optimizations(config: Optional[CPUOptimizationConfig] = None):
    """
    Apply CPU optimizations to PyTorch (convenience function)

    Args:
        config: CPU optimization configuration (auto-detected if None)
    """
    optimizer = CPUOptimizer()
    if config is None:
        config = optimizer.get_optimal_config()
    optimizer.apply_torch_optimizations(config)


if __name__ == "__main__":
    print("CPU Optimizer - Standalone Test")
    print()

    optimizer = CPUOptimizer()
    optimizer.print_optimization_report()

    print("\nTesting all CPU tiers:")
    print("=" * 70)
    for tier in CPUTier:
        config = optimizer.get_optimal_config(tier=tier)
        print(f"\n{tier.value}:")
        print(f"  Workers: {config.num_workers}, Batch: {config.batch_size}, " +
              f"Threads: {config.torch_threads}")
        min_t, max_t = config.expected_time_per_patient_sec
        print(f"  Expected: {min_t}-{max_t}s per patient")
