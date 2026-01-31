"""
Paired Dataset Module for Multi-Thickness CT Analysis.

Provides data loading utilities for paired thin/thick-slice CT volumes,
supporting multi-thickness validation research and RESCUE phenomenon analysis.

Example:
    >>> from cardiac_shared.data import PairedDatasetLoader, PairedSample
    >>> loader = PairedDatasetLoader()
    >>> loader.add_nlst_dataset('/data/nlst', thin_mm=2.0, thick_mm=5.0)
    >>> samples = loader.load_samples()
    >>> print(f"Loaded {len(samples)} paired samples")
"""

from typing import Dict, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import json
import csv
import logging

logger = logging.getLogger(__name__)


@dataclass
class PairedSample:
    """
    A single paired thin/thick-slice sample.
    
    Attributes:
        patient_id: Unique patient identifier
        dataset: Dataset name (e.g., "NLST", "Internal")
        thin_path: Path to thin-slice data (DICOM dir or NIfTI file)
        thick_path: Path to thick-slice data
        thin_thickness: Thin slice thickness in mm
        thick_thickness: Thick slice thickness in mm
        thin_agatston: CAC Agatston score from thin-slice (optional)
        thick_agatston: CAC Agatston score from thick-slice (optional)
        is_rescue: True if thick missed but thin detected
        is_reverse_rescue: True if thin missed but thick detected
        metadata: Additional metadata dictionary
    """
    patient_id: str
    dataset: str
    thin_path: Path
    thick_path: Path
    thin_thickness: float  # mm
    thick_thickness: float  # mm
    thin_agatston: Optional[float] = None
    thick_agatston: Optional[float] = None
    is_rescue: bool = False
    is_reverse_rescue: bool = False
    metadata: Dict = field(default_factory=dict)

    @property
    def upscale_factor(self) -> float:
        """Calculate required upscaling factor (thick/thin)."""
        if self.thin_thickness > 0:
            return self.thick_thickness / self.thin_thickness
        return 1.0

    @property
    def resolution_ratio(self) -> float:
        """Calculate resolution ratio (same as upscale_factor)."""
        return self.upscale_factor

    @property
    def thickness_pair_str(self) -> str:
        """Get thickness pair as string (e.g., '2mm_vs_5mm')."""
        return f"{self.thin_thickness:.1f}mm_vs_{self.thick_thickness:.1f}mm"

    @property
    def has_scores(self) -> bool:
        """Check if both Agatston scores are available."""
        return self.thin_agatston is not None and self.thick_agatston is not None

    @property
    def score_difference(self) -> Optional[float]:
        """Calculate score difference (thin - thick)."""
        if self.has_scores:
            return self.thin_agatston - self.thick_agatston
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'patient_id': self.patient_id,
            'dataset': self.dataset,
            'thin_path': str(self.thin_path),
            'thick_path': str(self.thick_path),
            'thin_thickness': self.thin_thickness,
            'thick_thickness': self.thick_thickness,
            'thin_agatston': self.thin_agatston,
            'thick_agatston': self.thick_agatston,
            'is_rescue': self.is_rescue,
            'is_reverse_rescue': self.is_reverse_rescue,
            'upscale_factor': self.upscale_factor,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PairedSample':
        """Create from dictionary."""
        return cls(
            patient_id=data['patient_id'],
            dataset=data.get('dataset', 'unknown'),
            thin_path=Path(data['thin_path']),
            thick_path=Path(data['thick_path']),
            thin_thickness=float(data['thin_thickness']),
            thick_thickness=float(data['thick_thickness']),
            thin_agatston=data.get('thin_agatston'),
            thick_agatston=data.get('thick_agatston'),
            is_rescue=data.get('is_rescue', False),
            is_reverse_rescue=data.get('is_reverse_rescue', False),
            metadata=data.get('metadata', {}),
        )


