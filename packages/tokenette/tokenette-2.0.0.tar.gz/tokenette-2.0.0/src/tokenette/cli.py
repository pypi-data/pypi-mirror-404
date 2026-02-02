"""
Tokenette CLI

Command-line interface for the Tokenette MCP server.

Commands:
- run: Start the MCP server
- metrics: View current metrics
- config: Manage configuration
- cache: Cache management
- analyze: Analyze code directly
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from .config import TokenetteConfig, get_config
from .core import MultiLayerCache, TaskRouter

app = typer.Typer(
    name="tokenette",
    help="🪙 Tokenette: The Ultimate AI Coding Enhancement MCP",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


# ─── RUN COMMAND ─────────────────────────────────────────────────


@app.command()
def run(
    host: Annotated[str, typer.Option(help="Host to bind to")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to bind to")] = 8000,
    transport: Annotated[str, typer.Option(help="Transport type: stdio, sse, http")] = "stdio",
    reload: Annotated[bool, typer.Option(help="Enable auto-reload")] = False,
    debug: Annotated[bool, typer.Option(help="Enable debug mode")] = False,
):
    """
    🚀 Start the Tokenette MCP server.

    Examples:
        tokenette run                    # stdio transport (default)
        tokenette run --transport sse    # SSE transport
        tokenette run --port 8080        # Custom port
    """
    from .server import mcp

    console.print(
        Panel.fit(
            "[bold green]🪙 Tokenette MCP Server[/bold green]\n"
            f"Transport: {transport} | Host: {host}:{port}",
            border_style="green",
        )
    )

    if transport == "stdio":
        # Run with stdio transport (default for MCP)
        mcp.run(transport="stdio")
    elif transport == "sse":
        # Run with SSE transport
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "http":
        # Run with HTTP/streamable transport
        import uvicorn

        uvicorn.run(
            "tokenette.server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="debug" if debug else "info",
        )
    else:
        console.print(f"[red]Unknown transport: {transport}[/red]")
        raise typer.Exit(1)


# ─── METRICS COMMAND ─────────────────────────────────────────────


@app.command()
def metrics(format: Annotated[str, typer.Option(help="Output format: table, json")] = "table"):
    """
    📊 View current metrics and statistics.

    Shows token savings, cache performance, and budget usage.
    """
    config = get_config()

    # Initialize components for stats
    cache = MultiLayerCache(config.cache)
    router = TaskRouter(config.router)

    if format == "json":
        data = {
            "cache": asyncio.run(_get_cache_stats(cache)),
            "budget": {
                "limit": router.budget_tracker.monthly_limit,
                "used": router.budget_tracker.used,
                "remaining": router.budget_tracker.remaining,
            },
            "config": {
                "cache_l1_size": config.cache.l1_max_size,
                "cache_l2_size": config.cache.l2_max_size,
                "compression_min_size": config.compression.min_size,
            },
        }
        console.print_json(json.dumps(data))
        return

    # Table format
    table = Table(title="🪙 Tokenette Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Description", style="dim")

    # Cache stats
    cache_stats = asyncio.run(_get_cache_stats(cache))
    table.add_row("L1 Cache Entries", str(cache_stats.get("l1_entries", 0)), "In-memory LRU cache")
    table.add_row("L2 Cache Entries", str(cache_stats.get("l2_entries", 0)), "Disk cache (warm)")
    table.add_row("Cache Hit Rate", f"{cache_stats.get('hit_rate', 0):.1%}", "Overall hit rate")

    # Budget stats
    table.add_row("", "", "")  # Separator
    table.add_row("Budget Used", f"{router.budget_tracker.used:.1f}", "Premium requests used")
    table.add_row(
        "Budget Remaining", f"{router.budget_tracker.remaining:.1f}", "Premium requests left"
    )
    table.add_row("Budget %", f"{router.budget_tracker.usage_pct:.1f}%", "Monthly usage")

    console.print(table)


async def _get_cache_stats(cache: MultiLayerCache) -> dict:
    """Get cache statistics."""
    return cache.get_stats()


# ─── CONFIG COMMAND ──────────────────────────────────────────────


@app.command()
def config(
    show: Annotated[bool, typer.Option(help="Show current configuration")] = False,
    init: Annotated[bool, typer.Option(help="Initialize config file")] = False,
    path: Annotated[Path | None, typer.Option(help="Config file path")] = None,
):
    """
    ⚙️ Manage Tokenette configuration.

    Examples:
        tokenette config --show          # Show current config
        tokenette config --init          # Create .tokenette.json
    """
    if init:
        config_path = path or Path(".tokenette.json")
        if config_path.exists():
            console.print(f"[yellow]Config already exists: {config_path}[/yellow]")
            if not typer.confirm("Overwrite?"):
                raise typer.Exit(0)

        # Create default config
        default_config = TokenetteConfig()
        config_path.write_text(default_config.model_dump_json(indent=2))
        console.print(f"[green]✓ Created config: {config_path}[/green]")
        return

    if show or not any([init]):
        cfg = get_config()
        syntax = Syntax(cfg.model_dump_json(indent=2), "json", theme="monokai", line_numbers=True)
        console.print(Panel(syntax, title="Current Configuration", border_style="blue"))


# ─── CACHE COMMAND ───────────────────────────────────────────────


@app.command()
def cache(
    clear: Annotated[bool, typer.Option(help="Clear all caches")] = False,
    clear_l1: Annotated[bool, typer.Option(help="Clear L1 cache only")] = False,
    stats: Annotated[bool, typer.Option(help="Show cache statistics")] = False,
):
    """
    🗄️ Cache management commands.

    Examples:
        tokenette cache --stats         # Show cache stats
        tokenette cache --clear         # Clear all caches
        tokenette cache --clear-l1      # Clear memory cache only
    """
    config = get_config()
    cache_instance = MultiLayerCache(config.cache)

    if clear:
        asyncio.run(cache_instance.clear())
        console.print("[green]✓ All caches cleared[/green]")
        return

    if clear_l1:
        cache_instance.l1.clear()
        console.print("[green]✓ L1 cache cleared[/green]")
        return

    if stats or not any([clear, clear_l1]):
        cache_stats = asyncio.run(_get_cache_stats(cache_instance))

        table = Table(title="🗄️ Cache Statistics")
        table.add_column("Layer", style="cyan")
        table.add_column("Entries", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Hit Rate", style="magenta")

        table.add_row(
            "L1 (Memory)",
            str(cache_stats.get("l1_entries", 0)),
            f"{cache_stats.get('l1_size_mb', 0):.1f} MB",
            f"{cache_stats.get('l1_hit_rate', 0):.1%}",
        )
        table.add_row(
            "L2 (Disk Warm)",
            str(cache_stats.get("l2_entries", 0)),
            f"{cache_stats.get('l2_size_mb', 0):.1f} MB",
            f"{cache_stats.get('l2_hit_rate', 0):.1%}",
        )
        table.add_row(
            "L3 (Disk Cold)",
            str(cache_stats.get("l3_entries", 0)),
            f"{cache_stats.get('l3_size_mb', 0):.1f} MB",
            "-",
        )
        table.add_row(
            "L4 (Semantic)",
            str(cache_stats.get("l4_entries", 0)),
            "-",
            f"{cache_stats.get('l4_hit_rate', 0):.1%}",
        )

        console.print(table)


# ─── ANALYZE COMMAND ─────────────────────────────────────────────


@app.command()
def analyze(
    path: Annotated[Path, typer.Argument(help="File or directory to analyze")],
    complexity: Annotated[bool, typer.Option(help="Check complexity")] = True,
    security: Annotated[bool, typer.Option(help="Check security issues")] = True,
    style: Annotated[bool, typer.Option(help="Check style issues")] = False,
    format: Annotated[str, typer.Option(help="Output format: table, json")] = "table",
):
    """
    🔍 Analyze code for issues and complexity.

    Examples:
        tokenette analyze src/              # Analyze directory
        tokenette analyze main.py           # Analyze file
        tokenette analyze . --security      # Security check only
    """
    from .tools.analysis import analyze_code as do_analyze

    checks = []
    if complexity:
        checks.append("complexity")
    if security:
        checks.append("security")
    if style:
        checks.append("style")

    result = asyncio.run(do_analyze(str(path), checks))

    if format == "json":
        console.print_json(json.dumps(result))
        return

    # Summary panel
    summary = result.get("summary", {})
    console.print(
        Panel(
            f"[bold]Files analyzed:[/bold] {summary.get('files_analyzed', 0)}\n"
            f"[bold]Total issues:[/bold] {summary.get('total_issues', 0)}\n"
            f"[red]High:[/red] {summary.get('high_severity', 0)} | "
            f"[yellow]Medium:[/yellow] {summary.get('medium_severity', 0)} | "
            f"[dim]Low:[/dim] {summary.get('low_severity', 0)}",
            title="🔍 Analysis Summary",
            border_style="blue",
        )
    )

    # Issues table
    issues = result.get("issues", [])
    if issues:
        table = Table(title="Issues Found")
        table.add_column("Severity", style="bold")
        table.add_column("Type", style="cyan")
        table.add_column("File:Line", style="dim")
        table.add_column("Message")

        for issue in issues[:20]:  # Limit display
            severity_color = {"high": "red", "medium": "yellow", "low": "dim"}.get(
                issue.get("severity", "low"), "dim"
            )

            table.add_row(
                f"[{severity_color}]{issue.get('severity', 'low').upper()}[/{severity_color}]",
                issue.get("type", "unknown"),
                f"{Path(issue.get('file', '')).name}:{issue.get('line', 0)}",
                issue.get("message", "")[:60],
            )

        console.print(table)

        if len(issues) > 20:
            console.print(f"[dim]... and {len(issues) - 20} more issues[/dim]")


# ─── ROUTE COMMAND ───────────────────────────────────────────────


@app.command()
def route(
    task: Annotated[str, typer.Argument(help="Task description")],
    files: Annotated[int, typer.Option(help="Number of affected files")] = 1,
):
    """
    🧭 Get model routing recommendation for a task.

    Examples:
        tokenette route "fix auth bug"
        tokenette route "refactor entire codebase" --files 50
    """
    config = get_config()
    router = TaskRouter(config.router)

    decision = router.route(task, {"affected_files": files})

    # Display recommendation
    console.print(
        Panel(
            f"[bold cyan]Recommended Model:[/bold cyan] {decision.model}\n"
            f"[bold]Complexity:[/bold] {decision.complexity.name}\n"
            f"[bold]Category:[/bold] {decision.category.value}\n"
            f"[bold]Multiplier:[/bold] {decision.multiplier}× → {decision.effective_multiplier}× (with auto)\n"
            f"[bold]Quality Boosters:[/bold] {', '.join(decision.quality_boosters[:3])}\n"
            f"[bold]Fallbacks:[/bold] {' → '.join(decision.fallback_chain[:3])}",
            title="🧭 Task Routing",
            border_style="green",
        )
    )

    console.print(f"\n[dim]{decision.reasoning}[/dim]")


# ─── VERSION COMMAND ─────────────────────────────────────────────


@app.command()
def version():
    """📦 Show Tokenette version."""
    from . import __version__

    console.print(f"[bold green]Tokenette[/bold green] v{__version__}")


# ─── MAIN ENTRY POINT ────────────────────────────────────────────


def main():
    """Main CLI entry point."""
    app()


if __name__ == "__main__":
    main()
