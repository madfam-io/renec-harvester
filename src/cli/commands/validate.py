"""Data validation commands."""

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import print
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Data validation commands")
console = Console()


@app.command()
def check(
    component: Optional[str] = typer.Option(None, "--component", "-c", help="Component type to validate"),
    limit: int = typer.Option(100, "--limit", "-l", help="Number of items to check"),
    fix: bool = typer.Option(False, "--fix", "-f", help="Attempt to fix issues"),
):
    """Validate data quality and integrity."""
    console.print("[bold cyan]Running data validation[/bold cyan]\n")
    
    from src.qa.validator import DataValidator
    from src.models import get_session
    from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
    
    validator = DataValidator()
    
    # Map component types to models
    models = {
        "ec_standard": ECStandard,
        "certificador": Certificador,
        "center": EvaluationCenter,
        "course": Course,
    }
    
    if component and component not in models:
        console.print(f"[red]Invalid component type: {component}[/red]")
        console.print(f"Valid types: {', '.join(models.keys())}")
        raise typer.Exit(1)
    
    # Run validation
    results = {}
    components_to_check = [component] if component else models.keys()
    
    for comp_type in components_to_check:
        console.print(f"\n[bold]Validating {comp_type}...[/bold]")
        
        with get_session() as session:
            # Get sample items
            items = session.query(models[comp_type]).limit(limit).all()
            
            if not items:
                console.print(f"[yellow]No {comp_type} items found[/yellow]")
                continue
            
            # Validate each item
            comp_results = validator.validate_component(comp_type, items, auto_fix=fix)
            results[comp_type] = comp_results
            
            # Show results
            console.print(f"Checked: {comp_results['total']}")
            console.print(f"Valid: [green]{comp_results['valid']}[/green]")
            console.print(f"Invalid: [red]{comp_results['invalid']}[/red]")
            
            if comp_results['errors']:
                # Show top errors
                table = Table(title=f"{comp_type} Validation Errors")
                table.add_column("Field", style="cyan")
                table.add_column("Error", style="yellow")
                table.add_column("Count", justify="right", style="red")
                
                for error in comp_results['errors'][:5]:
                    table.add_row(
                        error['field'],
                        error['message'],
                        str(error['count']),
                    )
                
                console.print(table)
    
    # Summary
    console.print("\n[bold]Validation Summary:[/bold]")
    total_valid = sum(r['valid'] for r in results.values())
    total_invalid = sum(r['invalid'] for r in results.values())
    total_checked = sum(r['total'] for r in results.values())
    
    console.print(f"Total items checked: {total_checked}")
    console.print(f"Total valid: [green]{total_valid}[/green]")
    console.print(f"Total invalid: [red]{total_invalid}[/red]")
    console.print(f"Success rate: {total_valid/total_checked*100:.1f}%")


@app.command()
def relationships():
    """Validate entity relationships and referential integrity."""
    console.print("[bold cyan]Validating entity relationships[/bold cyan]\n")
    
    from src.models import get_session
    from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
    
    issues = []
    
    with get_session() as session:
        # Check centers without certificadores
        orphan_centers = session.query(EvaluationCenter).filter(
            EvaluationCenter.certificador_id.is_(None),
            EvaluationCenter.certificador_code.isnot(None),
        ).count()
        
        if orphan_centers:
            issues.append({
                "type": "Orphan Centers",
                "description": "Centers with certificador_code but no certificador_id",
                "count": orphan_centers,
            })
        
        # Check courses without EC standards
        orphan_courses = session.query(Course).filter(
            Course.ec_standard_id.is_(None),
            Course.ec_code.isnot(None),
        ).count()
        
        if orphan_courses:
            issues.append({
                "type": "Orphan Courses",
                "description": "Courses with ec_code but no ec_standard_id",
                "count": orphan_courses,
            })
        
        # Check duplicate codes
        from sqlalchemy import func
        
        duplicate_ec = session.query(
            ECStandard.code, func.count(ECStandard.id)
        ).group_by(ECStandard.code).having(func.count(ECStandard.id) > 1).count()
        
        if duplicate_ec:
            issues.append({
                "type": "Duplicate EC Codes",
                "description": "EC standards with duplicate codes",
                "count": duplicate_ec,
            })
    
    # Show results
    if issues:
        console.print("[red]Relationship issues found:[/red]\n")
        
        table = Table(title="Relationship Issues")
        table.add_column("Issue Type", style="cyan")
        table.add_column("Description", style="yellow")
        table.add_column("Count", justify="right", style="red")
        
        for issue in issues:
            table.add_row(
                issue['type'],
                issue['description'],
                str(issue['count']),
            )
        
        console.print(table)
    else:
        console.print("[green]✅ No relationship issues found![/green]")