@dataclass
class PairedDatasetConfig:
    """
    Configuration for paired dataset loading.
    
    Attributes:
        thin_thickness: Target thin slice thickness in mm
        thick_thickness: Target thick slice thickness in mm
        dataset_name: Name identifier for this dataset
        data_root: Root directory containing patient data
        thin_subdir: Subdirectory name for thin-slice data
        thick_subdir: Subdirectory name for thick-slice data
        manifest_path: Optional path to manifest JSON file
        results_csv_path: Optional path to results CSV file
        series_inventory_path: Optional path to series inventory CSV
        thickness_tolerance: Tolerance for thickness matching (mm)
    """
    thin_thickness: float
    thick_thickness: float
    dataset_name: str
    data_root: Path
    thin_subdir: str = "2mm"
    thick_subdir: str = "5mm"
    manifest_path: Optional[Path] = None
    results_csv_path: Optional[Path] = None
    series_inventory_path: Optional[Path] = None
    thickness_tolerance: float = 0.5

    def __post_init__(self):
        self.data_root = Path(self.data_root)
        if self.manifest_path:
            self.manifest_path = Path(self.manifest_path)
        if self.results_csv_path:
            self.results_csv_path = Path(self.results_csv_path)
        if self.series_inventory_path:
            self.series_inventory_path = Path(self.series_inventory_path)


