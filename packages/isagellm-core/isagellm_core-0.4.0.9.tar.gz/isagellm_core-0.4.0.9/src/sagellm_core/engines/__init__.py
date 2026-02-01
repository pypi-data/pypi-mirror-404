"""Engine implementations for sageLLM Core.

DEPRECATED: This module contains legacy engine implementations.
Use LLMEngine from sagellm_core instead:

    from sagellm_core import LLMEngine, LLMEngineConfig

    config = LLMEngineConfig(
        model_path="Qwen/Qwen2-7B",
        backend_type="cuda",  # or "cpu", "ascend", "auto"
    )
    engine = LLMEngine(config)
    await engine.start()
    response = await engine.generate("Hello!")

Remaining engines:
- EmbeddingEngine: Embedding model inference (not yet migrated to LLMEngine)
"""

from __future__ import annotations

# Only EmbeddingEngine remains - others have been migrated to LLMEngine
from sagellm_core.engines.embedding import EmbeddingEngine, EmbeddingEngineConfig

__all__ = [
    # Embedding engine (still needed for embedding-only models)
    "EmbeddingEngine",
    "EmbeddingEngineConfig",
]
