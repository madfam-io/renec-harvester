"""Harvest command for data extraction."""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

app = typer.Typer(help="Data harvesting commands")
console = Console()


@app.command()
def start(
    components: Optional[List[str]] = typer.Option(
        None, "--component", "-c", help="Specific components to harvest"
    ),
    concurrent: int = typer.Option(10, "--concurrent", help="Concurrent spiders"),
    batch_size: int = typer.Option(100, "--batch", help="Batch size for processing"),
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume from last checkpoint"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Start harvesting RENEC data."""
    console.print("[bold cyan]Starting RENEC data harvest[/bold cyan]")
    
    # Default to all components if none specified
    if not components:
        components = ["ec_standard", "certificador", "center", "course"]
    
    console.print(f"Components: {', '.join(components)}")
    console.print(f"Concurrent spiders: {concurrent}")
    
    # Create session ID
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Build scrapy command
    cmd = [
        "scrapy", "crawl", "renec",
        "-a", "mode=harvest",
        "-s", f"CONCURRENT_REQUESTS={concurrent}",
        "-s", f"CONCURRENT_REQUESTS_PER_DOMAIN={concurrent}",
    ]
    
    if not verbose:
        cmd.extend(["-L", "WARNING"])
    
    # Add component filter if specified
    if components:
        cmd.extend(["-a", f"components={','.join(components)}"])
    
    # Run harvest with progress tracking
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("Harvesting data...", total=100)
        
        try:
            # Run the harvest
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            
            # Monitor progress (simplified for now)
            for i in range(100):
                import time
                time.sleep(0.1)  # Simulate progress
                progress.update(task, advance=1)
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                console.print(f"\n[green]✅ Harvest completed successfully![/green]")
                console.print(f"Session ID: {session_id}")
                
                # Show harvest summary
                _show_harvest_summary(session_id)
            else:
                console.print(f"[red]❌ Harvest failed with exit code: {process.returncode}[/red]")
                if stderr:
                    console.print(f"[red]Error: {stderr}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Error running harvest: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def status(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Harvest session ID"),
):
    """Check harvest status and progress."""
    console.print("[bold cyan]Harvest Status[/bold cyan]\n")
    
    if session_id:
        _show_harvest_summary(session_id)
    else:
        # Show all recent harvests
        _list_recent_harvests()


@app.command()
def validate(
    session_id: str = typer.Argument(..., help="Harvest session ID to validate"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Attempt to fix validation errors"),
):
    """Validate harvested data quality."""
    console.print(f"[bold cyan]Validating harvest: {session_id}[/bold cyan]\n")
    
    # Run validation
    from src.qa.validator import DataValidator
    
    validator = DataValidator()
    results = validator.validate_harvest(session_id, auto_fix=fix)
    
    # Show results
    console.print(f"Total items validated: {results['total_items']}")
    console.print(f"Valid items: [green]{results['valid_items']}[/green]")
    console.print(f"Invalid items: [red]{results['invalid_items']}[/red]")
    
    if results['errors']:
        console.print("\n[bold]Validation Errors:[/bold]")
        
        table = Table(title="Errors by Type")
        table.add_column("Component", style="cyan")
        table.add_column("Field", style="yellow")
        table.add_column("Count", justify="right", style="red")
        
        for error in results['errors'][:20]:  # Show top 20
            table.add_row(
                error['component_type'],
                error['field'],
                str(error['count']),
            )
        
        console.print(table)
        
        if len(results['errors']) > 20:
            console.print(f"\n... and {len(results['errors']) - 20} more error types")


@app.command()
def export(
    session_id: str = typer.Argument(..., help="Harvest session ID to export"),
    format: str = typer.Option("json", "--format", "-f", help="Export format (json, csv, parquet)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output directory"),
):
    """Export harvested data to various formats."""
    console.print(f"[bold cyan]Exporting harvest: {session_id}[/bold cyan]")
    console.print(f"Format: {format}")
    
    # Set default output directory
    if not output:
        output = Path(f"artifacts/exports/{session_id}")
    
    output.mkdir(parents=True, exist_ok=True)
    
    # Export data
    from src.storage.exporter import DataExporter
    
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Exporting to {format}...", total=None)
        
        try:
            files = exporter.export_harvest(session_id, format, output)
            
            console.print(f"\n[green]✅ Export completed![/green]")
            console.print(f"Files created:")
            
            for file_path in files:
                size = file_path.stat().st_size / 1024 / 1024  # MB
                console.print(f"  • {file_path.name} ({size:.1f} MB)")
                
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
            raise typer.Exit(1)


def _show_harvest_summary(session_id: str):
    """Show summary for a specific harvest session."""
    from src.models import get_session
    from src.models.crawl import CrawlSession
    
    try:
        with get_session() as db:
            session = db.query(CrawlSession).filter_by(id=session_id).first()
            
            if not session:
                console.print(f"[yellow]Session {session_id} not found[/yellow]")
                return
            
            # Show session info
            console.print(f"\n[bold]Session: {session_id}[/bold]")
            console.print(f"Status: {session.status}")
            console.print(f"Started: {session.started_at}")
            console.print(f"Duration: {session.duration_seconds or 'In progress'} seconds")
            console.print(f"URLs visited: {session.urls_visited}")
            console.print(f"Errors: {session.errors_count}")
            
    except Exception as e:
        console.print(f"[red]Error loading session: {e}[/red]")


def _list_recent_harvests():
    """List recent harvest sessions."""
    from src.models import get_session
    from src.models.crawl import CrawlSession
    
    try:
        with get_session() as db:
            sessions = db.query(CrawlSession).filter_by(
                mode="harvest"
            ).order_by(CrawlSession.started_at.desc()).limit(10).all()
            
            if not sessions:
                console.print("[yellow]No harvest sessions found[/yellow]")
                return
            
            table = Table(title="Recent Harvests")
            table.add_column("Session ID", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Started", style="yellow")
            table.add_column("Duration", justify="right")
            table.add_column("URLs", justify="right")
            table.add_column("Errors", justify="right", style="red")
            
            for session in sessions:
                duration = f"{session.duration_seconds:.0f}s" if session.duration_seconds else "-"
                table.add_row(
                    session.id,
                    session.status,
                    session.started_at.strftime("%Y-%m-%d %H:%M"),
                    duration,
                    str(session.urls_visited or 0),
                    str(session.errors_count or 0),
                )
            
            console.print(table)
            
    except Exception as e:
        console.print(f"[red]Error loading sessions: {e}[/red]")