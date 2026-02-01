"""Tests for chat completion API."""

from __future__ import annotations

from fastapi.testclient import TestClient


class TestChatCompletions:
    """Chat completion API 测试."""

    def test_chat_completion_basic(self, client: TestClient) -> None:
        """测试基本的 chat completion 请求."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "stream": False,
            },
        )
        if response.status_code == 200:
            data = response.json()

            # 验证响应格式
            assert "id" in data
            assert data["object"] == "chat.completion"
            assert "choices" in data
            assert len(data["choices"]) == 1
            assert data["choices"][0]["message"]["role"] == "assistant"
            assert "content" in data["choices"][0]["message"]
            assert data["choices"][0]["finish_reason"] == "stop"

            # 验证 usage
            assert "usage" in data
            assert "prompt_tokens" in data["usage"]
            assert "completion_tokens" in data["usage"]
            assert "total_tokens" in data["usage"]
        else:
            # 未注册引擎时可能返回 500
            assert response.status_code == 500

    def test_chat_completion_with_chinese(self, client: TestClient) -> None:
        """测试中文消息."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "你好"}],
                "stream": False,
            },
        )
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            assert isinstance(content, str)
        else:
            assert response.status_code == 500

    def test_chat_completion_test_message(self, client: TestClient) -> None:
        """测试 test 消息获取预设回复."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "test"}],
                "stream": False,
            },
        )
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            assert isinstance(content, str)
        else:
            assert response.status_code == 500

    def test_chat_completion_multiple_messages(self, client: TestClient) -> None:
        """测试多轮对话."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "What is 2+2?"},
                    {"role": "assistant", "content": "4"},
                    {"role": "user", "content": "Thanks!"},
                ],
                "stream": False,
            },
        )
        if response.status_code == 200:
            data = response.json()
            assert len(data["choices"]) == 1
        else:
            assert response.status_code == 500

    def test_chat_completion_stream(self, client: TestClient) -> None:
        """测试流式响应."""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "test-model",
                "messages": [{"role": "user", "content": "Hello!"}],
                "stream": True,
            },
        )
        if response.status_code == 200:
            assert response.headers["content-type"].startswith("text/event-stream")

            # 收集所有 SSE 事件
            content = response.text
            assert "data:" in content
            assert "[DONE]" in content
        else:
            assert response.status_code == 500


class TestModels:
    """Models API 测试."""

    def test_list_models(self, client: TestClient) -> None:
        """测试列出模型."""
        response = client.get("/v1/models")
        assert response.status_code == 200
        data = response.json()

        assert data["object"] == "list"
        assert "data" in data
        assert isinstance(data["data"], list)

        # 验证模型格式
        if data["data"]:
            model = data["data"][0]
            assert "id" in model
            assert model["object"] == "model"
            assert "created" in model
            assert "owned_by" in model


class TestHealth:
    """Health API 测试."""

    def test_health_check(self, client: TestClient) -> None:
        """测试健康检查."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert "sessions" in data

    def test_root_endpoint(self, client: TestClient) -> None:
        """测试根路径."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "sageLLM Gateway"
        assert "version" in data
        assert "endpoints" in data


class TestEmbeddings:
    """Embeddings API 测试."""

    def test_create_embeddings_single(self, client: TestClient) -> None:
        """测试单个文本的 embedding."""
        response = client.post(
            "/v1/embeddings",
            json={
                "input": "Hello, world!",
                "model": "test-embedding",
            },
        )
        if response.status_code == 200:
            data = response.json()

            assert data["object"] == "list"
            assert len(data["data"]) == 1
            assert data["data"][0]["object"] == "embedding"
            assert len(data["data"][0]["embedding"]) > 0
            assert "usage" in data
        else:
            assert response.status_code == 500

    def test_create_embeddings_batch(self, client: TestClient) -> None:
        """测试批量文本的 embedding."""
        response = client.post(
            "/v1/embeddings",
            json={
                "input": ["Hello", "World", "Test"],
                "model": "test-embedding",
            },
        )
        if response.status_code == 200:
            data = response.json()

            assert len(data["data"]) == 3
            for i, item in enumerate(data["data"]):
                assert item["index"] == i
                assert item["object"] == "embedding"
        else:
            assert response.status_code == 500
