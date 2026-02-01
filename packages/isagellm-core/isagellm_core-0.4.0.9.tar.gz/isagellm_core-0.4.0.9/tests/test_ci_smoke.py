"""CI smoke tests - fast validation without model loading.

These tests run quickly and verify basic functionality
without starting engines or loading models.
"""

from __future__ import annotations

import pytest


@pytest.mark.fast
class TestCISmokeTests:
    """Fast smoke tests for CI (<30s total)."""

    def test_core_module_importable(self) -> None:
        """Verify sagellm_core module can be imported."""
        try:
            import sagellm_core

            assert sagellm_core is not None
        except ImportError as e:
            pytest.fail(f"Failed to import sagellm_core: {e}")

    def test_backend_module_importable(self) -> None:
        """Verify sagellm_backend module can be imported."""
        try:
            import sagellm_backend

            assert sagellm_backend is not None
        except ImportError as e:
            pytest.fail(f"Failed to import sagellm_backend: {e}")

    def test_protocol_types_importable(self) -> None:
        """Verify protocol types can be imported."""
        try:
            from sagellm_protocol import Request

            assert Request is not None
        except ImportError as e:
            pytest.fail(f"Failed to import protocol types: {e}")

    def test_backend_providers_importable(self) -> None:
        """Verify backend providers package can be imported."""
        try:
            import sagellm_backend.providers

            assert sagellm_backend.providers is not None
        except ImportError as e:
            pytest.fail(f"Failed to import backend providers: {e}")

    def test_factory_functions_exist(self) -> None:
        """Verify factory functions are accessible."""
        try:
            from sagellm_core import create_engine, create_backend

            assert callable(create_engine)
            assert callable(create_backend)
        except ImportError as e:
            pytest.fail(f"Failed to import factory functions: {e}")

    def test_config_classes_exist(self) -> None:
        """Verify config classes are accessible."""
        try:
            from sagellm_core import EngineConfig, BackendConfig

            assert all([EngineConfig, BackendConfig])
        except ImportError as e:
            pytest.fail(f"Failed to import config classes: {e}")

    def test_health_status_enum_exists(self) -> None:
        """Verify HealthStatus enum is accessible."""
        try:
            from sagellm_core import HealthStatus

            assert hasattr(HealthStatus, "HEALTHY")
            assert hasattr(HealthStatus, "DEGRADED")
            assert hasattr(HealthStatus, "UNHEALTHY")
        except ImportError as e:
            pytest.fail(f"Failed to import HealthStatus: {e}")


@pytest.mark.fast
class TestFactorySmoke:
    """Smoke tests for factory functions (no model loading)."""

    def test_create_cpu_backend(self) -> None:
        """Factory can create CPU backend."""
        from sagellm_core import create_backend, BackendConfig

        backend = create_backend(BackendConfig(kind="cpu", device="cpu"))
        assert backend is not None

    def test_create_llm_engine(self) -> None:
        """LLMEngine can be created with CPU backend."""
        from sagellm_core import LLMEngine, LLMEngineConfig

        engine = LLMEngine(
            LLMEngineConfig(
                model_path="sshleifer/tiny-gpt2",
                backend_type="cpu",
                max_new_tokens=10,
            )
        )
        assert engine is not None
        assert engine.config is not None
        assert engine.config.backend_type == "cpu"


@pytest.mark.fast
class TestBackendProviderSmoke:
    """Smoke tests for backend providers (no actual operations)."""

    def test_cpu_backend_capability(self) -> None:
        """CPU backend reports capabilities."""
        from sagellm_core import create_backend, BackendConfig

        backend = create_backend(BackendConfig(kind="cpu", device="cpu"))
        cap = backend.capability()

        assert cap is not None
        assert hasattr(cap, "device_type")
        assert cap.device_type == "cpu"

    def test_cpu_backend_stream_creation(self) -> None:
        """CPU backend can create streams."""
        from sagellm_core import create_backend, BackendConfig

        backend = create_backend(BackendConfig(kind="cpu", device="cpu"))
        stream = backend.create_stream()

        assert stream is not None


@pytest.mark.fast
class TestEngineSmoke:
    """Smoke tests for engine instances (no model loading)."""

    def test_llm_engine_can_be_created(self) -> None:
        """LLMEngine can be created with auto backend."""
        from sagellm_core import LLMEngine, LLMEngineConfig

        engine = LLMEngine(
            LLMEngineConfig(
                model_path="sshleifer/tiny-gpt2",
                backend_type="auto",
                max_new_tokens=10,
            )
        )

        assert engine is not None
        assert engine.config.model_path == "sshleifer/tiny-gpt2"


@pytest.mark.fast
class TestProtocolTypesSmoke:
    """Smoke tests for protocol types (no I/O)."""

    def test_request_creation(self) -> None:
        """Can create Request objects."""
        from sagellm_protocol import Request

        request = Request(
            request_id="smoke-001",
            trace_id="smoke-trace",
            model="test-model",
            prompt="Test prompt",
            max_tokens=10,
            stream=False,
        )

        assert request.request_id == "smoke-001"
        assert request.prompt == "Test prompt"

    def test_config_classes_work(self) -> None:
        """Can create config objects."""
        from sagellm_core import EngineConfig, BackendConfig

        backend_config = BackendConfig(kind="cpu", device="cpu")
        engine_config = EngineConfig(
            kind="cpu",
            model="sshleifer/tiny-gpt2",
            model_path="sshleifer/tiny-gpt2",
            device="cpu",
        )

        assert backend_config.kind == "cpu"
        assert engine_config.model == "sshleifer/tiny-gpt2"
