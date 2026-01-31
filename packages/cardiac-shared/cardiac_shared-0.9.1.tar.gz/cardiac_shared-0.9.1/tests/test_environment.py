"""Tests for environment detection module."""

import pytest


def test_detect_runtime():
    """Test runtime environment detection."""
    from cardiac_shared.environment import detect_runtime, RuntimeEnvironment

    env = detect_runtime()

    assert isinstance(env, RuntimeEnvironment)
    assert env.runtime_type in ['colab', 'wsl', 'windows', 'linux', 'macos', 'unknown']
    assert isinstance(env.is_colab, bool)
    assert isinstance(env.is_wsl, bool)
    assert isinstance(env.is_jupyter, bool)


def test_detect_colab():
    """Test Colab detection."""
    from cardiac_shared.environment import detect_colab

    is_colab = detect_colab()

    # Should be False in local environment
    assert isinstance(is_colab, bool)


def test_detect_wsl():
    """Test WSL detection."""
    from cardiac_shared.environment import detect_wsl

    is_wsl = detect_wsl()

    assert isinstance(is_wsl, bool)


def test_runtime_properties():
    """Test RuntimeEnvironment properties."""
    from cardiac_shared.environment import detect_runtime

    env = detect_runtime()

    # Test properties exist and return correct types
    assert isinstance(env.is_hospital_environment, bool)
    assert isinstance(env.is_cloud_environment, bool)
    assert isinstance(env.supports_gpu, bool)
    assert isinstance(env.recommended_install_method, str)


def test_data_directory_recommendations():
    """Test data directory recommendations."""
    from cardiac_shared.environment import detect_runtime, get_data_directory_recommendations

    env = detect_runtime()
    recommendations = get_data_directory_recommendations(env)

    assert isinstance(recommendations, dict)
    assert 'data_dir' in recommendations
    assert 'output_dir' in recommendations
