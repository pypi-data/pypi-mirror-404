"""Tests for SageLLM adapter fail-fast behavior."""

from __future__ import annotations

import pytest

from sagellm_gateway.adapters.sagellm import SageLLMAdapter


@pytest.mark.asyncio
async def test_adapter_requires_control_plane() -> None:
    """SageLLMAdapter should fail-fast without Control Plane."""
    adapter = SageLLMAdapter(control_plane=None)

    with pytest.raises(RuntimeError, match="Control Plane is required"):
        await adapter.initialize()
