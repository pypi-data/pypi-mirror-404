# Copyright (c) 2026 Celestir LLC
# SPDX-License-Identifier: AGPL-3.0-or-later

"""GridSeal command-line interface."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from gridseal._version import __version__

app = typer.Typer(
    name="gridseal",
    help="GridSeal: Verification and audit logging for LLM applications.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def version() -> None:
    """Show GridSeal version."""
    console.print(f"GridSeal v{__version__}")


@app.command()
def verify(
    path: str = typer.Option(
        "./gridseal_audit.db",
        "--path",
        "-p",
        help="Path to SQLite database",
    ),
) -> None:
    """
    Verify audit log integrity.

    Checks that all records are valid and the hash chain is unbroken.
    """
    from gridseal.audit import AuditStore
    from gridseal.core.config import AuditConfig

    if not Path(path).exists():
        console.print(f"[red]Error:[/red] Database not found at {path}")
        raise typer.Exit(1)

    config = AuditConfig(backend="sqlite", path=path)
    store = AuditStore(config)

    console.print(f"Verifying integrity of {store.count()} records...")

    is_valid = store.verify_integrity()

    if is_valid:
        console.print("[green]Integrity check passed[/green]")
    else:
        console.print("[red]Integrity check failed[/red]")
        raise typer.Exit(1)


@app.command()
def export(
    path: str = typer.Option(
        "./gridseal_audit.db",
        "--path",
        "-p",
        help="Path to SQLite database",
    ),
    output: str = typer.Option(
        "./audit_export.json",
        "--output",
        "-o",
        help="Output file path",
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format (json or csv)",
    ),
) -> None:
    """Export audit records to file."""
    from gridseal.audit import AuditStore
    from gridseal.core.config import AuditConfig

    if not Path(path).exists():
        console.print(f"[red]Error:[/red] Database not found at {path}")
        raise typer.Exit(1)

    config = AuditConfig(backend="sqlite", path=path)
    store = AuditStore(config)

    count = store.export(output, format=format)

    console.print(f"Exported {count} records to [bold]{output}[/bold]")


@app.command()
def stats(
    path: str = typer.Option(
        "./gridseal_audit.db",
        "--path",
        "-p",
        help="Path to SQLite database",
    ),
) -> None:
    """Show audit store statistics."""
    from gridseal.audit import AuditStore
    from gridseal.core.config import AuditConfig

    if not Path(path).exists():
        console.print(f"[red]Error:[/red] Database not found at {path}")
        raise typer.Exit(1)

    config = AuditConfig(backend="sqlite", path=path)
    store = AuditStore(config)

    total = store.count()
    passed = len(store.query(verification_passed=True, limit=1000000))
    failed = len(store.query(verification_passed=False, limit=1000000))

    table = Table(title="Audit Store Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Database", path)
    table.add_row("Total Records", str(total))
    table.add_row("Passed Verification", str(passed))
    table.add_row("Failed Verification", str(failed))

    if total > 0:
        pass_rate = (passed / total) * 100
        table.add_row("Pass Rate", f"{pass_rate:.1f}%")

    console.print(table)


@app.command()
def init(
    path: str = typer.Option(
        "./gridseal_audit.db",
        "--path",
        "-p",
        help="Path for SQLite database",
    ),
) -> None:
    """Initialize a new audit database."""
    from gridseal.audit import AuditStore
    from gridseal.core.config import AuditConfig

    if Path(path).exists():
        console.print(f"[yellow]Warning:[/yellow] Database already exists at {path}")
        raise typer.Exit(0)

    config = AuditConfig(backend="sqlite", path=path)
    store = AuditStore(config)
    store.close()

    console.print(f"Initialized new audit database at [bold]{path}[/bold]")


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
