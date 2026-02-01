"""Worker - Executes model forward passes.

Workers are responsible for:
1. Loading model weights
2. Running ModelRunner for forward passes
3. Managing GPU memory (via BackendProvider)
"""

from sagellm_core.worker.worker import Worker

__all__ = ["Worker"]
