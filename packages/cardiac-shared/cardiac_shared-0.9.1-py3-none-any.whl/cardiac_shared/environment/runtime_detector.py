"""
Runtime Environment Detector

Auto-detect runtime environment: Colab/Windows/Linux/WSL/macOS
Supports Google Drive mounting (Colab environment)
"""

import os
import platform
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)


@dataclass
class RuntimeEnvironment:
    """Runtime environment information"""
    runtime_type: str  # 'colab' / 'windows' / 'linux' / 'wsl' / 'macos' / 'unknown'
    is_colab: bool
    is_wsl: bool
    is_jupyter: bool
    os_name: str
    os_version: str
    python_version: str
    working_directory: Path
    home_directory: Path
    google_drive_mounted: bool = False
    google_drive_path: Optional[Path] = None

    @property
    def is_hospital_environment(self) -> bool:
        """Likely hospital environment (Windows and not Colab)"""
        return self.runtime_type == 'windows' and not self.is_colab

    @property
    def is_cloud_environment(self) -> bool:
        """Is cloud environment"""
        return self.is_colab

    @property
    def supports_gpu(self) -> bool:
        """Environment may support GPU (requires hardware detection to confirm)"""
        return True  # Actual GPU availability detected by hardware.detector

    @property
    def recommended_install_method(self) -> str:
        """Recommended software installation method"""
        if self.is_colab:
            return "pip_online"  # Colab always online
        elif self.runtime_type in ['windows', 'wsl']:
            return "offline_package"  # Hospital environment - offline package
        else:
            return "pip_mirror"  # Linux - use mirror


def detect_colab() -> bool:
    """
    Detect if running in Google Colab

    Returns:
        True if running in Colab
    """
    try:
        import google.colab
        return True
    except ImportError:
        return False


def detect_jupyter() -> bool:
    """
    Detect if running in Jupyter environment

    Returns:
        True if running in Jupyter/IPython
    """
    try:
        from IPython import get_ipython
        ipython = get_ipython()
        if ipython is None:
            return False

        if 'IPKernelApp' in ipython.config:
            return True

        shell_type = type(ipython).__name__
        if 'ZMQInteractiveShell' in shell_type:
            return True

        return False
    except ImportError:
        return False


def detect_wsl() -> bool:
    """
    Detect if running in WSL (Windows Subsystem for Linux)

    Returns:
        True if running in WSL
    """
    if platform.system() != "Linux":
        return False

    try:
        # Method 1: Check /proc/version
        with open('/proc/version', 'r') as f:
            version_info = f.read().lower()
            if 'microsoft' in version_info or 'wsl' in version_info:
                return True

        # Method 2: Check /proc/sys/kernel/osrelease
        osrelease_path = Path('/proc/sys/kernel/osrelease')
        if osrelease_path.exists():
            osrelease = osrelease_path.read_text().lower()
            if 'microsoft' in osrelease or 'wsl' in osrelease:
                return True

        return False
    except Exception as e:
        logger.debug(f"WSL detection failed: {e}")
        return False


def detect_google_drive() -> Tuple[bool, Optional[Path]]:
    """
    Detect if Google Drive is mounted (Colab environment)

    Returns:
        (is_mounted, mount_path)
    """
    default_mount_path = Path('/content/drive')

    if default_mount_path.exists():
        my_drive = default_mount_path / 'MyDrive'
        if my_drive.exists():
            return True, default_mount_path

    alternative_paths = [
        Path('/content/gdrive'),
        Path('/gdrive'),
        Path('/drive'),
    ]

    for path in alternative_paths:
        if path.exists():
            return True, path

    return False, None


def mount_google_drive(force: bool = False) -> Tuple[bool, Optional[Path]]:
    """
    Mount Google Drive (Colab environment only)

    Args:
        force: Force remount

    Returns:
        (success, mount_path)
    """
    if not detect_colab():
        logger.warning("Not in Colab environment, cannot mount Google Drive")
        return False, None

    is_mounted, mount_path = detect_google_drive()
    if is_mounted and not force:
        logger.info(f"Google Drive already mounted: {mount_path}")
        return True, mount_path

    try:
        from google.colab import drive
        mount_point = '/content/drive'
        drive.mount(mount_point, force_remount=force)

        mount_path = Path(mount_point)
        if mount_path.exists():
            logger.info(f"Google Drive mounted successfully: {mount_path}")
            return True, mount_path
        else:
            logger.error("Google Drive mount failed")
            return False, None

    except Exception as e:
        logger.error(f"Google Drive mount exception: {e}")
        return False, None


