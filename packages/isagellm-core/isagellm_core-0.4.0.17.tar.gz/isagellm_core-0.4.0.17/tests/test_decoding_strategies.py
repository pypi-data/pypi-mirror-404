"""Tests for decoding strategies"""

from __future__ import annotations

import pytest

from sagellm_protocol.sampling import DecodingStrategy, SamplingParams

from sagellm_core.decoding import (
    BeamSearchDecoding,
    ContrastiveSearchDecoding,
    GreedyDecoding,
    SamplingDecoding,
    create_decoding_strategy,
)


class TestSamplingParamsInference:
    """Test SamplingParams automatic strategy inference

    用户可以通过参数推断策略，而不是显式指定 strategy。
    例如：temperature > 1.0 自动触发 SAMPLING 策略。
    """

    def test_default_is_greedy(self):
        """默认应该是贪婪解码"""
        params = SamplingParams()
        assert params.strategy == DecodingStrategy.GREEDY
        # Note: is_greedy 等辅助属性需要在 sagellm-protocol 中实现

    def test_explicit_greedy(self):
        """显式指定 GREEDY 策略"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        assert params.strategy == DecodingStrategy.GREEDY

    def test_explicit_sampling(self):
        """显式指定 SAMPLING 策略（即使 temperature=1.0）"""
        params = SamplingParams(strategy=DecodingStrategy.SAMPLING, temperature=0.7)
        assert params.strategy == DecodingStrategy.SAMPLING

    def test_explicit_beam_search(self):
        """显式指定 BEAM_SEARCH 策略"""
        params = SamplingParams(strategy=DecodingStrategy.BEAM_SEARCH, beam_size=5)
        assert params.strategy == DecodingStrategy.BEAM_SEARCH

    def test_explicit_contrastive(self):
        """显式指定 CONTRASTIVE 策略"""
        params = SamplingParams(
            strategy=DecodingStrategy.CONTRASTIVE,
            penalty_alpha=0.6,
        )
        assert params.strategy == DecodingStrategy.CONTRASTIVE


class TestGreedyDecoding:
    """Test greedy decoding strategy"""

    def test_greedy_basic(self):
        """Test basic greedy decoding"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY, max_tokens=100)
        strategy = GreedyDecoding(params)

        assert strategy.get_strategy_name() == "Greedy Decoding"

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["max_new_tokens"] == 100
        assert kwargs["do_sample"] is False
        assert "pad_token_id" in kwargs


class TestSamplingDecoding:
    """Test temperature sampling strategy"""

    def test_sampling_basic(self):
        """Test basic temperature sampling"""
        params = SamplingParams(
            strategy=DecodingStrategy.SAMPLING, temperature=0.7, top_p=0.9, max_tokens=200
        )
        strategy = SamplingDecoding(params)

        assert "Temperature Sampling" in strategy.get_strategy_name()

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["max_new_tokens"] == 200
        assert kwargs["do_sample"] is True
        assert kwargs["temperature"] == 0.7
        assert kwargs["top_p"] == 0.9

    def test_sampling_with_top_k(self):
        """Test sampling with top_k"""
        params = SamplingParams(
            strategy=DecodingStrategy.SAMPLING,
            temperature=0.8,
            top_k=50,
            max_tokens=150,
        )
        strategy = SamplingDecoding(params)

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["top_k"] == 50

    def test_sampling_with_repetition_penalty(self):
        """Test sampling with repetition penalty"""
        params = SamplingParams(
            strategy=DecodingStrategy.SAMPLING,
            temperature=0.7,
            repetition_penalty=1.2,
            max_tokens=150,
        )
        strategy = SamplingDecoding(params)

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["repetition_penalty"] == 1.2


class TestBeamSearchDecoding:
    """Test beam search strategy"""

    def test_beam_search_basic(self):
        """Test basic beam search"""
        params = SamplingParams(
            strategy=DecodingStrategy.BEAM_SEARCH,
            beam_size=5,
            length_penalty=0.8,
            max_tokens=150,
        )
        strategy = BeamSearchDecoding(params)

        assert "Beam Search" in strategy.get_strategy_name()
        assert "beams=5" in strategy.get_strategy_name()

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["max_new_tokens"] == 150
        assert kwargs["num_beams"] == 5
        assert kwargs["length_penalty"] == 0.8
        assert kwargs["early_stopping"] is True


class TestContrastiveSearchDecoding:
    """Test contrastive search strategy"""

    def test_contrastive_basic(self):
        """Test basic contrastive search"""
        params = SamplingParams(
            strategy=DecodingStrategy.CONTRASTIVE, penalty_alpha=0.6, max_tokens=300
        )
        strategy = ContrastiveSearchDecoding(params)

        assert "Contrastive Search" in strategy.get_strategy_name()
        assert "alpha=0.60" in strategy.get_strategy_name()

        kwargs = strategy.to_generate_kwargs()
        assert kwargs["max_new_tokens"] == 300
        assert kwargs["penalty_alpha"] == 0.6
        assert kwargs["top_k"] == 4  # Default for contrastive search


class TestDecodingStrategyFactory:
    """Test strategy factory function"""

    def test_create_greedy(self):
        """Test creating greedy strategy"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        strategy = create_decoding_strategy(params)
        assert isinstance(strategy, GreedyDecoding)

    def test_create_sampling(self):
        """Test creating sampling strategy"""
        params = SamplingParams(strategy=DecodingStrategy.SAMPLING, temperature=0.7)
        strategy = create_decoding_strategy(params)
        assert isinstance(strategy, SamplingDecoding)

    def test_create_beam_search(self):
        """Test creating beam search strategy"""
        params = SamplingParams(strategy=DecodingStrategy.BEAM_SEARCH, beam_size=4)
        strategy = create_decoding_strategy(params)
        assert isinstance(strategy, BeamSearchDecoding)

    def test_create_contrastive(self):
        """Test creating contrastive strategy"""
        params = SamplingParams(strategy=DecodingStrategy.CONTRASTIVE, penalty_alpha=0.6)
        strategy = create_decoding_strategy(params)
        assert isinstance(strategy, ContrastiveSearchDecoding)

    def test_unsupported_strategy(self):
        """Test unsupported strategy raises error"""
        params = SamplingParams(strategy=DecodingStrategy.GREEDY)
        # Manually set invalid strategy
        params.strategy = "invalid_strategy"  # type: ignore

        with pytest.raises(ValueError, match="Unsupported decoding strategy"):
            create_decoding_strategy(params)
