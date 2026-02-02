"""Executor - Manages Workers for model execution.

Executors dispatch scheduled batches to Workers for execution.
Different executor types handle different parallelism patterns:
- UniprocExecutor: Single-process execution
- MultiprocessExecutor: Multi-process (future)
- RayExecutor: Ray-based distributed (future)
"""

from sagellm_core.executor.executor_base import ExecutorBase
from sagellm_core.executor.uniproc_executor import UniprocExecutor

__all__ = [
    "ExecutorBase",
    "UniprocExecutor",
]
