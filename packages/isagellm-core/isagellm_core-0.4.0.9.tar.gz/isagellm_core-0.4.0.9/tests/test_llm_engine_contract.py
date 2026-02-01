"""Contract tests for LLMEngine - Protocol v0.1 compliance (Async API).

These tests verify that LLMEngine fully implements the engine protocol
and complies with Protocol v0.1 requirements. Uses tiny models to avoid
long model loading times in CI.

NOTE: All tests in this file require model loading and are marked @pytest.mark.slow.
Run with: pytest -m slow tests/test_llm_engine_contract.py
"""

from __future__ import annotations

import pytest

from sagellm_core import LLMEngine, LLMEngineConfig
from sagellm_protocol import Request, Response, StreamEventStart, StreamEventDelta, StreamEventEnd


@pytest.mark.llm_engine
@pytest.mark.contract
@pytest.mark.asyncio
class TestLLMEngineContract:
    """Verify LLMEngine fully implements engine Protocol."""

    @pytest.mark.slow
    async def test_llm_engine_implements_required_methods(self, llm_engine) -> None:
        """Contract: LLMEngine must implement all required methods."""
        required_methods = [
            "start",
            "stop",
            "execute",
            "stream",
            "health_check",
            "generate",
        ]

        for method in required_methods:
            assert hasattr(llm_engine, method), f"LLMEngine missing method: {method}"
            assert callable(getattr(llm_engine, method)), f"{method} must be callable"

    @pytest.mark.slow
    async def test_llm_engine_health_check_returns_bool(self, llm_engine) -> None:
        """Contract: health_check() must return bool."""
        health = await llm_engine.health_check()

        assert isinstance(health, bool)
        assert health is True  # Running engine should be healthy

    @pytest.mark.slow
    async def test_llm_engine_has_backend(self, llm_engine) -> None:
        """Contract: LLMEngine must have a backend provider."""
        assert llm_engine.backend is not None

    @pytest.mark.slow
    async def test_llm_engine_execute_returns_response(self, llm_engine, tiny_model) -> None:
        """Contract: execute() must accept Request and return Response."""
        request = Request(
            request_id="contract-llm-001",
            trace_id="contract-trace",
            model=tiny_model,
            prompt="Hello",
            max_tokens=5,  # Very short for fast test
            stream=False,
        )

        response = await llm_engine.execute(request)

        assert isinstance(response, Response)
        assert response.request_id == "contract-llm-001"
        assert response.output_text is not None
        assert len(response.output_text) > 0

    @pytest.mark.slow
    async def test_llm_engine_generate_returns_response(self, llm_engine) -> None:
        """Contract: generate() must return Response."""
        result = await llm_engine.generate("Hello world")

        assert isinstance(result, Response)
        assert len(result.output_text) > 0

    @pytest.mark.slow
    async def test_llm_engine_stream_yields_events(self, llm_engine, tiny_model) -> None:
        """Contract: stream() must yield StreamEvent objects."""
        request = Request(
            request_id="contract-llm-002",
            trace_id="contract-trace",
            model=tiny_model,
            prompt="Test",
            max_tokens=5,
            stream=True,
        )

        events = []
        async for event in llm_engine.stream(request):
            events.append(event)

        assert len(events) > 0
        for event in events:
            assert isinstance(event, (StreamEventStart, StreamEventDelta, StreamEventEnd))
            assert hasattr(event, "event")
            assert event.event in ["start", "delta", "end"]


