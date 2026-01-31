# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Integration tests for Langfuse adapter."""

from __future__ import annotations

import pytest

from gridseal import GridSeal
from gridseal.adapters.langfuse import LangfuseAdapter
from gridseal.audit.store import AuditStore
from gridseal.core.config import AuditConfig
from gridseal.core.exceptions import AdapterError


class TestLangfuseAdapter:
    """Tests for LangfuseAdapter."""

    def test_initialization(self) -> None:
        """Test adapter initialization."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        assert adapter.public_key == "pk-test"
        assert adapter.secret_key == "sk-test"
        assert adapter.host == "https://cloud.langfuse.com"
        assert adapter.poll_interval == 5.0
        assert adapter.is_syncing is False

    def test_custom_params(self) -> None:
        """Test adapter with custom parameters."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
            host="https://custom.langfuse.com",
            poll_interval=10.0,
        )

        assert adapter.host == "https://custom.langfuse.com"
        assert adapter.poll_interval == 10.0

    def test_attach_store(self) -> None:
        """Test attaching audit store."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )
        config = AuditConfig(backend="memory")
        store = AuditStore(config)

        adapter.attach_store(store)

        assert adapter._store is store

    def test_process_trace(self) -> None:
        """Test processing a trace."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )
        config = AuditConfig(backend="memory")
        store = AuditStore(config)
        adapter.attach_store(store)

        trace = {
            "id": "trace-123",
            "input": "Test query",
            "output": "Test response",
            "model": "gpt-4",
            "latency": 500,
        }

        adapter.process_trace(trace)

        assert store.count() == 1
        record = store.query()[0]
        assert record.query == "Test query"
        assert record.response == "Test response"
        assert record.metadata.get("source") == "langfuse"
        assert record.metadata.get("trace_id") == "trace-123"

    def test_process_trace_dict_input(self) -> None:
        """Test processing trace with dict input."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )
        config = AuditConfig(backend="memory")
        store = AuditStore(config)
        adapter.attach_store(store)

        trace = {
            "id": "trace-123",
            "input": {"query": "Structured input"},
            "output": {"result": "Structured output"},
        }

        adapter.process_trace(trace)

        assert store.count() == 1

    def test_process_trace_without_store(self) -> None:
        """Test that process_trace fails without store."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        with pytest.raises(AdapterError):
            adapter.process_trace({"id": "test"})

    def test_start_sync_without_store(self) -> None:
        """Test that start_sync fails without store."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        with pytest.raises(AdapterError):
            adapter.start_sync()

    def test_is_syncing_property(self) -> None:
        """Test is_syncing property."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        assert adapter.is_syncing is False

    def test_stop_sync_when_not_syncing(self) -> None:
        """Test stop_sync when not syncing is safe."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )

        adapter.stop_sync()

    def test_gridseal_with_adapter(self) -> None:
        """Test GridSeal initialization with adapter."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )
        gs = GridSeal(
            mode="adapter",
            audit={"backend": "memory"},
            adapter=adapter,
        )

        assert gs._adapter is adapter
        assert adapter._store is gs.store

    def test_multiple_traces(self) -> None:
        """Test processing multiple traces."""
        adapter = LangfuseAdapter(
            public_key="pk-test",
            secret_key="sk-test",
        )
        config = AuditConfig(backend="memory")
        store = AuditStore(config)
        adapter.attach_store(store)

        for i in range(5):
            adapter.process_trace(
                {
                    "id": f"trace-{i}",
                    "input": f"Query {i}",
                    "output": f"Response {i}",
                }
            )

        assert store.count() == 5
        assert store.verify_integrity() is True
