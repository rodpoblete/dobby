"Command-line interface for dobby transformation tool."

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from . import __version__
from .exceptions import DobbyError
from .logger import setup_logger
from .models import TransformConfig
from .transformer import StudentDataTransformer

app = typer.Typer(
    name="dobby",
    help="Transform student enrollment CSV data for SN system upload",
    add_completion=False,
)
console = Console()


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        console.print(f"dobby version {__version__}")
        raise typer.Exit()


@app.command()
def transform(
    input_file: Path = typer.Argument(
        ...,
        help="Input CSV file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output_file: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output CSV file path (default: YYYY-MM-DD-HHMM-carga-alumnos-sn.csv)",
    ),
    rbd: int = typer.Option(
        574,
        "--rbd",
        help="School RBD identifier",
    ),
    year: int = typer.Option(
        2025,
        "--year",
        help="Academic year",
    ),
    local: str = typer.Option(
        "Principal",
        "--local",
        help="School location",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview transformation without writing output file",
    ),
    skip_validation: bool = typer.Option(
        False,
        "--skip-validation",
        help="Skip RUT and email validation",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Transform student enrollment CSV from source format to SN system format.

    The transformation performs the following operations:

    - Cleans and formats addresses
    - Validates and formats RUTs
    - Splits names into first and second names
    - Maps commune codes to names
    - Converts dates to YYYY-MM-DD format
    - Adds metadata fields (RBD, year, level, location)
    - Reorders columns to match SN system requirements

    Example usage:

        dobby transform data/alumnos_ser.csv -o data/upload-sn.csv

        dobby transform input.csv --rbd 123 --year 2026 --verbose

        dobby transform input.csv --dry-run
    """
    # Setup logger
    log_file = Path("logs") / "dobby.log"
    log_file.parent.mkdir(exist_ok=True)
    setup_logger(verbose=verbose, log_file=log_file)

    # Set default output file if not provided
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        output_file = Path("data") / f"{timestamp}-alumnos-upload-sn.csv"
        output_file.parent.mkdir(exist_ok=True)

    try:
        # Display input info
        console.print(Panel.fit(
            f"[bold cyan]Entrada:[/bold cyan] {input_file}\n"
            f"[bold cyan]Salida:[/bold cyan] {output_file}\n"
            f"[bold cyan]RBD:[/bold cyan] {rbd} | "
            f"[bold cyan]Año:[/bold cyan] {year} | "
            f"[bold cyan]Local:[/bold cyan] {local}",
            title="Configuración",
            border_style="cyan",
        ))

        # Create configuration
        config = TransformConfig(
            rbd=rbd,
            year=year,
            local=local,
            validate_rut=not skip_validation,
            validate_email=not skip_validation,
        )

        # Execute transformation with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Transformando datos...", total=None)

            transformer = StudentDataTransformer(config)
            df = transformer.transform(input_file)

            progress.update(task, completed=True)

        # Display summary
        summary_table = Table(title="Resumen de Transformación", show_header=True)
        summary_table.add_column("Métrica", style="cyan")
        summary_table.add_column("Valor", style="green")

        summary_table.add_row("Filas de entrada", str(transformer.input_row_count))
        summary_table.add_row("Filas de salida", str(len(df)))
        summary_table.add_row("Columnas de salida", str(len(df.columns)))

        if transformer.errors:
            summary_table.add_row(
                "Advertencias de validación",
                f"[yellow]{len(transformer.errors)}[/yellow]"
            )

        console.print(summary_table)

        # Show validation errors if any
        if transformer.errors and verbose:
            error_table = Table(title="Advertencias de Validación", show_header=True)
            error_table.add_column("Fila", style="cyan")
            error_table.add_column("Campo", style="yellow")
            error_table.add_column("Error", style="red")

            for error in transformer.errors[:10]:  # Show first 10 errors
                error_table.add_row(
                    str(error["row"]),
                    error["field"],
                    error["error"],
                )

            if len(transformer.errors) > 10:
                error_table.add_row(
                    "...",
                    "...",
                    f"y {len(transformer.errors) - 10} más",
                    style="dim",
                )

            console.print(error_table)

        # Preview or save
        if dry_run:
            console.print("\n[yellow]Modo prueba - no se escribió ningún archivo[/yellow]")
            console.print("\n[bold]Vista previa (primeras 5 filas):[/bold]")
            console.print(df.head(5).to_string(index=False))
        else:
            transformer.save_csv(output_file)
            console.print(f"\n[green]Archivo guardado exitosamente en {output_file}[/green]")

    except DobbyError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.command()
def validate(
    input_file: Path = typer.Argument(
        ...,
        help="Input CSV file path",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
):
    """
    Validate input CSV without performing transformation.

    This command checks:
    - Required columns are present
    - RUT format and check digits
    - Email addresses format
    - Date formats

    Example usage:

        dobby validate data/alumnos_ser.csv
    """
    # Setup logger
    log_file = Path("logs") / "dobby.log"
    log_file.parent.mkdir(exist_ok=True)
    setup_logger(verbose=verbose, log_file=log_file)

    try:
        console.print(f"[cyan]Validando {input_file}...[/cyan]\n")

        config = TransformConfig(validate_rut=True, validate_email=True)
        transformer = StudentDataTransformer(config)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validando...", total=None)
            transformer.transform(input_file)
            progress.update(task, completed=True)

        if not transformer.errors:
            console.print("[green]Validación exitosa - no se encontraron errores[/green]")
        else:
            console.print(f"[yellow]Se encontraron {len(transformer.errors)} problemas de validación:[/yellow]\n")

            error_table = Table(show_header=True)
            error_table.add_column("Fila", style="cyan")
            error_table.add_column("Campo", style="yellow")
            error_table.add_column("Valor", style="white")
            error_table.add_column("Error", style="red")

            for error in transformer.errors[:20]:  # Show first 20 errors
                error_table.add_row(
                    str(error["row"]),
                    error["field"],
                    str(error.get("value", ""))[:30],
                    error["error"],
                )

            if len(transformer.errors) > 20:
                error_table.add_row(
                    "...",
                    "...",
                    "...",
                    f"y {len(transformer.errors) - 20} más",
                    style="dim",
                )

            console.print(error_table)
            raise typer.Exit(code=1)

    except DobbyError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()