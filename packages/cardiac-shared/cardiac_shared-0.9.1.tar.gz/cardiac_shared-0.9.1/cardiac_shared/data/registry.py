"""
Intermediate Results Registry
Cross-project data discovery and sharing for cardiac imaging projects

This module provides a central registry for discovering and accessing
intermediate processing results (TotalSegmentator masks, Stage 1 labels, etc.)
that can be shared across analysis modules.

Usage:
    from cardiac_shared.data import IntermediateResultsRegistry

    # Get singleton registry instance
    registry = IntermediateResultsRegistry()

    # Or use convenience function
    from cardiac_shared.data import get_registry
    registry = get_registry()

    # Discover available results
    if registry.exists('segmentation.totalsegmentator_organs.cohort_v2'):
        path = registry.get_path('segmentation.totalsegmentator_organs.cohort_v2')
        heart_mask = path / patient_id / 'heart.nii.gz'

    # List available results
    available = registry.list_available('segmentation')
    print(available)  # ['totalsegmentator_organs.cohort_v2', ...]

    # Get metadata
    meta = registry.get_metadata('body_composition.stage1_labels.cohort_v1')
    print(f"Patient count: {meta.get('patient_count')}")

Author: Cardiac ML Research Team
Created: 2026-01-02
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field

# Try to import yaml
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


@dataclass
class RegistryEntry:
    """
    Represents a single entry in the intermediate results registry
    """
    key: str
    path: Path
    source: Optional[str] = None
    version: Optional[str] = None
    status: str = "unknown"
    patient_count: Optional[int] = None
    date_created: Optional[str] = None
    consumers: List[str] = field(default_factory=list)
    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def exists(self) -> bool:
        """Check if the path exists"""
        return self.path.exists()


class IntermediateResultsRegistry:
    """
    Central registry for intermediate results discovery and sharing

    The registry loads configuration from intermediate_results_registry.yaml
    and provides methods to discover, validate, and access intermediate
    processing results across projects.

    Features:
    - Dot notation key access (e.g., 'segmentation.totalsegmentator_organs.chd_v2')
    - Automatic path conversion between Windows and WSL
    - Path existence validation
    - Metadata access (patient count, version, status, etc.)
    - Consumer tracking (which projects use each result)

    Example:
        >>> registry = IntermediateResultsRegistry()
        >>> registry.list_available('segmentation')
        ['totalsegmentator_organs.cohort_v2', ...]
        >>> registry.get_path('segmentation.totalsegmentator_organs.cohort_v2')
        PosixPath('/data/totalsegmentator/organs_cohort_v2')
    """

    # Default config locations (searched in order)
    DEFAULT_CONFIG_PATHS = [
        # Project-specific config
        "config/intermediate_results_registry.yaml",
        # Parent project config (for subprojects)
        "../config/intermediate_results_registry.yaml",
        # Home directory
        "~/.cardiac/intermediate_results_registry.yaml",
    ]

    def __init__(
        self,
        config_path: Optional[Union[str, Path]] = None,
        project_root: Optional[Union[str, Path]] = None,
        auto_convert_paths: bool = True,
    ):
        """
        Initialize the registry

        Args:
            config_path: Path to registry YAML config. If None, searches default locations.
            project_root: Project root directory. If None, auto-detected.
            auto_convert_paths: Automatically convert paths for current platform (WSL/Windows)
        """
        self.auto_convert_paths = auto_convert_paths
        self._entries: Dict[str, RegistryEntry] = {}
        self._config: Dict[str, Any] = {}

        # Detect project root
        if project_root is None:
            self.project_root = self._find_project_root()
        else:
            self.project_root = Path(project_root)

        # Load configuration
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = self._find_config()

        if self._config_path and self._config_path.exists():
            self._load_config()
        else:
            print(f"[!] Registry config not found. Searched: {self.DEFAULT_CONFIG_PATHS}")

    def _find_project_root(self) -> Path:
        """Find project root by looking for marker files"""
        markers = ['CLAUDE.md', 'pyproject.toml', '.git']
        current = Path.cwd()

        for _ in range(6):  # Check up to 6 levels
            for marker in markers:
                if (current / marker).exists():
                    return current
            if current.parent == current:
                break
            current = current.parent

        return Path.cwd()

    def _find_config(self) -> Optional[Path]:
        """Find registry config file from default locations"""
        for relative_path in self.DEFAULT_CONFIG_PATHS:
            # Handle home directory
            if relative_path.startswith("~"):
                config_path = Path(relative_path).expanduser()
            else:
                config_path = self.project_root / relative_path

            if config_path.exists():
                return config_path

        return None

    def _load_config(self) -> None:
        """Load and parse the registry configuration"""
        if not YAML_AVAILABLE:
            print("[!] PyYAML not installed, registry unavailable")
            return

        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

            # Get external root
            self._external_root = self._config.get('external_root', '')
            self._external_root_wsl = self._config.get('external_root_wsl', '')

            # Parse all entries
            self._parse_entries(self._config)

        except Exception as e:
            print(f"[X] Failed to load registry config: {e}")

    def _parse_entries(self, config: Dict, prefix: str = '') -> None:
        """
        Recursively parse config into registry entries

        Args:
            config: Configuration dictionary
            prefix: Current key prefix for dot notation
        """
        # Skip non-data keys
        skip_keys = {
            'registry_version', 'last_updated', 'external_root', 'external_root_wsl',
            'usage_patterns', 'dependencies', 'notes'
        }

        for key, value in config.items():
            if key in skip_keys:
                continue

            current_key = f"{prefix}.{key}" if prefix else key

            if isinstance(value, dict):
                # Check if this is a leaf entry (has 'path' key)
                if 'path' in value:
                    entry = self._create_entry(current_key, value)
                    self._entries[current_key] = entry
                else:
                    # Recurse into nested dict
                    self._parse_entries(value, current_key)

    def _create_entry(self, key: str, data: Dict) -> RegistryEntry:
        """Create a RegistryEntry from config data"""
        # Resolve path
        raw_path = data.get('path', '')
        resolved_path = self._resolve_path(raw_path)

        return RegistryEntry(
            key=key,
            path=resolved_path,
            source=data.get('source'),
            version=data.get('version'),
            status=data.get('status', 'unknown'),
            patient_count=data.get('patient_count'),
            date_created=data.get('date_created'),
            consumers=data.get('consumers', []),
            description=data.get('description'),
            metadata=data,
        )

    def _resolve_path(self, path: str) -> Path:
        """
        Resolve path with variable expansion and platform conversion

        Args:
            path: Path string (may contain ${external_root})

        Returns:
            Resolved Path object
        """
        # Expand ${external_root}
        if '${external_root}' in path:
            if self._is_wsl() and self.auto_convert_paths:
                path = path.replace('${external_root}', self._external_root_wsl)
            else:
                path = path.replace('${external_root}', self._external_root)
        elif not path.startswith('/') and not (len(path) > 1 and path[1] == ':'):
            # Relative path - prepend external root
            if self._is_wsl() and self.auto_convert_paths:
                path = f"{self._external_root_wsl}/{path}"
            else:
                path = f"{self._external_root}/{path}"

        # Convert Windows path to WSL if needed
        if self._is_wsl() and self.auto_convert_paths:
            path = self._windows_to_wsl(path)

        return Path(path)

    def _is_wsl(self) -> bool:
        """Check if running under WSL"""
        try:
            with open('/proc/version', 'r') as f:
                return 'microsoft' in f.read().lower()
        except:
            return False

    def _windows_to_wsl(self, path: str) -> str:
        """Convert Windows path to WSL path"""
        if len(path) > 1 and path[1] == ':':
            drive = path[0].lower()
            return f"/mnt/{drive}{path[2:].replace(chr(92), '/')}"
        return path

    def _wsl_to_windows(self, path: str) -> str:
        """Convert WSL path to Windows path"""
        if path.startswith('/mnt/') and len(path) > 6:
            drive = path[5].upper()
            return f"{drive}:{path[6:].replace('/', chr(92))}"
        return path

    # =========================================================================
    # Public API
    # =========================================================================

    def get_path(self, key: str) -> Optional[Path]:
        """
        Get path for a registered result using dot notation

        Args:
            key: Registry key (e.g., 'segmentation.totalsegmentator_organs.chd_v2')

        Returns:
            Path to the result directory, or None if not found
        """
        entry = self._entries.get(key)
        return entry.path if entry else None

    def exists(self, key: str) -> bool:
        """
        Check if a registered result exists on disk

        Args:
            key: Registry key

        Returns:
            True if entry exists in registry AND path exists on disk
        """
        entry = self._entries.get(key)
        return entry is not None and entry.exists

    def get_entry(self, key: str) -> Optional[RegistryEntry]:
        """
        Get full registry entry

        Args:
            key: Registry key

        Returns:
            RegistryEntry object or None
        """
        return self._entries.get(key)

    def get_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for a registered result

        Args:
            key: Registry key

        Returns:
            Metadata dictionary (empty if not found)
        """
        entry = self._entries.get(key)
        return entry.metadata if entry else {}

    def list_available(self, prefix: str = '') -> List[str]:
        """
        List available results matching prefix

        Args:
            prefix: Key prefix filter (e.g., 'segmentation' or 'body_composition')
                   Empty string returns all keys.

        Returns:
            List of matching registry keys
        """
        if not prefix:
            return list(self._entries.keys())

        return [
            key for key in self._entries.keys()
            if key.startswith(prefix)
        ]

    def list_existing(self, prefix: str = '') -> List[str]:
        """
        List results that exist on disk

        Args:
            prefix: Key prefix filter

        Returns:
            List of keys where the path exists
        """
        available = self.list_available(prefix)
        return [key for key in available if self.exists(key)]

    def find_consumers(self, key: str) -> List[str]:
        """
        Find projects that use this result

        Args:
            key: Registry key

        Returns:
            List of consumer project names
        """
        entry = self._entries.get(key)
        return entry.consumers if entry else []

    def get_usage_pattern(self, project: str) -> Dict[str, str]:
        """
        Get usage pattern for a project

        Args:
            project: Project or analysis module name

        Returns:
            Dictionary of input types to registry keys
        """
        patterns = self._config.get('usage_patterns', {})
        return patterns.get(project, {})

    def suggest_input(self, project: str, input_type: str, cohort: str = 'default') -> Optional[str]:
        """
        Suggest best input for a project

        Args:
            project: Project or analysis module name
            input_type: Input type (e.g., 'stage1_input', 'heart_masks')
            cohort: Cohort name for variable substitution

        Returns:
            Registry key for suggested input, or None
        """
        patterns = self.get_usage_pattern(project)
        pattern = patterns.get(input_type)

        if pattern:
            # Substitute variables
            return pattern.replace('{cohort}', cohort).replace('{dataset}', cohort)

        return None

    def validate(self) -> Dict[str, bool]:
        """
        Validate all registry entries (check if paths exist)

        Returns:
            Dictionary of key -> exists status
        """
        return {key: entry.exists for key, entry in self._entries.items()}

    def print_summary(self) -> None:
        """Print a summary of the registry"""
        print("=" * 70)
        print("Intermediate Results Registry")
        print("=" * 70)
        print(f"Config: {self._config_path}")
        print(f"Entries: {len(self._entries)}")
        print("-" * 70)

        # Group by top-level category
        categories: Dict[str, List[str]] = {}
        for key in self._entries:
            category = key.split('.')[0]
            if category not in categories:
                categories[category] = []
            categories[category].append(key)

        for category, keys in sorted(categories.items()):
            print(f"\n{category.upper()}:")
            for key in sorted(keys):
                entry = self._entries[key]
                status = "[OK]" if entry.exists else "[X]"
                count = f"({entry.patient_count} pts)" if entry.patient_count else ""
                print(f"  {status} {key} {count}")

        print("=" * 70)


