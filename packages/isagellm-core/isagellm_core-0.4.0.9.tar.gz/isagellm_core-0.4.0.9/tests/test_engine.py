"""Tests for engine interface

Updated to use new async API: start/stop/execute/stream/health_check.
"""

from __future__ import annotations

import pytest

from sagellm_core.engine import BaseEngine, EngineInstanceConfig
from sagellm_core.health import HealthStatus
from sagellm_protocol import (
    Metrics,
    Request,
    Response,
    StreamEventDelta,
    StreamEventEnd,
    StreamEventStart,
)


class MockLLMEngine(BaseEngine):
    """Lightweight mock LLM engine for testing BaseEngine interface."""

    @classmethod
    def is_available(cls) -> bool:
        return True

    @classmethod
    def priority(cls) -> int:
        return 0

    @classmethod
    def backend_type(cls) -> str:
        return "cpu"

    async def start(self) -> None:
        self._is_running = True

    async def stop(self) -> None:
        self._is_running = False

    async def health_check(self) -> bool:
        return self._is_running

    async def prefill(self, request: Request) -> dict:
        """Minimal prefill implementation for testing."""
        if not self._is_running:
            raise RuntimeError("not running")
        return {
            "kv_handle": {"test": "handle"},
            "num_tokens": len(request.prompt.split()) if request.prompt else 0,
            "first_token_id": 1,
        }

    async def decode(self, request: Request, kv_handle=None, max_new_tokens=None) -> dict:
        """Minimal decode implementation for testing."""
        if not self._is_running:
            raise RuntimeError("not running")
        num_tokens = max_new_tokens or request.max_tokens
        return {
            "output_tokens": [1, 2, 3][:num_tokens],
            "output_text": "test output",
            "finish_reason": "stop",
            "num_tokens": min(3, num_tokens),
        }

    async def execute(self, request: Request) -> Response:
        if not self._is_running:
            raise RuntimeError("not running")
        metrics = Metrics(
            ttft_ms=0.0,
            tbt_ms=0.0,
            tpot_ms=0.0,
            throughput_tps=0.0,
            peak_mem_mb=0,
            error_rate=0.0,
            kv_used_tokens=0,
            kv_used_bytes=0,
            prefix_hit_rate=0.0,
            evict_count=0,
            evict_ms=0.0,
            spec_accept_rate=0.0,
        )
        return Response(
            request_id=request.request_id,
            trace_id=request.trace_id,
            output_text=f"{request.prompt} [ok]",
            output_tokens=[1, 2, 3],
            finish_reason="stop",
            metrics=metrics,
            error=None,
        )

    async def stream(self, request: Request):
        if not self._is_running:
            raise RuntimeError("not running")
        yield StreamEventStart(
            request_id=request.request_id,
            trace_id=request.trace_id,
            engine_id=self.engine_id,
            prompt_tokens=None,
        )
        yield StreamEventDelta(
            request_id=request.request_id,
            trace_id=request.trace_id,
            engine_id=self.engine_id,
            chunk="ok",
            chunk_tokens=[1],
        )
        metrics = Metrics(
            ttft_ms=0.0,
            tbt_ms=0.0,
            tpot_ms=0.0,
            throughput_tps=0.0,
            peak_mem_mb=0,
            error_rate=0.0,
            kv_used_tokens=0,
            kv_used_bytes=0,
            prefix_hit_rate=0.0,
            evict_count=0,
            evict_ms=0.0,
            spec_accept_rate=0.0,
        )
        yield StreamEventEnd(
            request_id=request.request_id,
            trace_id=request.trace_id,
            engine_id=self.engine_id,
            output_text="ok",
            output_tokens=[1],
            finish_reason="stop",
            metrics=metrics,
            error=None,
        )


def test_base_engine_interface() -> None:
    """Test BaseEngine interface definition"""
    # BaseEngine is ABC, check required methods
    required_methods = [
        "start",
        "stop",
        "execute",
        "stream",
        "health_check",
        "is_available",
        "priority",
        "backend_type",
    ]

    for method in required_methods:
        assert hasattr(BaseEngine, method), f"BaseEngine missing method: {method}"


