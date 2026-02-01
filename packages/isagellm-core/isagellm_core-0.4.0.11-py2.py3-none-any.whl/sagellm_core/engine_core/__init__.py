"""EngineCore - Coordinates Scheduler and Executor.

The EngineCore is responsible for:
1. Managing request queues
2. Coordinating with Scheduler for batch formation
3. Dispatching batches to Executor
4. Collecting results
"""

from sagellm_core.engine_core.engine_core import EngineCore

__all__ = ["EngineCore"]
