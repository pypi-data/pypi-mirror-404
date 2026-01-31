# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Langfuse adapter for GridSeal."""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING, Any

from gridseal.adapters.base import BaseAdapter
from gridseal.core.exceptions import AdapterError

if TYPE_CHECKING:
    from gridseal.audit import AuditStore

logger = logging.getLogger(__name__)


class LangfuseAdapter(BaseAdapter):
    """
    Adapter for Langfuse observability platform.

    Polls Langfuse for new traces and logs them to GridSeal's
    audit store.
    """

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        host: str = "https://cloud.langfuse.com",
        poll_interval: float = 5.0,
    ) -> None:
        """
        Initialize Langfuse adapter.

        Args:
            public_key: Langfuse public key
            secret_key: Langfuse secret key
            host: Langfuse API host
            poll_interval: Seconds between polling for new traces
        """
        self.public_key = public_key
        self.secret_key = secret_key
        self.host = host
        self.poll_interval = poll_interval

        self._store: AuditStore | None = None
        self._syncing = False
        self._sync_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._last_trace_id: str | None = None

    def attach_store(self, store: AuditStore) -> None:
        """
        Attach an audit store for logging.

        Args:
            store: AuditStore instance
        """
        self._store = store

    def start_sync(self) -> None:
        """Start synchronizing traces to GridSeal."""
        if self._syncing:
            logger.warning("Sync already running")
            return

        if self._store is None:
            raise AdapterError("No audit store attached")

        self._stop_event.clear()
        self._syncing = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info("Started Langfuse sync")

    def stop_sync(self) -> None:
        """Stop synchronizing traces."""
        if not self._syncing:
            return

        self._stop_event.set()
        if self._sync_thread:
            self._sync_thread.join(timeout=10)
        self._syncing = False
        logger.info("Stopped Langfuse sync")

    def process_trace(self, trace: dict[str, Any]) -> None:
        """
        Process a trace from Langfuse.

        Args:
            trace: Trace data from Langfuse API
        """
        if self._store is None:
            raise AdapterError("No audit store attached")

        try:
            query = trace.get("input", "")
            if isinstance(query, dict):
                query = str(query)

            response = trace.get("output", "")
            if isinstance(response, dict):
                response = str(response)

            metadata = {
                "source": "langfuse",
                "trace_id": trace.get("id"),
                "model": trace.get("model"),
                "latency_ms": trace.get("latency"),
            }

            self._store.log(
                query=query,
                context=[],
                response=response,
                verification_passed=True,
                metadata=metadata,
            )
            logger.debug(f"Processed Langfuse trace {trace.get('id')}")

        except Exception as e:
            logger.error(f"Failed to process trace: {e}")

    @property
    def is_syncing(self) -> bool:
        """Check if sync is active."""
        return self._syncing

    def _sync_loop(self) -> None:
        """Background sync loop."""
        while not self._stop_event.is_set():
            try:
                traces = self._fetch_traces()
                for trace in traces:
                    self.process_trace(trace)
            except Exception as e:
                logger.error(f"Sync loop error: {e}")

            self._stop_event.wait(self.poll_interval)

    def _fetch_traces(self) -> list[dict[str, Any]]:
        """
        Fetch new traces from Langfuse.

        Returns:
            List of trace dictionaries
        """
        try:
            import urllib.request
            import base64
            import json as json_module

            credentials = base64.b64encode(
                f"{self.public_key}:{self.secret_key}".encode()
            ).decode()

            url = f"{self.host}/api/public/traces"
            if self._last_trace_id:
                url += f"?fromId={self._last_trace_id}"

            request = urllib.request.Request(
                url,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
            )

            with urllib.request.urlopen(request, timeout=30) as response:
                data = json_module.loads(response.read().decode())

            traces = data.get("data", [])
            if traces:
                self._last_trace_id = traces[-1].get("id")

            return traces

        except Exception as e:
            logger.debug(f"Failed to fetch traces: {e}")
            return []
