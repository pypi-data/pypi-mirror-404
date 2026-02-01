"""Test basic imports for sagellm-comm."""

from __future__ import annotations


def test_import_package():
    """Test that the package can be imported."""
    import sagellm_comm

    # 只检查版本号格式，不硬编码具体版本
    assert sagellm_comm.__version__
    assert isinstance(sagellm_comm.__version__, str)
    parts = sagellm_comm.__version__.split(".")
    assert len(parts) >= 3  # 至少 major.minor.patch


def test_import_all():
    """Test that __all__ is defined."""
    from sagellm_comm import __all__

    assert isinstance(__all__, list)
    assert "__version__" in __all__


def test_protocol_dependency():
    """Test that protocol dependency is accessible."""
    try:
        import sagellm_protocol  # noqa: F401

        protocol_available = True
    except ImportError:
        protocol_available = False

    # Protocol is a required dependency, should always be available
    assert protocol_available, "sagellm_protocol should be installed as a dependency"


def test_backend_dependency():
    """Test that backend dependency is accessible."""
    try:
        import sagellm_backend  # noqa: F401

        backend_available = True
    except ImportError:
        backend_available = False

    # Backend is a required dependency, should always be available
    assert backend_available, "sagellm_backend should be installed as a dependency"
