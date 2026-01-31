"""
Shared Environment Detection Module
Runtime environment detection for Colab/Windows/Linux/WSL
"""

from cardiac_shared.environment.runtime_detector import (
    # Data classes
    RuntimeEnvironment,

    # Detection functions
    detect_colab,
    detect_jupyter,
    detect_wsl,
    detect_google_drive,
    detect_runtime,

    # Google Drive operations
    mount_google_drive,

    # Utility functions
    print_environment_summary,
    get_data_directory_recommendations,
    setup_environment_for_tool,
)

__all__ = [
    # Data classes
    'RuntimeEnvironment',

    # Detection functions
    'detect_colab',
    'detect_jupyter',
    'detect_wsl',
    'detect_google_drive',
    'detect_runtime',

    # Google Drive operations
    'mount_google_drive',

    # Utility functions
    'print_environment_summary',
    'get_data_directory_recommendations',
    'setup_environment_for_tool',
]
