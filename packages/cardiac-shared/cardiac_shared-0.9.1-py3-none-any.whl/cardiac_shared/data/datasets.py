"""
Dataset Registry - Configuration-driven dataset definitions for cardiac imaging research

This module provides a framework for managing dataset definitions. Dataset information
is loaded from YAML configuration files, NOT hardcoded in the package.

This approach:
- Keeps internal/private data out of PyPI
- Allows easy updates without package releases
- Supports project-specific configurations

Usage:
    from cardiac_shared.data import DatasetRegistry

    # Load from YAML configuration
    registry = DatasetRegistry.from_yaml("config/datasets_registry.yaml")

    # Or register datasets programmatically
    registry = DatasetRegistry()
    registry.register(Dataset(
        id="internal.chd",
        name="CHD Group",
        patient_count=489,
        ...
    ))

    # Get dataset info
    chd = registry.get("internal.chd")
    print(f"CHD patients: {chd.patient_count}")

Author: Cardiac ML Research Team
Created: 2026-01-04
Version: 0.8.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import Enum
import yaml
import logging

logger = logging.getLogger(__name__)


class DatasetStatus(Enum):
    """Dataset processing status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VALIDATED = "validated"
    ARCHIVED = "archived"


class DatasetCategory(Enum):
    """Dataset category"""
    INTERNAL = "internal"  # Private/institutional data
    EXTERNAL = "external"  # Public datasets (NLST, COCA, etc.)
    FUTURE = "future"      # Planned datasets


@dataclass
class SliceThickness:
    """Slice thickness configuration for paired scans"""
    thin: Optional[str] = None  # e.g., "1.0mm", "1.5mm", "2.0mm"
    thick: Optional[str] = None  # e.g., "5.0mm"

    def __str__(self) -> str:
        if self.thin and self.thick:
            return f"{self.thin} + {self.thick}"
        return self.thin or self.thick or "unknown"

    @classmethod
    def from_dict(cls, data: Optional[Dict]) -> Optional["SliceThickness"]:
        """Create from dictionary"""
        if not data:
            return None
        return cls(
            thin=data.get("thin"),
            thick=data.get("thick")
        )


