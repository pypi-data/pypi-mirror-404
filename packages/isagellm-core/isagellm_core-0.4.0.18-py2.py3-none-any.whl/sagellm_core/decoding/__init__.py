from __future__ import annotations

from sagellm_protocol.sampling import DecodingStrategy, SamplingParams

from sagellm_core.decoding.base import DecodingStrategyBase
from sagellm_core.decoding.beam_search import BeamSearchDecoding
from sagellm_core.decoding.contrastive import ContrastiveSearchDecoding
from sagellm_core.decoding.greedy import GreedyDecoding
from sagellm_core.decoding.sampling import SamplingDecoding


def create_decoding_strategy(params: SamplingParams) -> DecodingStrategyBase:
    """工厂函数：根据 SamplingParams 创建解码策略

    Args:
        params: 采样参数配置

    Returns:
        对应的解码策略实例

    Raises:
        ValueError: 不支持的解码策略
    """
    if params.strategy == DecodingStrategy.GREEDY:
        return GreedyDecoding(params)
    elif params.strategy == DecodingStrategy.SAMPLING:
        return SamplingDecoding(params)
    elif params.strategy == DecodingStrategy.BEAM_SEARCH:
        return BeamSearchDecoding(params)
    elif params.strategy == DecodingStrategy.CONTRASTIVE:
        return ContrastiveSearchDecoding(params)
    else:
        raise ValueError(f"Unsupported decoding strategy: {params.strategy}")


__all__ = [
    "DecodingStrategyBase",
    "GreedyDecoding",
    "SamplingDecoding",
    "BeamSearchDecoding",
    "ContrastiveSearchDecoding",
    "create_decoding_strategy",
]
