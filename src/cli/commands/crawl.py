"""Crawl command for site mapping."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

app = typer.Typer(help="Site crawling and mapping commands")
console = Console()


@app.command()
def start(
    max_depth: int = typer.Option(5, "--depth", "-d", help="Maximum crawl depth"),
    concurrent: int = typer.Option(5, "--concurrent", "-c", help="Concurrent requests"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Start crawling to map the RENEC site structure."""
    console.print(f"[bold cyan]Starting RENEC site crawl[/bold cyan]")
    console.print(f"Max depth: {max_depth}")
    console.print(f"Concurrent requests: {concurrent}")
    
    # Generate output filename if not provided
    if not output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"artifacts/crawl_maps/crawl_map_{timestamp}.json")
        output.parent.mkdir(parents=True, exist_ok=True)
    
    # Build scrapy command
    cmd = [
        "scrapy", "crawl", "renec",
        "-a", "mode=crawl",
        "-a", f"max_depth={max_depth}",
        "-s", f"CONCURRENT_REQUESTS={concurrent}",
        "-s", f"FEEDS={output}::json",
    ]
    
    if not verbose:
        cmd.extend(["-L", "WARNING"])
    
    # Run crawler with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Crawling site...", total=None)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                console.print(f"\n[green]✅ Crawl completed successfully![/green]")
                console.print(f"Output saved to: {output}")
                
                # Show summary
                if output.exists():
                    with open(output) as f:
                        data = json.load(f)
                    
                    console.print(f"\n[bold]Crawl Summary:[/bold]")
                    console.print(f"Total URLs discovered: {len(data)}")
                    
                    # Count by type
                    type_counts = {}
                    for item in data:
                        item_type = item.get("type", "unknown")
                        type_counts[item_type] = type_counts.get(item_type, 0) + 1
                    
                    table = Table(title="URLs by Type")
                    table.add_column("Type", style="cyan")
                    table.add_column("Count", justify="right", style="green")
                    
                    for item_type, count in sorted(type_counts.items()):
                        table.add_row(item_type, str(count))
                    
                    console.print(table)
            else:
                console.print(f"[red]❌ Crawl failed with exit code: {result.returncode}[/red]")
                if result.stderr:
                    console.print(f"[red]Error: {result.stderr}[/red]")
                
        except Exception as e:
            console.print(f"[red]❌ Error running crawler: {e}[/red]")
            raise typer.Exit(1)


@app.command()
def network(
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Crawl session ID"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Analyze network requests captured during crawl."""
    console.print("[bold cyan]Analyzing network capture data[/bold cyan]")
    
    # Find network capture file
    if not session_id:
        # Find most recent
        capture_files = list(Path("artifacts").glob("network_requests_*.json"))
        if not capture_files:
            console.print("[red]No network capture files found[/red]")
            raise typer.Exit(1)
        
        capture_file = max(capture_files, key=lambda p: p.stat().st_mtime)
    else:
        capture_file = Path(f"artifacts/network_requests_{session_id}.json")
    
    if not capture_file.exists():
        console.print(f"[red]Network capture file not found: {capture_file}[/red]")
        raise typer.Exit(1)
    
    # Load and analyze
    with open(capture_file) as f:
        requests = json.load(f)
    
    console.print(f"\nTotal requests captured: {len(requests)}")
    
    # Analyze by type
    api_endpoints = []
    xhr_requests = []
    
    for req in requests:
        if req.get("resource_type") == "xhr" or "/api/" in req["url"]:
            api_endpoints.append(req)
        if req.get("resource_type") == "xhr":
            xhr_requests.append(req)
    
    # Show API endpoints
    if api_endpoints:
        console.print(f"\n[bold]Discovered API Endpoints:[/bold]")
        
        table = Table(title="API Endpoints")
        table.add_column("Method", style="cyan")
        table.add_column("URL", style="green")
        table.add_column("Count", justify="right")
        
        # Count unique endpoints
        endpoint_counts = {}
        for req in api_endpoints:
            key = f"{req['method']} {req['url']}"
            endpoint_counts[key] = endpoint_counts.get(key, 0) + 1
        
        for endpoint, count in sorted(endpoint_counts.items()):
            method, url = endpoint.split(" ", 1)
            # Truncate long URLs
            if len(url) > 80:
                url = url[:77] + "..."
            table.add_row(method, url, str(count))
        
        console.print(table)
    
    # Save filtered results if requested
    if output:
        output_data = {
            "session_id": session_id or capture_file.stem.split("_", 2)[-1],
            "total_requests": len(requests),
            "api_endpoints": api_endpoints,
            "xhr_requests": xhr_requests,
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }
        
        with open(output, "w") as f:
            json.dump(output_data, f, indent=2)
        
        console.print(f"\n[green]Analysis saved to: {output}[/green]")


@app.command()
def list():
    """List available crawl maps."""
    console.print("[bold cyan]Available Crawl Maps[/bold cyan]\n")
    
    crawl_dir = Path("artifacts/crawl_maps")
    if not crawl_dir.exists():
        console.print("[yellow]No crawl maps found[/yellow]")
        return
    
    crawl_files = list(crawl_dir.glob("crawl_map_*.json"))
    if not crawl_files:
        console.print("[yellow]No crawl maps found[/yellow]")
        return
    
    # Create table
    table = Table(title="Crawl Maps")
    table.add_column("Session ID", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("URLs", justify="right")
    table.add_column("Size", justify="right")
    
    for file_path in sorted(crawl_files, reverse=True):
        # Extract session ID from filename
        session_id = file_path.stem.replace("crawl_map_", "")
        
        # Get file stats
        stats = file_path.stat()
        date = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
        size = f"{stats.st_size / 1024:.1f} KB"
        
        # Count URLs
        try:
            with open(file_path) as f:
                data = json.load(f)
                url_count = str(len(data))
        except:
            url_count = "?"
        
        table.add_row(session_id, date, url_count, size)
    
    console.print(table)