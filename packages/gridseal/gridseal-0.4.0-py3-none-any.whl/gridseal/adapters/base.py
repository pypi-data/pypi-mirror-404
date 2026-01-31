# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Base class for observability adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAdapter(ABC):
    """
    Abstract base class for observability platform adapters.

    Adapters enable GridSeal to work with existing observability
    tools like Langfuse, LangSmith, etc.
    """

    @abstractmethod
    def start_sync(self) -> None:
        """Start synchronizing traces to GridSeal."""
        pass

    @abstractmethod
    def stop_sync(self) -> None:
        """Stop synchronizing traces."""
        pass

    @abstractmethod
    def process_trace(self, trace: dict[str, Any]) -> None:
        """
        Process a trace from the observability platform.

        Args:
            trace: Trace data from the platform
        """
        pass

    @property
    @abstractmethod
    def is_syncing(self) -> bool:
        """Check if sync is active."""
        pass
