"""
Tests for cardiac_shared.data.registry module
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from cardiac_shared.data import IntermediateResultsRegistry, RegistryEntry, get_registry


class TestRegistryEntry:
    """Test RegistryEntry dataclass"""

    def test_entry_creation(self):
        """Test creating a registry entry"""
        entry = RegistryEntry(
            key="test.entry",
            path=Path("/tmp/test"),
            source="test_source",
            version="1.0",
            status="complete",
            patient_count=100,
        )
        assert entry.key == "test.entry"
        assert entry.path == Path("/tmp/test")
        assert entry.patient_count == 100

    def test_entry_exists_false(self):
        """Test exists property for non-existent path"""
        entry = RegistryEntry(
            key="test.entry",
            path=Path("/nonexistent/path/12345"),
        )
        assert entry.exists is False

    def test_entry_exists_true(self):
        """Test exists property for existing path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            entry = RegistryEntry(
                key="test.entry",
                path=Path(tmpdir),
            )
            assert entry.exists is True


class TestIntermediateResultsRegistry:
    """Test IntermediateResultsRegistry class"""

    @pytest.fixture
    def sample_config(self):
        """Create a sample registry config"""
        return {
            'registry_version': '1.0',
            'external_root': '/tmp/test_external',
            'external_root_wsl': '/tmp/test_external',
            'segmentation': {
                'totalsegmentator_organs': {
                    'chd_v2': {
                        'path': 'intermediate_results/totalsegmentator/organs_chd_v2',
                        'source': 'converted.nifti.chd',
                        'version': 'TotalSegmentator 2.4.0',
                        'patient_count': 253,
                        'status': 'complete',
                        'consumers': ['pcfa', 'vbca'],
                    }
                }
            },
            'body_composition': {
                'vbca_stage1_labels': {
                    'zal_v3.2': {
                        'path': 'intermediate_results/zal_processing/stage1_labels',
                        'source': 'segmentation.totalsegmentator_organs.zal_120case',
                        'version': 'vbca 3.2',
                        'patient_count': 112,
                        'status': 'complete',
                    }
                }
            },
            'usage_patterns': {
                'vbca': {
                    'stage1_input': 'converted.nifti.{cohort}',
                    'totalsegmentator_organs': 'segmentation.totalsegmentator_organs.{cohort}',
                },
                'pcfa': {
                    'heart_masks': 'segmentation.totalsegmentator_organs.{cohort}',
                }
            }
        }

    @pytest.fixture
    def registry_with_config(self, sample_config):
        """Create a registry with sample config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / 'test_registry.yaml'
            with open(config_path, 'w') as f:
                yaml.dump(sample_config, f)

            registry = IntermediateResultsRegistry(
                config_path=config_path,
                auto_convert_paths=False,
            )
            yield registry

    def test_registry_init_no_config(self):
        """Test registry initialization without config"""
        # Should not raise, just warn
        registry = IntermediateResultsRegistry(
            config_path="/nonexistent/config.yaml"
        )
        assert len(registry._entries) == 0

    def test_list_available(self, registry_with_config):
        """Test listing available entries"""
        available = registry_with_config.list_available()
        assert 'segmentation.totalsegmentator_organs.chd_v2' in available
        assert 'body_composition.vbca_stage1_labels.zal_v3.2' in available

    def test_list_available_with_prefix(self, registry_with_config):
        """Test listing with prefix filter"""
        segmentation = registry_with_config.list_available('segmentation')
        assert len(segmentation) == 1
        assert 'segmentation.totalsegmentator_organs.chd_v2' in segmentation

    def test_get_path(self, registry_with_config):
        """Test getting path for an entry"""
        path = registry_with_config.get_path('segmentation.totalsegmentator_organs.chd_v2')
        assert path is not None
        assert 'organs_chd_v2' in str(path)

    def test_get_path_not_found(self, registry_with_config):
        """Test getting path for non-existent entry"""
        path = registry_with_config.get_path('nonexistent.key')
        assert path is None

    def test_get_entry(self, registry_with_config):
        """Test getting full entry"""
        entry = registry_with_config.get_entry('segmentation.totalsegmentator_organs.chd_v2')
        assert entry is not None
        assert entry.patient_count == 253
        assert entry.status == 'complete'
        assert 'pcfa' in entry.consumers

    def test_get_metadata(self, registry_with_config):
        """Test getting metadata"""
        meta = registry_with_config.get_metadata('segmentation.totalsegmentator_organs.chd_v2')
        assert meta.get('patient_count') == 253
        assert meta.get('version') == 'TotalSegmentator 2.4.0'

    def test_find_consumers(self, registry_with_config):
        """Test finding consumers"""
        consumers = registry_with_config.find_consumers('segmentation.totalsegmentator_organs.chd_v2')
        assert 'pcfa' in consumers
        assert 'vbca' in consumers

    def test_get_usage_pattern(self, registry_with_config):
        """Test getting usage pattern"""
        pattern = registry_with_config.get_usage_pattern('vbca')
        assert 'stage1_input' in pattern
        assert pattern['stage1_input'] == 'converted.nifti.{cohort}'

    def test_suggest_input(self, registry_with_config):
        """Test input suggestion"""
        suggestion = registry_with_config.suggest_input('pcfa', 'heart_masks', 'chd')
        assert suggestion == 'segmentation.totalsegmentator_organs.chd'

    def test_validate(self, registry_with_config):
        """Test validation"""
        results = registry_with_config.validate()
        # All paths should not exist (using /tmp/test_external which doesn't exist)
        assert all(v is False for v in results.values())


class TestGetRegistry:
    """Test get_registry convenience function"""

    def test_singleton(self):
        """Test singleton pattern"""
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2

    def test_force_reload(self):
        """Test force reload creates new instance"""
        reg1 = get_registry()
        reg2 = get_registry(force_reload=True)
        assert reg1 is not reg2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
