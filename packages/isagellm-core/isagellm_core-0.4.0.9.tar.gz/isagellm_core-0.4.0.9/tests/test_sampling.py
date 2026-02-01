"""Tests for sampling utilities."""

from __future__ import annotations

import pytest

from sagellm_core.sampling import SamplingParams, GreedySampler


class TestSamplingParams:
    """Test SamplingParams."""

    def test_default_params(self):
        """Test default parameters."""
        params = SamplingParams()
        assert params.temperature == 1.0
        assert params.top_k == -1
        assert params.top_p == 1.0
        assert params.max_tokens == 128
        assert params.do_sample is False

    def test_greedy_params(self):
        """Test greedy sampling parameters."""
        params = SamplingParams.greedy(max_tokens=64)
        assert params.temperature == 1.0
        assert params.top_k == -1
        assert params.top_p == 1.0
        assert params.max_tokens == 64
        assert params.do_sample is False

    def test_sampling_params(self):
        """Test sampling parameters."""
        params = SamplingParams.sampling(
            temperature=0.8, top_k=50, top_p=0.95, max_tokens=100
        )
        assert params.temperature == 0.8
        assert params.top_k == 50
        assert params.top_p == 0.95
        assert params.max_tokens == 100
        assert params.do_sample is True

    def test_invalid_temperature(self):
        """Test invalid temperature."""
        with pytest.raises(ValueError, match="temperature must be > 0"):
            SamplingParams(temperature=0.0)

    def test_invalid_top_p(self):
        """Test invalid top_p."""
        with pytest.raises(ValueError, match="top_p must be in"):
            SamplingParams(top_p=1.5)

    def test_invalid_max_tokens(self):
        """Test invalid max_tokens."""
        with pytest.raises(ValueError, match="max_tokens must be > 0"):
            SamplingParams(max_tokens=0)


class TestGreedySampler:
    """Test GreedySampler."""

    def test_sample_tensor(self):
        """Test sampling from tensor."""
        torch = pytest.importorskip("torch")
        
        sampler = GreedySampler()
        logits = torch.tensor([1.0, 3.0, 2.0])
        
        token_id = sampler.sample(logits)
        assert token_id == 1  # Index of max value

    def test_sample_numpy(self):
        """Test sampling from numpy array."""
        pytest.importorskip("torch")
        import numpy as np
        
        sampler = GreedySampler()
        logits = np.array([1.0, 3.0, 2.0])
        
        token_id = sampler.sample(logits)
        assert token_id == 1
