"""Tests for sagellm-compression package initialization."""

from __future__ import annotations

import sagellm_compression


def test_version():
    """Test that version is defined and valid."""
    assert hasattr(sagellm_compression, "__version__")
    assert isinstance(sagellm_compression.__version__, str)
    assert len(sagellm_compression.__version__) > 0


def test_package_import():
    """Test that the package can be imported."""
    import sagellm_compression  # noqa: F401

    assert sagellm_compression is not None


def test_all_exports():
    """Test that __all__ is defined."""
    assert hasattr(sagellm_compression, "__all__")
    assert isinstance(sagellm_compression.__all__, list)
