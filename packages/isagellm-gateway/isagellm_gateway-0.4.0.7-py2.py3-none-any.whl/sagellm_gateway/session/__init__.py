"""Session management module for sageLLM Gateway.

提供会话管理功能：
- 内存存储（默认）
- 文件持久化（支持压缩、文件锁、自动清理）
- Redis 分布式存储（可选依赖）
- 会话导出/导入
- 可扩展的存储后端接口
"""

from __future__ import annotations

from sagellm_gateway.session.manager import (
    ChatMessage,
    ChatSession,
    SessionManager,
    get_session_manager,
)
from sagellm_gateway.session.storage import (
    FileSessionStore,
    InMemorySessionStore,
    RedisSessionStore,
    SessionStorage,
)

__all__ = [
    "ChatMessage",
    "ChatSession",
    "SessionManager",
    "get_session_manager",
    "SessionStorage",
    "InMemorySessionStore",
    "FileSessionStore",
    "RedisSessionStore",
]
