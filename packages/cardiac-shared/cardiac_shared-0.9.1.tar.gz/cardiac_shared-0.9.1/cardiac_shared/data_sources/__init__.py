"""
Data Sources Module for Cardiac Imaging Analysis

Provides unified data source management across projects.

Usage:
    from cardiac_shared.data_sources import DataSourceManager, DataSource

    # Initialize with config file
    manager = DataSourceManager('/path/to/config.yaml')

    # Or use project auto-discovery
    manager = DataSourceManager.from_project('my-project')

    # Get a specific data source
    source = manager.get_source('default')
    for file in source.get_files():
        print(f"Processing: {file}")

    # Check status
    manager.print_status()
"""

from .manager import (
    DataSource,
    DataSourceManager,
    DataSourceStatus,
    get_manager,
    get_source,
    list_sources,
)

__all__ = [
    'DataSource',
    'DataSourceManager',
    'DataSourceStatus',
    'get_manager',
    'get_source',
    'list_sources',
]
