"""
GPU Utility Functions

Helper functions for GPU-related optimizations.
Added in v0.5.1 for TotalSegmentator pipeline optimization.
"""

import re
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# GPU stabilization times by series
# Based on empirical testing with TotalSegmentator pipeline
GPU_STABILIZATION_TIMES = {
    # RTX 40 series - Better memory management, faster stabilization
    '4090': 1.0,
    '4080': 1.0,
    '4070': 1.5,
    '4060': 1.5,
    '4050': 2.0,

    # RTX 30 series - Standard performance
    '3090': 1.5,
    '3080': 2.0,
    '3070': 2.0,
    '3060': 2.5,
    '3050': 3.0,

    # RTX 20 series - Older architecture
    '2080': 2.5,
    '2070': 3.0,
    '2060': 3.5,

    # GTX 16 series - Consumer grade
    '1660': 4.0,
    '1650': 4.0,

    # GTX 10 series - Legacy
    '1080': 3.5,
    '1070': 4.0,
    '1060': 4.5,

    # Quadro/Professional (newer)
    'A6000': 1.0,
    'A5000': 1.5,
    'A4000': 2.0,
    'RTX 6000': 1.0,
    'RTX 5000': 1.5,
    'RTX 4000': 2.0,

    # Tesla/Data Center
    'A100': 1.0,
    'V100': 2.0,
    'T4': 2.5,
}

# Default stabilization time for unknown GPUs
DEFAULT_STABILIZATION_TIME = 5.0


def _extract_gpu_model_number(device_name: str) -> Optional[str]:
    """
    Extract GPU model identifier from device name.

    Args:
        device_name: Full GPU device name (e.g., "NVIDIA GeForce RTX 4060")

    Returns:
        Model identifier (e.g., "4060") or None if not found

    Examples:
        >>> _extract_gpu_model_number("NVIDIA GeForce RTX 4060")
        '4060'
        >>> _extract_gpu_model_number("NVIDIA GeForce GTX 1660 Ti")
        '1660'
        >>> _extract_gpu_model_number("NVIDIA A100-SXM4-80GB")
        'A100'
    """
    if not device_name:
        return None

    device_upper = device_name.upper()

    # Check for data center/professional GPUs first (A100, V100, T4, etc.)
    for model in ['A100', 'A6000', 'A5000', 'A4000', 'V100', 'T4']:
        if model in device_upper:
            return model

    # Check for Quadro RTX series
    quadro_match = re.search(r'RTX\s*(6000|5000|4000)', device_upper)
    if quadro_match:
        return f"RTX {quadro_match.group(1)}"

    # Extract RTX/GTX model numbers (e.g., 4060, 3070, 2080, 1660)
    model_match = re.search(r'(?:RTX|GTX)\s*(\d{4})', device_upper)
    if model_match:
        return model_match.group(1)

    # Try to extract any 4-digit number as fallback
    number_match = re.search(r'\b(\d{4})\b', device_name)
    if number_match:
        return number_match.group(1)

    return None


