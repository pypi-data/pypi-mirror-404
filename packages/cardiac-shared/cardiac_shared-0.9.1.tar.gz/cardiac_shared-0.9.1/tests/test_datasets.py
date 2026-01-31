"""
Unit tests for Dataset Registry module (v0.8.0 - configuration-driven)

Tests the dataset registry framework with YAML configuration loading.
"""

import pytest
import tempfile
import os
from pathlib import Path
from cardiac_shared.data.datasets import (
    Dataset,
    DatasetStatus,
    DatasetCategory,
    SliceThickness,
    DatasetRegistry,
    get_dataset_registry,
    load_registry_from_yaml,
    get_dataset,
    get_patient_count,
    list_datasets,
)


# Sample YAML config for testing
SAMPLE_CONFIG = """
datasets:
  internal.chd:
    name: "CHD Group"
    description: "Test CHD dataset"
    patient_count: 100
    category: internal
    status: validated
    slice_thickness:
      thin: "1.0mm"
      thick: "5.0mm"
    group_tag: "chd"
    metadata:
      source: "Test"

  internal.normal:
    name: "Normal Group"
    patient_count: 50
    category: internal
    status: validated

  external.nlst:
    name: "NLST Dataset"
    patient_count: 200
    category: external
    status: completed
    slice_thickness:
      thin: "2.0mm"
      thick: "5.0mm"

  external.coca:
    name: "COCA Dataset"
    patient_count: 150
    category: external
    status: validated
"""


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(SAMPLE_CONFIG)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)


@pytest.fixture
def loaded_registry(temp_config_file):
    """Create a registry loaded from temp config"""
    return DatasetRegistry.from_yaml(temp_config_file)


class TestSliceThickness:
    """Tests for SliceThickness dataclass"""

    def test_slice_thickness_paired(self):
        st = SliceThickness(thin="1.0mm", thick="5.0mm")
        assert str(st) == "1.0mm + 5.0mm"

    def test_slice_thickness_thin_only(self):
        st = SliceThickness(thin="2.0mm")
        assert str(st) == "2.0mm"

    def test_slice_thickness_thick_only(self):
        st = SliceThickness(thick="5.0mm")
        assert str(st) == "5.0mm"

    def test_slice_thickness_none(self):
        st = SliceThickness()
        assert str(st) == "unknown"

    def test_from_dict(self):
        st = SliceThickness.from_dict({"thin": "1.0mm", "thick": "5.0mm"})
        assert st.thin == "1.0mm"
        assert st.thick == "5.0mm"

    def test_from_dict_none(self):
        st = SliceThickness.from_dict(None)
        assert st is None


class TestDataset:
    """Tests for Dataset dataclass"""

    def test_dataset_creation(self):
        ds = Dataset(
            id="test.dataset",
            name="Test Dataset",
            description="A test dataset",
            patient_count=100,
        )
        assert ds.id == "test.dataset"
        assert ds.patient_count == 100
        assert ds.category == DatasetCategory.INTERNAL
        assert ds.status == DatasetStatus.COMPLETED

    def test_dataset_is_paired(self):
        ds_paired = Dataset(
            id="test.paired",
            name="Paired",
            description="Paired dataset",
            patient_count=100,
            slice_thickness=SliceThickness(thin="1.0mm", thick="5.0mm"),
        )
        assert ds_paired.is_paired is True

        ds_single = Dataset(
            id="test.single",
            name="Single",
            description="Single thickness",
            patient_count=100,
            slice_thickness=SliceThickness(thin="1.0mm"),
        )
        assert ds_single.is_paired is False

    def test_from_dict(self):
        data = {
            "name": "Test",
            "patient_count": 100,
            "category": "external",
            "status": "validated",
            "slice_thickness": {"thin": "1.0mm"},
        }
        ds = Dataset.from_dict("test.id", data)
        assert ds.id == "test.id"
        assert ds.name == "Test"
        assert ds.patient_count == 100
        assert ds.category == DatasetCategory.EXTERNAL
        assert ds.status == DatasetStatus.VALIDATED


class TestDatasetRegistry:
    """Tests for DatasetRegistry class"""

    def test_empty_registry(self):
        registry = DatasetRegistry()
        assert len(registry) == 0
        assert registry.get("nonexistent") is None

    def test_register_dataset(self):
        registry = DatasetRegistry()
        ds = Dataset(id="test.ds", name="Test", patient_count=50)
        registry.register(ds)
        assert len(registry) == 1
        assert registry.get("test.ds") is not None
        assert registry.get("test.ds").patient_count == 50

    def test_unregister_dataset(self):
        registry = DatasetRegistry()
        ds = Dataset(id="test.ds", name="Test", patient_count=50)
        registry.register(ds)
        assert registry.unregister("test.ds") is True
        assert len(registry) == 0
        assert registry.unregister("nonexistent") is False

    def test_contains(self):
        registry = DatasetRegistry()
        ds = Dataset(id="test.ds", name="Test", patient_count=50)
        registry.register(ds)
        assert "test.ds" in registry
        assert "nonexistent" not in registry

    def test_getitem(self):
        registry = DatasetRegistry()
        ds = Dataset(id="test.ds", name="Test", patient_count=50)
        registry.register(ds)
        assert registry["test.ds"].patient_count == 50

    def test_getitem_keyerror(self):
        registry = DatasetRegistry()
        with pytest.raises(KeyError):
            _ = registry["nonexistent"]