@pytest.mark.llm_engine
@pytest.mark.contract
@pytest.mark.asyncio
class TestLLMEngineProtocolV01Compliance:
    """Verify LLMEngine complies with Protocol v0.1 requirements."""

    @pytest.mark.slow
    async def test_response_has_all_required_fields(self, llm_engine, tiny_model) -> None:
        """Protocol v0.1: Response must have all required fields."""
        request = Request(
            request_id="protocol-llm-001",
            trace_id="protocol-trace",
            model=tiny_model,
            prompt="Test",
            max_tokens=5,
            stream=False,
        )

        response = await llm_engine.execute(request)

        # Check required Protocol v0.1 fields
        assert hasattr(response, "request_id")
        assert hasattr(response, "trace_id")
        assert hasattr(response, "output_text")
        assert hasattr(response, "output_tokens")
        assert hasattr(response, "finish_reason")

        # Verify field values
        assert response.request_id == "protocol-llm-001"
        assert response.trace_id == "protocol-trace"
        assert isinstance(response.output_text, str)
        assert len(response.output_text) > 0

    @pytest.mark.slow
    async def test_metrics_compliance(self, llm_engine, tiny_model) -> None:
        """Protocol v0.1: Metrics must include required fields."""
        request = Request(
            request_id="metrics-llm-001",
            trace_id="metrics-trace",
            model=tiny_model,
            prompt="Metrics test",
            max_tokens=5,
            stream=False,
        )

        response = await llm_engine.execute(request)

        # Check if metrics are present
        if hasattr(response, "metrics") and response.metrics is not None:
            metrics = response.metrics
            # Protocol v0.1 required metric fields
            assert hasattr(metrics, "ttft_ms")
            assert metrics.ttft_ms >= 0

    @pytest.mark.slow
    async def test_stream_events_compliance(self, llm_engine, tiny_model) -> None:
        """Protocol v0.1: StreamEvent must follow spec."""
        request = Request(
            request_id="stream-llm-001",
            trace_id="stream-trace",
            model=tiny_model,
            prompt="Stream test",
            max_tokens=10,
            stream=True,
        )

        events = []
        async for event in llm_engine.stream(request):
            events.append(event)

        # Must have at least start and end events
        assert len(events) >= 2

        # First event should be 'start'
        assert events[0].event == "start"

        # Last event should be 'end'
        assert events[-1].event == "end"

        # Verify all events have request_id and trace_id
        for event in events:
            assert event.request_id == "stream-llm-001"
            assert event.trace_id == "stream-trace"


@pytest.mark.llm_engine
@pytest.mark.contract
@pytest.mark.asyncio
class TestLLMEngineBehaviorConsistency:
    """Verify LLMEngine behavior is consistent with contract expectations."""

    @pytest.mark.slow
    async def test_started_engine_health_is_healthy(self, llm_engine) -> None:
        """Contract: Started engine should report healthy (True)."""
        health = await llm_engine.health_check()
        assert health is True

    @pytest.mark.slow
    async def test_stopped_engine_not_healthy(self, tiny_model) -> None:
        """Contract: Stopped engine should not report healthy (False)."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
        )
        engine = LLMEngine(config)

        # Not started yet
        health = await engine.health_check()
        assert health is False

    @pytest.mark.slow
    async def test_multiple_requests_same_session(self, llm_engine, tiny_model) -> None:
        """Contract: Engine should handle multiple requests in same session."""
        # Send multiple requests
        for i in range(3):
            request = Request(
                request_id=f"multi-req-{i}",
                trace_id="multi-trace",
                model=tiny_model,
                prompt=f"Request {i}",
                max_tokens=5,
                stream=False,
            )

            response = await llm_engine.execute(request)
            assert response.request_id == f"multi-req-{i}"
            assert isinstance(response.output_text, str)
            assert len(response.output_text) > 0

    @pytest.mark.slow
    async def test_stop_after_start(self, tiny_model) -> None:
        """Contract: stop() should work after start()."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
        )
        engine = LLMEngine(config)

        await engine.start()
        assert engine.is_running

        # Should not raise
        await engine.stop()
        assert not engine.is_running

        # After stop, health should not be healthy
        health = await engine.health_check()
        assert health is False

    @pytest.mark.slow
    async def test_execute_after_stop_fails(self, llm_engine, tiny_model) -> None:
        """Contract: execute() after stop() should fail (fail-fast)."""
        # Stop the engine
        await llm_engine.stop()

        request = Request(
            request_id="after-stop-001",
            trace_id="after-stop-trace",
            model=tiny_model,
            prompt="Should fail",
            max_tokens=5,
            stream=False,
        )

        # Should raise exception
        with pytest.raises(RuntimeError, match="not running|not started"):
            await llm_engine.execute(request)


@pytest.mark.llm_engine
@pytest.mark.contract
@pytest.mark.asyncio
class TestLLMEngineBackendSelection:
    """Verify LLMEngine backend selection behavior."""

    @pytest.mark.slow
    async def test_auto_backend_selection(self, tiny_model) -> None:
        """Contract: auto backend should select available backend after start."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="auto",
        )
        engine = LLMEngine(config)

        # Backend is initialized on start()
        await engine.start()
        assert engine.backend is not None
        await engine.stop()

    @pytest.mark.slow
    async def test_cpu_backend_explicit(self, tiny_model) -> None:
        """Contract: cpu backend should be explicitly selectable."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
        )
        engine = LLMEngine(config)

        await engine.start()
        assert engine.backend is not None
        await engine.stop()

    def test_invalid_backend_fails(self, tiny_model) -> None:
        """Contract: invalid backend should fail fast."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="nonexistent",
        )

        with pytest.raises(ValueError):
            LLMEngine(config)