class PairedDatasetLoader:
    """
    Loader for paired thin/thick-slice CT datasets.
    
    Supports multiple dataset formats:
    - NLST dataset: 2mm vs 5mm paired data
    - Internal CHD dataset: 1.0/1.5mm vs 5mm paired data
    - Custom datasets with manifest files
    
    Example:
        >>> loader = PairedDatasetLoader()
        >>> loader.add_nlst_dataset(
        ...     data_root='/data/nlst',
        ...     series_inventory='/path/to/inventory.csv',
        ...     thin_mm=2.0,
        ...     thick_mm=5.0
        ... )
        >>> samples = loader.load_samples()
        >>> rescue_samples = loader.get_rescue_samples()
    """

    def __init__(self):
        """Initialize the paired dataset loader."""
        self.configs: List[PairedDatasetConfig] = []
        self.samples: List[PairedSample] = []
        self._loaded = False

    def add_dataset(self, config: PairedDatasetConfig):
        """
        Add a dataset configuration.
        
        Args:
            config: PairedDatasetConfig instance
        """
        self.configs.append(config)
        self._loaded = False
        logger.info(f"Added dataset config: {config.dataset_name} "
                   f"({config.thin_thickness}mm vs {config.thick_thickness}mm)")

    def add_nlst_dataset(
        self,
        data_root: Union[str, Path],
        series_inventory_path: Optional[Union[str, Path]] = None,
        thin_mm: float = 2.0,
        thick_mm: float = 5.0,
        thin_subdir: str = "2mm",
        thick_subdir: str = "5mm",
    ):
        """
        Add NLST dataset (convenience method).
        
        Args:
            data_root: Root directory containing NLST data
            series_inventory_path: Path to nlst_series_inventory.csv
            thin_mm: Thin slice thickness (default 2.0mm)
            thick_mm: Thick slice thickness (default 5.0mm)
            thin_subdir: Subdirectory name for thin slices
            thick_subdir: Subdirectory name for thick slices
        """
        config = PairedDatasetConfig(
            thin_thickness=thin_mm,
            thick_thickness=thick_mm,
            dataset_name=f"NLST_{thin_mm}mm_vs_{thick_mm}mm",
            data_root=Path(data_root),
            thin_subdir=thin_subdir,
            thick_subdir=thick_subdir,
            series_inventory_path=Path(series_inventory_path) if series_inventory_path else None,
        )
        self.add_dataset(config)

    def add_internal_dataset(
        self,
        data_root: Union[str, Path],
        thin_mm: float = 1.5,
        thick_mm: float = 5.0,
        manifest_path: Optional[Union[str, Path]] = None,
        results_csv_path: Optional[Union[str, Path]] = None,
    ):
        """
        Add Internal (CHD/Normal) dataset (convenience method).
        
        Args:
            data_root: Root directory containing patient data
            thin_mm: Thin slice thickness (1.0 or 1.5mm)
            thick_mm: Thick slice thickness (default 5.0mm)
            manifest_path: Path to manifest JSON
            results_csv_path: Path to results CSV
        """
        config = PairedDatasetConfig(
            thin_thickness=thin_mm,
            thick_thickness=thick_mm,
            dataset_name=f"Internal_{thin_mm}mm_vs_{thick_mm}mm",
            data_root=Path(data_root),
            manifest_path=Path(manifest_path) if manifest_path else None,
            results_csv_path=Path(results_csv_path) if results_csv_path else None,
        )
        self.add_dataset(config)

    def load_samples(self) -> List[PairedSample]:
        """
        Load all samples from configured datasets.
        
        Returns:
            List of PairedSample objects
        """
        self.samples = []

        for config in self.configs:
            try:
                samples = self._load_dataset(config)
                self.samples.extend(samples)
                logger.info(f"Loaded {len(samples)} samples from {config.dataset_name}")
            except Exception as e:
                logger.error(f"Failed to load {config.dataset_name}: {e}")

        self._loaded = True
        logger.info(f"Total samples loaded: {len(self.samples)}")
        return self.samples

    def _load_dataset(self, config: PairedDatasetConfig) -> List[PairedSample]:
        """Load samples from a single dataset configuration."""
        samples = []

        # Try different loading methods
        if config.series_inventory_path and config.series_inventory_path.exists():
            samples = self._load_from_series_inventory(config)
        elif config.manifest_path and config.manifest_path.exists():
            samples = self._load_from_manifest(config)
        elif config.results_csv_path and config.results_csv_path.exists():
            samples = self._load_from_results_csv(config)
        else:
            # Fallback: scan directory for paired data
            samples = self._scan_directory(config)

        return samples

    def _load_from_series_inventory(self, config: PairedDatasetConfig) -> List[PairedSample]:
        """Load samples from NLST-style series inventory CSV."""
        samples = []
        
        with open(config.series_inventory_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if patient has both thin and thick data
                has_thin = row.get('has_2mm', 'False').lower() == 'true'
                has_thick = row.get('has_5mm', 'False').lower() == 'true'
                
                if not (has_thin and has_thick):
                    continue
                
                patient_id = row.get('case_id', row.get('patient_id', ''))
                
                # Construct paths
                thin_path = config.data_root / config.thin_subdir / f"{patient_id}.nii.gz"
                thick_path = config.data_root / config.thick_subdir / f"{patient_id}.nii.gz"
                
                sample = PairedSample(
                    patient_id=patient_id,
                    dataset=config.dataset_name,
                    thin_path=thin_path,
                    thick_path=thick_path,
                    thin_thickness=config.thin_thickness,
                    thick_thickness=config.thick_thickness,
                    metadata={
                        'n_2mm_series': int(row.get('n_2mm_series', 0)),
                        'n_5mm_series': int(row.get('n_5mm_series', 0)),
                        'max_2mm_slices': int(row.get('max_2mm_slices', 0)),
                        'max_5mm_slices': int(row.get('max_5mm_slices', 0)),
                    }
                )
                samples.append(sample)
        
        return samples

    def _load_from_manifest(self, config: PairedDatasetConfig) -> List[PairedSample]:
        """Load samples from manifest JSON file."""
        samples = []
        
        with open(config.manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        
        patients = manifest.get('patients', manifest.get('samples', []))
        
        for patient in patients:
            patient_id = str(patient.get('patient_id', patient.get('id', '')))
            
            thin_path = Path(patient.get('thin_path', ''))
            thick_path = Path(patient.get('thick_path', ''))
            
            if not thin_path.is_absolute():
                thin_path = config.data_root / thin_path
            if not thick_path.is_absolute():
                thick_path = config.data_root / thick_path
            
            sample = PairedSample(
                patient_id=patient_id,
                dataset=config.dataset_name,
                thin_path=thin_path,
                thick_path=thick_path,
                thin_thickness=patient.get('thin_thickness', config.thin_thickness),
                thick_thickness=patient.get('thick_thickness', config.thick_thickness),
                thin_agatston=patient.get('thin_agatston'),
                thick_agatston=patient.get('thick_agatston'),
                is_rescue=patient.get('is_rescue', False),
                metadata=patient.get('metadata', {}),
            )
            samples.append(sample)
        
        return samples

    def _load_from_results_csv(self, config: PairedDatasetConfig) -> List[PairedSample]:
        """Load samples from results CSV file."""
        samples = []
        
        with open(config.results_csv_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                patient_id = str(row.get('patient_id', row.get('case_id', '')))
                
                thin_path = config.data_root / config.thin_subdir / f"{patient_id}.nii.gz"
                thick_path = config.data_root / config.thick_subdir / f"{patient_id}.nii.gz"
                
                thin_score = row.get('thin_agatston', row.get('agatston_2mm'))
                thick_score = row.get('thick_agatston', row.get('agatston_5mm'))
                
                sample = PairedSample(
                    patient_id=patient_id,
                    dataset=config.dataset_name,
                    thin_path=thin_path,
                    thick_path=thick_path,
                    thin_thickness=config.thin_thickness,
                    thick_thickness=config.thick_thickness,
                    thin_agatston=float(thin_score) if thin_score else None,
                    thick_agatston=float(thick_score) if thick_score else None,
                    is_rescue=str(row.get('is_rescue', 'false')).lower() == 'true',
                )
                samples.append(sample)
        
        return samples

    def _scan_directory(self, config: PairedDatasetConfig) -> List[PairedSample]:
        """Scan directory structure to find paired samples."""
        samples = []
        
        thin_dir = config.data_root / config.thin_subdir
        thick_dir = config.data_root / config.thick_subdir
        
        if not thin_dir.exists() or not thick_dir.exists():
            logger.warning(f"Directories not found: {thin_dir} or {thick_dir}")
            return samples
        
        # Find all thin-slice files
        thin_files = {f.stem.replace('.nii', ''): f for f in thin_dir.glob("*.nii*")}
        thick_files = {f.stem.replace('.nii', ''): f for f in thick_dir.glob("*.nii*")}
        
        # Find paired samples
        paired_ids = set(thin_files.keys()) & set(thick_files.keys())
        
        for patient_id in paired_ids:
            sample = PairedSample(
                patient_id=patient_id,
                dataset=config.dataset_name,
                thin_path=thin_files[patient_id],
                thick_path=thick_files[patient_id],
                thin_thickness=config.thin_thickness,
                thick_thickness=config.thick_thickness,
            )
            samples.append(sample)
        
        return samples

    def get_all_samples(self) -> List[PairedSample]:
        """Get all loaded samples."""
        if not self._loaded:
            self.load_samples()
        return self.samples

    def get_samples_by_dataset(self, dataset_name: str) -> List[PairedSample]:
        """Get samples for a specific dataset."""
        return [s for s in self.samples if s.dataset == dataset_name]

    def get_rescue_samples(self) -> List[PairedSample]:
        """Get RESCUE samples (thick missed, thin detected)."""
        return [s for s in self.samples if s.is_rescue]

    def get_reverse_rescue_samples(self) -> List[PairedSample]:
        """Get reverse RESCUE samples (thin missed, thick detected)."""
        return [s for s in self.samples if s.is_reverse_rescue]

    def get_samples_by_score_range(
        self,
        min_score: float = 0,
        max_score: float = float('inf'),
        use_thin: bool = True
    ) -> List[PairedSample]:
        """Get samples within a CAC score range."""
        samples = []
        for s in self.samples:
            score = s.thin_agatston if use_thin else s.thick_agatston
            if score is not None and min_score <= score <= max_score:
                samples.append(s)
        return samples

    def get_statistics(self) -> Dict:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.samples:
            return {'total_samples': 0}
        
        rescue_count = sum(1 for s in self.samples if s.is_rescue)
        reverse_rescue_count = sum(1 for s in self.samples if s.is_reverse_rescue)
        
        stats = {
            'total_samples': len(self.samples),
            'rescue_count': rescue_count,
            'rescue_rate': rescue_count / len(self.samples) * 100 if self.samples else 0,
            'reverse_rescue_count': reverse_rescue_count,
            'by_dataset': {},
        }
        
        for config in self.configs:
            dataset_samples = self.get_samples_by_dataset(config.dataset_name)
            if dataset_samples:
                ds_rescue = sum(1 for s in dataset_samples if s.is_rescue)
                stats['by_dataset'][config.dataset_name] = {
                    'count': len(dataset_samples),
                    'rescue_count': ds_rescue,
                    'rescue_rate': ds_rescue / len(dataset_samples) * 100,
                    'thin_thickness': config.thin_thickness,
                    'thick_thickness': config.thick_thickness,
                }
        
        return stats

    def save_to_json(self, output_path: Union[str, Path]):
        """
        Save loaded samples to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'samples': [s.to_dict() for s in self.samples],
            'statistics': self.get_statistics(),
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(self.samples)} samples to {output_path}")

    def load_from_json(self, input_path: Union[str, Path]):
        """
        Load samples from JSON file.
        
        Args:
            input_path: Path to input JSON file
        """
        input_path = Path(input_path)
        
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.samples = [PairedSample.from_dict(s) for s in data.get('samples', [])]
        self._loaded = True
        
        logger.info(f"Loaded {len(self.samples)} samples from {input_path}")


# Export all public classes and functions
__all__ = [
    'PairedSample',
    'PairedDatasetConfig',
    'PairedDatasetLoader',
]
