"""End-to-end integration test for LLMEngine (Async API).

This test validates the complete pipeline:
1. Create LLMEngine configuration
2. Create and start LLMEngine
3. Perform real inference with tiny model
4. Validate response and metrics
5. Clean up resources

Uses sshleifer/tiny-gpt2 - a tiny model for testing (only a few MB).

NOTE: All tests in this file require real model loading and are marked @pytest.mark.slow.
Run with: pytest -m slow tests/test_e2e_llm_integration.py
"""

from __future__ import annotations

import pytest

from sagellm_core import LLMEngine, LLMEngineConfig
from sagellm_protocol import Request


@pytest.mark.skipif(
    not pytest.importorskip("sagellm_core"),
    reason="sagellm-core not installed",
)
@pytest.mark.llm_engine
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_llm_engine_inference(tiny_model):
    """Test end-to-end: LLMEngine + real inference with tiny model."""

    # 1. Create LLMEngine config
    config = LLMEngineConfig(
        model_path=tiny_model,
        backend_type="cpu",
        max_new_tokens=32,
    )

    # 2. Create LLMEngine
    engine = LLMEngine(config)
    assert engine is not None
    assert not engine.is_running

    # 3. Start engine (loads tiny model)
    await engine.start()
    assert engine.is_running

    # 4. Verify health status
    health = await engine.health_check()
    assert health is True

    # 5. Create inference request
    request = Request(
        request_id="e2e-001",
        trace_id="e2e-trace",
        model=tiny_model,
        prompt="Hello world",
        max_tokens=5,  # Very short to keep test fast
        stream=False,
    )

    # 6. Perform REAL inference
    response = await engine.execute(request)

    # 7. Validate response
    assert response is not None
    assert response.request_id == "e2e-001"
    assert response.trace_id == "e2e-trace"
    assert response.output_text is not None
    assert len(response.output_text) > 0
    assert response.output_tokens is not None
    assert len(response.output_tokens) > 0
    assert response.finish_reason == "stop"
    assert response.error is None

    # 8. Validate metrics
    assert response.metrics is not None
    assert response.metrics.ttft_ms > 0
    assert response.metrics.throughput_tps > 0

    # 9. Stop engine
    await engine.stop()
    assert not engine.is_running

    # 10. Verify health after stop
    health = await engine.health_check()
    assert health is False


@pytest.mark.skipif(
    not pytest.importorskip("sagellm_core"),
    reason="sagellm-core not installed",
)
@pytest.mark.llm_engine
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_llm_engine_streaming(tiny_model):
    """Test end-to-end streaming inference with LLMEngine."""

    # 1. Create and start LLMEngine
    config = LLMEngineConfig(
        model_path=tiny_model,
        backend_type="cpu",
        max_new_tokens=32,
    )
    engine = LLMEngine(config)
    await engine.start()

    # 2. Create streaming request
    request = Request(
        request_id="e2e-stream-001",
        trace_id="e2e-stream-trace",
        model=tiny_model,
        prompt="Test streaming",
        max_tokens=10,
        stream=True,
    )

    # 3. Perform streaming inference
    events = []
    async for event in engine.stream(request):
        events.append(event)

    # 4. Validate stream events
    assert len(events) >= 2  # At least start and end

    # Verify start event
    assert events[0].event == "start"
    assert events[0].request_id == "e2e-stream-001"

    # Verify end event
    assert events[-1].event == "end"
    assert events[-1].request_id == "e2e-stream-001"
    assert events[-1].finish_reason == "stop"

    # Verify end event metrics
    end_metrics = events[-1].metrics
    assert end_metrics is not None
    assert end_metrics.ttft_ms > 0

    # 5. Clean up
    await engine.stop()


@pytest.mark.skipif(
    not pytest.importorskip("sagellm_core"),
    reason="sagellm-core not installed",
)
@pytest.mark.llm_engine
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_llm_engine_multiple_requests(tiny_model):
    """Test end-to-end with multiple sequential requests."""

    # 1. Create and start LLMEngine
    config = LLMEngineConfig(
        model_path=tiny_model,
        backend_type="cpu",
        max_new_tokens=32,
    )
    engine = LLMEngine(config)
    await engine.start()

    # 2. Send multiple requests
    for i in range(3):
        request = Request(
            request_id=f"e2e-multi-{i}",
            trace_id="e2e-multi-trace",
            model=tiny_model,
            prompt=f"Request {i}",
            max_tokens=5,
            stream=False,
        )

        response = await engine.execute(request)

        # Verify each response
        assert response.request_id == f"e2e-multi-{i}"
        assert response.output_text is not None
        assert len(response.output_text) > 0
        assert response.metrics is not None
        assert response.metrics.ttft_ms > 0

    # 3. Clean up
    await engine.stop()


@pytest.mark.skipif(
    not pytest.importorskip("sagellm_core"),
    reason="sagellm-core not installed",
)
@pytest.mark.llm_engine
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_llm_engine_lifecycle(tiny_model):
    """Test complete engine lifecycle: create -> start -> execute -> stop."""

    config = LLMEngineConfig(
        model_path=tiny_model,
        backend_type="cpu",
        max_new_tokens=32,
    )
    engine = LLMEngine(config)

    # Initially not running
    assert not engine.is_running
    health = await engine.health_check()
    assert health is False

    # Start engine
    await engine.start()
    assert engine.is_running
    health = await engine.health_check()
    assert health is True

    # Execute request
    request = Request(
        request_id="e2e-lifecycle",
        trace_id="e2e-trace",
        model=tiny_model,
        prompt="Lifecycle test",
        max_tokens=5,
        stream=False,
    )
    response = await engine.execute(request)
    assert response.request_id == "e2e-lifecycle"

    # Stop engine
    await engine.stop()
    assert not engine.is_running
    health = await engine.health_check()
    assert health is False


@pytest.mark.skipif(
    not pytest.importorskip("sagellm_core"),
    reason="sagellm-core not installed",
)
@pytest.mark.llm_engine
@pytest.mark.slow
@pytest.mark.asyncio
async def test_e2e_llm_engine_auto_backend_selection(tiny_model):
    """Test LLMEngine with auto backend selection."""

    # Create engine with auto backend selection
    config = LLMEngineConfig(
        model_path=tiny_model,
        backend_type="auto",  # Auto-select best available backend
        max_new_tokens=32,
    )
    engine = LLMEngine(config)

    # Backend is initialized on start(), not creation
    await engine.start()
    assert engine.is_running
    assert engine.backend is not None  # Now backend should be set

    # Verify inference works
    request = Request(
        request_id="auto-backend",
        trace_id="auto-trace",
        model=tiny_model,
        prompt="Auto backend test",
        max_tokens=5,
        stream=False,
    )
    response = await engine.execute(request)
    assert response.output_text is not None

    await engine.stop()
