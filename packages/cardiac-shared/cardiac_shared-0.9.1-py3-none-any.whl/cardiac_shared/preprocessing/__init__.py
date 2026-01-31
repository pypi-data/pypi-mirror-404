"""
Preprocessing utilities for cardiac imaging pipelines

Provides:
- DicomConverter: Unified DICOM to NIfTI conversion
- SharedPreprocessingPipeline: Multi-module preprocessing with deduplication
- PreprocessingConfig: Configuration for preprocessing pipeline
- ThicknessDetector: Automatic CT slice thickness detection (v0.9.0)
- ThicknessInfo: Thickness information container (v0.9.0)
"""

from .dicom_converter import (
    DicomConverter,
    ConversionResult,
    convert_dicom_to_nifti,
)

from .pipeline import (
    SharedPreprocessingPipeline,
    PreprocessingConfig,
    PreprocessingResult,
    create_pipeline,
)

from .thickness import (
    ThicknessSource,
    ThicknessCategory,
    ThicknessInfo,
    ThicknessDetector,
    detect_thickness,
)

__all__ = [
    # DICOM Converter
    'DicomConverter',
    'ConversionResult',
    'convert_dicom_to_nifti',
    # Preprocessing Pipeline
    'SharedPreprocessingPipeline',
    'PreprocessingConfig',
    'PreprocessingResult',
    'create_pipeline',
    # Thickness Detection (v0.9.0)
    'ThicknessSource',
    'ThicknessCategory',
    'ThicknessInfo',
    'ThicknessDetector',
    'detect_thickness',
]
