"""
Hardware Detection Module - Shared Version

Supports multiple environments: Windows/Linux/Colab/WSL
Auto-detects GPU, CPU, memory and provides performance recommendations.
"""

import psutil
import platform
import logging
import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path

# Optional torch import - graceful degradation if not available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information"""
    available: bool
    device_name: str
    vram_total_gb: float
    vram_available_gb: float
    cuda_version: Optional[str] = None
    device_count: int = 0
    compute_capability: Optional[tuple] = None

    def __post_init__(self):
        if self.available and self.cuda_version is None:
            try:
                if TORCH_AVAILABLE:
                    self.cuda_version = torch.version.cuda
                else:
                    self.cuda_version = "PyTorch not available"
            except:
                self.cuda_version = "Unknown"


@dataclass
class CPUInfo:
    """CPU information (enhanced for hospital CPU optimization)"""
    physical_cores: int
    logical_cores: int
    cpu_model: str
    cpu_freq_mhz: Optional[float] = None
    cpu_freq_min_mhz: Optional[float] = None
    cpu_freq_max_mhz: Optional[float] = None
    cache_size_mb: Optional[float] = None
    architecture: Optional[str] = None

    def __post_init__(self):
        # Detect CPU frequency
        if self.cpu_freq_mhz is None:
            try:
                freq = psutil.cpu_freq()
                if freq:
                    self.cpu_freq_mhz = freq.current
                    self.cpu_freq_min_mhz = freq.min
                    self.cpu_freq_max_mhz = freq.max
            except:
                pass

        # Detect architecture
        if self.architecture is None:
            self.architecture = platform.machine()

    @property
    def is_high_performance(self) -> bool:
        """Is high-performance CPU (8+ cores)"""
        return self.physical_cores >= 8

    @property
    def recommended_workers(self) -> int:
        """Recommended DataLoader worker count"""
        if self.physical_cores <= 2:
            return 0  # Minimal tier: single-threaded
        elif self.physical_cores <= 4:
            return 2  # Standard tier low
        elif self.physical_cores <= 8:
            return 4  # Standard tier
        elif self.physical_cores <= 16:
            return 8  # Performance tier
        else:
            return 16  # Professional tier


@dataclass
class RAMInfo:
    """Memory information"""
    total_gb: float
    available_gb: float
    percent_used: float

    @property
    def is_sufficient(self) -> bool:
        """Has sufficient memory (recommended 6GB+ available)"""
        return self.available_gb >= 6.0

    @property
    def recommended_batch_size(self) -> int:
        """Recommended batch size based on available memory"""
        if self.available_gb < 4:
            return 1
        elif self.available_gb < 8:
            return 2
        elif self.available_gb < 16:
            return 4
        else:
            return 8


@dataclass
class EnvironmentInfo:
    """Environment information"""
    runtime_type: str  # 'windows' / 'linux' / 'colab' / 'wsl' / 'macos'
    is_colab: bool
    is_wsl: bool
    os_name: str
    os_version: str

    @property
    def is_hospital_environment(self) -> bool:
        """Likely hospital environment (Windows and not Colab)"""
        return self.runtime_type == 'windows' and not self.is_colab


@dataclass
class HardwareInfo:
    """Complete hardware information"""
    gpu: GPUInfo
    cpu: CPUInfo
    ram: RAMInfo
    environment: EnvironmentInfo
    platform: str
    python_version: str

    @property
    def recommended_device(self) -> str:
        """Recommended compute device"""
        return "cuda" if self.gpu.available else "cpu"

    @property
    def performance_tier(self) -> str:
        """
        Performance tier (5 levels)
        Minimal -> Standard -> Performance -> Professional -> Enterprise
        """
        if self.gpu.available:
            if self.gpu.vram_total_gb >= 16:
                return "Enterprise"
            elif self.gpu.vram_total_gb >= 6:
                return "Professional"
            else:
                return "Performance"
        else:
            # CPU-only tiers (critical for hospital environments)
            if self.cpu.physical_cores >= 16 and self.ram.total_gb >= 32:
                return "Performance"
            elif self.cpu.physical_cores >= 8 and self.ram.total_gb >= 16:
                return "Standard"
            else:
                return "Minimal"


def detect_environment() -> EnvironmentInfo:
    """
    Detect runtime environment

    Supports:
    - Google Colab
    - WSL (Windows Subsystem for Linux)
    - Native Windows
    - Native Linux
    - macOS
    """
    os_name = platform.system()
    os_version = platform.release()

    # Detect Colab
    is_colab = False
    try:
        import google.colab
        is_colab = True
    except:
        pass

    # Detect WSL
    is_wsl = False
    if os_name == "Linux":
        try:
            with open('/proc/version', 'r') as f:
                version_info = f.read().lower()
                is_wsl = 'microsoft' in version_info or 'wsl' in version_info
        except:
            pass

    # Determine runtime type
    if is_colab:
        runtime_type = 'colab'
    elif is_wsl:
        runtime_type = 'wsl'
    elif os_name == "Windows":
        runtime_type = 'windows'
    elif os_name == "Linux":
        runtime_type = 'linux'
    elif os_name == "Darwin":
        runtime_type = 'macos'
    else:
        runtime_type = 'unknown'

    logger.info(f"Detected environment: {runtime_type}")

    return EnvironmentInfo(
        runtime_type=runtime_type,
        is_colab=is_colab,
        is_wsl=is_wsl,
        os_name=os_name,
        os_version=os_version
    )


