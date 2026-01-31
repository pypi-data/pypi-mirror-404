"""sageLLM Gateway - OpenAI/Anthropic Compatible API Gateway.

Layer: L6 (User Interface & API Gateway)
Dependencies: sagellm-protocol, sagellm-control-plane (optional)

提供标准化的 REST API 接口：
- OpenAI /v1/chat/completions
- OpenAI /v1/models
- OpenAI /v1/embeddings
- Session management
- Streaming support (SSE)
"""

from __future__ import annotations

from sagellm_gateway.adapters import BaseAdapter, SageLLMAdapter
from sagellm_gateway.server import app, get_adapter, set_adapter

__version__ = "0.4.0.6"
__layer__ = "L6"

__all__ = [
    "__version__",
    "__layer__",
    # Server
    "app",
    "get_adapter",
    "set_adapter",
    # Adapters
    "BaseAdapter",
    "SageLLMAdapter",
]
