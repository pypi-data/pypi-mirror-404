"""LLMEngine behavior validation tests.

These tests validate LLMEngine behavior using a tiny model.
All tests use CPU backend for validation (no GPU required).
"""

from __future__ import annotations

import pytest

from sagellm_core import LLMEngine, LLMEngineConfig
from sagellm_protocol import Request, Response


@pytest.mark.slow
@pytest.mark.asyncio
class TestLLMEngineBehavior:
    """Validate LLMEngine behavior."""

    async def test_llm_engine_has_required_methods(self, llm_engine) -> None:
        """LLMEngine must expose all required methods."""
        required_methods = [
            "start",
            "stop",
            "execute",
            "stream",
            "generate",
        ]

        for method in required_methods:
            assert hasattr(llm_engine, method), f"LLMEngine missing {method}"
            assert callable(getattr(llm_engine, method)), f"{method} must be callable"

    async def test_llm_engine_execute_returns_response(self, llm_engine) -> None:
        """LLMEngine execute returns Response."""
        request = Request(
            request_id="llm-001",
            trace_id="llm-trace",
            model="sshleifer/tiny-gpt2",
            prompt="Test prompt",
            max_tokens=16,
            stream=False,
        )

        response = await llm_engine.execute(request)

        assert isinstance(response, Response)
        assert response.request_id == "llm-001"
        assert response.output_text is not None

    async def test_llm_engine_stream_yields_events(self, llm_engine) -> None:
        """LLMEngine stream yields events."""
        events = []
        async for event in llm_engine.stream("Stream test", max_tokens=5):
            events.append(event)

        assert len(events) >= 2
        assert events[0].event == "start"
        assert events[-1].event == "end"

    async def test_llm_execute_before_start_fails(self, tiny_model) -> None:
        """LLMEngine must fail when execute() called before start()."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
            max_new_tokens=16,
        )
        engine = LLMEngine(config)

        request = Request(
            request_id="error-001",
            trace_id="error-trace",
            model=tiny_model,
            prompt="Should fail",
            max_tokens=16,
            stream=False,
        )

        with pytest.raises(RuntimeError, match="not running|not started"):
            await engine.execute(request)

    async def test_llm_stream_before_start_fails(self, tiny_model) -> None:
        """LLMEngine must fail when stream() called before start()."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
            max_new_tokens=16,
        )
        engine = LLMEngine(config)

        request = Request(
            request_id="error-002",
            trace_id="error-trace",
            model=tiny_model,
            prompt="Should fail",
            max_tokens=16,
            stream=True,
        )

        with pytest.raises(RuntimeError, match="not running|not started"):
            async for _ in engine.stream(request):
                pass

    async def test_llm_start_stop_cycle(self, tiny_model) -> None:
        """LLMEngine must support start -> stop cycle."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
            max_new_tokens=16,
        )
        engine = LLMEngine(config)

        assert not engine.is_running
        await engine.start()
        assert engine.is_running

        await engine.stop()
        assert not engine.is_running


class TestEngineErrorHandlingParity:
    """Test error handling parity between engines."""

    pass