def detect_gpu() -> GPUInfo:
    """Detect GPU information"""
    if not TORCH_AVAILABLE:
        logger.info("PyTorch not installed, GPU detection unavailable")
        return GPUInfo(
            available=False,
            device_name="CPU (PyTorch not available)",
            vram_total_gb=0.0,
            vram_available_gb=0.0,
            device_count=0
        )

    if not torch.cuda.is_available():
        logger.info("CUDA not available, using CPU mode")
        return GPUInfo(
            available=False,
            device_name="CPU",
            vram_total_gb=0.0,
            vram_available_gb=0.0,
            device_count=0
        )

    try:
        device_count = torch.cuda.device_count()
        device_name = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        vram_total_gb = props.total_memory / 1024**3

        # Compute capability
        compute_capability = (props.major, props.minor)

        # Available VRAM
        torch.cuda.empty_cache()
        vram_allocated = torch.cuda.memory_allocated(0) / 1024**3
        vram_available_gb = vram_total_gb - vram_allocated

        logger.info(f"Detected GPU: {device_name} ({vram_total_gb:.1f}GB VRAM)")

        return GPUInfo(
            available=True,
            device_name=device_name,
            vram_total_gb=vram_total_gb,
            vram_available_gb=vram_available_gb,
            device_count=device_count,
            compute_capability=compute_capability
        )

    except Exception as e:
        logger.warning(f"GPU detection failed: {e}")
        return GPUInfo(
            available=False,
            device_name="CPU",
            vram_total_gb=0.0,
            vram_available_gb=0.0,
            device_count=0
        )


def detect_cpu() -> CPUInfo:
    """Detect CPU information (enhanced)"""
    try:
        physical_cores = psutil.cpu_count(logical=False) or 1
        logical_cores = psutil.cpu_count(logical=True) or 1

        # Get CPU model
        cpu_model = platform.processor()
        if not cpu_model or cpu_model.strip() == "":
            # Fallback method
            import subprocess
            try:
                if platform.system() == "Windows":
                    result = subprocess.run(
                        ["wmic", "cpu", "get", "name"],
                        capture_output=True,
                        text=True
                    )
                    lines = result.stdout.strip().split('\n')
                    cpu_model = lines[1].strip() if len(lines) > 1 else "Unknown CPU"
                elif platform.system() == "Linux":
                    with open('/proc/cpuinfo', 'r') as f:
                        for line in f:
                            if 'model name' in line:
                                cpu_model = line.split(':')[1].strip()
                                break
                else:
                    cpu_model = "Unknown CPU"
            except:
                cpu_model = "Unknown CPU"

        # Try to get CPU cache size (Linux)
        cache_size_mb = None
        try:
            if platform.system() == "Linux":
                cache_info = Path("/sys/devices/system/cpu/cpu0/cache")
                if cache_info.exists():
                    for cache_dir in sorted(cache_info.glob("index*"), reverse=True):
                        size_file = cache_dir / "size"
                        if size_file.exists():
                            size_str = size_file.read_text().strip()
                            if 'K' in size_str:
                                cache_size_mb = int(size_str.replace('K', '')) / 1024
                                break
        except:
            pass

        logger.info(f"Detected CPU: {physical_cores} cores ({logical_cores} threads)")

        return CPUInfo(
            physical_cores=physical_cores,
            logical_cores=logical_cores,
            cpu_model=cpu_model,
            cache_size_mb=cache_size_mb
        )

    except Exception as e:
        logger.warning(f"CPU detection failed: {e}")
        return CPUInfo(
            physical_cores=1,
            logical_cores=1,
            cpu_model="Unknown CPU"
        )


def detect_ram() -> RAMInfo:
    """Detect memory information"""
    try:
        mem = psutil.virtual_memory()
        total_gb = mem.total / 1024**3
        available_gb = mem.available / 1024**3
        percent_used = mem.percent

        logger.info(f"Detected RAM: {total_gb:.1f}GB total, {available_gb:.1f}GB available")

        return RAMInfo(
            total_gb=total_gb,
            available_gb=available_gb,
            percent_used=percent_used
        )

    except Exception as e:
        logger.warning(f"RAM detection failed: {e}")
        return RAMInfo(
            total_gb=0.0,
            available_gb=0.0,
            percent_used=100.0
        )


