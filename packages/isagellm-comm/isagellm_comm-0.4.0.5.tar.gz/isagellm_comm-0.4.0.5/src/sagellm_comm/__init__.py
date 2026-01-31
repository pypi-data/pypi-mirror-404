"""sagellm-comm: Communication Layer for sageLLM distributed inference.

推荐使用方式 (vLLM v1 style):
    from sagellm_comm import get_comm_backend

    # 自动选择最佳可用后端
    comm = get_comm_backend()

    # 显式指定后端
    comm = get_comm_backend("gloo")   # CPU 或 fallback
    comm = get_comm_backend("nccl")   # CUDA (TODO)
    comm = get_comm_backend("hccl")   # Ascend (TODO)
"""

from __future__ import annotations

__version__ = "0.4.0.5"

# MVP: 公共 API 导出
from sagellm_comm.backend import (
    CommBackend,
    CommBackendType,
    CommGroup,
    CommOp,
    TopologyNode,
)
from sagellm_comm.gloo_backend import GlooBackend

# Registry and factory function (vLLM v1 style)
from sagellm_comm.registry import (
    get_comm_backend,
    is_comm_backend_available,
    list_comm_backends,
    register_comm_backend,
)

# Topology utilities (Phase 2)
from sagellm_comm.topology import DeviceId, Link, LinkKind

__all__ = [
    "__version__",
    # =========================================================================
    # Registry (vLLM v1 style) - RECOMMENDED
    # =========================================================================
    "get_comm_backend",  # Factory function to get CommBackend
    "register_comm_backend",  # Register custom backend
    "list_comm_backends",  # List available backends
    "is_comm_backend_available",  # Check if backend is available
    # =========================================================================
    # Backend interfaces
    # =========================================================================
    "CommBackend",
    "CommBackendType",
    "CommGroup",
    "CommOp",
    "TopologyNode",
    # Implementations
    "GlooBackend",
    # Topology (Phase 2)
    "DeviceId",
    "Link",
    "LinkKind",
]
