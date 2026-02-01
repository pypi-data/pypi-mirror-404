"""Tests for FileSessionStore and session export/import functionality."""

from __future__ import annotations

import gzip
import json
import threading
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from sagellm_gateway.session import (
    ChatSession,
    FileSessionStore,
    SessionManager,
)


class TestFileSessionStore:
    """FileSessionStore 单元测试."""

    def test_basic_save_and_load(self, tmp_path: Path) -> None:
        """测试基本的保存和加载."""
        file_path = tmp_path / "sessions.json"
        store = FileSessionStore(path=file_path)

        sessions = [
            {"id": "sess1", "messages": [], "metadata": {"title": "Test 1"}},
            {"id": "sess2", "messages": [], "metadata": {"title": "Test 2"}},
        ]

        store.save(sessions)
        loaded = store.load()

        assert len(loaded) == 2
        assert loaded[0]["id"] == "sess1"
        assert loaded[1]["id"] == "sess2"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """测试加载不存在的文件."""
        file_path = tmp_path / "nonexistent.json"
        store = FileSessionStore(path=file_path)

        loaded = store.load()
        assert loaded == []

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """测试加载无效 JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json {{{")

        store = FileSessionStore(path=file_path)
        loaded = store.load()
        assert loaded == []

    def test_load_non_list_json(self, tmp_path: Path) -> None:
        """测试加载非列表 JSON."""
        file_path = tmp_path / "notlist.json"
        file_path.write_text('{"key": "value"}')

        store = FileSessionStore(path=file_path)
        loaded = store.load()
        assert loaded == []

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        """测试自动创建父目录."""
        file_path = tmp_path / "deep" / "nested" / "path" / "sessions.json"
        store = FileSessionStore(path=file_path)

        store.save([{"id": "test", "messages": []}])

        assert file_path.exists()
        loaded = store.load()
        assert len(loaded) == 1


class TestFileSessionStoreCompression:
    """FileSessionStore 压缩功能测试."""

    def test_compression_enabled(self, tmp_path: Path) -> None:
        """测试启用压缩."""
        file_path = tmp_path / "sessions.json"
        store = FileSessionStore(path=file_path, compress=True)

        # 应该自动添加 .gz 后缀
        assert store.path.suffix == ".gz"
        assert store.compress_enabled is True

    def test_compression_save_and_load(self, tmp_path: Path) -> None:
        """测试压缩保存和加载."""
        file_path = tmp_path / "sessions.json"
        store = FileSessionStore(path=file_path, compress=True)

        sessions = [
            {"id": "sess1", "messages": [{"role": "user", "content": "Hello " * 100}]},
        ]

        store.save(sessions)
        loaded = store.load()

        assert len(loaded) == 1
        assert loaded[0]["id"] == "sess1"

        # 验证文件确实是 gzip 格式
        with gzip.open(store.path, "rt", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) == 1

    def test_compression_reduces_size(self, tmp_path: Path) -> None:
        """测试压缩确实减小了文件大小."""
        # 创建大量重复数据
        sessions = [
            {
                "id": f"sess{i}",
                "messages": [{"role": "user", "content": "Hello world! " * 100}],
            }
            for i in range(10)
        ]

        # 不压缩
        uncompressed_path = tmp_path / "uncompressed.json"
        store_uncompressed = FileSessionStore(path=uncompressed_path, compress=False)
        store_uncompressed.save(sessions)

        # 压缩
        compressed_path = tmp_path / "compressed.json"
        store_compressed = FileSessionStore(path=compressed_path, compress=True)
        store_compressed.save(sessions)

        uncompressed_size = uncompressed_path.stat().st_size
        compressed_size = store_compressed.path.stat().st_size

        # 压缩后应该更小
        assert compressed_size < uncompressed_size


class TestFileSessionStoreAutoCleanup:
    """FileSessionStore 自动清理功能测试."""

    def test_auto_cleanup_removes_expired(self, tmp_path: Path) -> None:
        """测试自动清理过期会话."""
        file_path = tmp_path / "sessions.json"

        # 先不启用 auto_cleanup 保存数据
        store_no_cleanup = FileSessionStore(path=file_path, auto_cleanup=False)

        # 创建一个过期和一个有效的会话
        old_time = (datetime.now() - timedelta(hours=25)).isoformat()
        new_time = datetime.now().isoformat()

        sessions = [
            {"id": "expired", "last_active": old_time, "messages": []},
            {"id": "valid", "last_active": new_time, "messages": []},
        ]
        store_no_cleanup.save(sessions)

        # 用启用 auto_cleanup 的 store 加载
        store_cleanup = FileSessionStore(
            path=file_path,
            auto_cleanup=True,
            max_age_minutes=1440,  # 24 小时
        )
        loaded = store_cleanup.load()

        # 应该只有有效的会话
        assert len(loaded) == 1
        assert loaded[0]["id"] == "valid"

    def test_manual_cleanup_expired(self, tmp_path: Path) -> None:
        """测试手动清理过期会话."""
        file_path = tmp_path / "sessions.json"
        store = FileSessionStore(
            path=file_path,
            auto_cleanup=False,
            max_age_minutes=1,  # 1 分钟过期
        )

        # 创建过期会话
        old_time = (datetime.now() - timedelta(minutes=5)).isoformat()
        sessions = [
            {"id": "expired1", "last_active": old_time, "messages": []},
            {"id": "expired2", "last_active": old_time, "messages": []},
            {"id": "valid", "last_active": datetime.now().isoformat(), "messages": []},
        ]
        store.save(sessions)

        # 手动清理
        cleaned = store.cleanup_expired()

        assert cleaned == 2

        # 验证只剩下有效的
        loaded = store.load()
        assert len(loaded) == 1
        assert loaded[0]["id"] == "valid"


class TestFileSessionStoreConcurrency:
    """FileSessionStore 并发安全测试."""

    def test_concurrent_writes(self, tmp_path: Path) -> None:
        """测试并发写入."""
        file_path = tmp_path / "sessions.json"
        store = FileSessionStore(path=file_path)

        errors: list[Exception] = []
        success_count = [0]

        def write_session(session_id: str) -> None:
            try:
                sessions = store.load()
                sessions.append({"id": session_id, "messages": []})
                store.save(sessions)
                success_count[0] += 1
            except Exception as e:
                errors.append(e)

        # 启动多个线程并发写入
        threads = []
        for i in range(10):
            t = threading.Thread(target=write_session, args=(f"sess{i}",))
            threads.append(t)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # 不应该有错误
        assert len(errors) == 0
        assert success_count[0] == 10

        # 文件应该是有效的 JSON
        loaded = store.load()
        assert isinstance(loaded, list)


class TestSessionExportImport:
    """Session 导出/导入功能测试."""

    def test_session_export_json(self) -> None:
        """测试单个会话导出为 JSON."""
        session = ChatSession(id="test-session")
        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi there!")

        json_str = session.export_json()
        data = json.loads(json_str)

        assert data["id"] == "test-session"
        assert len(data["messages"]) == 2

    def test_session_export_to_file(self, tmp_path: Path) -> None:
        """测试单个会话导出到文件."""
        session = ChatSession(id="export-test")
        session.add_message("user", "Test message")

        file_path = tmp_path / "session.json"
        session.export_to_file(file_path)

        assert file_path.exists()
        with open(file_path) as f:
            data = json.load(f)
            assert data["id"] == "export-test"

    def test_session_from_json(self) -> None:
        """测试从 JSON 恢复会话."""
        json_str = json.dumps(
            {
                "id": "restored-session",
                "messages": [
                    {"role": "user", "content": "Hello", "timestamp": "2025-01-01T00:00:00"},
                ],
                "created_at": "2025-01-01T00:00:00",
                "last_active": "2025-01-01T00:00:00",
                "metadata": {"title": "Restored Chat"},
            }
        )

        session = ChatSession.from_json(json_str)

        assert session.id == "restored-session"
        assert len(session.messages) == 1
        assert session.title == "Restored Chat"

    def test_session_from_file(self, tmp_path: Path) -> None:
        """测试从文件恢复会话."""
        file_path = tmp_path / "import.json"
        file_path.write_text(
            json.dumps(
                {
                    "id": "file-session",
                    "messages": [],
                    "metadata": {"title": "From File"},
                }
            )
        )

        session = ChatSession.from_file(file_path)

        assert session.id == "file-session"
        assert session.title == "From File"

    def test_session_from_nonexistent_file(self, tmp_path: Path) -> None:
        """测试从不存在的文件恢复."""
        file_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError):
            ChatSession.from_file(file_path)

    def test_session_from_invalid_json(self) -> None:
        """测试从无效 JSON 恢复."""
        with pytest.raises(ValueError, match="Invalid JSON"):
            ChatSession.from_json("not valid json")


class TestSessionManagerExportImport:
    """SessionManager 导出/导入功能测试."""

    def test_export_all_json(self) -> None:
        """测试导出所有会话为 JSON."""
        manager = SessionManager()
        manager.create_session(title="Session 1")
        manager.create_session(title="Session 2")

        json_str = manager.export_all_json()
        data = json.loads(json_str)

        assert data["version"] == "1.0"
        assert "exported_at" in data
        assert len(data["sessions"]) == 2

    def test_export_all_to_file(self, tmp_path: Path) -> None:
        """测试导出所有会话到文件."""
        manager = SessionManager()
        manager.create_session(title="Export Test")

        file_path = tmp_path / "all_sessions.json"
        count = manager.export_all_to_file(file_path)

        assert count == 1
        assert file_path.exists()

    def test_export_single_session(self) -> None:
        """测试导出单个会话."""
        manager = SessionManager()
        session = manager.create_session(title="Single Export")

        json_str = manager.export_session_json(session.id)

        assert json_str is not None
        data = json.loads(json_str)
        assert data["id"] == session.id

    def test_export_nonexistent_session(self) -> None:
        """测试导出不存在的会话."""
        manager = SessionManager()

        result = manager.export_session_json("nonexistent")
        assert result is None

    def test_import_from_json_export_format(self) -> None:
        """测试从导出格式导入."""
        manager = SessionManager()

        export_data = json.dumps(
            {
                "version": "1.0",
                "exported_at": "2025-01-01T00:00:00",
                "sessions": [
                    {"id": "import1", "messages": [], "metadata": {"title": "Imported 1"}},
                    {"id": "import2", "messages": [], "metadata": {"title": "Imported 2"}},
                ],
            }
        )

        imported, skipped = manager.import_from_json(export_data)

        assert imported == 2
        assert skipped == 0
        assert manager.get("import1") is not None
        assert manager.get("import2") is not None

    def test_import_from_json_single_session(self) -> None:
        """测试导入单个会话 JSON."""
        manager = SessionManager()

        session_data = json.dumps(
            {
                "id": "single-import",
                "messages": [],
                "metadata": {"title": "Single Import"},
            }
        )

        imported, skipped = manager.import_from_json(session_data)

        assert imported == 1
        assert skipped == 0
        assert manager.get("single-import") is not None

    def test_import_from_json_list_format(self) -> None:
        """测试导入会话列表."""
        manager = SessionManager()

        sessions_data = json.dumps(
            [
                {"id": "list1", "messages": [], "metadata": {}},
                {"id": "list2", "messages": [], "metadata": {}},
            ]
        )

        imported, skipped = manager.import_from_json(sessions_data)

        assert imported == 2
        assert skipped == 0

    def test_import_skip_existing_without_overwrite(self) -> None:
        """测试不覆盖已存在的会话."""
        manager = SessionManager()
        manager.create_session(session_id="existing", title="Original")

        import_data = json.dumps(
            {
                "id": "existing",
                "messages": [],
                "metadata": {"title": "New Title"},
            }
        )

        imported, skipped = manager.import_from_json(import_data, overwrite=False)

        assert imported == 0
        assert skipped == 1
        assert manager.get("existing").title == "Original"

    def test_import_overwrite_existing(self) -> None:
        """测试覆盖已存在的会话."""
        manager = SessionManager()
        manager.create_session(session_id="existing", title="Original")

        import_data = json.dumps(
            {
                "id": "existing",
                "messages": [],
                "metadata": {"title": "Overwritten"},
            }
        )

        imported, skipped = manager.import_from_json(import_data, overwrite=True)

        assert imported == 1
        assert skipped == 0
        assert manager.get("existing").title == "Overwritten"

    def test_import_from_file(self, tmp_path: Path) -> None:
        """测试从文件导入."""
        file_path = tmp_path / "import.json"
        file_path.write_text(
            json.dumps(
                {
                    "version": "1.0",
                    "sessions": [
                        {"id": "file-import", "messages": [], "metadata": {}},
                    ],
                }
            )
        )

        manager = SessionManager()
        imported, skipped = manager.import_from_file(file_path)

        assert imported == 1
        assert manager.get("file-import") is not None

    def test_import_from_nonexistent_file(self, tmp_path: Path) -> None:
        """测试从不存在的文件导入."""
        manager = SessionManager()

        with pytest.raises(FileNotFoundError):
            manager.import_from_file(tmp_path / "nonexistent.json")

    def test_import_invalid_json(self) -> None:
        """测试导入无效 JSON."""
        manager = SessionManager()

        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.import_from_json("not valid json")

    def test_roundtrip_export_import(self) -> None:
        """测试导出-导入往返."""
        # 创建并填充 manager
        manager1 = SessionManager()
        session = manager1.create_session(title="Roundtrip Test")
        session.add_message("user", "Hello!")
        session.add_message("assistant", "Hi there!")
        manager1.persist()

        # 导出
        exported = manager1.export_all_json()

        # 导入到新 manager
        manager2 = SessionManager()
        imported, _ = manager2.import_from_json(exported)

        assert imported == 1
        restored = manager2.get(session.id)
        assert restored is not None
        assert restored.title == "Roundtrip Test"
        assert len(restored.messages) == 2
