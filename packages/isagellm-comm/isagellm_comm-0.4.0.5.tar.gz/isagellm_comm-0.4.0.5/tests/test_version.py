"""Test version information."""

from __future__ import annotations


def test_version_string():
    """Test version is a valid string."""
    from sagellm_comm import __version__

    assert isinstance(__version__, str)
    assert len(__version__) > 0


def test_version_format():
    """Test version follows semantic versioning."""
    from sagellm_comm import __version__

    # Should match X.Y.Z or X.Y.Z.N format
    parts = __version__.split(".")
    assert len(parts) in [3, 4], f"Version {__version__} should be X.Y.Z or X.Y.Z.N"
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"
