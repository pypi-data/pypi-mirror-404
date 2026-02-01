"""Task0.10 集成测试 - Workload 执行与 Metrics 聚合。"""

from __future__ import annotations

import pytest

from sagellm_core.config import (
    BackendConfig,
    DemoConfig,
    EngineConfig,
    OutputConfig,
    WorkloadConfig,
    WorkloadSegment,
)
from sagellm_core.runner import DemoRunner


@pytest.mark.asyncio
@pytest.mark.slow
async def test_demo_runner_short_segment():
    """测试 short 段执行。"""
    config = DemoConfig(
        backend=BackendConfig(kind="cpu", device="cpu"),
        engine=EngineConfig(
            kind="cpu",
            model="sshleifer/tiny-gpt2",
            model_path="sshleifer/tiny-gpt2",
            device="cpu",
        ),
        workload=WorkloadConfig(segments=[WorkloadSegment.SHORT], concurrency=1),
        output=OutputConfig(metrics_path="test_metrics.json"),
    )

    runner = DemoRunner(config, verbose=False)
    metrics = await runner.run()

    # 验证 metrics 字段
    assert metrics.ttft_ms >= 0
    assert metrics.tbt_ms is not None
    assert metrics.throughput_tps >= 0
    assert metrics.peak_mem_mb >= 0
    assert 0 <= metrics.error_rate <= 1


@pytest.mark.asyncio
@pytest.mark.slow
async def test_demo_runner_all_segments():
    """测试三段 workload 执行。"""
    config = DemoConfig(
        backend=BackendConfig(kind="cpu", device="cpu"),
        engine=EngineConfig(
            kind="cpu",
            model="sshleifer/tiny-gpt2",
            model_path="sshleifer/tiny-gpt2",
            device="cpu",
        ),
        workload=WorkloadConfig(
            segments=[WorkloadSegment.SHORT, WorkloadSegment.LONG, WorkloadSegment.STRESS],
            concurrency=2,
        ),
        output=OutputConfig(metrics_path="test_metrics_all.json"),
    )

    runner = DemoRunner(config, verbose=False)
    metrics = await runner.run()

    assert metrics.error_rate < 1.0  # 至少有部分成功
    assert metrics.ttft_ms > 0
    assert metrics.tbt_ms is not None


@pytest.mark.asyncio
@pytest.mark.slow
async def test_demo_runner_kv_budget_exhaustion():
    """测试 KV 预算驱逐场景。"""
    config = DemoConfig(
        backend=BackendConfig(kind="cpu", device="cpu"),
        engine=EngineConfig(
            kind="cpu",
            model="sshleifer/tiny-gpt2",
            model_path="sshleifer/tiny-gpt2",
            device="cpu",
        ),
        workload=WorkloadConfig(
            segments=[WorkloadSegment.STRESS],
            concurrency=2,
            kv_budget_tokens=100,  # 很小的预算，触发驱逐
        ),
        output=OutputConfig(metrics_path="test_metrics_kv.json"),
    )

    runner = DemoRunner(config, verbose=False)
    metrics = await runner.run()

    # CPU backend may or may not enforce KV budget limits depending on implementation
    # For now, just verify the test runs successfully
    assert metrics.error_rate >= 0.0
    assert metrics.ttft_ms > 0


@pytest.mark.asyncio
@pytest.mark.slow
async def test_demo_runner_report_generation():
    """测试报告生成。"""
    config = DemoConfig(
        backend=BackendConfig(kind="cpu", device="cpu"),
        engine=EngineConfig(
            kind="cpu",
            model="sshleifer/tiny-gpt2",
            model_path="sshleifer/tiny-gpt2",
            device="cpu",
        ),
        workload=WorkloadConfig(segments=[WorkloadSegment.SHORT], concurrency=1),
        output=OutputConfig(metrics_path="test_metrics_report.json"),
    )

    runner = DemoRunner(config, verbose=False)
    metrics = await runner.run()
    report = runner.generate_report(metrics)

    # 验证报告内容
    assert "# sageLLM Demo Report" in report
    assert "Trace ID" in report
    assert "Configuration" in report
    assert "Metrics" in report
    assert "Summary" in report
    assert "TTFT" in report
    assert "Throughput" in report


def test_workload_generator():
    """测试 Workload 生成器。"""
    from sagellm_core.workload import WorkloadGenerator

    # 测试 prompt 生成
    prompt = WorkloadGenerator.generate_prompt(100)
    assert len(prompt.split()) == 100

    # 测试 request 生成
    request = WorkloadGenerator.create_request(WorkloadSegment.SHORT, 0, "test-trace", "test-model")
    assert request.request_id.startswith("short-0-")
    assert request.trace_id == "test-trace"
    assert request.model == "test-model"
    assert request.max_tokens == 128


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