@dataclass
class Dataset:
    """
    Dataset definition with patient count and metadata

    Attributes:
        id: Unique dataset identifier (e.g., 'internal.chd', 'nlst.batch1')
        name: Human-readable name
        description: Dataset description
        patient_count: Number of patients (authoritative count)
        category: Dataset category (internal/external/future)
        status: Processing status
        slice_thickness: Slice thickness configuration
        metadata: Additional metadata
    """
    id: str
    name: str
    description: str = ""
    patient_count: int = 0
    category: DatasetCategory = DatasetCategory.INTERNAL
    status: DatasetStatus = DatasetStatus.COMPLETED
    slice_thickness: Optional[SliceThickness] = None
    group_tag: Optional[str] = None
    root_dir: Optional[str] = None
    results_dir: Optional[str] = None
    metadata_index: Optional[str] = None
    notes: Optional[str] = None
    sub_batches: Optional[List[str]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_paired(self) -> bool:
        """Check if dataset has paired thin/thick scans"""
        return self.slice_thickness is not None and \
               self.slice_thickness.thin is not None and \
               self.slice_thickness.thick is not None

    @classmethod
    def from_dict(cls, dataset_id: str, data: Dict[str, Any]) -> "Dataset":
        """Create Dataset from dictionary (YAML parsing)"""
        # Parse category
        category_str = data.get("category", "internal").lower()
        try:
            category = DatasetCategory(category_str)
        except ValueError:
            category = DatasetCategory.INTERNAL

        # Parse status
        status_str = data.get("status", "completed").lower()
        try:
            status = DatasetStatus(status_str)
        except ValueError:
            status = DatasetStatus.COMPLETED

        # Parse slice thickness
        slice_data = data.get("slice_thickness")
        slice_thickness = SliceThickness.from_dict(slice_data) if slice_data else None

        return cls(
            id=dataset_id,
            name=data.get("name", dataset_id),
            description=data.get("description", ""),
            patient_count=data.get("patient_count", 0),
            category=category,
            status=status,
            slice_thickness=slice_thickness,
            group_tag=data.get("group_tag"),
            root_dir=data.get("root_dir"),
            results_dir=data.get("results_dir"),
            metadata_index=data.get("metadata_index"),
            notes=data.get("notes"),
            sub_batches=data.get("sub_batches"),
            metadata=data.get("metadata", {}),
        )


class DatasetRegistry:
    """
    Central registry for dataset definitions

    Provides unified access to dataset definitions. Datasets are loaded
    from YAML configuration files, keeping sensitive data out of the
    public PyPI package.

    Example:
        # Load from YAML
        registry = DatasetRegistry.from_yaml("config/datasets.yaml")

        # Get dataset
        chd = registry.get("internal.chd")

        # Print summary
        registry.print_summary()
    """

    def __init__(self):
        self._datasets: Dict[str, Dataset] = {}
        self._config_path: Optional[Path] = None

    @classmethod
    def from_yaml(cls, config_path: Union[str, Path]) -> "DatasetRegistry":
        """
        Load registry from YAML configuration file

        Args:
            config_path: Path to YAML configuration file

        Returns:
            DatasetRegistry with loaded datasets

        Example YAML format:
            datasets:
              internal.chd:
                name: "CHD Group"
                patient_count: 489
                category: internal
                status: validated
              nlst.all:
                name: "NLST Dataset"
                patient_count: 857
                category: external
        """
        registry = cls()
        registry._config_path = Path(config_path)

        if not registry._config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return registry

        with open(registry._config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if not config:
            logger.warning(f"Empty config file: {config_path}")
            return registry

        # Load datasets section
        datasets_config = config.get("datasets", {})
        for dataset_id, dataset_data in datasets_config.items():
            try:
                dataset = Dataset.from_dict(dataset_id, dataset_data)
                registry._datasets[dataset_id] = dataset
            except Exception as e:
                logger.error(f"Error loading dataset {dataset_id}: {e}")

        logger.info(f"Loaded {len(registry._datasets)} datasets from {config_path}")
        return registry

    def register(self, dataset: Dataset) -> None:
        """Register a dataset programmatically"""
        self._datasets[dataset.id] = dataset

    def unregister(self, dataset_id: str) -> bool:
        """Unregister a dataset"""
        if dataset_id in self._datasets:
            del self._datasets[dataset_id]
            return True
        return False

    def get(self, dataset_id: str) -> Optional[Dataset]:
        """Get dataset by ID"""
        return self._datasets.get(dataset_id)

    def __getitem__(self, dataset_id: str) -> Dataset:
        """Get dataset by ID (raises KeyError if not found)"""
        return self._datasets[dataset_id]

    def __len__(self) -> int:
        """Get number of registered datasets"""
        return len(self._datasets)

    def __contains__(self, dataset_id: str) -> bool:
        """Check if dataset exists"""
        return dataset_id in self._datasets

    def exists(self, dataset_id: str) -> bool:
        """Check if dataset exists"""
        return dataset_id in self._datasets

    def list_datasets(self, category: Optional[str] = None) -> List[str]:
        """
        List all dataset IDs, optionally filtered by category prefix

        Args:
            category: Filter by category prefix (e.g., 'internal', 'nlst', 'coca')
        """
        if category:
            return [k for k in self._datasets.keys() if k.startswith(f"{category}.")]
        return list(self._datasets.keys())

    def get_patient_count(self, dataset_id: str) -> int:
        """Get patient count for a dataset"""
        dataset = self.get(dataset_id)
        return dataset.patient_count if dataset else 0

    def get_total_patients(self, dataset_ids: List[str]) -> int:
        """Get total patient count for multiple datasets"""
        return sum(self.get_patient_count(did) for did in dataset_ids)

    def get_by_category(self, category: DatasetCategory) -> List[Dataset]:
        """Get all datasets in a category"""
        return [d for d in self._datasets.values() if d.category == category]

    def get_by_status(self, status: DatasetStatus) -> List[Dataset]:
        """Get all datasets with a specific status"""
        return [d for d in self._datasets.values() if d.status == status]

    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        internal_datasets = self.get_by_category(DatasetCategory.INTERNAL)
        external_datasets = self.get_by_category(DatasetCategory.EXTERNAL)

        internal_total = sum(d.patient_count for d in internal_datasets)
        external_total = sum(d.patient_count for d in external_datasets)

        # Try to get specific counts if datasets exist
        internal_summary = {"total": internal_total}
        for ds in internal_datasets:
            # Use last part of ID as key (e.g., "internal.chd" -> "chd")
            key = ds.id.split(".")[-1] if "." in ds.id else ds.id
            if key != "all":  # Don't duplicate "all" count
                internal_summary[key] = ds.patient_count

        external_summary = {}
        for ds in external_datasets:
            key = ds.id.split(".")[0] if "." in ds.id else ds.id
            if key not in external_summary:
                # Find the ".all" dataset or sum up
                all_ds = self.get(f"{key}.all")
                if all_ds:
                    external_summary[key] = all_ds.patient_count
                else:
                    external_summary[key] = ds.patient_count

        validated_total = sum(
            d.patient_count for d in self._datasets.values()
            if d.status in (DatasetStatus.VALIDATED, DatasetStatus.COMPLETED)
            and not d.sub_batches  # Don't double count
        )

        return {
            "internal": internal_summary,
            "external": external_summary,
            "grand_total": {
                "datasets": len(self._datasets),
                "validated": validated_total,
            }
        }

    def print_summary(self) -> None:
        """Print formatted summary"""
        print("=" * 60)
        print("CARDIAC IMAGING DATASET REGISTRY")
        print("=" * 60)

        if not self._datasets:
            print("\n[No datasets loaded]")
            print("Use DatasetRegistry.from_yaml('config/datasets.yaml') to load")
            print("=" * 60)
            return

        if self._config_path:
            print(f"Config: {self._config_path}")

        internal = self.get_by_category(DatasetCategory.INTERNAL)
        external = self.get_by_category(DatasetCategory.EXTERNAL)

        if internal:
            print("\nInternal Datasets:")
            for ds in internal:
                if not ds.sub_batches:  # Skip aggregate datasets
                    print(f"  {ds.name}: {ds.patient_count:>5} patients")

        if external:
            print("\nExternal Datasets:")
            for ds in external:
                if not ds.sub_batches:
                    status = f" ({ds.status.value})" if ds.status != DatasetStatus.COMPLETED else ""
                    print(f"  {ds.name}: {ds.patient_count:>5} patients{status}")

        s = self.summary()
        print(f"\nTotal: {s['grand_total']['datasets']} datasets, "
              f"{s['grand_total']['validated']} patients (validated)")
        print("=" * 60)


# Singleton instance (empty by default)
_registry_instance: Optional[DatasetRegistry] = None


def get_dataset_registry() -> DatasetRegistry:
    """
    Get the global registry instance

    Note: The registry is empty by default. Use load_registry_from_yaml()
    or registry.from_yaml() to load dataset definitions.
    """
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = DatasetRegistry()
    return _registry_instance


def load_registry_from_yaml(config_path: Union[str, Path]) -> DatasetRegistry:
    """
    Load the global registry from a YAML configuration file

    Args:
        config_path: Path to YAML configuration file

    Returns:
        The global DatasetRegistry instance with loaded datasets
    """
    global _registry_instance
    _registry_instance = DatasetRegistry.from_yaml(config_path)
    return _registry_instance


def get_dataset(dataset_id: str) -> Optional[Dataset]:
    """Get dataset by ID from global registry"""
    return get_dataset_registry().get(dataset_id)


def get_patient_count(dataset_id: str) -> int:
    """Get patient count for a dataset from global registry"""
    return get_dataset_registry().get_patient_count(dataset_id)


def list_datasets(category: Optional[str] = None) -> List[str]:
    """List all dataset IDs from global registry"""
    return get_dataset_registry().list_datasets(category)


def print_dataset_summary() -> None:
    """Print dataset summary from global registry"""
    get_dataset_registry().print_summary()
