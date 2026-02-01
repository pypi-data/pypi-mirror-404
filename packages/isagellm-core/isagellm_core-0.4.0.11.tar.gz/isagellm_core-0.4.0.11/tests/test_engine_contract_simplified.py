"""Simplified Engine Contract Tests

Tests the actual BaseEngine interface from sagellm-backend.
"""

from __future__ import annotations

import pytest

from sagellm_core.engine import BaseEngine, HealthStatus
from sagellm_core.engine_factory import EngineFactory


class TestBaseEngineContract:
    """Test BaseEngine interface"""

    def test_protocol_has_required_methods(self):
        """Verify BaseEngine has all required methods"""
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

    def test_engine_id_property(self):
        """Verify engine_id property exists"""
        assert hasattr(BaseEngine, "engine_id")

    def test_config_property(self):
        """Verify config property exists"""
        assert hasattr(BaseEngine, "config")

    def test_is_running_property(self):
        """Verify is_running property exists"""
        assert hasattr(BaseEngine, "is_running")


class TestHealthStatus:
    """Test HealthStatus enum"""

    def test_health_status_values(self):
        """Verify HealthStatus has correct values"""
        from enum import Enum

        assert issubclass(HealthStatus, Enum)

        required_values = ["HEALTHY", "DEGRADED", "UNHEALTHY"]
        actual_values = [e.name for e in HealthStatus]

        for value in required_values:
            assert value in actual_values, f"HealthStatus missing value: {value}"


@pytest.mark.skip(reason="create_engine replaced by EngineFactory.create()")
class TestCreateEngineFactory:
    """Test create_engine factory function"""

    def test_factory_exists(self):
        """Verify factory function exists"""
        pass  # Deprecated


@pytest.mark.skip(reason="Old test design - needs refactoring")
class TestProtocolAlignment:
    """Old protocol alignment tests - to be refactored"""

    pass
