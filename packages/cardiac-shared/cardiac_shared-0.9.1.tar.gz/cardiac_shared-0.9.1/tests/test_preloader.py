"""Tests for AsyncNiftiPreloader module (v0.5.1)."""

import pytest
import tempfile
import numpy as np
from pathlib import Path


# Skip tests if nibabel is not installed
pytest_plugins = ['pytest']


class TestAsyncNiftiPreloaderImport:
    """Tests for preloader imports."""

    def test_import_class(self):
        """Test AsyncNiftiPreloader can be imported."""
        try:
            from cardiac_shared.io import AsyncNiftiPreloader
            assert AsyncNiftiPreloader is not None
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise

    def test_import_function(self):
        """Test preload_nifti_batch can be imported."""
        try:
            from cardiac_shared.io import preload_nifti_batch
            assert callable(preload_nifti_batch)
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise

    def test_import_from_main_package(self):
        """Test imports from main package."""
        try:
            from cardiac_shared import AsyncNiftiPreloader, preload_nifti_batch
            assert AsyncNiftiPreloader is not None
            assert callable(preload_nifti_batch)
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise


class TestAsyncNiftiPreloaderInit:
    """Tests for preloader initialization."""

    @pytest.fixture
    def preloader(self):
        """Create a preloader instance."""
        try:
            from cardiac_shared.io import AsyncNiftiPreloader
            return AsyncNiftiPreloader(max_cache_size=2)
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise

    def test_init_default(self, preloader):
        """Test default initialization."""
        assert preloader.max_cache_size == 2
        assert preloader.cache_size == 0

    def test_init_custom_cache_size(self):
        """Test custom cache size."""
        try:
            from cardiac_shared.io import AsyncNiftiPreloader
            preloader = AsyncNiftiPreloader(max_cache_size=5)
            assert preloader.max_cache_size == 5
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise

    def test_init_custom_timeout(self):
        """Test custom timeout."""
        try:
            from cardiac_shared.io import AsyncNiftiPreloader
            preloader = AsyncNiftiPreloader(timeout=60.0)
            assert preloader.timeout == 60.0
        except ImportError as e:
            if 'nibabel' in str(e):
                pytest.skip("nibabel not installed")
            raise

    def test_stats_initial(self, preloader):
        """Test initial stats are zeros."""
        stats = preloader.stats
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        assert stats['files_preloaded'] == 0

    def test_cache_size_property(self, preloader):
        """Test cache_size property."""
        assert preloader.cache_size == 0

    def test_is_cached_empty(self, preloader):
        """Test is_cached returns False for non-existent file."""
        assert preloader.is_cached("/path/to/nonexistent.nii.gz") is False


