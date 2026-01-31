"""
Cardiac Shared - Common utilities for cardiac imaging projects

This package provides shared IO, hardware detection, environment detection,
parallel processing, progress tracking, caching, configuration management,
data registry, data sources, vertebra detection, tissue classification,
batch management, and preprocessing pipelines for cardiac imaging analysis
across multiple projects.

Modules:
- io: DICOM, NIfTI, and ZIP file handling
- hardware: Hardware detection and CPU optimization
- environment: Runtime environment detection
- parallel: Parallel processing with checkpoint support
- progress: Multi-level progress tracking
- cache: Result caching with resume capability
- batch: Batch processing framework
- config: YAML configuration management
- data: Intermediate results registry, batch management, paired dataset (v0.9.0)
- data_sources: Multi-source data management
- vertebra: Vertebra detection and ROI calculation
- tissue: Tissue classification and HU filtering (SAT, VAT, IMAT)
- preprocessing: DICOM conversion, TotalSegmentator pipelines, thickness detection (v0.9.0)
"""

__version__ = "0.9.1"

# IO modules
from cardiac_shared.io.dicom import read_dicom_series, get_dicom_metadata
from cardiac_shared.io.nifti import load_nifti, save_nifti
from cardiac_shared.io.zip_handler import extract_zip, find_dicom_root
from cardiac_shared.io.preloader import AsyncNiftiPreloader, preload_nifti_batch

# Hardware detection
from cardiac_shared.hardware import (
    detect_hardware,
    HardwareInfo,
    GPUInfo,
    CPUInfo,
    RAMInfo,
    print_hardware_summary,
    get_optimal_config,
    CPUOptimizer,
    get_cpu_optimizer,
    apply_cpu_optimizations,
    # GPU utilities (v0.5.1)
    get_recommended_gpu_stabilization_time,
    get_gpu_performance_tier,
)

# Environment detection
from cardiac_shared.environment import (
    detect_runtime,
    RuntimeEnvironment,
    detect_colab,
    detect_wsl,
    print_environment_summary,
)

# Parallel processing
from cardiac_shared.parallel import (
    ParallelProcessor,
    ProcessingResult,
    Checkpoint,
    parallel_map,
    parallel_map_with_checkpoint,
)

# Progress tracking
from cardiac_shared.progress import (
    ProgressTracker,
    ProgressLevel,
    create_tracker,
)

# Cache management
from cardiac_shared.cache import CacheManager

# Batch processing
from cardiac_shared.batch import BatchProcessor, BatchConfig

# Configuration management
from cardiac_shared.config import ConfigManager, load_config

# Data registry and batch management
from cardiac_shared.data import (
    IntermediateResultsRegistry,
    RegistryEntry,
    get_registry,
    # Batch management (v0.6.0)
    BatchManager,
    BatchManifest,
    PatientEntry,
    ConsumerRecord,
    create_nifti_batch,
    load_batch,
    # Paired dataset (v0.9.0)
    PairedSample,
    PairedDatasetConfig,
    PairedDatasetLoader,
)

# Data sources management (v0.5.0)
from cardiac_shared.data_sources import (
    DataSourceManager,
    DataSource,
    DataSourceStatus,
    get_source,
    list_sources,
)

# Vertebra detection (v0.5.0)
from cardiac_shared.vertebra import (
    VertebraDetector,
    VertebraInfo,
    VertebraROI,
    parse_vertebrae,
    sort_vertebrae,
    VERTEBRAE_ORDER,
)

# Tissue classification (v0.5.0)
from cardiac_shared.tissue import (
    TissueClassifier,
    TissueMetrics,
    FilterStats,
    TISSUE_HU_RANGES,
    filter_tissue,
    get_tissue_hu_range,
)

# Preprocessing pipelines (v0.6.0) and thickness detection (v0.9.0)
from cardiac_shared.preprocessing import (
    DicomConverter,
    ConversionResult,
    convert_dicom_to_nifti,
    SharedPreprocessingPipeline,
    PreprocessingConfig,
    PreprocessingResult,
    create_pipeline,
    # Thickness detection (v0.9.0)
    ThicknessSource,
    ThicknessCategory,
    ThicknessInfo,
    ThicknessDetector,
    detect_thickness,
)

__all__ = [
    # Version
    '__version__',

    # IO
    'read_dicom_series',
    'get_dicom_metadata',
    'load_nifti',
    'save_nifti',
    'extract_zip',
    'find_dicom_root',
    # Preloader (v0.5.1)
    'AsyncNiftiPreloader',
    'preload_nifti_batch',

    # Hardware
    'detect_hardware',
    'HardwareInfo',
    'GPUInfo',
    'CPUInfo',
    'RAMInfo',
    'print_hardware_summary',
    'get_optimal_config',
    'CPUOptimizer',
    'get_cpu_optimizer',
    'apply_cpu_optimizations',
    # GPU utilities (v0.5.1)
    'get_recommended_gpu_stabilization_time',
    'get_gpu_performance_tier',

    # Environment
    'detect_runtime',
    'RuntimeEnvironment',
    'detect_colab',
    'detect_wsl',
    'print_environment_summary',

    # Parallel
    'ParallelProcessor',
    'ProcessingResult',
    'Checkpoint',
    'parallel_map',
    'parallel_map_with_checkpoint',

    # Progress
    'ProgressTracker',
    'ProgressLevel',
    'create_tracker',

    # Cache
    'CacheManager',

    # Batch
    'BatchProcessor',
    'BatchConfig',

    # Config
    'ConfigManager',
    'load_config',

    # Data registry
    'IntermediateResultsRegistry',
    'RegistryEntry',
    'get_registry',
    # Batch management (v0.6.0)
    'BatchManager',
    'BatchManifest',
    'PatientEntry',
    'ConsumerRecord',
    'create_nifti_batch',
    'load_batch',
    # Paired dataset (v0.9.0)
    'PairedSample',
    'PairedDatasetConfig',
    'PairedDatasetLoader',

    # Data sources (v0.5.0)
    'DataSourceManager',
    'DataSource',
    'DataSourceStatus',
    'get_source',
    'list_sources',

    # Vertebra (v0.5.0)
    'VertebraDetector',
    'VertebraInfo',
    'VertebraROI',
    'parse_vertebrae',
    'sort_vertebrae',
    'VERTEBRAE_ORDER',

    # Tissue (v0.5.0)
    'TissueClassifier',
    'TissueMetrics',
    'FilterStats',
    'TISSUE_HU_RANGES',
    'filter_tissue',
    'get_tissue_hu_range',

    # Preprocessing (v0.6.0)
    'DicomConverter',
    'ConversionResult',
    'convert_dicom_to_nifti',
    'SharedPreprocessingPipeline',
    'PreprocessingConfig',
    'PreprocessingResult',
    'create_pipeline',
    # Thickness detection (v0.9.0)
    'ThicknessSource',
    'ThicknessCategory',
    'ThicknessInfo',
    'ThicknessDetector',
    'detect_thickness',
]
