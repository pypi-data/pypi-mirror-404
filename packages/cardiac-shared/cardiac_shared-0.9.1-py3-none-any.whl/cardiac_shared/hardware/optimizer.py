"""
Unified Hardware Optimizer

Provides hardware-aware optimization recommendations for medical imaging tasks.
Backward compatible with shared/hardware_manager/optimizer.py API.

Combines optimization logic from:
- shared/hardware_manager/optimizer.py (2025-11-02): PerformanceOptimizer class
- scripts/body_composition/hardware_config.py (2025-11-20): Empirical optimizations

This module uses the unified detector and GPU profiles to provide consistent
optimization recommendations across all modules.

Usage:
    >>> from cardiac_shared.hardware import PerformanceOptimizer
    >>> optimizer = PerformanceOptimizer()
    >>>
    >>> # Check if GPU is suitable for task
    >>> device_rec = optimizer.recommend_device('totalsegmentator', min_vram_gb=5.5)
    >>> print(device_rec.device)  # 'cuda' or 'cpu'
    >>>
    >>> # Get optimized TotalSegmentator configuration
    >>> config = optimizer.get_totalsegmentator_config()
    >>> print(config['timeout_sec'])  # Optimized timeout based on GPU

Version: 1.0.0
Created: 2025-11-27
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from .detector import detect_hardware, HardwareInfo as HardwareProfile
from .profiles import GPUProfile, estimate_batch_time, match_gpu_profile


@dataclass
class DeviceRecommendation:
    """
    Device recommendation with reasoning

    Attributes:
        device: Recommended device ('cuda' or 'cpu')
        reasoning: Human-readable explanation of recommendation
        vram_sufficient: Whether GPU VRAM is sufficient for task
        warning: Optional warning message (e.g., "CPU will be 3× slower")
        alternative_suggestion: Optional suggestion for better hardware
    """
    device: str  # 'cuda' or 'cpu'
    reasoning: str
    vram_sufficient: bool
    warning: Optional[str] = None
    alternative_suggestion: Optional[str] = None

    def __str__(self) -> str:
        """Human-readable recommendation"""
        lines = [f"Device: {self.device.upper()}"]
        lines.append(f"Reason: {self.reasoning}")

        if self.warning:
            lines.append(f"Warning: {self.warning}")

        if self.alternative_suggestion:
            lines.append(f"Suggestion: {self.alternative_suggestion}")

        return "\n".join(lines)


@dataclass
class TimeEstimate:
    """
    Time estimation for batch processing

    Attributes:
        total_hours: Estimated total time in hours
        total_minutes: Estimated total time in minutes
        total_seconds: Estimated total time in seconds
        per_case_seconds: Estimated time per case in seconds
        formatted: Human-readable time string
        confidence: Confidence level ('high', 'medium', 'low')
        based_on: What the estimate is based on ('empirical', 'hardware', 'default')
    """
    total_hours: float
    total_minutes: float
    total_seconds: float
    per_case_seconds: float
    formatted: str
    confidence: str  # 'high', 'medium', 'low'
    based_on: str  # 'empirical', 'hardware', 'default'


class PerformanceOptimizer:
    """
    Hardware-aware performance optimizer

    Provides optimization recommendations for medical imaging tasks based on
    detected hardware capabilities. Uses empirical GPU profiles for accurate
    time estimation and parameter optimization.

    Backward compatible with shared.hardware_manager.PerformanceOptimizer

    Attributes:
        hw: Detected hardware profile (HardwareProfile)

    Example:
        >>> optimizer = PerformanceOptimizer()
        >>>
        >>> # Get device recommendation
        >>> device_rec = optimizer.recommend_device('totalsegmentator', min_vram_gb=5.5)
        >>> if device_rec.device == 'cuda':
        ...     print("Using GPU acceleration")
        ... else:
        ...     print(device_rec.warning)
        >>>
        >>> # Get optimized configuration
        >>> config = optimizer.get_totalsegmentator_config()
        >>> cmd = ['TotalSegmentator', '-i', input_file, '--device', config['device']]
    """

    def __init__(self, hardware_profile: Optional[HardwareProfile] = None):
        """
        Initialize performance optimizer

        Args:
            hardware_profile: Optional pre-detected hardware profile.
                            If None, will auto-detect hardware.

        Example:
            >>> # Auto-detect hardware
            >>> optimizer = PerformanceOptimizer()
            >>>
            >>> # Use pre-detected hardware (for efficiency)
            >>> hw = detect_hardware()
            >>> optimizer = PerformanceOptimizer(hardware_profile=hw)
        """
        if hardware_profile is None:
            self.hw = detect_hardware()
        else:
            self.hw = hardware_profile

        # Cache GPU profile for optimization
        self._gpu_profile = match_gpu_profile(
            vram_gb=self.hw.gpu.vram_total_gb if self.hw.gpu.available else 0.0,
            gpu_name=self.hw.gpu.device_name if self.hw.gpu.available else None
        )

    def recommend_device(
        self,
        task: str = 'totalsegmentator',
        min_vram_gb: float = 5.5,
        force_device: Optional[str] = None
    ) -> DeviceRecommendation:
        """
        Recommend compute device (CUDA GPU or CPU)

        Args:
            task: Task name (for logging/documentation)
            min_vram_gb: Minimum GPU VRAM required in GB (default: 5.5GB for TotalSegmentator)
            force_device: Force specific device ('cuda' or 'cpu'), overrides detection

        Returns:
            DeviceRecommendation with device choice and reasoning

        Example:
            >>> optimizer = PerformanceOptimizer()
            >>> rec = optimizer.recommend_device('totalsegmentator', min_vram_gb=5.5)
            >>> if rec.device == 'cpu':
            ...     print(f"Warning: {rec.warning}")
            ...     # Adjust timeout for CPU mode
            ...     timeout *= 3
        """
        # Force device override (for testing or user preference)
        if force_device is not None:
            if force_device == 'cpu':
                return DeviceRecommendation(
                    device='cpu',
                    reasoning=f'User forced CPU mode (--device cpu)',
                    vram_sufficient=False,
                    warning='CPU mode will be significantly slower than GPU (3-5× slower)'
                )
            elif force_device == 'cuda':
                if not self.hw.gpu.available:
                    return DeviceRecommendation(
                        device='cpu',
                        reasoning='User requested GPU but none detected - falling back to CPU',
                        vram_sufficient=False,
                        warning='GPU requested but not available, using CPU instead'
                    )
                else:
                    vram_gb = self.hw.gpu.vram_total_gb
                    return DeviceRecommendation(
                        device='cuda',
                        reasoning=f'User forced GPU mode: {self.hw.gpu.device_name}',
                        vram_sufficient=vram_gb >= min_vram_gb,
                        warning=None if vram_gb >= min_vram_gb
                                else f'GPU VRAM may be insufficient ({vram_gb:.1f}GB < {min_vram_gb}GB)'
                    )

        # No GPU detected
        if not self.hw.gpu.available:
            return DeviceRecommendation(
                device='cpu',
                reasoning='No GPU detected',
                vram_sufficient=False,
                warning='CPU mode will be 3-5× slower than GPU',
                alternative_suggestion='Consider using a system with GPU (RTX 2060 6GB or better recommended)'
            )

        # GPU detected but insufficient VRAM
        vram_gb = self.hw.gpu.vram_total_gb
        if vram_gb < min_vram_gb:
            return DeviceRecommendation(
                device='cpu',
                reasoning=f'GPU VRAM insufficient: {vram_gb:.1f}GB < {min_vram_gb}GB required',
                vram_sufficient=False,
                warning='CPU mode will be 3-5× slower than GPU',
                alternative_suggestion=f'Consider using GPU with ≥{min_vram_gb}GB VRAM (RTX 2060 or better)'
            )

        # GPU available and sufficient
        return DeviceRecommendation(
            device='cuda',
            reasoning=f'GPU available: {self.hw.gpu.device_name} ({vram_gb:.1f}GB VRAM)',
            vram_sufficient=True,
            warning=None,
            alternative_suggestion=None
        )

    def get_totalsegmentator_config(
        self,
        force_device: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get optimized TotalSegmentator configuration

        Returns device, timeout, fast_mode, and max_parallel settings based on
        detected hardware and empirical GPU profiles.

        Args:
            force_device: Force specific device ('cuda' or 'cpu')

        Returns:
            Dictionary with optimized configuration:
            {
                'device': 'cuda' or 'cpu',
                'fast_mode': True/False,
                'timeout_sec': int,
                'max_parallel': int,
                'estimated_time_per_case': float (seconds),
            }

        Example:
            >>> optimizer = PerformanceOptimizer()
            >>> config = optimizer.get_totalsegmentator_config()
            >>> print(f"Device: {config['device']}")
            >>> print(f"Timeout: {config['timeout_sec']} seconds")
            >>> print(f"Expected time per case: {config['estimated_time_per_case']:.1f}s")
        """
        # Get device recommendation
        device_rec = self.recommend_device('totalsegmentator', min_vram_gb=5.5, force_device=force_device)

        # Get GPU profile (cached in __init__)
        profile = self._gpu_profile

        return {
            'device': device_rec.device,
            'fast_mode': profile.totalseg_fast_mode,
            'timeout_sec': profile.totalseg_timeout_sec,
            'max_parallel': profile.totalseg_parallel_cases,
            'estimated_time_per_case': profile.totalseg_measured_time_per_case,
            'vram_sufficient': device_rec.vram_sufficient,
            'warning': device_rec.warning,
        }

    def estimate_batch_time(
        self,
        num_cases: int,
        task: str = 'totalsegmentator'
    ) -> TimeEstimate:
        """
        Estimate batch processing time

        Args:
            num_cases: Number of cases to process
            task: Task type (currently only 'totalsegmentator' supported)

        Returns:
            TimeEstimate with detailed time breakdown

        Example:
            >>> optimizer = PerformanceOptimizer()
            >>> estimate = optimizer.estimate_batch_time(377)
            >>> print(estimate.formatted)
            '10.1 hours (605 minutes)'
            >>> print(f"Confidence: {estimate.confidence}")
            'high'
        """
        # Get GPU profile (cached in __init__)
        profile = self._gpu_profile

        # Calculate time using profile
        time_info = estimate_batch_time(num_cases, profile, include_overhead=True)

        # Determine confidence level
        if profile.name in ['RTX 2060', 'CPU Only']:
            confidence = 'high'  # Empirical data available
            based_on = 'empirical'
        elif profile.name in ['RTX 3060', 'RTX 3090', 'RTX 4060', 'RTX 4090']:
            confidence = 'medium'  # Estimated based on VRAM/compute scaling
            based_on = 'hardware'
        else:
            confidence = 'low'  # Fallback estimate
            based_on = 'default'

        return TimeEstimate(
            total_hours=time_info['total_hours'],
            total_minutes=time_info['total_minutes'],
            total_seconds=time_info['total_seconds'],
            per_case_seconds=time_info['time_per_case_seconds'],
            formatted=time_info['formatted'],
            confidence=confidence,
            based_on=based_on,
        )

    def print_hardware_status(self, show_profile_details: bool = False):
        """
        Print hardware status to console

        Args:
            show_profile_details: Whether to show detailed GPU profile info

        Example:
            >>> optimizer = PerformanceOptimizer()
            >>> optimizer.print_hardware_status()
            ======================================================================
            HARDWARE PROFILE
            ======================================================================
            GPU: NVIDIA GeForce RTX 2060 (6.0GB VRAM)
            Matched Profile: RTX 2060
            CPU: 8 physical cores (16 logical)
            ...
        """
        print(str(self.hw))

        if show_profile_details:
            profile = self._gpu_profile
            print()
            print("TotalSegmentator Optimization:")
            print(f"  Fast Mode: {profile.totalseg_fast_mode}")
            print(f"  Timeout: {profile.totalseg_timeout_sec}s ({profile.totalseg_timeout_sec/60:.0f} min)")
            print(f"  Max Parallel: {profile.totalseg_parallel_cases} case(s)")
            print(f"  Expected Time: {profile.totalseg_measured_time_per_case:.1f}s ({profile.totalseg_measured_time_per_case/60:.1f} min) per case")
            print("=" * 70)

    def get_hardware_summary(self) -> str:
        """
        Get concise hardware summary (one-line)

        Returns:
            One-line hardware summary string

        Example:
            >>> optimizer = PerformanceOptimizer()
            >>> print(optimizer.get_hardware_summary())
            'GPU: RTX 2060 (6.0GB) | CPU: 8 cores | RAM: 16.0GB available'
        """
        if self.hw.gpu.available:
            gpu_str = f"{self._gpu_profile.name} ({self.hw.gpu.vram_total_gb:.1f}GB)"
        else:
            gpu_str = "None (CPU-only mode)"

        return (f"GPU: {gpu_str} | "
                f"CPU: {self.hw.cpu.physical_cores} cores | "
                f"RAM: {self.hw.ram.available_gb:.1f}GB available")


__version__ = '1.0.0'
