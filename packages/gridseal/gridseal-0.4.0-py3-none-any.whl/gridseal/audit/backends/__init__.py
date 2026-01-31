# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Audit storage backends."""

from gridseal.audit.backends.base import BaseBackend
from gridseal.audit.backends.memory import MemoryBackend
from gridseal.audit.backends.sqlite import SQLiteBackend

__all__ = [
    "BaseBackend",
    "MemoryBackend",
    "SQLiteBackend",
]


def get_postgresql_backend() -> type:
    """
    Get PostgreSQL backend class (lazy import).

    Returns:
        PostgreSQLBackend class

    Raises:
        ImportError: If psycopg2 is not installed
    """
    from gridseal.audit.backends.postgresql import PostgreSQLBackend

    return PostgreSQLBackend
