"""Tests for session management."""

from __future__ import annotations

from fastapi.testclient import TestClient

from sagellm_gateway.session import (
    ChatSession,
    InMemorySessionStore,
    SessionManager,
)


class TestSessionManager:
    """SessionManager 单元测试."""

    def test_create_session(self) -> None:
        """测试创建会话."""
        manager = SessionManager(storage=InMemorySessionStore())
        session = manager.create_session(title="Test Chat")

        assert session.id is not None
        assert session.title == "Test Chat"
        assert len(session.messages) == 0

    def test_get_or_create_session(self) -> None:
        """测试获取或创建会话."""
        manager = SessionManager(storage=InMemorySessionStore())

        # 创建新会话
        session1 = manager.get_or_create()
        assert session1.id is not None

        # 获取已有会话
        session2 = manager.get_or_create(session1.id)
        assert session2.id == session1.id

        # 传入不存在的 ID 会创建新会话
        session3 = manager.get_or_create("non-existent-id")
        assert session3.id == "non-existent-id"

    def test_delete_session(self) -> None:
        """测试删除会话."""
        manager = SessionManager(storage=InMemorySessionStore())
        session = manager.create_session()

        assert manager.get(session.id) is not None
        assert manager.delete(session.id) is True
        assert manager.get(session.id) is None

        # 删除不存在的会话
        assert manager.delete("non-existent") is False

    def test_list_sessions(self) -> None:
        """测试列出会话."""
        manager = SessionManager(storage=InMemorySessionStore())
        manager.create_session(title="Session 1")
        manager.create_session(title="Session 2")

        sessions = manager.list_sessions()
        assert len(sessions) == 2

    def test_session_stats(self) -> None:
        """测试会话统计."""
        manager = SessionManager(storage=InMemorySessionStore())
        session = manager.create_session()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi!")

        stats = manager.get_stats()
        assert stats["total_sessions"] == 1
        assert stats["total_messages"] == 2


class TestChatSession:
    """ChatSession 单元测试."""

    def test_add_message(self) -> None:
        """测试添加消息."""
        session = ChatSession()
        msg = session.add_message("user", "Hello!")

        assert len(session.messages) == 1
        assert msg.role == "user"
        assert msg.content == "Hello!"

    def test_auto_title_generation(self) -> None:
        """测试自动标题生成."""
        session = ChatSession()
        assert session.title == "New Chat"

        session.add_message("user", "What is the weather today?")
        assert session.title == "What is the weather today?"

    def test_clear_history(self) -> None:
        """测试清空历史."""
        session = ChatSession()
        session.add_message("user", "Hello")
        session.add_message("assistant", "Hi")

        assert len(session.messages) == 2
        session.clear_history()
        assert len(session.messages) == 0

    def test_get_messages(self) -> None:
        """测试获取消息."""
        session = ChatSession()
        session.add_message("user", "1")
        session.add_message("assistant", "2")
        session.add_message("user", "3")

        # 获取全部
        messages = session.get_messages()
        assert len(messages) == 3

        # 获取最后 2 条
        messages = session.get_messages(limit=2)
        assert len(messages) == 2
        assert messages[0]["content"] == "2"
        assert messages[1]["content"] == "3"

    def test_to_dict(self) -> None:
        """测试转换为字典."""
        session = ChatSession()
        session.add_message("user", "Test")

        data = session.to_dict()
        assert "id" in data
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert "created_at" in data
        assert "last_active" in data
        assert "metadata" in data


class TestSessionAPI:
    """Session API 集成测试."""

    def test_list_sessions_api(self, client: TestClient) -> None:
        """测试列出会话 API."""
        response = client.get("/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "stats" in data

    def test_create_session_api(self, client: TestClient) -> None:
        """测试创建会话 API."""
        response = client.post(
            "/sessions",
            json={"title": "Test Session"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["metadata"]["title"] == "Test Session"

    def test_get_session_api(self, client: TestClient) -> None:
        """测试获取会话 API."""
        # 先创建会话
        create_response = client.post(
            "/sessions",
            json={"title": "Test"},
        )
        session_id = create_response.json()["id"]

        # 获取会话
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == session_id

    def test_get_nonexistent_session(self, client: TestClient) -> None:
        """测试获取不存在的会话."""
        response = client.get("/sessions/nonexistent-id")
        assert response.status_code == 404

    def test_delete_session_api(self, client: TestClient) -> None:
        """测试删除会话 API."""
        # 先创建会话
        create_response = client.post(
            "/sessions",
            json={"title": "To Delete"},
        )
        session_id = create_response.json()["id"]

        # 删除会话
        response = client.delete(f"/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "deleted"

        # 验证已删除
        response = client.get(f"/sessions/{session_id}")
        assert response.status_code == 404

    def test_clear_session_api(self, client: TestClient) -> None:
        """测试清空会话历史 API."""
        # 先创建会话
        create_response = client.post(
            "/sessions",
            json={"title": "Test"},
        )
        session_id = create_response.json()["id"]

        # 清空会话
        response = client.post(f"/sessions/{session_id}/clear")
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"

    def test_rename_session_api(self, client: TestClient) -> None:
        """测试重命名会话 API."""
        # 先创建会话
        create_response = client.post(
            "/sessions",
            json={"title": "Original Title"},
        )
        session_id = create_response.json()["id"]

        # 重命名
        response = client.patch(
            f"/sessions/{session_id}/title",
            json={"title": "New Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "New Title"
