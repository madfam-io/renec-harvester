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