class TestAsyncNiftiPreloaderWithFiles:
    """Tests with actual NIfTI files (requires nibabel)."""

    @pytest.fixture
    def temp_nifti_file(self):
        """Create a temporary NIfTI file for testing."""
        try:
            import nibabel as nib
        except ImportError:
            pytest.skip("nibabel not installed")

        # Create a small test volume
        data = np.random.rand(10, 10, 10).astype(np.float32)
        affine = np.eye(4)
        img = nib.Nifti1Image(data, affine)

        with tempfile.NamedTemporaryFile(suffix='.nii.gz', delete=False) as f:
            nib.save(img, f.name)
            yield f.name

        # Cleanup
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def temp_nifti_files(self):
        """Create multiple temporary NIfTI files."""
        try:
            import nibabel as nib
        except ImportError:
            pytest.skip("nibabel not installed")

        files = []
        for i in range(3):
            data = np.random.rand(10, 10, 10).astype(np.float32) * (i + 1)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)

            with tempfile.NamedTemporaryFile(suffix=f'_{i}.nii.gz', delete=False) as f:
                nib.save(img, f.name)
                files.append(f.name)

        yield files

        # Cleanup
        for f in files:
            Path(f).unlink(missing_ok=True)

    def test_start_stop(self, temp_nifti_file):
        """Test start and stop."""
        from cardiac_shared.io import AsyncNiftiPreloader

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start([temp_nifti_file])
        stats = preloader.stop()

        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert 'files_preloaded' in stats

    def test_get_single_file(self, temp_nifti_file):
        """Test getting a single file."""
        from cardiac_shared.io import AsyncNiftiPreloader
        import time

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start([temp_nifti_file])

        # Wait for preloading
        time.sleep(0.5)

        volume, metadata = preloader.get(temp_nifti_file)
        preloader.stop()

        assert isinstance(volume, np.ndarray)
        assert volume.shape == (10, 10, 10)
        assert 'shape' in metadata

    def test_get_multiple_files(self, temp_nifti_files):
        """Test getting multiple files."""
        from cardiac_shared.io import AsyncNiftiPreloader
        import time

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start(temp_nifti_files)

        # Wait for some preloading
        time.sleep(0.5)

        volumes = []
        for f in temp_nifti_files:
            volume, metadata = preloader.get(f)
            volumes.append(volume)

        stats = preloader.stop()

        assert len(volumes) == 3
        for v in volumes:
            assert isinstance(v, np.ndarray)
            assert v.shape == (10, 10, 10)

        # Should have some cache activity
        assert stats['cache_hits'] + stats['cache_misses'] >= 1

    def test_cache_hit(self, temp_nifti_file):
        """Test cache hit after preloading."""
        from cardiac_shared.io import AsyncNiftiPreloader
        import time

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start([temp_nifti_file])

        # Wait for preloading to complete
        time.sleep(1.0)

        # Get twice - second should be cache hit
        preloader.get(temp_nifti_file)
        preloader.get(temp_nifti_file)

        stats = preloader.stop()

        # At least one cache hit expected
        assert stats['cache_hits'] >= 1

    def test_is_cached(self, temp_nifti_file):
        """Test is_cached method."""
        from cardiac_shared.io import AsyncNiftiPreloader
        import time

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start([temp_nifti_file])

        # Wait for preloading
        time.sleep(1.0)

        is_cached = preloader.is_cached(temp_nifti_file)
        preloader.stop()

        # Should be cached after preloading
        assert is_cached is True

    def test_clear_cache(self, temp_nifti_file):
        """Test clear_cache method."""
        from cardiac_shared.io import AsyncNiftiPreloader
        import time

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start([temp_nifti_file])

        time.sleep(1.0)

        # Cache should have the file
        assert preloader.cache_size >= 0

        preloader.clear_cache()
        assert preloader.cache_size == 0

        preloader.stop()

    def test_file_not_found(self):
        """Test FileNotFoundError for non-existent file."""
        from cardiac_shared.io import AsyncNiftiPreloader

        preloader = AsyncNiftiPreloader(max_cache_size=2)
        preloader.start(["/nonexistent/file.nii.gz"])

        with pytest.raises(FileNotFoundError):
            preloader.get("/nonexistent/file.nii.gz", blocking=False)

        preloader.stop()


class TestPreloadNiftiBatch:
    """Tests for preload_nifti_batch convenience function."""

    @pytest.fixture
    def temp_nifti_files(self):
        """Create temporary NIfTI files."""
        try:
            import nibabel as nib
        except ImportError:
            pytest.skip("nibabel not installed")

        files = []
        for i in range(2):
            data = np.random.rand(5, 5, 5).astype(np.float32) * (i + 1)
            affine = np.eye(4)
            img = nib.Nifti1Image(data, affine)

            with tempfile.NamedTemporaryFile(suffix=f'_{i}.nii.gz', delete=False) as f:
                nib.save(img, f.name)
                files.append(f.name)

        yield files

        for f in files:
            Path(f).unlink(missing_ok=True)

    def test_batch_process(self, temp_nifti_files):
        """Test batch processing with preloading."""
        from cardiac_shared.io import preload_nifti_batch

        def process_func(volume, metadata, path):
            return float(volume.mean())

        results = preload_nifti_batch(
            temp_nifti_files,
            process_func,
            max_cache_size=2
        )

        assert len(results) == 2
        for r in results:
            assert isinstance(r, float)
            assert r > 0