# =========================================================================
# Singleton and convenience functions
# =========================================================================

_registry_instance: Optional[IntermediateResultsRegistry] = None


def get_registry(
    config_path: Optional[Union[str, Path]] = None,
    force_reload: bool = False,
) -> IntermediateResultsRegistry:
    """
    Get singleton registry instance

    Args:
        config_path: Optional path to config file
        force_reload: Force reload of configuration

    Returns:
        IntermediateResultsRegistry instance
    """
    global _registry_instance

    if _registry_instance is None or force_reload:
        _registry_instance = IntermediateResultsRegistry(config_path=config_path)

    return _registry_instance


# =========================================================================
# CLI interface
# =========================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Intermediate Results Registry')
    parser.add_argument('--config', '-c', help='Path to registry config')
    parser.add_argument('--list', '-l', action='store_true', help='List all entries')
    parser.add_argument('--validate', '-v', action='store_true', help='Validate all paths')
    parser.add_argument('--get', '-g', help='Get path for key')
    parser.add_argument('--prefix', '-p', default='', help='Filter prefix for --list')

    args = parser.parse_args()

    registry = IntermediateResultsRegistry(config_path=args.config)

    if args.list:
        keys = registry.list_available(args.prefix)
        for key in sorted(keys):
            entry = registry.get_entry(key)
            status = "[OK]" if entry and entry.exists else "[X]"
            print(f"{status} {key}")

    elif args.validate:
        results = registry.validate()
        ok = sum(1 for v in results.values() if v)
        total = len(results)
        print(f"Validation: {ok}/{total} paths exist")
        for key, exists in sorted(results.items()):
            status = "[OK]" if exists else "[X]"
            print(f"  {status} {key}")

    elif args.get:
        path = registry.get_path(args.get)
        if path:
            print(f"Path: {path}")
            print(f"Exists: {path.exists()}")
        else:
            print(f"Key not found: {args.get}")

    else:
        registry.print_summary()
