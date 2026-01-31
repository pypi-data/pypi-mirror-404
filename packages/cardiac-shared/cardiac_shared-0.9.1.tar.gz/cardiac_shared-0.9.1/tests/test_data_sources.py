"""
Unit tests for data_sources module
"""

import pytest
import tempfile
from pathlib import Path
import yaml

from cardiac_shared.data_sources import (
    DataSourceManager,
    DataSource,
    DataSourceStatus,
)


class TestDataSource:
    """Tests for DataSource class."""

    def test_data_source_creation(self):
        """Test DataSource creation."""
        source = DataSource(
            name='test',
            description='Test source',
            type='nifti',
            input_dir='/tmp/test',
            output_dir='/tmp/output',
        )

        assert source.name == 'test'
        assert source.description == 'Test source'
        assert source.type == 'nifti'

    def test_data_source_path_properties(self):
        """Test path properties."""
        source = DataSource(
            name='test',
            description='',
            type='nifti',
            input_dir='/tmp/test',
            output_dir='/tmp/output',
        )

        assert source.input_path == Path('/tmp/test')
        assert source.output_path == Path('/tmp/output')

    def test_data_source_exists(self):
        """Test exists() method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            source = DataSource(
                name='test',
                description='',
                type='nifti',
                input_dir=tmpdir,
                output_dir=tmpdir,
            )
            assert source.exists() is True

            # Non-existent directory
            source2 = DataSource(
                name='test2',
                description='',
                type='nifti',
                input_dir='/nonexistent/path',
                output_dir='/tmp',
            )
            assert source2.exists() is False

    def test_data_source_to_dict(self):
        """Test to_dict() method."""
        source = DataSource(
            name='test',
            description='Test',
            type='nifti',
            input_dir='/tmp/in',
            output_dir='/tmp/out',
            expected_count=100,
        )

        d = source.to_dict()
        assert d['name'] == 'test'
        assert d['expected_count'] == 100


class TestDataSourceManager:
    """Tests for DataSourceManager class."""

    def test_manager_from_dict(self):
        """Test manager creation from dict."""
        config = {
            'default_source': 'test',
            'data_sources': {
                'test': {
                    'description': 'Test source',
                    'type': 'nifti',
                    'input_dir': '/tmp/test',
                    'output_dir': '/tmp/output',
                }
            }
        }

        manager = DataSourceManager(config_dict=config)
        assert len(manager) == 1
        assert 'test' in manager

    def test_manager_from_yaml(self):
        """Test manager creation from YAML file."""
        config = {
            'default_source': 'test',
            'data_sources': {
                'test': {
                    'description': 'Test source',
                    'type': 'nifti',
                    'input_dir': '/tmp/test',
                    'output_dir': '/tmp/output',
                }
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config, f)
            yaml_path = f.name

        try:
            manager = DataSourceManager(config_path=yaml_path)
            assert len(manager) == 1
        finally:
            Path(yaml_path).unlink()

    def test_manager_get_source(self):
        """Test get_source method."""
        config = {
            'default_source': 'test1',
            'data_sources': {
                'test1': {
                    'description': 'Test 1',
                    'type': 'nifti',
                    'input_dir': '/tmp/test1',
                    'output_dir': '/tmp/out1',
                },
                'test2': {
                    'description': 'Test 2',
                    'type': 'nifti',
                    'input_dir': '/tmp/test2',
                    'output_dir': '/tmp/out2',
                }
            }
        }

        manager = DataSourceManager(config_dict=config)

        # Get by name
        source = manager.get_source('test1')
        assert source.name == 'test1'

        # Get default
        source = manager.get_source()
        assert source.name == 'test1'

        # Error on unknown
        with pytest.raises(ValueError):
            manager.get_source('unknown')

    def test_manager_list_sources(self):
        """Test list_sources method."""
        config = {
            'data_sources': {
                'test1': {'description': '', 'type': 'nifti', 'input_dir': '/a', 'output_dir': '/b'},
                'test2': {'description': '', 'type': 'nifti', 'input_dir': '/c', 'output_dir': '/d'},
            }
        }

        manager = DataSourceManager(config_dict=config)
        sources = manager.list_sources()

        assert len(sources) == 2
        assert 'test1' in sources
        assert 'test2' in sources

    def test_manager_iteration(self):
        """Test iteration over manager."""
        config = {
            'data_sources': {
                'test1': {'description': '', 'type': 'nifti', 'input_dir': '/a', 'output_dir': '/b'},
                'test2': {'description': '', 'type': 'nifti', 'input_dir': '/c', 'output_dir': '/d'},
            }
        }

        manager = DataSourceManager(config_dict=config)

        names = [s.name for s in manager]
        assert len(names) == 2

    def test_manager_check_source(self):
        """Test check_source method."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = {
                'data_sources': {
                    'test': {
                        'description': 'Test source',
                        'type': 'nifti',
                        'input_dir': tmpdir,
                        'output_dir': tmpdir,
                        'expected_count': 10,
                    }
                }
            }

            manager = DataSourceManager(config_dict=config)
            status = manager.check_source('test')

            assert status.name == 'test'
            assert status.exists is True
            assert status.file_count == 0
            assert status.expected_count == 10


class TestImports:
    """Test module imports."""

    def test_import_from_main_module(self):
        """Test importing from cardiac_shared."""
        from cardiac_shared import (
            DataSourceManager,
            DataSource,
            DataSourceStatus,
            get_source,
            list_sources,
        )

        assert DataSourceManager is not None
        assert DataSource is not None
