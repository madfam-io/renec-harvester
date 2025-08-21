"""
Diff and change detection commands.
"""
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from src.diff import DiffEngine, DiffReporter

app = typer.Typer(help="Diff and change detection commands")
console = Console()


@app.command()
def compare(
    date1: str = typer.Argument(..., help="First date (YYYY-MM-DD or 'yesterday')"),
    date2: str = typer.Argument("today", help="Second date (YYYY-MM-DD or 'today')"),
    output_format: str = typer.Option("all", "--format", "-f", help="Output format: html, json, markdown, all"),
    output_dir: Path = typer.Option("artifacts/diffs", "--output", "-o", help="Output directory"),
    entity_types: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
):
    """Compare data between two harvest dates."""
    console.print("[bold cyan]Running diff comparison[/bold cyan]\n")
    
    # Parse dates
    try:
        if date1 == "yesterday":
            timestamp1 = datetime.now() - timedelta(days=1)
        else:
            timestamp1 = datetime.strptime(date1, "%Y-%m-%d")
        
        if date2 == "today":
            timestamp2 = datetime.now()
        else:
            timestamp2 = datetime.strptime(date2, "%Y-%m-%d")
    except ValueError as e:
        console.print(f"[red]Invalid date format: {e}[/red]")
        raise typer.Exit(1)
    
    # Parse entity types
    entities = None
    if entity_types:
        entities = [e.strip() for e in entity_types.split(",")]
    
    # Run diff
    engine = DiffEngine()
    console.print(f"Comparing data between {timestamp1.date()} and {timestamp2.date()}...")
    
    try:
        diff_report = engine.compare_harvests(timestamp1, timestamp2, entities)
    except Exception as e:
        console.print(f"[red]Error during comparison: {e}[/red]")
        raise typer.Exit(1)
    
    # Display summary
    _display_diff_summary(diff_report)
    
    # Generate reports
    reporter = DiffReporter()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    generated_reports = []
    
    if output_format in ["html", "all"]:
        html_path = output_dir / f"diff_{timestamp_str}.html"
        reporter.generate_html_report(diff_report, str(html_path))
        generated_reports.append(("HTML", html_path))
    
    if output_format in ["json", "all"]:
        json_path = output_dir / f"diff_{timestamp_str}.json"
        reporter.generate_json_report(diff_report, str(json_path))
        generated_reports.append(("JSON", json_path))
    
    if output_format in ["markdown", "all"]:
        md_path = output_dir / f"diff_{timestamp_str}.md"
        reporter.generate_markdown_report(diff_report, str(md_path))
        generated_reports.append(("Markdown", md_path))
    
    # Show generated reports
    if generated_reports:
        console.print("\n[bold green]Generated Reports:[/bold green]")
        for format_name, path in generated_reports:
            console.print(f"  • {format_name}: {path}")


