"""
Data export commands.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import typer
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from src.export import DataExporter

app = typer.Typer(help="Data export commands")
console = Console()


@app.command()
def json(
    output: Path = typer.Option("artifacts/exports/data.json", "--output", "-o", help="Output file path"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
    pretty: bool = typer.Option(True, "--pretty", help="Pretty print JSON"),
    vigente_only: bool = typer.Option(False, "--vigente", help="Export only vigente EC standards"),
    tipo: Optional[str] = typer.Option(None, "--tipo", help="Filter certificadores by type (ECE/OC)"),
):
    """Export data to JSON format."""
    console.print("[bold cyan]Exporting data to JSON...[/bold cyan]\n")
    
    # Parse filters
    filters = {}
    if vigente_only:
        filters['vigente'] = True
    if tipo:
        filters['tipo'] = tipo.upper()
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting...", total=None)
        
        exported_path = exporter.export_to_json(
            str(output),
            entity_types=entity_types,
            filters=filters if filters else None,
            pretty=pretty
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    summary = exporter.get_export_summary()
    console.print(f"\n[green]✅ Export complete![/green]")
    console.print(f"Records exported: {summary['total_records']:,}")
    console.print(f"File: {exported_path}")
    console.print(f"Time: {summary['runtime_seconds']:.2f}s")


@app.command()
def csv(
    output_dir: Path = typer.Option("artifacts/exports/csv", "--output", "-o", help="Output directory"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
    vigente_only: bool = typer.Option(False, "--vigente", help="Export only vigente EC standards"),
    tipo: Optional[str] = typer.Option(None, "--tipo", help="Filter certificadores by type (ECE/OC)"),
):
    """Export data to CSV format."""
    console.print("[bold cyan]Exporting data to CSV...[/bold cyan]\n")
    
    # Parse filters
    filters = {}
    if vigente_only:
        filters['vigente'] = True
    if tipo:
        filters['tipo'] = tipo.upper()
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting...", total=None)
        
        created_files = exporter.export_to_csv(
            str(output_dir),
            entity_types=entity_types,
            filters=filters if filters else None
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    summary = exporter.get_export_summary()
    console.print(f"\n[green]✅ Export complete![/green]")
    console.print(f"Records exported: {summary['total_records']:,}")
    console.print("\nCreated files:")
    for file_path in created_files:
        console.print(f"  • {file_path}")
    console.print(f"\nTime: {summary['runtime_seconds']:.2f}s")


@app.command()
def excel(
    output: Path = typer.Option("artifacts/exports/data.xlsx", "--output", "-o", help="Output file path"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
    vigente_only: bool = typer.Option(False, "--vigente", help="Export only vigente EC standards"),
    tipo: Optional[str] = typer.Option(None, "--tipo", help="Filter certificadores by type (ECE/OC)"),
):
    """Export data to Excel format."""
    console.print("[bold cyan]Exporting data to Excel...[/bold cyan]\n")
    
    # Check if pandas is available
    try:
        import pandas as pd
    except ImportError:
        console.print("[red]Error: pandas is required for Excel export[/red]")
        console.print("Install with: pip install pandas openpyxl")
        raise typer.Exit(1)
    
    # Parse filters
    filters = {}
    if vigente_only:
        filters['vigente'] = True
    if tipo:
        filters['tipo'] = tipo.upper()
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting...", total=None)
        
        exported_path = exporter.export_to_excel(
            str(output),
            entity_types=entity_types,
            filters=filters if filters else None
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    summary = exporter.get_export_summary()
    console.print(f"\n[green]✅ Export complete![/green]")
    console.print(f"Records exported: {summary['total_records']:,}")
    console.print(f"File: {exported_path}")
    console.print(f"Time: {summary['runtime_seconds']:.2f}s")


@app.command()
def bundle(
    output: Path = typer.Option(
        f"artifacts/exports/bundle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
        "--output", "-o",
        help="Output ZIP file path"
    ),
    formats: str = typer.Option("json,csv,excel", "--formats", "-f", help="Comma-separated export formats"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
    vigente_only: bool = typer.Option(False, "--vigente", help="Export only vigente EC standards"),
    tipo: Optional[str] = typer.Option(None, "--tipo", help="Filter certificadores by type (ECE/OC)"),
):
    """Export data bundle with multiple formats in ZIP."""
    console.print("[bold cyan]Creating export bundle...[/bold cyan]\n")
    
    # Parse formats
    format_list = [f.strip() for f in formats.split(",")]
    invalid_formats = [f for f in format_list if f not in ['json', 'csv', 'excel']]
    if invalid_formats:
        console.print(f"[red]Invalid formats: {', '.join(invalid_formats)}[/red]")
        console.print("Valid formats: json, csv, excel")
        raise typer.Exit(1)
    
    # Parse filters
    filters = {}
    if vigente_only:
        filters['vigente'] = True
    if tipo:
        filters['tipo'] = tipo.upper()
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating bundle...", total=None)
        
        bundle_path = exporter.export_bundle(
            str(output),
            formats=format_list,
            entity_types=entity_types,
            filters=filters if filters else None
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    summary = exporter.get_export_summary()
    console.print(f"\n[green]✅ Bundle created![/green]")
    console.print(f"Records exported: {summary['total_records']:,}")
    console.print(f"Formats: {', '.join(format_list)}")
    console.print(f"Bundle: {bundle_path}")
    console.print(f"Time: {summary['runtime_seconds']:.2f}s")


@app.command()
def graph(
    output: Path = typer.Option("artifacts/exports/graph.json", "--output", "-o", help="Output file path"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
):
    """Export data in graph format (nodes and edges) for visualization."""
    console.print("[bold cyan]Exporting data to graph format...[/bold cyan]\n")
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting graph...", total=None)
        
        exported_path = exporter.export_graph_json(
            str(output),
            entity_types=entity_types
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    console.print(f"\n[green]✅ Graph export complete![/green]")
    console.print(f"File: {exported_path}")
    console.print("\nGraph format includes:")
    console.print("  • Nodes: EC Standards, Certificadores, Centers, Sectors")
    console.print("  • Edges: Accreditation relationships, Sector memberships")
    console.print("\nUse with visualization tools like D3.js, vis.js, or Gephi")


@app.command()
def denormalized(
    output: Path = typer.Option("artifacts/exports/denormalized.json", "--output", "-o", help="Output file path"),
    entities: Optional[str] = typer.Option(None, "--entities", "-e", help="Comma-separated entity types"),
):
    """Export denormalized data with embedded relationships."""
    console.print("[bold cyan]Exporting denormalized data...[/bold cyan]\n")
    
    # Parse entity types
    entity_types = None
    if entities:
        entity_types = [e.strip() for e in entities.split(",")]
    
    # Export data
    exporter = DataExporter()
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting denormalized data...", total=None)
        
        exported_path = exporter.export_denormalized_json(
            str(output),
            entity_types=entity_types
        )
        
        progress.update(task, completed=True)
    
    # Show summary
    console.print(f"\n[green]✅ Denormalized export complete![/green]")
    console.print(f"File: {exported_path}")
    console.print("\nDenormalized format includes:")
    console.print("  • EC Standards with embedded certificador lists")
    console.print("  • Certificadores with embedded EC standard lists")
    console.print("  • Pre-joined data for easy consumption")


@app.command()
def stats():
    """Show export statistics and available data."""
    console.print("[bold cyan]Export Statistics[/bold cyan]\n")
    
    from src.models import get_session
    from src.models.ec_standard import ECStandard
    from src.models.certificador import Certificador
    from src.models.centro import Centro
    from src.models.sector import Sector
    from src.models.comite import Comite
    
    with get_session() as session:
        # Get counts for all entities
        stats_data = []
        
        # EC Standards
        total_ec = session.query(ECStandard).count()
        vigente_ec = session.query(ECStandard).filter(ECStandard.vigente == True).count()
        stats_data.append({
            'entity': 'EC Standards',
            'total': total_ec,
            'details': f"Vigente: {vigente_ec}, Inactive: {total_ec - vigente_ec}"
        })
        
        # Certificadores
        total_cert = session.query(Certificador).count()
        ece_count = session.query(Certificador).filter(Certificador.tipo == 'ECE').count()
        oc_count = session.query(Certificador).filter(Certificador.tipo == 'OC').count()
        stats_data.append({
            'entity': 'Certificadores',
            'total': total_cert,
            'details': f"ECE: {ece_count}, OC: {oc_count}"
        })
        
        # Centers
        total_centers = session.query(Centro).count()
        stats_data.append({
            'entity': 'Centros',
            'total': total_centers,
            'details': f"Evaluation Centers"
        })
        
        # Sectors
        total_sectors = session.query(Sector).count()
        stats_data.append({
            'entity': 'Sectors',
            'total': total_sectors,
            'details': f"Productive Sectors"
        })
        
        # Committees
        total_comites = session.query(Comite).count()
        stats_data.append({
            'entity': 'Comités',
            'total': total_comites,
            'details': f"Management Committees"
        })
    
    # Display stats
    table = Table(title="Available Data for Export")
    table.add_column("Entity Type", style="cyan")
    table.add_column("Total Records", justify="right")
    table.add_column("Details", style="yellow")
    
    for stat in stats_data:
        table.add_row(
            stat['entity'],
            str(stat['total']),
            stat['details']
        )
    
    console.print(table)
    
    # Show relationships count
    from src.models.relations import ECEEC, CentroEC, ECSector
    with get_session() as session:
        ece_ec_count = session.query(ECEEC).count()
        centro_ec_count = session.query(CentroEC).count()
        ec_sector_count = session.query(ECSector).count()
    
    console.print("\n[bold]Relationships:[/bold]")
    console.print(f"  • ECE-EC: {ece_ec_count} accreditations")
    console.print(f"  • Centro-EC: {centro_ec_count} center evaluations")
    console.print(f"  • EC-Sector: {ec_sector_count} sector assignments")
    
    # Show recent exports
    export_dir = Path("artifacts/exports")
    if export_dir.exists():
        console.print("\n[bold]Recent Exports:[/bold]")
        
        export_files = sorted(
            [f for f in export_dir.rglob("*") if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:10]
        
        if export_files:
            for f in export_files:
                size_mb = f.stat().st_size / (1024 * 1024)
                mod_time = datetime.fromtimestamp(f.stat().st_mtime)
                console.print(f"  • {f.name} ({size_mb:.2f} MB) - {mod_time.strftime('%Y-%m-%d %H:%M')}")
        else:
            console.print("  No exports found")
    
    # Show export formats
    console.print("\n[bold]Available Export Formats:[/bold]")
    console.print("  • JSON - Complete data with metadata")
    console.print("  • CSV - Tabular format for spreadsheets")
    console.print("  • Excel - Multi-sheet workbook")
    console.print("  • Graph - Node-edge format for visualization")
    console.print("  • Denormalized - Pre-joined data with embedded relations")
    console.print("  • Bundle - ZIP with multiple formats")