def get_recommended_gpu_stabilization_time(
    gpu_info: Optional[Dict[str, Any]] = None,
    device_name: Optional[str] = None
) -> float:
    """
    Get recommended GPU stabilization wait time.

    Replaces hardcoded time.sleep(5) with GPU-aware dynamic wait time.
    Newer GPUs (RTX 40 series) have better memory management and need
    shorter stabilization times. Older GPUs need longer wait times.

    Args:
        gpu_info: GPU info dict with 'device_name' key, or GPUInfo object
        device_name: Direct device name string (alternative to gpu_info)

    Returns:
        Recommended wait time in seconds (1.0-5.0)

    Examples:
        >>> # Using dict from detect_hardware()
        >>> gpu_info = {'device_name': 'NVIDIA GeForce RTX 4060'}
        >>> get_recommended_gpu_stabilization_time(gpu_info)
        1.5

        >>> # Using direct device name
        >>> get_recommended_gpu_stabilization_time(device_name='NVIDIA GeForce RTX 2060')
        3.5

        >>> # Unknown GPU returns conservative default
        >>> get_recommended_gpu_stabilization_time(device_name='Unknown GPU')
        5.0

    Note:
        This function is designed for TotalSegmentator pipeline where
        GPU memory needs time to stabilize between patient processing.
    """
    # Get device name from various input formats
    name = None

    if device_name:
        name = device_name
    elif gpu_info:
        # Handle both dict and dataclass
        if isinstance(gpu_info, dict):
            name = gpu_info.get('device_name')
        elif hasattr(gpu_info, 'device_name'):
            name = gpu_info.device_name

    if not name:
        logger.debug(f"No GPU device name provided, using default: {DEFAULT_STABILIZATION_TIME}s")
        return DEFAULT_STABILIZATION_TIME

    # Extract model number
    model = _extract_gpu_model_number(name)

    if model and model in GPU_STABILIZATION_TIMES:
        wait_time = GPU_STABILIZATION_TIMES[model]
        logger.debug(f"GPU '{name}' (model: {model}) -> stabilization time: {wait_time}s")
        return wait_time

    # Check if it's an RTX 40/30/20 series by pattern
    if model:
        try:
            model_num = int(model)
            if 4000 <= model_num < 5000:  # RTX 40 series
                wait_time = 2.0
            elif 3000 <= model_num < 4000:  # RTX 30 series
                wait_time = 3.0
            elif 2000 <= model_num < 3000:  # RTX 20 series
                wait_time = 4.0
            elif 1000 <= model_num < 2000:  # GTX 10/16 series
                wait_time = 4.5
            else:
                wait_time = DEFAULT_STABILIZATION_TIME

            logger.debug(f"GPU '{name}' (model: {model}) -> estimated time: {wait_time}s")
            return wait_time
        except ValueError:
            pass

    logger.debug(f"Unknown GPU '{name}', using default: {DEFAULT_STABILIZATION_TIME}s")
    return DEFAULT_STABILIZATION_TIME


def get_gpu_performance_tier(device_name: str) -> str:
    """
    Get GPU performance tier for quick classification.

    Args:
        device_name: GPU device name

    Returns:
        Performance tier: 'high', 'medium', 'low', or 'unknown'

    Examples:
        >>> get_gpu_performance_tier("NVIDIA GeForce RTX 4090")
        'high'
        >>> get_gpu_performance_tier("NVIDIA GeForce RTX 3060")
        'medium'
        >>> get_gpu_performance_tier("NVIDIA GeForce GTX 1060")
        'low'
    """
    model = _extract_gpu_model_number(device_name)

    if not model:
        return 'unknown'

    # High tier: RTX 40 series high-end, A100, etc.
    high_tier = ['4090', '4080', '3090', 'A100', 'A6000', 'V100']
    if model in high_tier:
        return 'high'

    # Medium tier: RTX 40/30 mid-range
    medium_tier = ['4070', '4060', '3080', '3070', '3060', 'A5000', 'A4000', 'T4']
    if model in medium_tier:
        return 'medium'

    # Low tier: Older or entry-level
    return 'low'


if __name__ == "__main__":
    # Test code
    test_gpus = [
        "NVIDIA GeForce RTX 4090",
        "NVIDIA GeForce RTX 4060",
        "NVIDIA GeForce RTX 3080",
        "NVIDIA GeForce RTX 2060",
        "NVIDIA GeForce GTX 1660 Ti",
        "NVIDIA A100-SXM4-80GB",
        "NVIDIA Tesla T4",
        "Unknown GPU Model",
    ]

    print("GPU Stabilization Time Test")
    print("=" * 60)

    for gpu in test_gpus:
        time = get_recommended_gpu_stabilization_time(device_name=gpu)
        tier = get_gpu_performance_tier(gpu)
        print(f"{gpu:40s} -> {time:.1f}s (tier: {tier})")
