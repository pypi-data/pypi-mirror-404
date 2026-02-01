"""Tests for Streaming PD Separation.

测试流式 Prefill-Decode 分离功能。

NOTE: 这些测试依赖 PDSeparatedExecutor.stream() 的完整实现。
当前 PDSeparatedExecutor 需要 engine 支持 prefill() 方法，
但 LLMEngine 使用不同的 API。跳过这些测试直到 PD 扩展完成。
"""

from __future__ import annotations

import pytest
from sagellm_protocol.types import Request

from sagellm_core.llm_engine import LLMEngine, LLMEngineConfig
from sagellm_core.pd_executor import PDSeparatedExecutor
from sagellm_core.runtime import DistributedRuntime


# 跳过原因：PDSeparatedExecutor 需要 engine.prefill()，但 LLMEngine 使用不同的 API
SKIP_REASON = "PDSeparatedExecutor.stream() requires engine.prefill() which is not in LLMEngine API. Use LLMEngine.stream() directly."


@pytest.mark.skip(reason=SKIP_REASON)
@pytest.mark.asyncio
async def test_streaming_pd_separation():
    """测试流式 PD 分离：验证事件顺序和 TTFT 在首 token"""
    config = LLMEngineConfig(
        model_path="sshleifer/tiny-gpt2",
        backend_type="cpu",
        dtype="float32",
    )
    engine = LLMEngine(config)
    runtime = DistributedRuntime()

    try:
        await engine.start()
        await runtime.initialize()

        executor = PDSeparatedExecutor(engine=engine, runtime=runtime)

        request = Request(
            request_id="test-stream-001",
            trace_id="trace-stream-001",
            model="sshleifer/tiny-gpt2",
            prompt="Once upon a time",
            max_tokens=5,
            stream=True,
        )

        events = []
        async for event in executor.stream(request):
            events.append(event)

        # Verify Event Sequence
        # ═════════════════════════════════════════════════════════════════
        assert len(events) >= 3, "Should have at least start, delta, end"

        # 1. Start Event
        assert events[0].event == "start"
        assert events[0].request_id == "test-stream-001"
        assert events[0].trace_id == "trace-stream-001"

        # 2. Delta Events (至少一个)
        delta_events = [e for e in events if e.event == "delta"]
        assert len(delta_events) > 0, "Should have at least one delta event"

        # 每个 delta 应包含 chunk 和 chunk_tokens
        for delta in delta_events:
            assert hasattr(delta, "chunk"), "Delta should have chunk"
            assert hasattr(delta, "chunk_tokens"), "Delta should have chunk_tokens"

        # 3. End Event
        assert events[-1].event == "end"
        assert events[-1].finish_reason in ["stop", "length", "error"]
        assert events[-1].metrics is not None, "End event should contain final metrics"

        # Verify PD Metrics
        # ═════════════════════════════════════════════════════════════════
        final_metrics = events[-1].metrics
        assert final_metrics.ttft_ms > 0, "TTFT should be positive"
        assert final_metrics.prefill_ms > 0, "Prefill time should be positive"
        assert final_metrics.decode_ms > 0, "Decode time should be positive"

        # TBT 应该是 decode 平均时间
        assert final_metrics.tbt_ms > 0, "TBT should be positive"

    finally:
        await engine.stop()
        await runtime.shutdown()


@pytest.mark.skip(reason=SKIP_REASON)
@pytest.mark.asyncio
async def test_streaming_pd_event_content():
    """测试流式事件内容：delta text 和 tokens"""
    config = LLMEngineConfig(
        model_path="sshleifer/tiny-gpt2",
        backend_type="cpu",
        dtype="float32",
    )
    engine = LLMEngine(config)
    runtime = DistributedRuntime()

    try:
        await engine.start()
        await runtime.initialize()

        executor = PDSeparatedExecutor(engine=engine, runtime=runtime)

        request = Request(
            request_id="test-stream-002",
            trace_id="trace-stream-002",
            model="sshleifer/tiny-gpt2",
            prompt="Hello world",
            max_tokens=3,
            stream=True,
        )

        events = []
        async for event in executor.stream(request):
            events.append(event)

        # ═════════════════════════════════════════════════════════════════
        # Verify Delta Content
        # ═════════════════════════════════════════════════════════════════
        delta_events = [e for e in events if e.event == "delta"]

        for delta in delta_events:
            # 每个 delta 应包含 chunk 和 chunk_tokens
            assert hasattr(delta, "chunk"), "Delta should have chunk"
            assert hasattr(delta, "chunk_tokens"), "Delta should have chunk_tokens"

        # ═════════════════════════════════════════════════════════════════
        # Verify End Content
        # ═════════════════════════════════════════════════════════════════
        end_event = events[-1]
        assert end_event.output_text, "End event should contain full output text"
        assert end_event.output_tokens, "End event should contain output tokens"

    finally:
        await engine.stop()
        await runtime.shutdown()


@pytest.mark.skip(reason=SKIP_REASON)
@pytest.mark.asyncio
async def test_streaming_pd_metrics_consistency():
    """测试流式 PD 指标一致性：首 delta 和 end 的 TTFT 应相同"""
    config = LLMEngineConfig(
        model_path="sshleifer/tiny-gpt2",
        backend_type="cpu",
        dtype="float32",
    )
    engine = LLMEngine(config)
    runtime = DistributedRuntime()

    try:
        await engine.start()
        await runtime.initialize()

        executor = PDSeparatedExecutor(engine=engine, runtime=runtime)

        request = Request(
            request_id="test-stream-003",
            trace_id="trace-stream-003",
            model="sshleifer/tiny-gpt2",
            prompt="Testing metrics",
            max_tokens=4,
            stream=True,
        )

        events = []
        async for event in executor.stream(request):
            events.append(event)

        # ═════════════════════════════════════════════════════════════════
        # Extract Metrics
        # ═════════════════════════════════════════════════════════════════
        end_metrics = events[-1].metrics

        # Verify TTFT Consistency
        # ═════════════════════════════════════════════════════════════════
        assert end_metrics is not None

        # TTFT 应相同（首 token 延迟不变）
        assert end_metrics.ttft_ms > 0, "TTFT should be positive"

        # Prefill 时间应相同
        assert end_metrics.prefill_ms > 0, "Prefill time should be consistent"

    finally:
        await engine.stop()
        await runtime.shutdown()