def test_health_status_enum() -> None:
    """Test HealthStatus enum"""
    assert HealthStatus.HEALTHY.name == "HEALTHY"
    assert HealthStatus.DEGRADED.name == "DEGRADED"
    assert HealthStatus.UNHEALTHY.name == "UNHEALTHY"


@pytest.mark.skip(reason="TestCPUEngine has been removed in favor of LLMEngine")
def test_create_cpu_test_engine() -> None:
    """Test creating lightweight CPU test engine instance"""
    config = EngineInstanceConfig(engine_id="test-cpu-1", model_path="sshleifer/tiny-gpt2")
    engine = TestCPUEngine(config)

    assert engine is not None
    assert hasattr(engine, "start")
    assert hasattr(engine, "execute")
    assert hasattr(engine, "stream")


def test_create_engine_invalid_config() -> None:
    """Test creating engine with invalid configuration"""
    # Missing engine_id should raise ValueError
    with pytest.raises(ValueError, match="engine_id is required"):
        EngineInstanceConfig(engine_id="", model_path=None, device="cpu")


@pytest.mark.asyncio
async def test_engine_start_stop() -> None:
    """Test engine start and stop lifecycle"""
    from sagellm_core import LLMEngine
    from sagellm_core.llm_engine import LLMEngineConfig

    config = LLMEngineConfig(model_path="sshleifer/tiny-gpt2", backend_type="cpu")
    engine = LLMEngine(config=config)

    # Initially not running
    assert not engine.is_running

    # Start engine
    await engine.start()
    assert engine.is_running

    # Health check should return True when running
    health = await engine.health_check()
    assert health is True

    # Stop engine
    await engine.stop()
    assert not engine.is_running


@pytest.mark.asyncio
async def test_engine_execute() -> None:
    """Test engine execute method"""
    from sagellm_core import LLMEngine
    from sagellm_core.llm_engine import LLMEngineConfig

    config = LLMEngineConfig(model_path="sshleifer/tiny-gpt2", backend_type="cpu")
    engine = LLMEngine(config=config)
    await engine.start()

    request = Request(
        request_id="test-001",
        trace_id="trace-001",
        model="test-model",
        prompt="Hello",
        max_tokens=10,
        stream=False,
    )

    response = await engine.execute(request)

    assert response.request_id == "test-001"
    assert response.trace_id == "trace-001"
    assert response.output_text is not None
    assert len(response.output_tokens) > 0
    assert response.metrics is not None

    await engine.stop()


@pytest.mark.asyncio
async def test_engine_stream() -> None:
    """Test engine streaming"""
    from sagellm_core import LLMEngine
    from sagellm_core.llm_engine import LLMEngineConfig

    config = LLMEngineConfig(model_path="sshleifer/tiny-gpt2", backend_type="cpu")
    engine = LLMEngine(config=config)
    await engine.start()

    request = Request(
        request_id="test-002",
        trace_id="trace-002",
        model="test-model",
        prompt="Hello",
        max_tokens=10,
        stream=True,
    )

    events = []
    async for event in engine.stream(request):
        events.append(event)

    assert len(events) > 0
    assert events[0].event == "start"
    assert events[-1].event == "end"

    delta_count = sum(1 for e in events if e.event == "delta")
    assert delta_count > 0

    await engine.stop()


@pytest.mark.asyncio
async def test_engine_execute_before_start() -> None:
    """Test that execute fails when engine not started"""
    from sagellm_core import LLMEngine
    from sagellm_core.llm_engine import LLMEngineConfig

    config = LLMEngineConfig(model_path="sshleifer/tiny-gpt2", backend_type="cpu")
    engine = LLMEngine(config=config)

    # Engine is not started
    assert not engine.is_running

    request = Request(
        request_id="test-003",
        trace_id="trace-003",
        model="test-model",
        prompt="Hello",
        max_tokens=10,
        stream=False,
    )

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="not running"):
        await engine.execute(request)


@pytest.mark.skip(reason="LLMEngine does not have get_info() method - implementation detail")
@pytest.mark.asyncio
async def test_engine_get_info() -> None:
    """Test engine get_info method (skipped - implementation detail)"""
    pass


@pytest.mark.skip(reason="LLMEngine does not have class methods is_available(), priority(), backend_type()")
def test_engine_class_methods() -> None:
    """Test Engine class methods (skipped - these are implementation details)"""
    pass
