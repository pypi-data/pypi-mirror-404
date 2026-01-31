# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Tests for audit store."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from gridseal.audit.backends.memory import MemoryBackend
from gridseal.audit.backends.sqlite import SQLiteBackend
from gridseal.audit.store import AuditStore
from gridseal.core.config import AuditConfig
from gridseal.core.exceptions import AuditError


class TestAuditStore:
    """Tests for AuditStore."""

    def test_default_config(self) -> None:
        """Test store with default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = AuditConfig(
                backend="sqlite",
                path=os.path.join(tmpdir, "test.db"),
            )
            store = AuditStore(config)

            assert store.config.backend == "sqlite"
            store.close()

    def test_memory_backend(self) -> None:
        """Test store with memory backend."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        assert isinstance(store._backend, MemoryBackend)

    def test_sqlite_backend(self, temp_db_path: str) -> None:
        """Test store with SQLite backend."""
        config = AuditConfig(backend="sqlite", path=temp_db_path)
        store = AuditStore(config)

        assert isinstance(store._backend, SQLiteBackend)
        store.close()

    def test_log_creates_record(self) -> None:
        """Test that log creates an audit record."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        record = store.log(
            query="Test query",
            context=["doc1", "doc2"],
            response="Test response",
            verification_passed=True,
        )

        assert record.query == "Test query"
        assert record.context == ["doc1", "doc2"]
        assert record.response == "Test response"
        assert record.verification_passed is True
        assert record.id is not None

    def test_log_with_metadata(self) -> None:
        """Test logging with metadata."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        record = store.log(
            query="Test",
            context=[],
            response="Response",
            metadata={"user_id": "123", "session": "abc"},
        )

        assert record.metadata["user_id"] == "123"
        assert record.metadata["session"] == "abc"

    def test_log_with_verification_results(self) -> None:
        """Test logging with verification results."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        results = {"grounding": {"score": 0.85, "passed": True}}
        record = store.log(
            query="Test",
            context=[],
            response="Response",
            verification_results=results,
        )

        assert record.verification_results == results

    def test_get_record(self) -> None:
        """Test retrieving a record by ID."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        logged = store.log(query="Test", context=[], response="Response")
        retrieved = store.get(logged.id)

        assert retrieved is not None
        assert retrieved.id == logged.id
        assert retrieved.query == "Test"

    def test_get_nonexistent(self) -> None:
        """Test retrieving nonexistent record."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        result = store.get("nonexistent-id")

        assert result is None

    def test_count(self) -> None:
        """Test record counting."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        assert store.count() == 0

        store.log(query="1", context=[], response="r1")
        assert store.count() == 1

        store.log(query="2", context=[], response="r2")
        assert store.count() == 2

    def test_query_all(self) -> None:
        """Test querying all records."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=[], response="r1")
        store.log(query="2", context=[], response="r2")

        results = store.query()

        assert len(results) == 2

    def test_query_by_verification_passed(self) -> None:
        """Test filtering by verification_passed."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=[], response="r1", verification_passed=True)
        store.log(query="2", context=[], response="r2", verification_passed=False)
        store.log(query="3", context=[], response="r3", verification_passed=True)

        passed = store.query(verification_passed=True)
        failed = store.query(verification_passed=False)

        assert len(passed) == 2
        assert len(failed) == 1

    def test_query_limit(self) -> None:
        """Test query limit."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        for i in range(10):
            store.log(query=str(i), context=[], response=f"r{i}")

        results = store.query(limit=5)

        assert len(results) == 5

    def test_verify_integrity_empty(self) -> None:
        """Test integrity verification on empty store."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        assert store.verify_integrity() is True

    def test_verify_integrity_valid(self) -> None:
        """Test integrity verification with valid chain."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=[], response="r1")
        store.log(query="2", context=[], response="r2")
        store.log(query="3", context=[], response="r3")

        assert store.verify_integrity() is True

    def test_hash_chain_linkage(self) -> None:
        """Test that records are linked via hash chain."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        r1 = store.log(query="1", context=[], response="r1")
        r2 = store.log(query="2", context=[], response="r2")

        assert r1.previous_hash == "genesis"
        assert r2.previous_hash == r1.record_hash

    def test_export_json(self) -> None:
        """Test JSON export."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=["c1"], response="r1")
        store.log(query="2", context=["c2"], response="r2")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            count = store.export(output_path, format="json")

            assert count == 2
            assert Path(output_path).exists()

            with open(output_path) as f:
                data = json.load(f)

            assert len(data) == 2
            assert data[0]["query"] in ["1", "2"]
        finally:
            os.unlink(output_path)

    def test_export_csv(self) -> None:
        """Test CSV export."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=[], response="r1")

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            output_path = f.name

        try:
            count = store.export(output_path, format="csv")

            assert count == 1
            assert Path(output_path).exists()

            with open(output_path) as f:
                content = f.read()

            assert "id" in content
            assert "query" in content
        finally:
            os.unlink(output_path)

    def test_export_invalid_format(self) -> None:
        """Test export with invalid format."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        with pytest.raises(AuditError):
            store.export("/tmp/test.txt", format="invalid")

    def test_unknown_backend(self) -> None:
        """Test error on unknown backend."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            AuditConfig(backend="unknown")  # type: ignore[arg-type]

    def test_close(self) -> None:
        """Test closing store."""
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        store.log(query="1", context=[], response="r1")
        store.close()


