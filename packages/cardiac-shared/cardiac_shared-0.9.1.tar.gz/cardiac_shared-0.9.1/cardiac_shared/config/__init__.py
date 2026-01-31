"""
Configuration Management Module

YAML-based configuration management for medical imaging pipelines.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import os


class ConfigManager:
    """
    YAML configuration manager

    Features:
    - Load configuration from YAML files
    - Environment variable substitution
    - Default values
    - Nested key access

    Example:
        config = ConfigManager("config/settings.yaml")
        db_host = config.get("database.host", default="localhost")
        config.set("database.port", 5432)
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialize config manager

        Args:
            config_file: Path to YAML configuration file
        """
        self.config_file = Path(config_file) if config_file else None
        self._config: Dict[str, Any] = {}

        if self.config_file:
            self._load()

    def _load(self):
        """Load configuration from file"""
        if self.config_file and self.config_file.exists():
            try:
                import yaml
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except ImportError:
                # Fallback to JSON if PyYAML not available
                import json
                if self.config_file.suffix == '.json':
                    with open(self.config_file, 'r', encoding='utf-8') as f:
                        self._config = json.load(f)
            except Exception:
                self._config = {}

    def save(self, config_file: Optional[Path] = None):
        """Save configuration to file"""
        file_path = config_file or self.config_file
        if file_path:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                import yaml
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self._config, f, default_flow_style=False)
            except ImportError:
                import json
                with open(file_path.with_suffix('.json'), 'w', encoding='utf-8') as f:
                    json.dump(self._config, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Dot-notation key (e.g., "database.host")
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        # Environment variable substitution
        if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
            env_key = value[2:-1]
            return os.environ.get(env_key, default)

        return value

    def set(self, key: str, value: Any):
        """
        Set configuration value by dot-notation key

        Args:
            key: Dot-notation key
            value: Value to set
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()

    def update(self, data: Dict[str, Any]):
        """Update configuration with dictionary"""
        self._deep_update(self._config, data)

    def _deep_update(self, base: Dict, updates: Dict):
        """Deep merge dictionaries"""
        for key, value in updates.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_update(base[key], value)
            else:
                base[key] = value


def load_config(config_file: Path, defaults: Optional[Dict] = None) -> ConfigManager:
    """
    Load configuration with defaults

    Args:
        config_file: Path to config file
        defaults: Default configuration values

    Returns:
        ConfigManager instance
    """
    config = ConfigManager(config_file)
    if defaults:
        # Apply defaults for missing keys
        for key, value in defaults.items():
            if config.get(key) is None:
                config.set(key, value)
    return config


__all__ = ['ConfigManager', 'load_config']
