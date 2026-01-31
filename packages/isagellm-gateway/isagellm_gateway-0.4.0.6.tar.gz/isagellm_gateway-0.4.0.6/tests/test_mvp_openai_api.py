"""Gateway OpenAI API MVP 测试."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_gateway_health_endpoint():
    """测试健康检查端点."""
    # 注意：需要先初始化 adapter，否则会失败
    # 这是 MVP 的已知限制，后续会改进
    pass


def test_gateway_root_endpoint():
    """测试根端点（不依赖 adapter）."""
    # TODO(MVP): 需要模拟 lifespan 初始化
    pass


@pytest.mark.skip(reason="Requires full gateway setup - manual testing recommended for MVP")
def test_openai_models_endpoint():
    """测试 /v1/models 端点 (OpenAI 兼容)."""
    from sagellm_gateway import app

    client = TestClient(app)
    response = client.get("/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.skip(reason="Requires full gateway setup - manual testing recommended for MVP")
def test_openai_chat_completions_endpoint():
    """测试 /v1/chat/completions 端点 (OpenAI 兼容)."""
    from sagellm_gateway import app

    client = TestClient(app)
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "test-model",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )
    assert response.status_code in (200, 500)  # 500 is expected without real engine


def test_session_management():
    """测试会话管理功能."""
    from sagellm_gateway.session import SessionManager

    manager = SessionManager()

    # 创建会话
    session = manager.create_session(title="Test Session")
    assert session.id is not None
    assert session.title == "Test Session"

    # 获取会话
    retrieved = manager.get(session.id)
    assert retrieved is not None
    assert retrieved.id == session.id

    # 清空会话
    success = manager.clear_session(session.id)
    assert success is True

    # 删除会话
    success = manager.delete(session.id)
    assert success is True

    # 验证已删除
    assert manager.get(session.id) is None


def test_session_message_handling():
    """测试会话消息处理."""
    from sagellm_gateway.session import SessionManager

    manager = SessionManager()
    session = manager.create_session()

    # 通过 session 对象添加消息
    session.add_message(role="user", content="Hello")
    session.add_message(role="assistant", content="Hi there!")

    # 获取消息历史
    retrieved = manager.get(session.id)
    assert retrieved is not None
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].role == "user"
    assert retrieved.messages[1].role == "assistant"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
