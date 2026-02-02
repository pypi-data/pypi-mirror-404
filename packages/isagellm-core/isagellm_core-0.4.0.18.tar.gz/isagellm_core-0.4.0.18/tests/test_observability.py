"""Tests for observability utilities."""

from __future__ import annotations


from sagellm_core.observability import (
    MetricsCollector,
    EngineMetrics,
    setup_logger,
    get_logger,
)


class TestEngineMetrics:
    """Test EngineMetrics."""

    def test_default_metrics(self):
        """Test default metrics."""
        metrics = EngineMetrics()
        assert metrics.ttft_ms == 0.0
        assert metrics.throughput_tps == 0.0
        assert metrics.num_requests == 0

    def test_to_dict(self):
        """Test converting to dict."""
        metrics = EngineMetrics(ttft_ms=50.0, throughput_tps=100.0)
        d = metrics.to_dict()
        
        assert d["ttft_ms"] == 50.0
        assert d["throughput_tps"] == 100.0


class TestMetricsCollector:
    """Test MetricsCollector."""

    def test_record_ttft(self):
        """Test recording TTFT."""
        collector = MetricsCollector()
        collector.record_ttft(50.0)
        collector.record_ttft(60.0)
        
        metrics = collector.compute_metrics()
        assert metrics.ttft_ms == 55.0  # Average

    def test_record_latency(self):
        """Test recording request latency."""
        collector = MetricsCollector()
        collector.record_request_latency(100.0)
        collector.record_request_latency(200.0)
        collector.record_request_latency(150.0)
        
        metrics = collector.compute_metrics()
        assert metrics.num_requests == 3
        assert metrics.latency_p50_ms == 150.0

    def test_record_token_generation(self):
        """Test recording token generation time."""
        collector = MetricsCollector()
        
        for _ in range(10):
            collector.record_token_generation(10.0)
        
        metrics = collector.compute_metrics()
        assert metrics.num_tokens_generated == 10
        assert metrics.tpot_ms == 10.0
        assert metrics.throughput_tps > 0

    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        collector.record_ttft(50.0)
        collector.reset()
        
        metrics = collector.get_metrics()
        assert metrics.ttft_ms == 0.0


class TestLogger:
    """Test logging utilities."""

    def test_setup_logger(self):
        """Test setting up logger."""
        logger = setup_logger("test_logger")
        assert logger.name == "test_logger"

    def test_get_logger(self):
        """Test getting logger."""
        logger = get_logger("test_logger2")
        assert logger.name == "test_logger2"
