#!/usr/bin/env python3
"""
Data Sources Manager for Cardiac Imaging Analysis

Provides a unified interface for managing multiple data sources
across cardiac imaging analysis projects.

Usage:
    from cardiac_shared.data_sources import DataSourceManager

    # Initialize with config file
    manager = DataSourceManager('/path/to/config.yaml')

    # Or use project auto-discovery
    manager = DataSourceManager.from_project('my-project')

    # Get a specific data source
    source = manager.get_source('default')
    print(f"Input: {source.input_dir}")

    # List all available data sources
    for name, source in manager.list_sources().items():
        print(f"{name}: {source.description}")

Version: 1.0.0
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

import yaml


@dataclass
class DataSource:
    """Represents a data source configuration."""

    name: str
    description: str
    type: str  # 'nifti', 'dicom'
    input_dir: str
    output_dir: str
    file_pattern: str = "*.nii.gz"
    file_filter: Optional[str] = None
    expected_count: int = 0
    notes: str = ""
    # Optional Windows path
    input_dir_windows: Optional[str] = None
    # Optional DICOM source for converted datasets
    dicom_source: Optional[str] = None
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def input_path(self) -> Path:
        """Return input directory as Path object."""
        return Path(self.input_dir)

    @property
    def output_path(self) -> Path:
        """Return output directory as Path object."""
        return Path(self.output_dir)

    def exists(self) -> bool:
        """Check if input directory exists."""
        return self.input_path.exists()

    def get_files(self, limit: Optional[int] = None) -> List[Path]:
        """
        Get list of input files matching pattern and filter.

        Args:
            limit: Maximum number of files to return

        Returns:
            List of Path objects for matching files
        """
        if not self.exists():
            return []

        files = sorted(self.input_path.glob(self.file_pattern))

        if self.file_filter:
            files = [f for f in files if self.file_filter in f.name]

        if limit:
            files = files[:limit]

        return files

    def file_count(self) -> int:
        """Return count of matching files."""
        return len(self.get_files())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'input_dir': self.input_dir,
            'output_dir': self.output_dir,
            'file_pattern': self.file_pattern,
            'file_filter': self.file_filter,
            'expected_count': self.expected_count,
            'notes': self.notes,
            'input_dir_windows': self.input_dir_windows,
            'dicom_source': self.dicom_source,
            'metadata': self.metadata,
        }


@dataclass
class DataSourceStatus:
    """Status of a data source."""

    name: str
    description: str
    input_dir: str
    exists: bool
    file_count: int
    expected_count: int
    ready: bool
    message: str


class DataSourceManager:
    """
    Manages multiple data sources for cardiac imaging analysis.

    Provides unified access to data sources with automatic environment
    detection (WSL/Windows/Linux) and path conversion.
    """

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        config_dict: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize DataSourceManager.

        Args:
            config_path: Path to YAML configuration file
            config_dict: Configuration dictionary (alternative to file)
        """
        self._config: Dict[str, Any] = {}
        self._sources: Dict[str, DataSource] = {}
        self._environment: Optional[str] = None

        if config_dict:
            self._config = config_dict
        elif config_path:
            self._load_config(Path(config_path))

        if self._config:
            self._parse_sources()

    @classmethod
    def from_project(cls, project_name: str, search_dirs: Optional[list] = None) -> 'DataSourceManager':
        """
        Create manager by discovering a project's data_sources.yaml config.

        Searches for config/data_sources.yaml under common project locations.

        Args:
            project_name: Project directory name (e.g., 'my-project')
            search_dirs: Optional list of parent directories to search.
                         Defaults to ~/projects/

        Returns:
            DataSourceManager instance

        Raises:
            FileNotFoundError: If project config not found
        """
        if search_dirs is None:
            search_dirs = [Path.home() / 'projects']

        search_paths = []
        for parent in search_dirs:
            candidate = parent / project_name / 'config' / 'data_sources.yaml'
            search_paths.append(candidate)
            if candidate.exists():
                return cls(config_path=candidate)

        raise FileNotFoundError(
            f"Config not found for project '{project_name}'. "
            f"Searched: {[str(p) for p in search_paths]}"
        )

    def _load_config(self, config_path: Path) -> None:
        """Load configuration from YAML file."""
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f) or {}

    def _parse_sources(self) -> None:
        """Parse data sources from configuration."""
        sources_config = self._config.get('data_sources', {})

        for name, config in sources_config.items():
            # Resolve path based on environment
            input_dir = config.get('input_dir', '')
            if self.environment == 'windows' and config.get('input_dir_windows'):
                input_dir = config['input_dir_windows']

            self._sources[name] = DataSource(
                name=name,
                description=config.get('description', ''),
                type=config.get('type', 'nifti'),
                input_dir=input_dir,
                output_dir=config.get('output_dir', ''),
                file_pattern=config.get('file_pattern', '*.nii.gz'),
                file_filter=config.get('file_filter'),
                expected_count=config.get('expected_count', 0),
                notes=config.get('notes', ''),
                input_dir_windows=config.get('input_dir_windows'),
                dicom_source=config.get('dicom_source'),
                metadata=config.get('metadata', {}),
            )

    @property
    def environment(self) -> str:
        """Detect and cache runtime environment."""
        if self._environment is None:
            self._environment = self._detect_environment()
        return self._environment

    def _detect_environment(self) -> str:
        """Detect runtime environment (wsl, linux, windows)."""
        # Try cardiac-shared environment module first
        try:
            from cardiac_shared.environment import detect_runtime
            runtime = detect_runtime()
            if runtime.is_wsl:
                return 'wsl'
            elif runtime.os_name == 'Windows':
                return 'windows'
            else:
                return 'linux'
        except ImportError:
            pass

        # Fallback detection
        if os.path.exists('/mnt/c'):
            return 'wsl'
        elif os.name == 'nt':
            return 'windows'
        else:
            return 'linux'

    @property
    def default_source(self) -> str:
        """Get default data source name."""
        return self._config.get('default_source', 'default')

    def get_source(self, name: Optional[str] = None) -> DataSource:
        """
        Get data source by name.

        Args:
            name: Data source name. If None, returns default source.

        Returns:
            DataSource object

        Raises:
            ValueError: If source not found
        """
        if name is None:
            name = self.default_source

        if name not in self._sources:
            available = list(self._sources.keys())
            raise ValueError(f"Data source '{name}' not found. Available: {available}")

        return self._sources[name]

    def list_sources(self) -> Dict[str, DataSource]:
        """Return all data sources."""
        return self._sources.copy()

    def check_source(self, name: Optional[str] = None) -> DataSourceStatus:
        """
        Check data source availability and status.

        Args:
            name: Data source name

        Returns:
            DataSourceStatus object
        """
        source = self.get_source(name)

        exists = source.exists()
        file_count = source.file_count() if exists else 0
        ready = file_count > 0

        if ready:
            message = f"[OK] {file_count} files available"
        elif exists:
            message = f"[!] No matching files found (pattern: {source.file_pattern})"
        else:
            message = f"[X] Directory not found: {source.input_dir}"

        return DataSourceStatus(
            name=source.name,
            description=source.description,
            input_dir=source.input_dir,
            exists=exists,
            file_count=file_count,
            expected_count=source.expected_count,
            ready=ready,
            message=message,
        )

    def check_all_sources(self) -> Dict[str, DataSourceStatus]:
        """Check status of all data sources."""
        return {name: self.check_source(name) for name in self._sources}

    def print_status(self) -> None:
        """Print status of all data sources."""
        print("\n" + "=" * 60)
        print("Data Sources Status")
        print("=" * 60)

        for name in self._sources:
            status = self.check_source(name)
            is_default = " (default)" if name == self.default_source else ""

            print(f"\n[{name.upper()}]{is_default}")
            print(f"  Description: {status.description}")
            print(f"  Status:      {status.message}")
            if status.exists:
                print(f"  Files:       {status.file_count} / {status.expected_count} expected")

        print("\n" + "=" * 60)
        print(f"Environment: {self.environment}")
        print("=" * 60 + "\n")

    def __iter__(self) -> Iterator[DataSource]:
        """Iterate over data sources."""
        return iter(self._sources.values())

    def __len__(self) -> int:
        """Return number of data sources."""
        return len(self._sources)

    def __contains__(self, name: str) -> bool:
        """Check if data source exists."""
        return name in self._sources


# Convenience functions for simple usage
_default_manager: Optional[DataSourceManager] = None


def get_manager(config_path: Optional[str] = None) -> DataSourceManager:
    """Get or create default DataSourceManager."""
    global _default_manager
    if _default_manager is None or config_path:
        _default_manager = DataSourceManager(config_path=config_path)
    return _default_manager


def get_source(name: Optional[str] = None) -> DataSource:
    """Get data source from default manager."""
    return get_manager().get_source(name)


def list_sources() -> Dict[str, DataSource]:
    """List all data sources from default manager."""
    return get_manager().list_sources()
