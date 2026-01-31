"""Tests for sagellm-comm MVP implementation.

测试通信后端、拓扑发现和集合操作。

注意：遵循 sageLLM No Mock Policy，所有测试使用真实实现。
"""

from __future__ import annotations

import os

import pytest
import torch

from sagellm_comm import (
    CommBackendType,
    CommGroup,
    CommOp,
    GlooBackend,
    Topology,
    TopologyDetector,
    TopologyNode,
)


class TestTopologyDetector:
    """测试拓扑发现器"""

    def test_detect_fail_fast_no_rank(self):
        """测试 Fail-Fast：缺少 RANK 环境变量"""
        # 清除环境变量
        env_backup = os.environ.copy()
        for key in ["RANK", "WORLD_SIZE", "LOCAL_RANK", "LOCAL_WORLD_SIZE"]:
            os.environ.pop(key, None)

        try:
            with pytest.raises(RuntimeError, match="RANK environment variable is not set"):
                TopologyDetector.detect()
        finally:
            os.environ.update(env_backup)

    def test_detect_fail_fast_no_world_size(self):
        """测试 Fail-Fast：缺少 WORLD_SIZE 环境变量"""
        env_backup = os.environ.copy()
        os.environ["RANK"] = "0"
        os.environ.pop("WORLD_SIZE", None)

        try:
            with pytest.raises(RuntimeError, match="WORLD_SIZE environment variable is not set"):
                TopologyDetector.detect()
        finally:
            os.environ.update(env_backup)

    def test_detect_success(self):
        """测试成功检测拓扑"""
        env_backup = os.environ.copy()
        os.environ.update(
            {"RANK": "0", "WORLD_SIZE": "2", "LOCAL_RANK": "0", "LOCAL_WORLD_SIZE": "1"}
        )

        try:
            topology = TopologyDetector.detect()

            assert topology.rank == 0
            assert topology.world_size == 2
            assert topology.local_rank == 0
            assert topology.local_world_size == 1
            assert len(topology.nodes) == 2
            assert topology.hostname is not None

            # 检查节点
            node = topology.nodes[0]
            assert node.rank == 0
            assert node.device_type in ["cuda", "cpu"]

        finally:
            os.environ.update(env_backup)


class TestGlooBackend:
    """测试 Gloo 后端"""

    def test_init_fail_fast_invalid_rank(self):
        """测试 Fail-Fast：无效的 rank"""
        backend = GlooBackend()

        with pytest.raises(ValueError, match="Invalid rank"):
            backend.init(rank=-1, world_size=2, master_addr="localhost", master_port=29500)

        with pytest.raises(ValueError, match="Invalid rank"):
            backend.init(rank=2, world_size=2, master_addr="localhost", master_port=29500)

    def test_init_fail_fast_invalid_world_size(self):
        """测试 Fail-Fast：无效的 world_size"""
        backend = GlooBackend()

        with pytest.raises(ValueError, match="Invalid world_size"):
            backend.init(rank=0, world_size=0, master_addr="localhost", master_port=29500)

        with pytest.raises(ValueError, match="Invalid world_size"):
            backend.init(rank=0, world_size=-1, master_addr="localhost", master_port=29500)

    def test_not_initialized_error(self):
        """测试未初始化时的错误"""
        backend = GlooBackend()

        with pytest.raises(RuntimeError, match="not initialized"):
            backend.get_rank()

        # 使用真实的 tensor 而非 MagicMock
        tensor = torch.zeros(10)
        with pytest.raises(RuntimeError, match="not initialized"):
            backend.all_reduce(tensor)

    def test_create_group_fail_fast_empty_ranks(self):
        """测试 Fail-Fast：空的 ranks 列表"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2

        with pytest.raises(ValueError, match="ranks cannot be empty"):
            backend.create_group([])

    def test_create_group_fail_fast_invalid_ranks(self):
        """测试 Fail-Fast：无效的 ranks"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2

        with pytest.raises(ValueError, match="Invalid ranks"):
            backend.create_group([-1, 0])

        with pytest.raises(ValueError, match="Invalid ranks"):
            backend.create_group([0, 2])

    def test_all_reduce_unsupported_op(self):
        """测试不支持的操作"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2
        backend._rank = 0

        # 模拟 torch.distributed 已加载
        try:
            import torch.distributed as dist

            backend._torch_dist = dist
        except ImportError:
            pytest.skip("torch.distributed not available")

        # 使用真实的 tensor
        tensor = torch.zeros(10)

        # 使用不存在的操作（AVG 未实现）
        with pytest.raises(ValueError, match="Unsupported operation"):
            backend.all_reduce(tensor, op=CommOp.AVG)

    def test_send_fail_fast_invalid_rank(self):
        """测试 Fail-Fast：send 无效 rank"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2

        # 使用真实的 tensor
        tensor = torch.zeros(10)

        with pytest.raises(ValueError, match="Invalid dst_rank"):
            backend.send(tensor, dst_rank=-1)

        with pytest.raises(ValueError, match="Invalid dst_rank"):
            backend.send(tensor, dst_rank=2)

    def test_recv_fail_fast_invalid_rank(self):
        """测试 Fail-Fast：recv 无效 rank"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2

        # 使用真实的 tensor
        tensor = torch.zeros(10)

        with pytest.raises(ValueError, match="Invalid src_rank"):
            backend.recv(tensor, src_rank=-1)

        with pytest.raises(ValueError, match="Invalid src_rank"):
            backend.recv(tensor, src_rank=2)

    def test_broadcast_fail_fast_invalid_rank(self):
        """测试 Fail-Fast：broadcast 无效 rank"""
        backend = GlooBackend()
        backend._initialized = True
        backend._world_size = 2

        # 使用真实的 tensor
        tensor = torch.zeros(10)

        with pytest.raises(ValueError, match="Invalid src_rank"):
            backend.broadcast(tensor, src_rank=-1)

        with pytest.raises(ValueError, match="Invalid src_rank"):
            backend.broadcast(tensor, src_rank=2)


class TestCommGroup:
    """测试通信组"""

    def test_comm_group_creation(self):
        """测试通信组创建"""
        group = CommGroup(
            group_id="test_group",
            ranks=[0, 1, 2],
            world_size=3,
            backend_type=CommBackendType.GLOO,
        )

        assert group.group_id == "test_group"
        assert group.ranks == [0, 1, 2]
        assert group.world_size == 3
        assert group.backend_type == CommBackendType.GLOO


class TestTopology:
    """测试拓扑"""

    def test_topology_to_dict(self):
        """测试拓扑转换为字典"""
        nodes = [
            TopologyNode(
                node_id="node_0",
                rank=0,
                device_type="cpu",
                device_index=0,
                hostname="localhost",
            )
        ]

        topology = Topology(
            nodes=nodes,
            rank=0,
            world_size=1,
            local_rank=0,
            local_world_size=1,
            hostname="localhost",
        )

        data = topology.to_dict()
        assert data["rank"] == 0
        assert data["world_size"] == 1
        assert len(data["nodes"]) == 1
        assert data["nodes"][0]["node_id"] == "node_0"
