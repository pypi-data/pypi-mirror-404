"""Tests for configuration schema and validation"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from sagellm_core.config import (
    BackendConfig,
    DemoConfig,
    EngineConfig,
    OutputConfig,
    WorkloadConfig,
    WorkloadSegment,
    load_config,
)


def test_backend_config_creation() -> None:
    """测试 BackendConfig 创建"""
    config = BackendConfig(kind="cpu", device=None)
    assert config.kind == "cpu"
    assert config.device is None


def test_engine_config_creation() -> None:
    """测试 EngineConfig 创建"""
    config = EngineConfig(kind="cpu", model="test-model", device="cpu")
    assert config.kind == "cpu"
    assert config.model == "test-model"
    assert config.device == "cpu"


def test_workload_config_creation() -> None:
    """测试 WorkloadConfig 创建"""
    config = WorkloadConfig(
        segments=[WorkloadSegment.SHORT],
        concurrency=1,
        kv_budget_tokens=4096,
    )
    assert config.segments == [WorkloadSegment.SHORT]
    assert config.concurrency == 1
    assert config.kv_budget_tokens == 4096


def test_output_config_creation() -> None:
    """测试 OutputConfig 创建"""
    config = OutputConfig(
        metrics_path="/tmp/metrics.json",
        report_path="/tmp/report.txt",
    )
    assert config.metrics_path == "/tmp/metrics.json"
    assert config.report_path == "/tmp/report.txt"


def test_demo_config_creation() -> None:
    """测试 DemoConfig 创建"""
    config = DemoConfig(
        backend=BackendConfig(kind="cpu", device=None),
        engine=EngineConfig(kind="cpu", model="test", device="cpu"),
        workload=WorkloadConfig(
            segments=[WorkloadSegment.SHORT],
            concurrency=1,
            kv_budget_tokens=4096,
        ),
        output=OutputConfig(
            metrics_path="/tmp/metrics.json",
            report_path="/tmp/report.txt",
        ),
    )
    assert config.backend.kind == "cpu"
    assert config.engine.kind == "cpu"
    assert config.workload.segments == [WorkloadSegment.SHORT]


def test_load_config_yaml() -> None:
    """测试从 YAML 加载配置"""
    yaml_content = """
backend:
  kind: cpu
  device: null

engine:
  kind: cpu
  model: test-model
  device: cpu

workload:
  segments: [short]
  concurrency: 1
  kv_budget_tokens: 4096

output:
  metrics_path: /tmp/metrics.json
  report_path: /tmp/report.txt
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config.backend.kind == "cpu"
        assert config.engine.model == "test-model"
        assert config.workload.segments == [WorkloadSegment.SHORT]
    finally:
        Path(temp_path).unlink()


def test_load_config_json() -> None:
    """测试从 JSON 加载配置"""
    json_content = """
{
  "backend": {"kind": "cpu", "device": null},
  "engine": {"kind": "cpu", "model": "test-model", "device": "cpu"},
  "workload": {"segments": ["short"], "concurrency": 1, "kv_budget_tokens": 4096},
  "output": {"metrics_path": "/tmp/metrics.json", "report_path": "/tmp/report.txt"}
}
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(json_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config.backend.kind == "cpu"
        assert config.engine.model == "test-model"
    finally:
        Path(temp_path).unlink()


def test_workload_segment_enum() -> None:
    """测试 WorkloadSegment 枚举"""
    assert WorkloadSegment.SHORT == "short"
    assert WorkloadSegment.LONG == "long"
    assert WorkloadSegment.STRESS == "stress"


def test_config_validation() -> None:
    """测试配置验证"""
    # 应该允许有效配置
    config = EngineConfig(kind="cpu", model="test", device="cpu")
    assert config.kind == "cpu"

    # Pydantic 会验证必填字段
    with pytest.raises(Exception):
        EngineConfig(kind="cpu")  # 缺少 model
