"Command-line interface for dobby transformation tool."

from datetime import datetime
from pathlib import Path
from typing import Optional

import questionary
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
        # Get start time
        start_time = datetime.now()

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
            task = progress.add_task("Procesando...", total=None)

            transformer = StudentDataTransformer(config)
            df = transformer.transform(input_file)

            progress.update(task, completed=True)

        # Calculate statistics
        total_records = transformer.input_row_count
        successful_records = total_records - len(transformer.errors)
        error_records = len(transformer.errors)

        # Display KISS summary
        console.print("\n" + "=" * 70)
        console.print(f"[bold cyan]REPORTE DE TRANSFORMACIÓN[/bold cyan]")
        console.print("=" * 70)
        console.print(f"Fecha y hora: [cyan]{start_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
        console.print(f"Archivo entrada: [cyan]{input_file}[/cyan]")
        console.print(f"Archivo salida: [cyan]{output_file}[/cyan]")
        console.print("-" * 70)
        console.print(f"Registros totales: [bold]{total_records}[/bold]")
        console.print(f"Procesados correctamente: [green]{successful_records}[/green]")
        console.print(f"Procesados con errores: [{'yellow' if error_records > 0 else 'green'}]{error_records}[/{'yellow' if error_records > 0 else 'green'}]")

        # Show errors if any
        if transformer.errors:
            console.print("\n" + "-" * 70)
            console.print("[yellow]ERRORES ENCONTRADOS:[/yellow]")
            console.print("-" * 70)

            error_table = Table(show_header=True, box=None, padding=(0, 2))
            error_table.add_column("Fila", style="cyan", justify="right")
            error_table.add_column("Campo", style="yellow")
            error_table.add_column("Valor", style="white", max_width=30)
            error_table.add_column("Error", style="red")

            for error in transformer.errors:
                error_table.add_row(
                    str(error["row"] + 2),  # +2 para incluir header y convertir a 1-based
                    error["field"],
                    str(error.get("value", ""))[:28],
                    error["error"],
                )

            console.print(error_table)
            console.print("\n[dim]Nota: El número de fila corresponde a la línea en el archivo CSV de entrada[/dim]")

        console.print("=" * 70 + "\n")

        # Preview or save
        if dry_run:
            console.print("[yellow]Modo prueba - no se escribió ningún archivo[/yellow]\n")
        else:
            transformer.save_csv(output_file)
            console.print(f"[green]✓ Transformación completada exitosamente[/green]\n")

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
            console.print()
            raise typer.Exit(code=1)

    except typer.Exit:
        # Re-raise typer.Exit to let it propagate naturally
        raise
    except DobbyError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[red]Error inesperado: {e}[/red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """
    Dobby - Transformador de Datos de Matrícula Estudiantil.

    Si no se especifica un comando, se mostrará un menú interactivo.
    """
    # If a subcommand was invoked, let it run
    if ctx.invoked_subcommand is not None:
        return

    # Show interactive menu
    show_interactive_menu()


def show_dobby_header():
    """Display Dobby ASCII art header."""
    dobby_art = """[bold cyan]
       /$$           /$$       /$$
      | $$          | $$      | $$
  /$$$$$$$  /$$$$$$ | $$$$$$$ | $$$$$$$  /$$   /$$
 /$$__  $$ /$$__  $$| $$__  $$| $$__  $$| $$  | $$
| $$  | $$| $$  \\ $$| $$  \\ $$| $$  \\ $$| $$  | $$
| $$  | $$| $$  | $$| $$  | $$| $$  | $$| $$  | $$
|  $$$$$$$|  $$$$$$/| $$$$$$$/| $$$$$$$/|  $$$$$$$
 \\_______/ \\______/ |_______/ |_______/  \\____  $$
                                         /$$  | $$
                                        |  $$$$$$/
                                         \\______/ [/bold cyan]
"""
    console.print(dobby_art)


def show_interactive_menu():
    """Show interactive menu for user to select action."""
    show_dobby_header()
    console.print("[bold cyan]Estoy aquí para ayudar con los datos, señor[/bold cyan]\n")

    while True:
        action = questionary.select(
            "¿Qué deseas hacer?",
            choices=[
                "Transformar archivo CSV",
                "Validar archivo CSV",
                "Ver información y ayuda",
                "Salir",
            ],
            style=questionary.Style(
                [
                    ("selected", "fg:cyan bold"),
                    ("pointer", "fg:cyan bold"),
                    ("question", "bold"),
                ]
            ),
        ).ask()

        if action is None or action == "Salir":
            console.print("\n[dim]¡Hasta luego! Dobby está feliz de haber ayudado.[/dim]\n")
            break

        if action == "Transformar archivo CSV":
            interactive_transform()
        elif action == "Validar archivo CSV":
            interactive_validate()
        elif action == "Ver información y ayuda":
            show_help()


def interactive_transform():
    """Interactive transformation workflow."""
    console.print("\n[bold]Transformación de archivo CSV[/bold]\n")

    # Get input file
    input_file_str = questionary.path(
        "Ruta del archivo CSV de entrada:",
        default="data/alumnos_ser.csv",
        only_directories=False,
    ).ask()

    if not input_file_str:
        return

    input_file = Path(input_file_str)

    if not input_file.exists():
        console.print(f"[red]Error: El archivo {input_file} no existe[/red]")
        return

    # Get output file
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    default_output = f"data/{timestamp}-alumnos-upload-sn.csv"

    use_default_output = questionary.confirm(
        f"¿Usar nombre de salida por defecto? ({default_output})", default=True
    ).ask()

    if use_default_output:
        output_file = Path(default_output)
    else:
        output_file_str = questionary.path(
            "Ruta del archivo CSV de salida:", default=default_output, only_directories=False
        ).ask()
        if not output_file_str:
            return
        output_file = Path(output_file_str)

    # Get configuration
    rbd = questionary.text("RBD del colegio:", default="574").ask()
    if not rbd:
        return

    year = questionary.text("Año académico:", default="2025").ask()
    if not year:
        return

    local = questionary.text("Ubicación del colegio:", default="Principal").ask()
    if not local:
        return

    # Additional options
    dry_run = questionary.confirm("¿Modo de prueba (no guardar archivo)?", default=False).ask()
    skip_validation = questionary.confirm("¿Omitir validación de RUT y email?", default=False).ask()
    verbose = questionary.confirm("¿Habilitar modo verboso?", default=False).ask()

    # Setup logger
    log_file = Path("logs") / "dobby.log"
    log_file.parent.mkdir(exist_ok=True)
    setup_logger(verbose=verbose, log_file=log_file)

    # Create output directory
    output_file.parent.mkdir(exist_ok=True)

    try:
        start_time = datetime.now()

        # Create configuration
        config = TransformConfig(
            rbd=int(rbd),
            year=int(year),
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
            task = progress.add_task("Procesando...", total=None)

            transformer = StudentDataTransformer(config)
            df = transformer.transform(input_file)

            progress.update(task, completed=True)

        # Calculate statistics
        total_records = transformer.input_row_count
        successful_records = total_records - len(transformer.errors)
        error_records = len(transformer.errors)

        # Display KISS summary
        console.print("\n" + "=" * 70)
        console.print(f"[bold cyan]REPORTE DE TRANSFORMACIÓN[/bold cyan]")
        console.print("=" * 70)
        console.print(f"Fecha y hora: [cyan]{start_time.strftime('%Y-%m-%d %H:%M:%S')}[/cyan]")
        console.print(f"Archivo entrada: [cyan]{input_file}[/cyan]")
        console.print(f"Archivo salida: [cyan]{output_file}[/cyan]")
        console.print("-" * 70)
        console.print(f"Registros totales: [bold]{total_records}[/bold]")
        console.print(f"Procesados correctamente: [green]{successful_records}[/green]")
        console.print(
            f"Procesados con errores: [{'yellow' if error_records > 0 else 'green'}]{error_records}[/{'yellow' if error_records > 0 else 'green'}]"
        )

        # Show errors if any
        if transformer.errors:
            console.print("\n" + "-" * 70)
            console.print("[yellow]ERRORES ENCONTRADOS:[/yellow]")
            console.print("-" * 70)

            error_table = Table(show_header=True, box=None, padding=(0, 2))
            error_table.add_column("Fila", style="cyan", justify="right")
            error_table.add_column("Campo", style="yellow")
            error_table.add_column("Valor", style="white", max_width=30)
            error_table.add_column("Error", style="red")

            for error in transformer.errors:
                error_table.add_row(
                    str(error["row"] + 2),  # +2 para incluir header y convertir a 1-based
                    error["field"],
                    str(error.get("value", ""))[:28],
                    error["error"],
                )

            console.print(error_table)
            console.print(
                "\n[dim]Nota: El número de fila corresponde a la línea en el archivo CSV de entrada[/dim]"
            )

        console.print("=" * 70 + "\n")

        # Preview or save
        if dry_run:
            console.print("[yellow]Modo prueba - no se escribió ningún archivo[/yellow]\n")
        else:
            transformer.save_csv(output_file)
            console.print(f"[green]✓ Transformación completada exitosamente[/green]\n")

    except DobbyError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error inesperado: {e}[/red]")
        if verbose:
            console.print_exception()


def interactive_validate():
    """Interactive validation workflow."""
    console.print("\n[bold]Validación de archivo CSV[/bold]\n")

    # Get input file
    input_file_str = questionary.path(
        "Ruta del archivo CSV a validar:",
        default="data/alumnos_ser.csv",
        only_directories=False,
    ).ask()

    if not input_file_str:
        return

    input_file = Path(input_file_str)

    if not input_file.exists():
        console.print(f"[red]Error: El archivo {input_file} no existe[/red]")
        return

    verbose = questionary.confirm("¿Habilitar modo verboso?", default=False).ask()

    # Setup logger
    log_file = Path("logs") / "dobby.log"
    log_file.parent.mkdir(exist_ok=True)
    setup_logger(verbose=verbose, log_file=log_file)

    try:
        console.print(f"\n[cyan]Validando {input_file}...[/cyan]\n")

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
            console.print("[green]✓ Validación exitosa - no se encontraron errores[/green]\n")
        else:
            console.print(
                f"[yellow]Se encontraron {len(transformer.errors)} problemas de validación:[/yellow]\n"
            )

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
            console.print()

    except DobbyError as e:
        console.print(f"[red]Error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Error inesperado: {e}[/red]")
        if verbose:
            console.print_exception()


def show_help():
    """Show help information."""
    console.print("\n[bold cyan]Información y Ayuda[/bold cyan]\n")

    help_text = f"""
[bold]Dobby v{__version__}[/bold] - Transformador de Datos de Matrícula Estudiantil

[bold yellow]Descripción:[/bold yellow]
Herramienta CLI para transformar datos CSV de matrícula estudiantil desde formato
fuente (74 columnas) al formato de carga del sistema SN (29 columnas).

[bold yellow]Características principales:[/bold yellow]
• Transforma datos de estudiantes a formato SN
• Valida RUT chileno y dígitos verificadores (incluye IPE)
• Limpia y formatea direcciones
• Valida emails y teléfonos (móviles y fijos)
• Reportes de errores detallados
• Soporte para modo prueba (dry-run)

[bold yellow]Validación de RUT:[/bold yellow]
• RUT Regular: XXXXXXXX-Y (valida dígito verificador)
• IPE: 100,000,000-199,999,999 o 200,000,000-299,999,999 (no valida dígito)

[bold yellow]Validación de Teléfonos:[/bold yellow]
• Móviles: 9 dígitos empezando con 9 (ej: 987654321)
• Fijos: 9 dígitos empezando con 2-7 (ej: 223456789, 512345678)

[bold yellow]Formato de entrada:[/bold yellow]
• Separador: punto y coma (;)
• Codificación: UTF-8 con BOM (utf-8-sig)

[bold yellow]Formato de salida:[/bold yellow]
• 29 columnas en formato SN
• Archivo: YYYY-MM-DD-HHMM-alumnos-upload-sn.csv

[bold yellow]Uso desde línea de comandos:[/bold yellow]
  dobby                              # Menú interactivo
  dobby transform archivo.csv        # Transformar directamente
  dobby validate archivo.csv         # Validar directamente

[bold yellow]Archivos de log:[/bold yellow]
Los logs se guardan en: logs/dobby.log

[bold yellow]Más información:[/bold yellow]
Consulta el archivo README.md para documentación completa.
"""

    console.print(Panel(help_text, border_style="cyan"))
    console.print()


if __name__ == "__main__":
    app()