"""Integration tests for SageLLMAdapter with Control Plane execution layer."""

from __future__ import annotations

import pytest

from sagellm_gateway.adapters import SageLLMAdapter
from sagellm_gateway.models import ChatCompletionRequest, ChatMessage


@pytest.fixture
def adapter_with_control_plane() -> SageLLMAdapter:
    """Create SageLLMAdapter with ControlPlaneManager."""
    try:
        from sagellm_control import ControlPlaneManager
    except ImportError:
        pytest.skip("sagellm-control-plane not installed")

    cp = ControlPlaneManager()
    return SageLLMAdapter(control_plane=cp, default_model="sshleifer/tiny-gpt2")


class TestSageLLMAdapterIntegration:
    """Integration tests for SageLLMAdapter with Control Plane execution."""

    @pytest.mark.asyncio
    async def test_execute_request_integration(
        self, adapter_with_control_plane: SageLLMAdapter
    ) -> None:
        """Test non-streaming chat completion fail-fast when no engines."""
        request = ChatCompletionRequest(
            model="sshleifer/tiny-gpt2",
            messages=[ChatMessage(role="user", content="Hello from integration test")],
            stream=False,
        )

        with pytest.raises(RuntimeError):
            await adapter_with_control_plane.chat_completions(request)

    @pytest.mark.asyncio
    async def test_stream_request_integration(
        self, adapter_with_control_plane: SageLLMAdapter
    ) -> None:
        """Test streaming chat completion fail-fast when no engines."""
        request = ChatCompletionRequest(
            model="sshleifer/tiny-gpt2",
            messages=[ChatMessage(role="user", content="Stream me a story")],
            stream=True,
        )

        with pytest.raises(RuntimeError):
            await adapter_with_control_plane.chat_completions(request)

    @pytest.mark.asyncio
    async def test_execute_with_different_model(
        self, adapter_with_control_plane: SageLLMAdapter
    ) -> None:
        """Test execute with model not in control plane raises RuntimeError (fail-fast)."""
        request = ChatCompletionRequest(
            model="nonexistent-model",
            messages=[ChatMessage(role="user", content="Hello")],
            stream=False,
        )

        with pytest.raises(RuntimeError) as exc_info:
            await adapter_with_control_plane.chat_completions(request)

        # Verify error message contains useful information
        assert "Engine execution failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_adapter_lifecycle_with_control_plane(
        self, adapter_with_control_plane: SageLLMAdapter
    ) -> None:
        """Test adapter lifecycle with control plane."""
        # Initialize
        await adapter_with_control_plane.initialize()
        assert adapter_with_control_plane._initialized is True

        # Shutdown
        await adapter_with_control_plane.shutdown()
        assert adapter_with_control_plane._initialized is False

    @pytest.mark.asyncio
    async def test_list_models_from_control_plane(
        self, adapter_with_control_plane: SageLLMAdapter
    ) -> None:
        """Test listing models from control plane."""
        await adapter_with_control_plane.initialize()

        models = await adapter_with_control_plane.list_models()

        assert isinstance(models, list)


class TestControlPlaneExecuteMethods:
    """Direct tests for Control Plane execute methods via adapter."""

    @pytest.mark.asyncio
    async def test_control_plane_execute_request_no_engines(self) -> None:
        """Control Plane should return error response when no engines are available."""
        try:
            from sagellm_control import ControlPlaneManager
        except ImportError:
            pytest.skip("sagellm-control-plane not installed")

        from sagellm_protocol import Request

        cp = ControlPlaneManager()
        request = Request(
            request_id="direct-req-001",
            trace_id="direct-trace-001",
            model="sshleifer/tiny-gpt2",
            prompt="Hello direct test",
            max_tokens=16,
            stream=False,
        )

        response = await cp.execute_request(request)

        assert response.finish_reason == "error"
        assert response.error is not None

    @pytest.mark.asyncio
    async def test_control_plane_stream_request_no_engines(self) -> None:
        """Control Plane stream_request should end with error when no engines are available."""
        try:
            from sagellm_control import ControlPlaneManager
        except ImportError:
            pytest.skip("sagellm-control-plane not installed")

        from sagellm_protocol import Request

        cp = ControlPlaneManager()
        request = Request(
            request_id="stream-req-001",
            trace_id="stream-trace-001",
            model="sshleifer/tiny-gpt2",
            prompt="Stream me something",
            max_tokens=16,
            stream=True,
        )

        events = []
        async for event in cp.stream_request(request):
            events.append(event)

        # No engines -> should emit a single end event with error
        assert len(events) == 1
        end_event = events[0]
        assert end_event.event == "end"
        assert end_event.request_id == "stream-req-001"
        assert end_event.finish_reason == "error"
        assert end_event.error is not None