class TestMemoryBackend:
    """Tests for MemoryBackend."""

    def test_insert_and_get(self, memory_backend: MemoryBackend) -> None:
        """Test insert and get operations."""
        from gridseal.core.types import AuditRecord

        record = AuditRecord(query="test", response="response")
        memory_backend.insert(record)

        retrieved = memory_backend.get(record.id)

        assert retrieved is not None
        assert retrieved.id == record.id

    def test_get_last_record(self, memory_backend: MemoryBackend) -> None:
        """Test get_last_record."""
        from gridseal.core.types import AuditRecord

        r1 = AuditRecord(query="1", response="r1")
        r2 = AuditRecord(query="2", response="r2")

        memory_backend.insert(r1)
        memory_backend.insert(r2)

        last = memory_backend.get_last_record()

        assert last is not None
        assert last.id == r2.id

    def test_get_last_record_empty(self, memory_backend: MemoryBackend) -> None:
        """Test get_last_record on empty backend."""
        result = memory_backend.get_last_record()

        assert result is None

    def test_get_all_ordered(self, memory_backend: MemoryBackend) -> None:
        """Test get_all_ordered."""
        from gridseal.core.types import AuditRecord

        r1 = AuditRecord(query="1", response="r1")
        r2 = AuditRecord(query="2", response="r2")

        memory_backend.insert(r1)
        memory_backend.insert(r2)

        all_records = memory_backend.get_all_ordered()

        assert len(all_records) == 2
        assert all_records[0].id == r1.id
        assert all_records[1].id == r2.id

    def test_count(self, memory_backend: MemoryBackend) -> None:
        """Test count."""
        from gridseal.core.types import AuditRecord

        assert memory_backend.count() == 0

        memory_backend.insert(AuditRecord(query="1", response="r1"))
        assert memory_backend.count() == 1

    def test_clear(self, memory_backend: MemoryBackend) -> None:
        """Test clear."""
        from gridseal.core.types import AuditRecord

        memory_backend.insert(AuditRecord(query="1", response="r1"))
        assert memory_backend.count() == 1

        memory_backend.clear()
        assert memory_backend.count() == 0


class TestSQLiteBackend:
    """Tests for SQLiteBackend."""

    def test_creates_database(self, temp_db_path: str) -> None:
        """Test that database file is created."""
        backend = SQLiteBackend(temp_db_path)

        assert Path(temp_db_path).exists()
        backend.close()

    def test_insert_and_get(self, temp_db_path: str) -> None:
        """Test insert and get operations."""
        from gridseal.core.types import AuditRecord

        backend = SQLiteBackend(temp_db_path)
        record = AuditRecord(query="test", response="response")
        backend.insert(record)

        retrieved = backend.get(record.id)

        assert retrieved is not None
        assert retrieved.id == record.id
        assert retrieved.query == "test"

        backend.close()

    def test_persistence(self, temp_db_path: str) -> None:
        """Test that data persists across connections."""
        from gridseal.core.types import AuditRecord

        backend1 = SQLiteBackend(temp_db_path)
        record = AuditRecord(query="persistent", response="data")
        backend1.insert(record)
        backend1.close()

        backend2 = SQLiteBackend(temp_db_path)
        retrieved = backend2.get(record.id)

        assert retrieved is not None
        assert retrieved.query == "persistent"

        backend2.close()

    def test_count(self, temp_db_path: str) -> None:
        """Test count."""
        from gridseal.core.types import AuditRecord

        backend = SQLiteBackend(temp_db_path)

        assert backend.count() == 0

        backend.insert(AuditRecord(query="1", response="r1"))
        assert backend.count() == 1

        backend.insert(AuditRecord(query="2", response="r2"))
        assert backend.count() == 2

        backend.close()