@app.command()
def coverage():
    """Check data coverage and completeness."""
    console.print("[bold cyan]Analyzing data coverage[/bold cyan]\n")
    
    from src.models import get_session
    from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
    from sqlalchemy import func
    
    with get_session() as session:
        # Get coverage statistics
        coverage_stats = []
        
        # EC Standards coverage
        total_ec = session.query(ECStandard).count()
        ec_with_sector = session.query(ECStandard).filter(
            ECStandard.sector.isnot(None)
        ).count()
        ec_with_level = session.query(ECStandard).filter(
            ECStandard.level.isnot(None)
        ).count()
        
        coverage_stats.append({
            "entity": "EC Standards",
            "total": total_ec,
            "with_sector": ec_with_sector,
            "with_level": ec_with_level,
            "sector_coverage": f"{ec_with_sector/total_ec*100:.1f}%" if total_ec else "0%",
            "level_coverage": f"{ec_with_level/total_ec*100:.1f}%" if total_ec else "0%",
        })
        
        # Certificadores coverage
        total_cert = session.query(Certificador).count()
        cert_with_email = session.query(Certificador).filter(
            Certificador.contact_email.isnot(None)
        ).count()
        cert_with_phone = session.query(Certificador).filter(
            Certificador.contact_phone.isnot(None)
        ).count()
        
        coverage_stats.append({
            "entity": "Certificadores",
            "total": total_cert,
            "with_email": cert_with_email,
            "with_phone": cert_with_phone,
            "email_coverage": f"{cert_with_email/total_cert*100:.1f}%" if total_cert else "0%",
            "phone_coverage": f"{cert_with_phone/total_cert*100:.1f}%" if total_cert else "0%",
        })
        
        # Show results
        table = Table(title="Data Coverage Analysis")
        table.add_column("Entity", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Field", style="yellow")
        table.add_column("Count", justify="right")
        table.add_column("Coverage", justify="right", style="green")
        
        for stats in coverage_stats:
            table.add_row(
                stats['entity'],
                str(stats['total']),
                "Sector" if 'sector_coverage' in stats else "Email",
                str(stats.get('with_sector', stats.get('with_email', 0))),
                stats.get('sector_coverage', stats.get('email_coverage', '0%')),
            )
            table.add_row(
                "",
                "",
                "Level" if 'level_coverage' in stats else "Phone",
                str(stats.get('with_level', stats.get('with_phone', 0))),
                stats.get('level_coverage', stats.get('phone_coverage', '0%')),
            )
        
        console.print(table)
        
        # Overall coverage
        console.print("\n[bold]Overall Statistics:[/bold]")
        console.print(f"Total EC Standards: {total_ec:,}")
        console.print(f"Total Certificadores: {total_cert:,}")
        console.print(f"Total Evaluation Centers: {session.query(EvaluationCenter).count():,}")
        console.print(f"Total Courses: {session.query(Course).count():,}")


@app.command()
def quality(
    source: str = typer.Option("database", "--source", "-s", help="Data source: database, json, csv"),
    input_file: Optional[Path] = typer.Option(None, "--input", "-i", help="Input file for json/csv validation"),
    output: Path = typer.Option("artifacts/validation_report.json", "--output", "-o", help="Output report path"),
    entity_type: str = typer.Option("all", "--entity", "-e", help="Entity type to validate"),
    strict: bool = typer.Option(False, "--strict", help="Use strict validation rules"),
    sample_size: Optional[int] = typer.Option(None, "--sample", help="Validate only a sample of records"),
):
    """Validate data quality using Sprint 1 validation pipeline."""
    console.print(f"[bold cyan]Starting data quality validation from {source}...[/bold cyan]\n")
    
    from src.validation import DataValidator, ValidationExpectations
    from src.models import get_session
    from src.models.ec_standard import ECStandard
    from src.models.certificador import Certificador
    import json
    
    # Initialize validator
    expectations = ValidationExpectations()
    if strict:
        expectations.MIN_EC_STANDARDS = 1500
        expectations.MIN_CERTIFICADORES = 200
    
    validator = DataValidator(expectations)
    
    # Load data based on source
    items = []
    
    if source == "database":
        with get_session() as session:
            # Load EC Standards
            if entity_type in ["all", "ec_standards"]:
                query = session.query(ECStandard)
                if sample_size:
                    query = query.limit(sample_size)
                
                for ec in query.all():
                    items.append({
                        'ec_clave': ec.ec_clave,
                        'titulo': ec.titulo,
                        'version': ec.version,
                        'vigente': ec.vigente,
                        'sector': ec.sector,
                        'sector_id': ec.sector_id,
                        'comite': ec.comite,
                        'comite_id': ec.comite_id,
                        'descripcion': ec.descripcion,
                        'nivel': ec.nivel,
                        'duracion_horas': ec.duracion_horas,
                        'tipo_norma': ec.tipo_norma,
                        'fecha_publicacion': ec.fecha_publicacion.isoformat() if ec.fecha_publicacion else None,
                        'fecha_vigencia': ec.fecha_vigencia.isoformat() if ec.fecha_vigencia else None,
                        'renec_url': ec.renec_url
                    })
            
            # Load Certificadores
            if entity_type in ["all", "certificadores"]:
                query = session.query(Certificador)
                if sample_size:
                    query = query.limit(sample_size)
                
                for cert in query.all():
                    items.append({
                        'cert_id': cert.cert_id,
                        'tipo': cert.tipo,
                        'nombre_legal': cert.nombre_legal,
                        'siglas': cert.siglas,
                        'estatus': cert.estatus,
                        'estado': cert.estado,
                        'estado_inegi': cert.estado_inegi,
                        'municipio': cert.municipio,
                        'cp': cert.cp,
                        'telefono': cert.telefono,
                        'correo': cert.correo,
                        'sitio_web': cert.sitio_web,
                        'representante_legal': cert.representante_legal,
                        'fecha_acreditacion': cert.fecha_acreditacion.isoformat() if cert.fecha_acreditacion else None,
                        'estandares_acreditados': cert.estandares_acreditados,
                        'src_url': cert.src_url
                    })
    
    elif source == "json" and input_file:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for values in data.values():
                    if isinstance(values, list):
                        items.extend(values)
    
    elif source == "csv" and input_file:
        import csv
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            items = list(reader)
    
    if not items:
        console.print("[red]No items found to validate[/red]")
        raise typer.Exit(1)
    
    console.print(f"Loaded {len(items)} items for validation")
    
    # Run validation
    with typer.progressbar(items, label="Validating items") as progress:
        for item in progress:
            validator.validate_item(item)
    
    # Generate report
    report = validator.generate_validation_report()
    
    # Display summary
    console.print("\n" + "="*60)
    console.print("[bold cyan]VALIDATION SUMMARY[/bold cyan]")
    console.print("="*60)
    
    summary = report['summary']
    console.print(f"Total Items: {summary['total_items']}")
    console.print(f"Valid Items: [green]{summary['valid_items']}[/green] ({summary['validation_rate']:.1%})")
    console.print(f"Invalid Items: [red]{summary['invalid_items']}[/red]")
    
    # Coverage status
    console.print("\n[bold]Coverage Status:[/bold]")
    for entity, met in report['coverage_status'].items():
        status = "[green]✅[/green]" if met else "[red]❌[/red]"
        console.print(f"  {status} {entity}")
    
    # Entity breakdown
    if report['by_entity_type']:
        console.print("\n[bold]Validation by Entity Type:[/bold]")
        table = Table()
        table.add_column("Entity", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Valid", justify="right", style="green")
        table.add_column("Invalid", justify="right", style="red")
        table.add_column("Rate", justify="right")
        
        for entity, stats in report['by_entity_type'].items():
            table.add_row(
                entity,
                str(stats['total']),
                str(stats['valid']),
                str(stats['invalid']),
                f"{stats['validation_rate']:.1%}"
            )
        
        console.print(table)
    
    # Common errors
    if report['common_errors']:
        console.print("\n[bold]Most Common Errors:[/bold]")
        error_table = Table()
        error_table.add_column("Error", style="yellow")
        error_table.add_column("Count", justify="right", style="red")
        
        for error in report['common_errors'][:5]:
            error_table.add_row(error['error'], str(error['count']))
        
        console.print(error_table)
    
    # Save report
    output.parent.mkdir(parents=True, exist_ok=True)
    validator.save_validation_report(report, str(output))
    
    console.print(f"\n[green]✅ Validation report saved to: {output}[/green]")
    
    # Exit with error code if validation failed
    if summary['validation_rate'] < 0.95:
        console.print("\n[red]⚠️  Validation rate below 95% threshold[/red]")
        raise typer.Exit(1)