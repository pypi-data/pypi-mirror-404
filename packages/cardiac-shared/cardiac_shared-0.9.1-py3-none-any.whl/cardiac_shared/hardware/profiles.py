"""
GPU/CPU Performance Profiles - Empirical Data Repository

This module contains empirical performance profiles for various GPU models and CPU-only mode.
All timing data is based on real-world measurements from TotalSegmentator processing.

Data Sources:
- RTX 2060 (6GB): Measured from CT batch processing (21 cases)
- CPU-only: Measured from CT batch processing
- Other GPUs: Estimated based on VRAM scaling and compute capability

Usage:
    >>> from cardiac_shared.hardware.profiles import GPU_PROFILES, match_gpu_profile
    >>> profile = match_gpu_profile(vram_gb=6.0)
    >>> print(profile.name)  # "RTX 2060"
    >>> print(profile.totalseg_measured_time_per_case)  # 96.0 seconds

Version: 1.0.0
Created: 2025-11-27
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class GPUProfile:
    """
    GPU performance profile with empirical measurements

    Attributes:
        name: GPU model name (e.g., "RTX 2060", "CPU Only")
        vram_gb: GPU VRAM in GB (0.0 for CPU)

        # TotalSegmentator Optimization Parameters
        totalseg_fast_mode: Use fast mode (True) or accuracy mode (False)
        totalseg_timeout_sec: Recommended timeout in seconds
        totalseg_parallel_cases: Max parallel cases to process
        totalseg_measured_time_per_case: Average processing time per case (seconds)

        # Resource Requirements
        min_vram_gb: Minimum VRAM required for this task (default 5.5GB)
        recommended_ram_gb: Recommended system RAM (default 16GB)
    """
    name: str
    vram_gb: float

    # TotalSegmentator optimization parameters
    totalseg_fast_mode: bool
    totalseg_timeout_sec: int
    totalseg_parallel_cases: int
    totalseg_measured_time_per_case: float  # seconds

    # Resource requirements
    min_vram_gb: float = 5.5  # TotalSegmentator minimum VRAM
    recommended_ram_gb: float = 16.0  # Recommended system RAM

    def __str__(self) -> str:
        return f"{self.name} ({self.vram_gb}GB VRAM)" if self.vram_gb > 0 else self.name

    def __repr__(self) -> str:
        return (f"GPUProfile(name='{self.name}', vram_gb={self.vram_gb}, "
                f"fast_mode={self.totalseg_fast_mode}, "
                f"time_per_case={self.totalseg_measured_time_per_case:.1f}s)")


# Empirical GPU performance profiles
GPU_PROFILES: Dict[str, GPUProfile] = {
    'rtx_2060': GPUProfile(
        name='RTX 2060',
        vram_gb=6.0,
        totalseg_fast_mode=True,  # 6GB VRAM requires fast mode
        totalseg_timeout_sec=1800,  # 30 minutes
        totalseg_parallel_cases=1,  # Single case only (VRAM limited)
        totalseg_measured_time_per_case=96.0,  # 1.6 min/case (measured)
        min_vram_gb=5.5,
        recommended_ram_gb=16.0,
    ),

    'rtx_3060': GPUProfile(
        name='RTX 3060',
        vram_gb=12.0,
        totalseg_fast_mode=True,  # Balance speed and accuracy
        totalseg_timeout_sec=1500,  # 25 minutes
        totalseg_parallel_cases=2,  # 2 cases in parallel (5GB/case in fast mode)
        totalseg_measured_time_per_case=78.0,  # 1.3 min/case (estimated, based on VRAM/compute ratio)
        min_vram_gb=5.5,
        recommended_ram_gb=24.0,  # More RAM for parallel processing
    ),

    'rtx_3070': GPUProfile(
        name='RTX 3070',
        vram_gb=8.0,
        totalseg_fast_mode=True,
        totalseg_timeout_sec=1500,  # 25 minutes
        totalseg_parallel_cases=1,  # Single case (VRAM borderline for parallel)
        totalseg_measured_time_per_case=72.0,  # 1.2 min/case (estimated)
        min_vram_gb=5.5,
        recommended_ram_gb=16.0,
    ),

    'rtx_3090': GPUProfile(
        name='RTX 3090',
        vram_gb=24.0,
        totalseg_fast_mode=False,  # Can afford accuracy mode
        totalseg_timeout_sec=1200,  # 20 minutes (faster GPU)
        totalseg_parallel_cases=4,  # 4 cases in parallel (~6GB/case)
        totalseg_measured_time_per_case=60.0,  # 1.0 min/case (estimated)
        min_vram_gb=5.5,
        recommended_ram_gb=32.0,  # More RAM for parallel processing
    ),

    'rtx_4060': GPUProfile(
        name='RTX 4060',
        vram_gb=8.0,
        totalseg_fast_mode=True,
        totalseg_timeout_sec=1400,  # 23 minutes
        totalseg_parallel_cases=1,
        totalseg_measured_time_per_case=70.0,  # 1.17 min/case (estimated, Ada architecture)
        min_vram_gb=5.5,
        recommended_ram_gb=16.0,
    ),

    'rtx_4090': GPUProfile(
        name='RTX 4090',
        vram_gb=24.0,
        totalseg_fast_mode=False,  # Accuracy mode (fastest GPU)
        totalseg_timeout_sec=1000,  # 16.7 minutes
        totalseg_parallel_cases=4,
        totalseg_measured_time_per_case=45.0,  # 0.75 min/case (estimated, Ada architecture)
        min_vram_gb=5.5,
        recommended_ram_gb=32.0,
    ),

    'cpu_only': GPUProfile(
        name='CPU Only',
        vram_gb=0.0,
        totalseg_fast_mode=True,  # Fast mode still helps on CPU
        totalseg_timeout_sec=5400,  # 90 minutes (3× GPU time)
        totalseg_parallel_cases=1,  # Single case (CPU bottleneck)
        totalseg_measured_time_per_case=288.0,  # 4.8 min/case (~3x RTX 2060, measured)
        min_vram_gb=0.0,
        recommended_ram_gb=16.0,
    ),
}


def match_gpu_profile(vram_gb: float, gpu_name: Optional[str] = None) -> GPUProfile:
    """
    Match detected GPU to closest performance profile

    Args:
        vram_gb: Detected GPU VRAM in GB (0.0 for CPU-only)
        gpu_name: Optional GPU model name for exact matching

    Returns:
        GPUProfile: Closest matching profile

    Examples:
        >>> # Exact match by name
        >>> profile = match_gpu_profile(6.0, "NVIDIA GeForce RTX 2060")
        >>> profile.name
        'RTX 2060'

        >>> # Match by VRAM size
        >>> profile = match_gpu_profile(12.0)
        >>> profile.name
        'RTX 3060'

        >>> # CPU fallback
        >>> profile = match_gpu_profile(0.0)
        >>> profile.name
        'CPU Only'
    """
    # CPU fallback
    if vram_gb == 0.0:
        return GPU_PROFILES['cpu_only']

    # Exact match by name (if provided)
    if gpu_name:
        gpu_name_lower = gpu_name.lower()
        for key, profile in GPU_PROFILES.items():
            if key != 'cpu_only' and key.replace('_', ' ') in gpu_name_lower:
                return profile

    # Match by VRAM size (closest match)
    if vram_gb >= 20:
        # High-end GPU (RTX 3090, RTX 4090, A100, etc.)
        return GPU_PROFILES.get('rtx_4090', GPU_PROFILES['rtx_3090'])
    elif vram_gb >= 10:
        # Mid-range GPU (RTX 3060, RTX 3070, RTX 4060, etc.)
        if vram_gb >= 11:
            return GPU_PROFILES['rtx_3060']  # 12GB
        else:
            return GPU_PROFILES['rtx_3070']  # 8GB
    elif vram_gb >= 6:
        # Entry-level GPU (RTX 2060, GTX 1660, etc.)
        if vram_gb >= 7:
            return GPU_PROFILES.get('rtx_4060', GPU_PROFILES['rtx_3070'])  # 8GB
        else:
            return GPU_PROFILES['rtx_2060']  # 6GB
    elif vram_gb >= 4:
        # Very low VRAM GPU (use RTX 2060 settings but warn)
        return GPU_PROFILES['rtx_2060']
    else:
        # Insufficient VRAM - fallback to CPU
        return GPU_PROFILES['cpu_only']


def get_all_profiles() -> Dict[str, GPUProfile]:
    """
    Get all available GPU profiles

    Returns:
        Dictionary of all GPU profiles
    """
    return GPU_PROFILES.copy()


def estimate_batch_time(
    num_cases: int,
    profile: GPUProfile,
    include_overhead: bool = True
) -> dict:
    """
    Estimate total batch processing time

    Args:
        num_cases: Number of cases to process
        profile: GPU profile to use for estimation
        include_overhead: Include 5% overhead for I/O, checkpointing, etc.

    Returns:
        Dictionary with time estimates:
        {
            'total_seconds': float,
            'total_minutes': float,
            'total_hours': float,
            'time_per_case_seconds': float,
            'parallel_cases': int,
            'formatted': str,
        }

    Example:
        >>> profile = GPU_PROFILES['rtx_2060']
        >>> estimate = estimate_batch_time(377, profile)
        >>> print(estimate['formatted'])
        '10.1 hours (605 minutes)'
    """
    # Base time calculation
    time_per_case = profile.totalseg_measured_time_per_case
    parallel_cases = profile.totalseg_parallel_cases

    # Calculate total time (considering parallelism)
    base_time_seconds = (num_cases * time_per_case) / parallel_cases

    # Add overhead (I/O, checkpointing, logging)
    if include_overhead:
        total_seconds = base_time_seconds * 1.05  # 5% overhead
    else:
        total_seconds = base_time_seconds

    total_minutes = total_seconds / 60
    total_hours = total_seconds / 3600

    # Format human-readable string
    if total_hours >= 1:
        formatted = f"{total_hours:.1f} hours ({total_minutes:.0f} minutes)"
    elif total_minutes >= 1:
        formatted = f"{total_minutes:.1f} minutes"
    else:
        formatted = f"{total_seconds:.0f} seconds"

    return {
        'total_seconds': total_seconds,
        'total_minutes': total_minutes,
        'total_hours': total_hours,
        'time_per_case_seconds': time_per_case,
        'parallel_cases': parallel_cases,
        'formatted': formatted,
    }


# Version information
__version__ = '1.0.0'
