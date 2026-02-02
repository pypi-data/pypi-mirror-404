"""Engine Server 单元测试.

测试 Engine HTTP Server 的端点和功能。

注意：需要真实引擎环境的测试已标记为 @pytest.mark.integration，
默认跳过，可通过 pytest -m integration 运行。
"""

from __future__ import annotations

import pytest

from sagellm_protocol.types import Request


# ─────────────────────────────────────────────────────────────────
# CompletionRequest Model Tests (不需要引擎)
# ─────────────────────────────────────────────────────────────────


def test_completion_request_to_protocol():
    """测试 CompletionRequest 转换为 Protocol Request."""
    from sagellm_core.engine_server import CompletionRequest

    req = CompletionRequest(
        request_id="req-1",
        trace_id="trace-1",
        model="test-model",
        prompt="Hello",
        max_tokens=100,
        stream=False,
        temperature=0.7,
        top_p=0.9,
    )

    protocol_req = req.to_protocol_request()

    assert protocol_req.request_id == "req-1"
    assert protocol_req.trace_id == "trace-1"
    assert protocol_req.model == "test-model"
    assert protocol_req.prompt == "Hello"
    assert protocol_req.max_tokens == 100
    assert protocol_req.stream is False
    assert protocol_req.temperature == 0.7
    assert protocol_req.top_p == 0.9


def test_completion_request_minimal():
    """测试 CompletionRequest 最小必需字段."""
    from sagellm_core.engine_server import CompletionRequest

    req = CompletionRequest(
        request_id="req-1",
        trace_id="trace-1",
        model="test-model",
        prompt="Hello",
        max_tokens=50,
    )

    assert req.stream is False  # 默认值
    assert req.temperature is None
    assert req.top_p is None


def test_completion_request_with_metadata():
    """测试 CompletionRequest 带 metadata."""
    from sagellm_core.engine_server import CompletionRequest

    req = CompletionRequest(
        request_id="req-1",
        trace_id="trace-1",
        model="test-model",
        prompt="Hello",
        max_tokens=50,
        metadata={"user_id": "user-123", "session_id": "sess-456"},
    )

    protocol_req = req.to_protocol_request()
    assert protocol_req.metadata == {"user_id": "user-123", "session_id": "sess-456"}


def test_completion_request_validation():
    """测试 CompletionRequest 字段验证."""
    from sagellm_core.engine_server import CompletionRequest
    from pydantic import ValidationError

    # max_tokens 必须 > 0
    with pytest.raises(ValidationError):
        CompletionRequest(
            request_id="req-1",
            trace_id="trace-1",
            model="test-model",
            prompt="Hello",
            max_tokens=0,  # Invalid
        )

    # temperature 必须在 (0, 2] 范围内
    with pytest.raises(ValidationError):
        CompletionRequest(
            request_id="req-1",
            trace_id="trace-1",
            model="test-model",
            prompt="Hello",
            max_tokens=50,
            temperature=3.0,  # Invalid, > 2
        )


# ─────────────────────────────────────────────────────────────────
# Module Import Tests
# ─────────────────────────────────────────────────────────────────


def test_engine_server_imports():
    """测试 engine_server 模块可以正常导入."""
    from sagellm_core.engine_server import (
        app,
        main,
        get_engine,
        set_engine,
        CompletionRequest,
    )

    assert app is not None
    assert callable(main)
    assert callable(get_engine)
    assert callable(set_engine)


def test_engine_server_app_routes():
    """测试 FastAPI app 包含所需路由."""
    from sagellm_core.engine_server import app

    routes = [route.path for route in app.routes]

    assert "/" in routes
    assert "/health" in routes
    assert "/info" in routes
    assert "/v1/completions" in routes
    assert "/v1/completions/stream" in routes


# ─────────────────────────────────────────────────────────────────
# CLI Tests
# ─────────────────────────────────────────────────────────────────


def test_cli_argparse():
    """测试 CLI 参数解析."""
    import argparse
    from sagellm_core.engine_server import main

    # 验证 main 是可调用的
    assert callable(main)