def detect_hardware() -> HardwareInfo:
    """
    Detect complete hardware information

    Returns:
        HardwareInfo: Complete hardware info including GPU, CPU, RAM, environment

    Example:
        >>> hw = detect_hardware()
        >>> print(f"Environment: {hw.environment.runtime_type}")
        >>> print(f"GPU: {hw.gpu.device_name}, VRAM: {hw.gpu.vram_total_gb:.1f}GB")
        >>> print(f"CPU: {hw.cpu.physical_cores} cores")
        >>> print(f"RAM: {hw.ram.total_gb:.1f}GB")
        >>> print(f"Performance tier: {hw.performance_tier}")
    """
    logger.info("="*70)
    logger.info("Detecting hardware configuration...")
    logger.info("="*70)

    environment = detect_environment()
    gpu = detect_gpu()
    cpu = detect_cpu()
    ram = detect_ram()

    hw_info = HardwareInfo(
        gpu=gpu,
        cpu=cpu,
        ram=ram,
        environment=environment,
        platform=platform.system(),
        python_version=platform.python_version()
    )

    logger.info("="*70)
    logger.info(f"Hardware detection complete - Tier: {hw_info.performance_tier}")
    logger.info("="*70)

    return hw_info


def print_hardware_summary(hw: HardwareInfo):
    """
    Print hardware information summary

    Args:
        hw: HardwareInfo object
    """
    print("\n" + "="*70)
    print("[i] Hardware Configuration")
    print("="*70)

    # Environment info
    print(f"[ENV] Runtime: {hw.environment.runtime_type.upper()}")
    if hw.environment.is_colab:
        print(f"  - Google Colab environment")
    elif hw.environment.is_wsl:
        print(f"  - WSL (Windows Subsystem for Linux)")
    elif hw.environment.is_hospital_environment:
        print(f"  - Hospital environment (Windows)")
    print(f"  - System: {hw.environment.os_name} {hw.environment.os_version}")

    # GPU info
    if hw.gpu.available:
        print(f"[OK] GPU: {hw.gpu.device_name}")
        print(f"  - VRAM: {hw.gpu.vram_total_gb:.1f}GB (available: {hw.gpu.vram_available_gb:.1f}GB)")
        print(f"  - CUDA: {hw.gpu.cuda_version}")
        if hw.gpu.compute_capability:
            print(f"  - Compute capability: {hw.gpu.compute_capability[0]}.{hw.gpu.compute_capability[1]}")
    else:
        print(f"[X] GPU: Not available")
        print(f"  - Mode: CPU inference")

    # CPU info
    print(f"[OK] CPU: {hw.cpu.physical_cores} cores ({hw.cpu.logical_cores} threads)")
    if hw.cpu.cpu_freq_max_mhz:
        print(f"  - Frequency: {hw.cpu.cpu_freq_mhz:.0f}MHz (max: {hw.cpu.cpu_freq_max_mhz:.0f}MHz)")
    if hw.cpu.cache_size_mb:
        print(f"  - Cache: {hw.cpu.cache_size_mb:.1f}MB")
    if hw.cpu.architecture:
        print(f"  - Architecture: {hw.cpu.architecture}")

    # RAM info
    print(f"[OK] RAM: {hw.ram.total_gb:.1f}GB total")
    print(f"  - Available: {hw.ram.available_gb:.1f}GB ({100-hw.ram.percent_used:.1f}% free)")
    if not hw.ram.is_sufficient:
        print(f"  [!] Warning: Available memory <6GB, may affect performance")

    # Performance tier and recommendations
    print("\n" + "-"*70)
    print("[i] Performance Analysis")
    print("-"*70)
    print(f"Tier: {hw.performance_tier}")
    print(f"Recommended device: {hw.recommended_device.upper()}")
    print(f"Recommended workers: {hw.cpu.recommended_workers}")
    print(f"Recommended batch size: {hw.ram.recommended_batch_size}")

    # Hospital environment tips
    if hw.environment.is_hospital_environment and not hw.gpu.available:
        print("\n[i] Hospital CPU Mode Optimization:")
        if hw.cpu.physical_cores >= 8:
            print("  [OK] Good CPU performance (8+ cores), expected: <60s/patient")
        else:
            print("  [!] Low CPU core count, recommend 8+ cores for best performance")

    print("="*70 + "\n")


def get_optimal_config(hw: HardwareInfo) -> Dict[str, Any]:
    """
    Get optimal configuration based on hardware

    Args:
        hw: Hardware information

    Returns:
        Dictionary with optimal configuration
    """
    config = {
        'device': hw.recommended_device,
        'num_workers': hw.cpu.recommended_workers,
        'batch_size': hw.ram.recommended_batch_size,
        'pin_memory': hw.gpu.available,
        'prefetch_factor': 2 if hw.cpu.recommended_workers > 0 else None,
        'performance_tier': hw.performance_tier,
    }

    # CPU optimization (hospital environment)
    if not hw.gpu.available:
        config['cpu_optimization'] = {
            'torch_threads': hw.cpu.physical_cores,
            'mkl_threads': hw.cpu.physical_cores,
            'omp_threads': hw.cpu.physical_cores,
        }

    return config


if __name__ == "__main__":
    # Test code
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("\nTesting hardware detection module (shared version)...")
    print("="*70)

    hw = detect_hardware()
    print_hardware_summary(hw)

    # Get optimal config
    print("\nOptimal configuration:")
    print("="*70)
    optimal_config = get_optimal_config(hw)
    for key, value in optimal_config.items():
        print(f"{key}: {value}")