def detect_runtime() -> RuntimeEnvironment:
    """
    Detect complete runtime environment

    Returns:
        RuntimeEnvironment object
    """
    logger.info("="*70)
    logger.info("Detecting runtime environment...")
    logger.info("="*70)

    os_name = platform.system()
    os_version = platform.release()
    python_version = platform.python_version()
    working_dir = Path.cwd()
    home_dir = Path.home()

    is_colab = detect_colab()
    is_jupyter = detect_jupyter()
    is_wsl = detect_wsl()

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

    # Colab: Check Google Drive
    google_drive_mounted = False
    google_drive_path = None
    if is_colab:
        google_drive_mounted, google_drive_path = detect_google_drive()

    env = RuntimeEnvironment(
        runtime_type=runtime_type,
        is_colab=is_colab,
        is_wsl=is_wsl,
        is_jupyter=is_jupyter,
        os_name=os_name,
        os_version=os_version,
        python_version=python_version,
        working_directory=working_dir,
        home_directory=home_dir,
        google_drive_mounted=google_drive_mounted,
        google_drive_path=google_drive_path
    )

    logger.info("="*70)
    logger.info(f"Runtime detection complete: {runtime_type.upper()}")
    logger.info("="*70)

    return env


def print_environment_summary(env: RuntimeEnvironment):
    """
    Print runtime environment summary

    Args:
        env: RuntimeEnvironment object
    """
    print("\n" + "="*70)
    print("[i] Runtime Environment")
    print("="*70)

    print(f"Runtime type: {env.runtime_type.upper()}")
    print(f"OS: {env.os_name} {env.os_version}")
    print(f"Python: {env.python_version}")

    # Environment flags
    flags = []
    if env.is_colab:
        flags.append("Google Colab")
    if env.is_wsl:
        flags.append("WSL")
    if env.is_jupyter:
        flags.append("Jupyter")
    if env.is_hospital_environment:
        flags.append("Hospital Environment")
    if env.is_cloud_environment:
        flags.append("Cloud Environment")

    if flags:
        print(f"Environment features: {', '.join(flags)}")

    # Path info
    print(f"\n[i] Paths:")
    print(f"  Working directory: {env.working_directory}")
    print(f"  Home directory: {env.home_directory}")

    # Google Drive (Colab)
    if env.is_colab:
        if env.google_drive_mounted:
            print(f"  Google Drive: [OK] Mounted ({env.google_drive_path})")
        else:
            print(f"  Google Drive: [X] Not mounted")

    # Deployment recommendations
    print(f"\n[i] Recommended install method: {env.recommended_install_method}")
    if env.is_hospital_environment:
        print(f"  Suggestion: Use offline package (hospital isolated network)")
    elif env.is_colab:
        print(f"  Suggestion: pip online install (Colab connected)")

    print("="*70 + "\n")


def get_data_directory_recommendations(env: RuntimeEnvironment) -> Dict[str, Path]:
    """
    Get recommended data directory paths based on environment

    Args:
        env: RuntimeEnvironment object

    Returns:
        Dictionary of recommended directory paths
    """
    recommendations = {}

    if env.is_colab:
        if env.google_drive_mounted:
            base = env.google_drive_path / 'MyDrive'
            recommendations['data_dir'] = base / 'data'
            recommendations['output_dir'] = base / 'output'
            recommendations['cache_dir'] = base / 'cache'
        else:
            base = Path('/content')
            recommendations['data_dir'] = base / 'data'
            recommendations['output_dir'] = base / 'output'
            recommendations['cache_dir'] = base / 'cache'
            recommendations['warning'] = "Colab temporary storage, recommend mounting Google Drive"

    elif env.runtime_type in ['windows', 'wsl']:
        base = env.working_directory
        recommendations['data_dir'] = base / 'data' / 'dicom_original'
        recommendations['output_dir'] = base / 'output'
        recommendations['cache_dir'] = base / 'data' / 'cache'
        recommendations['log_dir'] = base / 'logs'

    else:
        base = env.working_directory
        recommendations['data_dir'] = base / 'data' / 'dicom_original'
        recommendations['output_dir'] = base / 'output'
        recommendations['cache_dir'] = base / 'data' / 'cache'
        recommendations['log_dir'] = base / 'logs'

    return recommendations


def setup_environment_for_tool(tool_name: str = "default") -> Dict[str, Any]:
    """
    Setup environment for a specific tool (one-click initialization)

    Args:
        tool_name: Tool name

    Returns:
        Environment setup result dictionary
    """
    env = detect_runtime()

    result = {
        'environment': env,
        'recommendations': get_data_directory_recommendations(env),
        'tool_name': tool_name,
    }

    if env.is_colab:
        if not env.google_drive_mounted:
            print("Detected Colab environment but Google Drive not mounted")
            result['google_drive_mount_required'] = True

    return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    print("\nTesting runtime environment detection module...")
    print("="*70)

    env = detect_runtime()
    print_environment_summary(env)

    print("\nRecommended data directories:")
    print("="*70)
    recommendations = get_data_directory_recommendations(env)
    for key, value in recommendations.items():
        print(f"{key}: {value}")

    print("\nValidation checks:")
    print(f"[OK] Runtime type: {env.runtime_type}")
    print(f"[OK] Colab detection: {env.is_colab}")
    print(f"[OK] WSL detection: {env.is_wsl}")
    print(f"[OK] Jupyter detection: {env.is_jupyter}")
    print(f"[OK] Hospital environment: {env.is_hospital_environment}")
    print(f"[OK] Recommended install: {env.recommended_install_method}")
