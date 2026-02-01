"""Tests for fail-fast behavior.

验证 Gateway 在控制面不可用时应抛出明确错误，
控制面可用时可以正常启动。
"""

from __future__ import annotations

import importlib.util

import pytest
from fastapi.testclient import TestClient

from sagellm_gateway.server import app


def _control_plane_available() -> bool:
    return importlib.util.find_spec("sagellm_control") is not None


class TestFailFastBehavior:
    """Fail-fast 行为测试."""

    def test_fail_fast_when_control_plane_missing(self) -> None:
        """控制面不可用时应 fail-fast."""
        if _control_plane_available():
            pytest.skip("Control Plane installed")

        with pytest.raises(RuntimeError) as exc_info:
            with TestClient(app):
                pass

        error_msg = str(exc_info.value).lower()
        assert "control plane" in error_msg or "sagellm-control-plane" in error_msg

    def test_control_plane_works_when_installed(self) -> None:
        """控制面已安装时可以正常启动."""
        if not _control_plane_available():
            pytest.skip("Control Plane not installed")

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
