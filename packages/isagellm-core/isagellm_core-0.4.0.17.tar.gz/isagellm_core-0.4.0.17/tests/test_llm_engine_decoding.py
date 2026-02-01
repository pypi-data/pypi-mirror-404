"""集成测试：LLMEngine + 解码策略系统

测试 LLMEngine 与解码策略的完整集成，包括：
- 默认贪婪解码行为
- 向后兼容的参数传递
- SamplingParams 对象使用
- 参数优先级处理
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from sagellm_core import LLMEngine, LLMEngineConfig
from sagellm_protocol.sampling import DecodingStrategy, SamplingParams


@pytest_asyncio.fixture
async def engine():
    """创建测试用 LLMEngine 实例"""
    config = LLMEngineConfig(
        model_path="sshleifer/tiny-gpt2",  # 使用小模型快速测试
        backend_type="cpu",
        max_new_tokens=20,
    )
    engine = LLMEngine(config)
    await engine.start()
    yield engine
    await engine.stop()


@pytest.mark.asyncio
async def test_default_greedy_decoding(engine):
    """测试默认参数使用贪婪解码（temperature=0.0）"""
    response = await engine.generate("Hello, how are")

    assert response.output_text is not None
    assert len(response.output_text) > 0
    assert response.metrics.ttft_ms is not None
    print(f"✓ 默认贪婪解码输出: {response.output_text[:100]}...")


@pytest.mark.asyncio
async def test_backward_compatible_params(engine):
    """测试向后兼容的参数传递"""
    response = await engine.generate("The weather today is", temperature=0.8, top_p=0.9, top_k=50)

    assert response.output_text is not None
    assert len(response.output_text) > 0
    print(f"✓ 向后兼容参数输出: {response.output_text[:100]}...")


@pytest.mark.asyncio
async def test_sampling_params_object(engine):
    """测试使用 SamplingParams 对象（推荐方式）"""
    params = SamplingParams(
        strategy=DecodingStrategy.SAMPLING,
        max_tokens=15,
        temperature=0.7,
        top_p=0.9,
        top_k=40,
    )

    response = await engine.generate("Once upon a time", sampling_params=params)

    assert response.output_text is not None
    assert len(response.output_text) > 0
    print(f"✓ SamplingParams 对象输出: {response.output_text[:100]}...")


@pytest.mark.asyncio
async def test_sampling_params_override(engine):
    """测试 SamplingParams 覆盖向后兼容参数"""
    # SamplingParams 应优先于单独参数
    params = SamplingParams(
        strategy=DecodingStrategy.GREEDY,
        temperature=0.0,  # 贪婪解码
    )

    response = await engine.generate(
        "Hello",
        temperature=0.9,  # 这个会被 SamplingParams 覆盖
        sampling_params=params,
    )

    assert response.output_text is not None
    assert len(response.output_text) > 0
    print(f"✓ 参数优先级测试输出: {response.output_text[:100]}...")


@pytest.mark.asyncio
async def test_reproducible_sampling(engine):
    """测试使用 seed 的可复现采样"""
    params = SamplingParams(
        strategy=DecodingStrategy.SAMPLING,
        temperature=0.7,
        top_p=0.9,
        seed=42,
        max_tokens=10,
    )

    response1 = await engine.generate("Hello", sampling_params=params)
    response2 = await engine.generate("Hello", sampling_params=params)

    # 相同 seed 应产生相同结果
    assert response1.output_text == response2.output_text
    print(f"✓ 可复现采样输出: {response1.output_text}")
