"""Protocol adapters for different API formats.

提供不同后端的适配器实现：
- SageLLMAdapter: 通过 Control Plane 连接 sageLLM 引擎的生产适配器
"""

from __future__ import annotations

from sagellm_gateway.adapters.base import BaseAdapter
from sagellm_gateway.adapters.sagellm import SageLLMAdapter

__all__ = [
    "BaseAdapter",
    "SageLLMAdapter",
]
