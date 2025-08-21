"""Database management commands."""

import subprocess
from pathlib import Path

import typer
from rich import print
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Database management commands")
console = Console()


@app.command()
def init(
    drop: bool = typer.Option(False, "--drop", help="Drop existing tables first"),
):
    """Initialize database tables."""
    console.print("[bold cyan]Initializing database[/bold cyan]\n")
    
    if drop:
        if not typer.confirm("⚠️  This will drop all existing tables. Continue?"):
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)
        
        console.print("Dropping existing tables...")
        from src.models.base import drop_db
        drop_db()
        console.print("[green]✅ Tables dropped[/green]")
    
    # Create tables
    console.print("Creating database tables...")
    from src.models.base import init_db
    
    try:
        init_db()
        console.print("[green]✅ Database initialized successfully![/green]")
    except Exception as e:
        console.print(f"[red]❌ Database initialization failed: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def migrate(
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
):
    """Run database migrations."""
    console.print("[bold cyan]Running database migrations[/bold cyan]\n")
    
    # Check if alembic is initialized
    if not Path("alembic.ini").exists():
        console.print("[yellow]Alembic not initialized. Initializing now...[/yellow]")
        subprocess.run(["alembic", "init", "alembic"])
    
    if message:
        # Create new migration
        console.print(f"Creating migration: {message}")
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            capture_output=True,
            text=True,
        )
        
        if result.returncode == 0:
            console.print("[green]✅ Migration created[/green]")
        else:
            console.print(f"[red]❌ Failed to create migration: {result.stderr}[/red]")
            raise typer.Exit(1)
    
    # Run migrations
    console.print("Applying migrations...")
    result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✅ Migrations applied successfully![/green]")
    else:
        console.print(f"[red]❌ Migration failed: {result.stderr}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Show database status and statistics."""
    console.print("[bold cyan]Database Status[/bold cyan]\n")
    
    from src.models import get_session
    from src.models.components import ECStandard, Certificador, EvaluationCenter, Course
    
    try:
        with get_session() as session:
            # Get counts
            stats = {
                "EC Standards": session.query(ECStandard).count(),
                "Certificadores": session.query(Certificador).count(),
                "Evaluation Centers": session.query(EvaluationCenter).count(),
                "Courses": session.query(Course).count(),
            }
            
            # Create table
            table = Table(title="Database Statistics")
            table.add_column("Entity Type", style="cyan")
            table.add_column("Count", justify="right", style="green")
            
            for entity, count in stats.items():
                table.add_row(entity, f"{count:,}")
            
            console.print(table)
            
            # Show recent updates
            console.print("\n[bold]Recent Updates:[/bold]")
            
            recent_ec = session.query(ECStandard).order_by(
                ECStandard.last_seen.desc()
            ).first()
            
            if recent_ec:
                console.print(f"Latest EC Standard: {recent_ec.code} - {recent_ec.last_seen}")
            
    except Exception as e:
        console.print(f"[red]❌ Error connecting to database: {e}[/red]")
        console.print("[yellow]Make sure PostgreSQL is running (docker-compose up -d)[/yellow]")


@app.command()
def backup(
    output: Path = typer.Option(Path("backups"), "--output", "-o", help="Backup directory"),
):
    """Backup database to file."""
    import os
    from datetime import datetime
    
    console.print("[bold cyan]Creating database backup[/bold cyan]\n")
    
    # Create backup directory
    output.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = output / f"renec_backup_{timestamp}.sql"
    
    # Get database credentials from environment
    db_host = os.getenv("DATABASE_HOST", "localhost")
    db_port = os.getenv("DATABASE_PORT", "5432")
    db_name = os.getenv("DATABASE_NAME", "renec_harvester")
    db_user = os.getenv("DATABASE_USER", "renec")
    
    # Run pg_dump
    cmd = [
        "docker", "exec", "renec-postgres",
        "pg_dump", "-U", db_user, "-d", db_name,
    ]
    
    try:
        with open(backup_file, "w") as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            size = backup_file.stat().st_size / 1024 / 1024  # MB
            console.print(f"[green]✅ Backup created successfully![/green]")
            console.print(f"File: {backup_file}")
            console.print(f"Size: {size:.1f} MB")
        else:
            console.print(f"[red]❌ Backup failed: {result.stderr}[/red]")
            backup_file.unlink()  # Remove failed backup
            raise typer.Exit(1)
            
    except Exception as e:
        console.print(f"[red]❌ Error creating backup: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="Backup file to restore"),
    force: bool = typer.Option(False, "--force", "-f", help="Force restore without confirmation"),
):
    """Restore database from backup file."""
    console.print(f"[bold cyan]Restoring database from: {backup_file}[/bold cyan]\n")
    
    if not backup_file.exists():
        console.print(f"[red]Backup file not found: {backup_file}[/red]")
        raise typer.Exit(1)
    
    if not force:
        console.print("[bold red]⚠️  WARNING: This will overwrite the current database![/bold red]")
        if not typer.confirm("Continue with restore?"):
            console.print("[yellow]Aborted[/yellow]")
            raise typer.Exit(0)
    
    # Get database credentials
    import os
    db_user = os.getenv("DATABASE_USER", "renec")
    db_name = os.getenv("DATABASE_NAME", "renec_harvester")
    
    # Drop and recreate database
    console.print("Preparing database...")
    
    drop_cmd = [
        "docker", "exec", "renec-postgres",
        "psql", "-U", db_user, "-d", "postgres",
        "-c", f"DROP DATABASE IF EXISTS {db_name};"
    ]
    
    create_cmd = [
        "docker", "exec", "renec-postgres",
        "psql", "-U", db_user, "-d", "postgres",
        "-c", f"CREATE DATABASE {db_name};"
    ]
    
    # Execute commands
    subprocess.run(drop_cmd, capture_output=True)
    subprocess.run(create_cmd, capture_output=True)
    
    # Restore from backup
    console.print("Restoring data...")
    
    with open(backup_file, "r") as f:
        restore_cmd = [
            "docker", "exec", "-i", "renec-postgres",
            "psql", "-U", db_user, "-d", db_name,
        ]
        
        result = subprocess.run(restore_cmd, stdin=f, capture_output=True, text=True)
    
    if result.returncode == 0:
        console.print("[green]✅ Database restored successfully![/green]")
    else:
        console.print(f"[red]❌ Restore failed: {result.stderr}[/red]")
        raise typer.Exit(1)