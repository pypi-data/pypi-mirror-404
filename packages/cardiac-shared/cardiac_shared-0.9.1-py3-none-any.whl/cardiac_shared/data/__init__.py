"""
Data management module for cardiac imaging projects

Provides:
- IntermediateResultsRegistry: Cross-project data discovery and sharing
- BatchManager: Batch processing with manifest tracking
- BatchManifest: Manifest data structure for batch outputs
- BatchDiscovery: Dynamic batch discovery and selection (v0.6.4)
- DatasetRegistry: Unified dataset definitions with patient counts (v0.8.0)
- PairedDatasetLoader: Paired thin/thick slice dataset management (v0.9.0)
"""

from .registry import (
    IntermediateResultsRegistry,
    RegistryEntry,
    get_registry,
)

from .batch_manager import (
    BatchManager,
    BatchManifest,
    PatientEntry,
    ConsumerRecord,
    create_nifti_batch,
    load_batch,
)

from .batch_discovery import (
    BatchDiscovery,
    BatchInfo,
    PatientBatchRecord,
    discover_batches,
)

from .datasets import (
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
    print_dataset_summary,
)

from .paired_dataset import (
    PairedSample,
    PairedDatasetConfig,
    PairedDatasetLoader,
)

__all__ = [
    # Registry
    'IntermediateResultsRegistry',
    'RegistryEntry',
    'get_registry',
    # Batch Manager
    'BatchManager',
    'BatchManifest',
    'PatientEntry',
    'ConsumerRecord',
    'create_nifti_batch',
    'load_batch',
    # Batch Discovery (v0.6.4)
    'BatchDiscovery',
    'BatchInfo',
    'PatientBatchRecord',
    'discover_batches',
    # Dataset Registry (v0.8.0 - configuration-driven)
    'Dataset',
    'DatasetStatus',
    'DatasetCategory',
    'SliceThickness',
    'DatasetRegistry',
    'get_dataset_registry',
    'load_registry_from_yaml',
    'get_dataset',
    'get_patient_count',
    'list_datasets',
    'print_dataset_summary',
    # Paired Dataset (v0.9.0)
    'PairedSample',
    'PairedDatasetConfig',
    'PairedDatasetLoader',
]
