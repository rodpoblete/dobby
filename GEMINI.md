# GEMINI.md

## Project Overview

This project is a Python command-line interface (CLI) tool named "dobby". Its primary purpose is to transform student enrollment data from a source CSV format to a specific format required for the "SN system".

The tool is built using Python and leverages several libraries:
-   **Typer:** For creating the command-line interface.
-   **Pandas:** For data manipulation and transformation of the CSV files.
-   **Pydantic:** For data validation and configuration management.
-   **Rich:** For creating rich and colorful terminal outputs.
-   **Loguru:** For logging.

The core functionality includes:
-   Reading a source CSV file with student data.
-   Cleaning and formatting various fields like addresses, names, and phone numbers.
-   Validating Chilean RUTs (Rol Único Tributario) and email addresses.
-   Mapping commune codes to commune names.
-   Adding metadata to the records.
-   Generating a new CSV file in the desired output format.

The project is structured with separate modules for the CLI, data transformation logic, data models, constants, and validators.

## Building and Running

The project uses `uv` for dependency management.

**Installation:**

```bash
# Clone the repository
git clone <repository-url>
cd dobby

# Install dependencies
uv sync
```

**Running the tool:**

The main command is `dobby transform`, which takes an input CSV file and transforms it.

```bash
# Transform a CSV file
uv run dobby transform data/alumnos_ser.csv -o upload-sn.csv

# Run with options
uv run dobby transform input.csv --rbd 123 --year 2026
```

There is also a `validate` command to check the input data without performing a full transformation.

```bash
# Validate an input file
uv run dobby validate data/alumnos_ser.csv
```

## Development Conventions

### Testing

The project uses `pytest` for testing. Tests are located in the `tests/` directory.

To run the tests:

```bash
uv run pytest
```

### Code Quality

The project uses `ruff` for linting and formatting.

To format the code:

```bash
uv run ruff format .
```

To lint the code:

```bash
uv run ruff check .
```