class TestYAMLLoading:
    """Tests for YAML configuration loading"""

    def test_load_from_yaml(self, loaded_registry):
        assert len(loaded_registry) == 4
        assert loaded_registry.exists("internal.chd")
        assert loaded_registry.exists("internal.normal")
        assert loaded_registry.exists("external.nlst")
        assert loaded_registry.exists("external.coca")

    def test_patient_counts(self, loaded_registry):
        assert loaded_registry.get_patient_count("internal.chd") == 100
        assert loaded_registry.get_patient_count("internal.normal") == 50
        assert loaded_registry.get_patient_count("external.nlst") == 200
        assert loaded_registry.get_patient_count("external.coca") == 150

    def test_categories(self, loaded_registry):
        chd = loaded_registry.get("internal.chd")
        assert chd.category == DatasetCategory.INTERNAL

        nlst = loaded_registry.get("external.nlst")
        assert nlst.category == DatasetCategory.EXTERNAL

    def test_status(self, loaded_registry):
        chd = loaded_registry.get("internal.chd")
        assert chd.status == DatasetStatus.VALIDATED

        nlst = loaded_registry.get("external.nlst")
        assert nlst.status == DatasetStatus.COMPLETED

    def test_slice_thickness(self, loaded_registry):
        chd = loaded_registry.get("internal.chd")
        assert chd.slice_thickness is not None
        assert chd.slice_thickness.thin == "1.0mm"
        assert chd.slice_thickness.thick == "5.0mm"
        assert chd.is_paired is True

    def test_metadata(self, loaded_registry):
        chd = loaded_registry.get("internal.chd")
        assert chd.metadata.get("source") == "Test"

    def test_nonexistent_file(self):
        registry = DatasetRegistry.from_yaml("/nonexistent/path.yaml")
        assert len(registry) == 0

    def test_list_datasets(self, loaded_registry):
        all_ids = loaded_registry.list_datasets()
        assert len(all_ids) == 4

        internal = loaded_registry.list_datasets("internal")
        assert len(internal) == 2
        assert "internal.chd" in internal

        external = loaded_registry.list_datasets("external")
        assert len(external) == 2
        assert "external.nlst" in external

    def test_get_total_patients(self, loaded_registry):
        total = loaded_registry.get_total_patients(["internal.chd", "internal.normal"])
        assert total == 150

    def test_get_by_category(self, loaded_registry):
        internal = loaded_registry.get_by_category(DatasetCategory.INTERNAL)
        assert len(internal) == 2

        external = loaded_registry.get_by_category(DatasetCategory.EXTERNAL)
        assert len(external) == 2

    def test_get_by_status(self, loaded_registry):
        validated = loaded_registry.get_by_status(DatasetStatus.VALIDATED)
        assert len(validated) == 3  # chd, normal, coca

        completed = loaded_registry.get_by_status(DatasetStatus.COMPLETED)
        assert len(completed) == 1  # nlst

    def test_summary(self, loaded_registry):
        summary = loaded_registry.summary()
        assert "internal" in summary
        assert "external" in summary
        assert "grand_total" in summary


class TestGlobalRegistry:
    """Tests for global registry functions"""

    def test_get_dataset_registry_empty(self):
        # Reset global registry
        import cardiac_shared.data.datasets as ds_module
        ds_module._registry_instance = None

        registry = get_dataset_registry()
        assert len(registry) == 0

    def test_load_registry_from_yaml(self, temp_config_file):
        # Reset global registry
        import cardiac_shared.data.datasets as ds_module
        ds_module._registry_instance = None

        registry = load_registry_from_yaml(temp_config_file)
        assert len(registry) == 4

        # Verify global registry is updated
        assert get_dataset_registry() is registry

    def test_convenience_functions(self, temp_config_file):
        # Reset and load
        import cardiac_shared.data.datasets as ds_module
        ds_module._registry_instance = None
        load_registry_from_yaml(temp_config_file)

        ds = get_dataset("internal.chd")
        assert ds is not None
        assert ds.patient_count == 100

        count = get_patient_count("internal.chd")
        assert count == 100

        datasets = list_datasets("internal")
        assert "internal.chd" in datasets


class TestEmptyRegistry:
    """Tests for empty registry behavior"""

    def test_empty_print_summary(self, capsys):
        registry = DatasetRegistry()
        registry.print_summary()
        captured = capsys.readouterr()
        assert "No datasets loaded" in captured.out

    def test_empty_summary(self):
        registry = DatasetRegistry()
        summary = registry.summary()
        assert summary["grand_total"]["datasets"] == 0
        assert summary["grand_total"]["validated"] == 0
