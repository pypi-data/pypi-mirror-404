"""Tests for SageLLMAdapter."""

from __future__ import annotations

import pytest

from sagellm_gateway.adapters import SageLLMAdapter
from sagellm_gateway.models import (
    ChatCompletionRequest,
    ChatMessage,
    EmbeddingRequest,
)


@pytest.fixture
def adapter() -> SageLLMAdapter:
    """创建测试用的 SageLLMAdapter."""
    return SageLLMAdapter(control_plane=None, default_model="test-model")


class TestSageLLMAdapter:
    """SageLLMAdapter 测试."""

    @pytest.mark.asyncio
    async def test_chat_completion_non_stream(self, adapter: SageLLMAdapter) -> None:
        """测试非流式 chat completion."""
        request = ChatCompletionRequest(
            model="test-model",
            messages=[ChatMessage(role="user", content="Hello")],
            stream=False,
        )

        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.chat_completions(request)

    @pytest.mark.asyncio
    async def test_chat_completion_stream(self, adapter: SageLLMAdapter) -> None:
        """测试流式 chat completion."""
        request = ChatCompletionRequest(
            model="test-model",
            messages=[ChatMessage(role="user", content="Hello")],
            stream=True,
        )

        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.chat_completions(request)

    @pytest.mark.asyncio
    async def test_embeddings(self, adapter: SageLLMAdapter) -> None:
        """测试 embedding 请求."""
        request = EmbeddingRequest(
            input="Hello world",
            model="test-model",
        )

        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.embeddings(request)

    @pytest.mark.asyncio
    async def test_embeddings_batch(self, adapter: SageLLMAdapter) -> None:
        """测试批量 embedding 请求."""
        request = EmbeddingRequest(
            input=["Hello", "World", "Test"],
            model="test-model",
        )

        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.embeddings(request)

    @pytest.mark.asyncio
    async def test_list_models(self, adapter: SageLLMAdapter) -> None:
        """测试模型列表."""
        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.list_models()

    @pytest.mark.asyncio
    async def test_initialize_shutdown(self, adapter: SageLLMAdapter) -> None:
        """测试初始化和关闭."""
        with pytest.raises(RuntimeError, match="Control Plane is required"):
            await adapter.initialize()

    @pytest.mark.asyncio
    async def test_messages_to_prompt(self, adapter: SageLLMAdapter) -> None:
        """测试消息转换为 prompt."""
        messages = [
            ChatMessage(role="system", content="You are a helpful assistant."),
            ChatMessage(role="user", content="Hello!"),
            ChatMessage(role="assistant", content="Hi there!"),
            ChatMessage(role="user", content="How are you?"),
        ]

        prompt = adapter._messages_to_prompt(messages)

        assert "System: You are a helpful assistant." in prompt
        assert "User: Hello!" in prompt
        assert "Assistant: Hi there!" in prompt
        assert "User: How are you?" in prompt
        assert prompt.endswith("Assistant:")

    @pytest.mark.asyncio
    async def test_create_protocol_request(self, adapter: SageLLMAdapter) -> None:
        """测试创建 Protocol 请求."""
        request = adapter._create_protocol_request(
            request_id="test-123",
            prompt="Hello world",
            model="test-model",
            max_tokens=100,
            temperature=0.7,
            stream=False,
        )

        # 现在返回 ProtocolRequest 对象
        assert request.request_id == "test-123"
        assert request.prompt == "Hello world"
        assert request.model == "test-model"
        assert request.max_tokens == 100
        assert request.temperature == 0.7
        assert request.stream is False
