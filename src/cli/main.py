"""Main CLI application for RENEC harvester."""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from src import __version__
from src.cli.commands import crawl, db, harvest, validate, diff, export

# Create Typer app
app = typer.Typer(
    name="renec-harvester",
    help="RENEC Harvester - Site-wide public data harvester for México's RENEC platform",
    add_completion=True,
    rich_markup_mode="rich",
)

# Create console for rich output
console = Console()

# Add command groups
app.add_typer(crawl.app, name="crawl", help="Site crawling and mapping commands")
app.add_typer(harvest.app, name="harvest", help="Data harvesting commands")
app.add_typer(db.app, name="db", help="Database management commands")
app.add_typer(validate.app, name="validate", help="Data validation commands")
app.add_typer(diff.app, name="diff", help="Diff and change detection commands")
app.add_typer(export.app, name="export", help="Data export commands")


@app.command()
def version():
    """Show version information."""
    print(f"[bold cyan]RENEC Harvester[/bold cyan] version [bold green]{__version__}[/bold green]")


@app.command()
def status():
    """Show system status and health check."""
    from src.utils.health import check_system_health
    
    console.print("[bold cyan]RENEC Harvester System Status[/bold cyan]\n")
    
    # Check system health
    health_status = check_system_health()
    
    # Create status table
    table = Table(title="Service Status", show_header=True, header_style="bold magenta")
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="yellow")
    
    for service, status in health_status.items():
        status_icon = "✅" if status["healthy"] else "❌"
        table.add_row(
            service,
            f"{status_icon} {status['status']}",
            status.get("message", ""),
        )
    
    console.print(table)
    
    # Show configuration
    console.print("\n[bold cyan]Configuration[/bold cyan]")
    console.print(f"Database: {health_status.get('database', {}).get('url', 'Not configured')}")
    console.print(f"Redis: {health_status.get('redis', {}).get('url', 'Not configured')}")
    console.print(f"Environment: {health_status.get('environment', 'development')}")


@app.command()
def init():
    """Initialize the harvester environment."""
    console.print("[bold cyan]Initializing RENEC Harvester...[/bold cyan]\n")
    
    # Create directories
    directories = [
        "artifacts",
        "artifacts/crawl_maps",
        "artifacts/harvests",
        "artifacts/exports",
        "artifacts/diffs",
        "logs",
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        console.print(f"✅ Created directory: {dir_path}")
    
    # Check environment file
    if not Path(".env").exists() and Path(".env.example").exists():
        import shutil
        shutil.copy(".env.example", ".env")
        console.print("✅ Created .env file from .env.example")
        console.print("[yellow]⚠️  Please update .env with your configuration[/yellow]")
    
    # Initialize database
    console.print("\n[bold]Initializing database...[/bold]")
    try:
        from src.models.base import init_db
        init_db()
        console.print("✅ Database tables created")
    except Exception as e:
        console.print(f"[red]❌ Database initialization failed: {e}[/red]")
        sys.exit(1)
    
    console.print("\n[bold green]✨ Initialization complete![/bold green]")
    console.print("Run [bold]make start[/bold] to start Docker services")


@app.command()
def info():
    """Show detailed information about the harvester."""
    from src.core.constants import COMPONENT_TYPES, RENEC_ENDPOINTS
    
    console.print("[bold cyan]RENEC Harvester Information[/bold cyan]\n")
    
    # Component types
    console.print("[bold]Supported Component Types:[/bold]")
    for comp_type, patterns in COMPONENT_TYPES.items():
        console.print(f"  • {comp_type}: {', '.join(patterns[:3])}...")
    
    # Endpoints
    console.print("\n[bold]Known Endpoints:[/bold]")
    for endpoint_type, endpoints in RENEC_ENDPOINTS.items():
        console.print(f"  • {endpoint_type}:")
        for endpoint in endpoints[:2]:
            console.print(f"    - {endpoint}")
    
    # Performance targets
    console.print("\n[bold]Performance Targets:[/bold]")
    console.print("  • Full harvest: ≤20 minutes")
    console.print("  • API response: ≤50ms")
    console.print("  • Coverage: ≥99%")
    
    # Architecture
    console.print("\n[bold]Architecture:[/bold]")
    console.print("  • Scrapy + Playwright for parallel crawling")
    console.print("  • PostgreSQL for data storage")
    console.print("  • Redis for caching and rate limiting")
    console.print("  • Prometheus + Grafana for monitoring")


@app.callback()
def callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress output"),
):
    """RENEC Harvester CLI - Main entry point."""
    # Set logging level based on flags
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        import logging
        logging.basicConfig(level=logging.ERROR)
    
    # Store options in context
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet


def main():
    """Main CLI entry point."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()