"""LLM Engine error handling and failure modes (Async API).

Tests verify that LLMEngine follows fail-fast principle:
- No silent fallbacks
- Clear error messages
- Explicit failures on invalid input

NOTE: Tests using real model loading are marked @pytest.mark.slow.
"""

from __future__ import annotations

import pytest

from sagellm_core import LLMEngine, LLMEngineConfig
from sagellm_protocol import Request


@pytest.mark.llm_engine
class TestLLMEngineErrorHandling:
    """Verify LLMEngine error handling follows fail-fast principle."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_execute_without_start_fails(self, tiny_model) -> None:
        """Fail-fast: Inference before starting engine must fail explicitly."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
            max_new_tokens=5,
        )
        engine = LLMEngine(config)
        # Deliberately not calling start()

        request = Request(
            request_id="error-001",
            trace_id="error-trace",
            model="dummy",
            prompt="This should fail",
            max_tokens=5,
            stream=False,
        )

        # Should raise exception, not return empty response
        with pytest.raises(RuntimeError, match="not running|not started") as exc_info:
            await engine.execute(request)

        # Error should be clear
        error_msg = str(exc_info.value).lower()
        assert "not" in error_msg

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_stream_without_start_fails(self, tiny_model) -> None:
        """Fail-fast: Streaming before starting engine must fail explicitly."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
            max_new_tokens=5,
        )
        engine = LLMEngine(config)
        # Deliberately not calling start()

        request = Request(
            request_id="error-002",
            trace_id="error-trace",
            model="dummy",
            prompt="Stream should fail",
            max_tokens=5,
            stream=True,
        )

        # Should raise exception, not yield empty events
        with pytest.raises(RuntimeError, match="not running|not started"):
            async for _ in engine.stream(request):
                pass

    def test_invalid_config_type_fails(self) -> None:
        """Fail-fast: Invalid config type must fail at creation."""
        # Passing wrong type for config
        with pytest.raises((TypeError, ValueError, AttributeError)):
            # Should fail because we're passing a dict instead of config
            LLMEngine({"model_path": "test"})  # type: ignore

    def test_unavailable_backend_fails(self) -> None:
        """Fail-fast: Requesting unavailable backend must fail clearly."""
        config = LLMEngineConfig(
            model_path="test-model",
            backend_type="nonexistent",  # Invalid backend
            max_new_tokens=10,
        )

        with pytest.raises(ValueError, match="Unknown backend|not available|not found"):
            LLMEngine(config)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_invalid_max_tokens_fails_gracefully(self, llm_engine) -> None:
        """Fail-fast: Invalid max_tokens should fail with clear error."""
        # Protocol v0.1 validates max_tokens > 0 at Request creation time
        # So creating the Request itself should fail with ValidationError
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            request = Request(
                request_id="error-003",
                trace_id="error-trace",
                model="sshleifer/tiny-gpt2",
                prompt="Test",
                max_tokens=-5,  # Invalid - pydantic validation will fail
                stream=False,
            )

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self, llm_engine) -> None:
        """Behavior test: Empty prompt handling."""
        request = Request(
            request_id="error-004",
            trace_id="error-trace",
            model="sshleifer/tiny-gpt2",
            prompt="",  # Empty prompt
            max_tokens=5,
            stream=False,
        )

        # Different handling is acceptable:
        # Either: (1) raise error, or (2) return valid response with empty/default text
        try:
            response = await llm_engine.execute(request)
            # If it succeeds, should return a valid Response
            assert hasattr(response, "request_id")
            assert response.request_id == "error-004"
        except Exception:
            # If it fails, that's also acceptable (fail-fast)
            pass


@pytest.mark.llm_engine
class TestLLMEngineConfigValidation:
    """Test configuration validation at engine creation."""

    def test_valid_config_accepted(self) -> None:
        """Valid config should create engine successfully."""
        config = LLMEngineConfig(
            model_path="sshleifer/tiny-gpt2",
            backend_type="cpu",
            max_new_tokens=32,
        )

        engine = LLMEngine(config)
        assert engine is not None
        assert engine.config == config

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_auto_backend_selection(self) -> None:
        """Auto backend should select cpu when cuda/ascend not available."""
        config = LLMEngineConfig(
            model_path="sshleifer/tiny-gpt2",
            backend_type="auto",
            max_new_tokens=32,
        )

        engine = LLMEngine(config)
        # Backend is initialized on start()
        await engine.start()
        # On CI/test machines without GPU, should default to cpu
        assert engine.backend is not None
        await engine.stop()


@pytest.mark.llm_engine
class TestLLMEngineLifecycleErrors:
    """Test error handling in engine lifecycle operations."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_double_start_handling(self, tiny_model) -> None:
        """Starting same engine twice should be handled."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
        )
        engine = LLMEngine(config)

        # First start
        await engine.start()
        assert engine.is_running

        # Second start - should either:
        # 1. Succeed (idempotent), or
        # 2. Raise error (fail-fast)
        try:
            await engine.start()
            # If succeeds, still running
            assert engine.is_running
        except RuntimeError:
            # If fails, that's also fine (fail-fast)
            pass
        finally:
            await engine.stop()

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_double_stop_handling(self, tiny_model) -> None:
        """Stopping same engine twice should be handled."""
        config = LLMEngineConfig(
            model_path=tiny_model,
            backend_type="cpu",
        )
        engine = LLMEngine(config)

        await engine.start()
        await engine.stop()
        assert not engine.is_running

        # Second stop - should either:
        # 1. Succeed (idempotent), or
        # 2. Raise error (fail-fast)
        try:
            await engine.stop()
            # If succeeds, still stopped
            assert not engine.is_running
        except RuntimeError:
            # If fails, that's also fine (fail-fast)
            pass

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_operations_after_stop_fail(self, llm_engine, tiny_model) -> None:
        """Operations after stop should fail explicitly."""
        # Stop the engine
        await llm_engine.stop()
        assert not llm_engine.is_running

        # Trying to execute after stop should fail
        request = Request(
            request_id="error-005",
            trace_id="error-trace",
            model=tiny_model,
            prompt="This should fail",
            max_tokens=5,
            stream=False,
        )

        with pytest.raises(RuntimeError, match="not running|not started"):
            await llm_engine.execute(request)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_health_check_after_stop(self, llm_engine) -> None:
        """Health check after stop should reflect unhealthy state."""
        await llm_engine.stop()

        health = await llm_engine.health_check()
        assert health is False
