# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Dobby is a Python CLI tool that transforms student enrollment CSV data from a 74-column source format to a 29-column SN system upload format. Originally converted from a Jupyter notebook into a production-ready application.

## Common Commands

### Development Setup
```bash
# Install dependencies (includes dev tools)
uv sync

# Install without dev dependencies
uv sync --no-dev
```

### Running the Application
```bash
# Transform CSV with default settings
uv run dobby transform data/alumnos_ser.csv

# Transform with custom output and parameters
uv run dobby transform input.csv -o output.csv --rbd 123 --year 2026

# Preview transformation without writing file
uv run dobby transform input.csv --dry-run

# Validate input CSV without transformation
uv run dobby validate data/alumnos_ser.csv

# Verbose mode for detailed logging
uv run dobby transform input.csv -v
```

### Testing
```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov

# Run specific test file
uv run pytest tests/test_validators.py

# Run single test
uv run pytest tests/test_transformer.py::test_format_ruts -v
```

### Code Quality
```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Type checking (if needed)
uv run pyright
```

## Architecture

### Transformation Pipeline

The `StudentDataTransformer` class (src/dobby/transformer.py) executes a 15-step pipeline:

1. **Load CSV** - Read with UTF-8-sig encoding, semicolon separator
2. **Validate Columns** - Check required columns exist
3. **Clean Addresses** - Remove city names (La Serena, Coquimbo, Vicuña), normalize whitespace
4. **Uppercase Addresses** - Convert to uppercase
5. **Format RUTs** - Combine "Rut" + "-" + "Digito verificador"
6. **Split Names** - Separate "Nombres" into first/second names for students and guardians
7. **Create Course Codes** - Combine Grado + Letra (e.g., "5A")
8. **Map Communes** - Convert numeric codes (1-16) to commune names
9. **Create Full Addresses** - Merge address + commune
10. **Add Metadata** - Insert RBD, year, nivel (grade level), local
11. **Convert Dates** - Transform to YYYY-MM-DD (from DD-MM-YYYY input)
12. **Clean Phones** - Format as integers (9XXXXXXXX or 0)
13. **Rename Columns** - Map to SN system field names
14. **Reorder Columns** - Match 29-column output schema
15. **Validate Emails** - Check format (optional, controlled by config)

Each step modifies `self.df` in place. The pipeline is sequential and order-dependent.

### Key Modules

**src/dobby/transformer.py** - Main transformation logic
- `StudentDataTransformer` class orchestrates the pipeline
- Each transformation step is a separate method
- Tracks validation errors in `self.errors` list
- Does not raise exceptions for validation failures, allowing processing to continue

**src/dobby/validators.py** - Data validation functions
- `validate_rut()` - Chilean RUT check digit algorithm with IPE support
- `validate_email()` - Basic email format validation
- `clean_address()` - Address cleaning with regex patterns
- `format_rut()` - Combines RUT components

**src/dobby/models.py** - Pydantic data models
- `StudentOutputRecord` - 29-field output schema with validators
- `TransformConfig` - Pipeline configuration (RBD, year, encoding, validation flags)

**src/dobby/constants.py** - Configuration data
- `COMUNA_CODES` - Dict mapping 16 commune codes to names
- `GRADE_LEVELS` - Maps grades (PK-12) to level descriptions
- `COLUMN_RENAME_MAP` - Maps input columns to output field names
- `OUTPUT_COLUMNS` - Ordered list of 29 output columns

**src/dobby/cli.py** - Typer-based CLI interface
- `transform` command - Main transformation with rich progress/table output
- `validate` command - Validation-only mode without file output
- Uses Rich library for colorful terminal output

**src/dobby/exceptions.py** - Custom exception hierarchy
- `DobbyError` - Base exception
- `FileProcessingError`, `MissingColumnError`, `TransformationError`, `ValidationError`

### Data Flow

```
CSV Input (UTF-8-sig, semicolon-separated, 74+ columns)
    ↓
StudentDataTransformer.transform()
    ↓ (15 sequential steps)
DataFrame (29 columns, validated)
    ↓
CSV Output (UTF-8-sig, semicolon-separated)
```

### Error Handling Strategy

- File I/O errors raise `FileProcessingError`
- Missing columns raise `MissingColumnError`
- Pipeline failures raise `TransformationError`
- Data validation issues are logged to `self.errors` list but don't stop processing
- CLI displays validation warnings in table format
- Logs written to `logs/dobby.log` with rotation

### Chilean RUT Validation

Supports two types of identifiers:

**Regular RUT:** XXXXXXXX-Y where Y is check digit (0-9 or K)

Algorithm:
1. Multiply each digit by weights 2,3,4,5,6,7,2,3... (right to left)
2. Sum products
3. Calculate: 11 - (sum % 11)
4. Special cases: 11→0, 10→K

**IPE (Identificador Provisorio del Estudiante):** RUTs starting with 100 or 200 million
- Used for foreign students without definitive Chilean ID
- RUTs in ranges: 100,000,000-199,999,999 or 200,000,000-299,999,999
- Check digit is NOT validated (accepted as-is)
- Example: 100123456-0, 200987654-K

## Configuration

Default values in `TransformConfig`:
- RBD: 574
- Year: 2025
- Local: "Principal"
- CSV separator: semicolon (;)
- Encoding: utf-8-sig (handles Excel BOM)
- Validation: RUT and email enabled by default

Override via CLI flags: `--rbd`, `--year`, `--local`, `--skip-validation`

## Testing

Test structure mirrors source:
- `tests/test_transformer.py` - Pipeline integration and individual steps
- `tests/test_validators.py` - RUT/email/address validation

Current coverage: 66% (23 tests passing)

When adding features:
1. Add transformation method to `StudentDataTransformer`
2. Call in `transform()` pipeline at appropriate position
3. Add unit test covering the new step
4. Update `COLUMN_RENAME_MAP` or `OUTPUT_COLUMNS` if needed

## Known Data Issues

- Some real RUTs fail validation (likely source data quality issues)
- Phone numbers must be 9 digits starting with 9, or 0 for empty
- Dates assumed to be DD-MM-YYYY in input
- Commune codes limited to 16 communes (extendable in `constants.py`)

## Project Structure

```
dobby/
├── src/dobby/
│   ├── cli.py              # CLI commands (transform, validate)
│   ├── transformer.py      # Main pipeline logic
│   ├── validators.py       # RUT, email, address validation
│   ├── models.py           # Pydantic schemas
│   ├── constants.py        # Mappings and configuration
│   ├── exceptions.py       # Custom exceptions
│   └── logger.py           # Loguru setup
├── tests/
│   ├── test_transformer.py # Pipeline tests
│   └── test_validators.py  # Validation tests
├── data/                   # Input/output CSV files
├── logs/                   # Application logs
└── pyproject.toml          # Package config, dependencies, tool settings
```
