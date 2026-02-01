"""sageLLM Core 运行时。

本包提供 sageLLM 的核心运行时组件：
- LLMEngine: 统一的硬件无关推理引擎（vLLM v1 风格）
- EngineCore: 协调 Scheduler 和 Executor
- Scheduler: Continuous Batching 调度器
- Executor: 管理 Worker 执行
- Worker/ModelRunner: 模型前向传播
- 配置 schema 与校验
- Engine 工厂函数
- 插件系统
- Demo Runner
- 分布式 Runtime（PD 分离 MVP）
- PD 分离执行器

Architecture (vLLM v1 style):
    LLMEngine (hardware-agnostic)
        ├── EngineCore (coordinates Scheduler and Executor)
        │       └── Scheduler (Continuous Batching)
        └── Executor
                └── Worker
                        └── ModelRunner
                                ├── uses BackendProvider (from sagellm-backend)
                                └── uses CommBackend (from sagellm-comm)
"""

from __future__ import annotations

__version__ = "0.4.0.16"

# ============================================================================
# New Architecture (vLLM v1 style) - Hardware Agnostic
# ============================================================================
from sagellm_core.llm_engine import LLMEngine, LLMEngineConfig
from sagellm_core.engine_core import EngineCore
from sagellm_core.engine_core.engine_core import EngineCoreConfig
from sagellm_core.engine_core.scheduler import (
    ContinuousBatchingScheduler,
    SchedulerConfig,
    SchedulerOutput,
)
from sagellm_core.executor import ExecutorBase, UniprocExecutor
from sagellm_core.executor.executor_base import ExecutorConfig
from sagellm_core.worker import Worker
from sagellm_core.worker.model_runner import ModelRunner

# ============================================================================
# Legacy Architecture (still supported, being refactored)
# ============================================================================
from sagellm_core.engine import BaseEngine, EngineInstanceConfig
from sagellm_core.config import (
    BackendConfig,
    DemoConfig,
    EngineConfig,
    OutputConfig,
    WorkloadConfig,
    WorkloadSegment,
    load_config,
)
from sagellm_core.demo import main as demo_main
from sagellm_core.engine_factory import EngineFactory

# Only EmbeddingEngine remains from legacy engines
from sagellm_core.engines import (
    EmbeddingEngine,
    EmbeddingEngineConfig,
)
from sagellm_core.factory import create_backend, create_engine
from sagellm_core.health import HealthStatus
from sagellm_core.plugins import PluginResolutionError, list_entry_points, resolve_kind
from sagellm_core.runner import DemoRunner, RunnerContext

# PD 分离 MVP 模块
from sagellm_core.runtime import DistributedConfig, DistributedRuntime, RuntimeState
from sagellm_core.pd_executor import PDExecutionContext, PDSeparatedExecutor

# Engine HTTP Server
from sagellm_core.engine_server import app as engine_server_app
from sagellm_core.engine_server import main as serve_engine

# ============================================================================
# Phase 2: New Modules (P2 Priority)
# ============================================================================
# Model loading utilities
from sagellm_core.model import ModelLoader, load_model

# Input processing
from sagellm_core.inputs import InputProcessor, ProcessedInput, TokenizerWrapper

# Sampling utilities
from sagellm_core.sampling import SamplingParams, Sampler, GreedySampler

# Distributed strategies
from sagellm_core.distributed import DistributedStrategy, TensorParallelStrategy

# Observability
from sagellm_core.observability import MetricsCollector, EngineMetrics, setup_logger

# PyTorch engine (optional, loaded lazily)
PyTorchEngine = None
create_pytorch_engine = None

# Optional PyTorchEngine import (deprecated, use LLMEngine)
# try:
#     from sagellm_core.engines.pytorch_engine import (
#         PyTorchEngine,
#         create_pytorch_engine,
#     )
# except ImportError:
#     pass  # torch or transformers not available

# =========================================================================
# DEPRECATED: Old hardware-specific engines have been removed
# Use LLMEngine instead:
#   from sagellm_core import LLMEngine, LLMEngineConfig
#   engine = LLMEngine(LLMEngineConfig(model="..."))
#
# The following engines no longer exist:
#   - CPUEngine → use LLMEngine(backend="cpu")
#   - HFCudaEngine → use LLMEngine(backend="cuda")
#   - AscendEngine → use LLMEngine(backend="ascend")
#   - PyTorchEngine → use LLMEngine
#
# EmbeddingEngine is still available for embedding-only use cases.
# =========================================================================

# Version is defined at the top of the file (line 29)

__all__ = [
    # Version
    "__version__",
    # =========================================================================
    # New Architecture (vLLM v1 style) - RECOMMENDED
    # =========================================================================
    # LLMEngine - Unified hardware-agnostic engine
    "LLMEngine",
    "LLMEngineConfig",
    # EngineCore - Coordinates Scheduler and Executor
    "EngineCore",
    "EngineCoreConfig",
    # Scheduler - Continuous Batching
    "ContinuousBatchingScheduler",
    "SchedulerConfig",
    "SchedulerOutput",
    # Executor - Manages Workers
    "ExecutorBase",
    "ExecutorConfig",
    "UniprocExecutor",
    # Worker - Model execution
    "Worker",
    "ModelRunner",
    # =========================================================================
    # Configuration (for YAML/config files)
    # =========================================================================
    "BackendConfig",
    "DemoConfig",
    "EngineConfig",
    "OutputConfig",
    "WorkloadConfig",
    "WorkloadSegment",
    "load_config",
    # Engine abstraction
    "BaseEngine",
    "EngineInstanceConfig",  # For runtime engine instantiation
    "HealthStatus",
    # Engine implementations
    # DEPRECATED: Old engines removed, use LLMEngine instead
    # Only EmbeddingEngine remains for embedding-only use cases
    "EmbeddingEngine",
    "EmbeddingEngineConfig",
    # Factory functions
    "create_backend",
    "create_engine",
    "EngineFactory",
    # Plugin system
    "PluginResolutionError",
    "list_entry_points",
    "resolve_kind",
    # Demo runner
    "demo_main",
    "DemoRunner",
    "RunnerContext",
    # PD Separation MVP
    "DistributedConfig",
    "DistributedRuntime",
    "RuntimeState",
    "PDExecutionContext",
    "PDSeparatedExecutor",
    # Engine HTTP Server
    "engine_server_app",
    "serve_engine",
    # Phase 2 modules
    "ModelLoader",
    "load_model",
    "InputProcessor",
    "ProcessedInput",
    "TokenizerWrapper",
    "SamplingParams",
    "Sampler",
    "GreedySampler",
    "DistributedStrategy",
    "TensorParallelStrategy",
    "MetricsCollector",
    "EngineMetrics",
    "setup_logger",
]
