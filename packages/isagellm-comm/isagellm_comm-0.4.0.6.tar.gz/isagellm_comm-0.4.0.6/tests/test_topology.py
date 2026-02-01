"""Tests for topology utilities."""

from __future__ import annotations

import pytest

from sagellm_comm.topology import DeviceId, Link, LinkKind


class TestDeviceId:
    """Test DeviceId."""

    def test_create_device_id(self):
        """Test creating DeviceId."""
        device = DeviceId(node_id="node0", device_index=0, device_type="cuda")
        assert device.node_id == "node0"
        assert device.device_index == 0
        assert device.device_type == "cuda"

    def test_device_id_str(self):
        """Test DeviceId string representation."""
        device = DeviceId(node_id="node0", device_index=1, device_type="cuda")
        assert str(device) == "node0:cuda:1"

    def test_parse_device_id(self):
        """Test parsing device ID from string."""
        device = DeviceId.parse("node1:cuda:2")
        assert device.node_id == "node1"
        assert device.device_type == "cuda"
        assert device.device_index == 2

    def test_parse_invalid_device_id(self):
        """Test parsing invalid device ID."""
        with pytest.raises(ValueError, match="Invalid device string"):
            DeviceId.parse("invalid")

    def test_device_id_hashable(self):
        """Test DeviceId is hashable (frozen)."""
        device1 = DeviceId(node_id="node0", device_index=0)
        device2 = DeviceId(node_id="node0", device_index=0)

        # Should be usable in set/dict
        devices = {device1, device2}
        assert len(devices) == 1


class TestLink:
    """Test Link."""

    def test_create_link(self):
        """Test creating Link."""
        src = DeviceId(node_id="node0", device_index=0)
        dst = DeviceId(node_id="node1", device_index=0)

        link = Link(
            src=src,
            dst=dst,
            kind=LinkKind.NVLINK,
            bandwidth_gbps=300.0,
            bidirectional=True,
        )

        assert link.src == src
        assert link.dst == dst
        assert link.kind == LinkKind.NVLINK
        assert link.bandwidth_gbps == 300.0
        assert link.bidirectional is True

    def test_link_str(self):
        """Test Link string representation."""
        src = DeviceId(node_id="node0", device_index=0)
        dst = DeviceId(node_id="node1", device_index=0)

        link = Link(
            src=src,
            dst=dst,
            kind=LinkKind.PCIE,
            bandwidth_gbps=32.0,
            bidirectional=False,
        )

        link_str = str(link)
        assert "node0:cuda:0" in link_str
        assert "node1:cuda:0" in link_str
        assert "pcie" in link_str
        assert "32.0" in link_str
        assert "->" in link_str  # Unidirectional


class TestLinkKind:
    """Test LinkKind enum."""

    def test_link_kinds(self):
        """Test all link kinds."""
        assert LinkKind.NVLINK.value == "nvlink"
        assert LinkKind.PCIE.value == "pcie"
        assert LinkKind.IB.value == "infiniband"
        assert LinkKind.ROCE.value == "roce"
        assert LinkKind.HCCS.value == "hccs"
        assert LinkKind.NETWORK.value == "network"