@app.command()
def baseline(
    create: bool = typer.Option(False, "--create", "-c", help="Create new baseline"),
    show: bool = typer.Option(False, "--show", "-s", help="Show current baseline info"),
    compare_with: Optional[str] = typer.Option(None, "--compare", help="Compare with baseline"),
):
    """Manage baseline for change detection."""
    from src.models import get_session
    from src.models.ec_standard import ECStandard
    from src.models.certificador import Certificador
    import json
    
    baseline_path = Path("artifacts/baseline.json")
    
    if create:
        console.print("[bold cyan]Creating baseline snapshot...[/bold cyan]")
        
        baseline_data = {
            "created_at": datetime.now().isoformat(),
            "ec_standards": [],
            "certificadores": []
        }
        
        with get_session() as session:
            # Get all EC standards
            for ec in session.query(ECStandard).all():
                baseline_data["ec_standards"].append({
                    "ec_clave": ec.ec_clave,
                    "titulo": ec.titulo,
                    "version": ec.version,
                    "vigente": ec.vigente,
                    "content_hash": ec.content_hash
                })
            
            # Get all certificadores
            for cert in session.query(Certificador).all():
                baseline_data["certificadores"].append({
                    "cert_id": cert.cert_id,
                    "tipo": cert.tipo,
                    "nombre_legal": cert.nombre_legal,
                    "estatus": cert.estatus,
                    "row_hash": cert.row_hash
                })
        
        # Save baseline
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(baseline_path, 'w', encoding='utf-8') as f:
            json.dump(baseline_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Baseline created with:[/green]")
        console.print(f"  • EC Standards: {len(baseline_data['ec_standards'])}")
        console.print(f"  • Certificadores: {len(baseline_data['certificadores'])}")
        console.print(f"  • Saved to: {baseline_path}")
    
    elif show:
        if not baseline_path.exists():
            console.print("[red]No baseline found. Create one with --create[/red]")
            raise typer.Exit(1)
        
        with open(baseline_path, 'r') as f:
            baseline_data = json.load(f)
        
        console.print("[bold cyan]Current Baseline:[/bold cyan]")
        console.print(f"Created: {baseline_data['created_at']}")
        console.print(f"EC Standards: {len(baseline_data['ec_standards'])}")
        console.print(f"Certificadores: {len(baseline_data['certificadores'])}")
    
    elif compare_with:
        if not baseline_path.exists():
            console.print("[red]No baseline found. Create one with --create[/red]")
            raise typer.Exit(1)
        
        console.print("[bold cyan]Comparing with baseline...[/bold cyan]")
        
        # Load baseline
        with open(baseline_path, 'r') as f:
            baseline_data = json.load(f)
        
        # Load current data
        current_data = {
            "ec_standards": [],
            "certificadores": []
        }
        
        with get_session() as session:
            for ec in session.query(ECStandard).all():
                current_data["ec_standards"].append({
                    "ec_clave": ec.ec_clave,
                    "titulo": ec.titulo,
                    "version": ec.version,
                    "vigente": ec.vigente,
                    "content_hash": ec.content_hash
                })
            
            for cert in session.query(Certificador).all():
                current_data["certificadores"].append({
                    "cert_id": cert.cert_id,
                    "tipo": cert.tipo,
                    "nombre_legal": cert.nombre_legal,
                    "estatus": cert.estatus,
                    "row_hash": cert.row_hash
                })
        
        # Compare
        engine = DiffEngine()
        
        ec_comparison = engine.compare_with_baseline(
            current_data["ec_standards"],
            baseline_data["ec_standards"],
            "ec_clave"
        )
        
        cert_comparison = engine.compare_with_baseline(
            current_data["certificadores"],
            baseline_data["certificadores"],
            "cert_id"
        )
        
        # Display results
        console.print("\n[bold]EC Standards Changes:[/bold]")
        console.print(f"  Added: [green]{ec_comparison['summary']['added_count']}[/green]")
        console.print(f"  Removed: [red]{ec_comparison['summary']['removed_count']}[/red]")
        console.print(f"  Modified: [yellow]{ec_comparison['summary']['modified_count']}[/yellow]")
        console.print(f"  Unchanged: {ec_comparison['summary']['unchanged_count']}")
        
        console.print("\n[bold]Certificadores Changes:[/bold]")
        console.print(f"  Added: [green]{cert_comparison['summary']['added_count']}[/green]")
        console.print(f"  Removed: [red]{cert_comparison['summary']['removed_count']}[/red]")
        console.print(f"  Modified: [yellow]{cert_comparison['summary']['modified_count']}[/yellow]")
        console.print(f"  Unchanged: {cert_comparison['summary']['unchanged_count']}")
    
    else:
        console.print("Use --create to create baseline, --show to view, or --compare to compare")


def _display_diff_summary(diff_report: Dict):
    """Display diff summary in console."""
    summary = diff_report.get('summary', {})
    
    console.print("\n[bold]Diff Summary:[/bold]")
    console.print(f"Total Changes: [cyan]{summary.get('total_changes', 0)}[/cyan]")
    
    # Changes by operation
    if 'by_operation' in summary:
        table = Table(title="Changes by Operation")
        table.add_column("Operation", style="cyan")
        table.add_column("Count", justify="right")
        
        for op, count in summary['by_operation'].items():
            table.add_row(op.capitalize(), str(count))
        
        console.print(table)
    
    # Changes by entity
    if 'by_entity' in summary:
        table = Table(title="Changes by Entity")
        table.add_column("Entity", style="cyan")
        table.add_column("Added", justify="right", style="green")
        table.add_column("Removed", justify="right", style="red")
        table.add_column("Modified", justify="right", style="yellow")
        table.add_column("Total", justify="right")
        
        for entity, stats in summary['by_entity'].items():
            table.add_row(
                entity,
                str(stats.get('added', 0)),
                str(stats.get('removed', 0)),
                str(stats.get('modified', 0)),
                str(stats.get('total', 0))
            )
        
        console.print(table)
    
    # Notable changes
    if summary.get('notable_changes'):
        console.print("\n[bold]Notable Changes:[/bold]")
        for change in summary['notable_changes']:
            console.print(f"  • {change['description']}")