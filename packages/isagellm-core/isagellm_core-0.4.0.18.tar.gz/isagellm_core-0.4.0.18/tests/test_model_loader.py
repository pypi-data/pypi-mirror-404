"""Tests for model loading utilities."""

from __future__ import annotations

import pytest

from sagellm_core.model import ModelLoader


class TestModelLoader:
    """Test ModelLoader."""

    def test_get_device_map_cpu(self):
        """Test device map for CPU."""
        device_map = ModelLoader._get_device_map("cpu")
        assert device_map == "cpu"

    def test_get_device_map_cuda(self):
        """Test device map for CUDA."""
        device_map = ModelLoader._get_device_map("cuda")
        assert device_map == "auto"

    def test_get_device_map_ascend(self):
        """Test device map for Ascend."""
        device_map = ModelLoader._get_device_map("ascend")
        assert device_map == "auto"

    def test_get_device_map_unknown(self):
        """Test device map for unknown backend."""
        device_map = ModelLoader._get_device_map("unknown")
        assert device_map == "cpu"

    def test_get_torch_dtype(self):
        """Test torch dtype conversion."""
        # Skip if torch not available
        pytest.importorskip("torch")
        
        import torch
        
        dtype = ModelLoader._get_torch_dtype("fp32")
        assert dtype == torch.float32
        
        dtype = ModelLoader._get_torch_dtype("fp16")
        assert dtype == torch.float16

    def test_get_torch_dtype_unknown(self):
        """Test unknown dtype."""
        dtype = ModelLoader._get_torch_dtype("unknown")
        assert dtype is None
