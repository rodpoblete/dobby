# Quick Start Guide

## Installation

```bash
# Install dependencies
uv sync

# Verify installation
uv run matrix --help
```

## Basic Usage

### Transform CSV File

```bash
# Basic transformation
uv run matrix transform data/alumnos_ser.csv

# Custom output file
uv run matrix transform data/alumnos_ser.csv -o output.csv

# Preview changes without writing
uv run matrix transform data/alumnos_ser.csv --dry-run
```

### Validate CSV File

```bash
# Validate input
uv run matrix validate data/alumnos_ser.csv

# Verbose validation
uv run matrix validate data/alumnos_ser.csv -v
```

## Development Workflow

### Run Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov

# Specific test file
uv run pytest tests/test_validators.py -v

# Watch mode (requires pytest-watch)
uv run ptw
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Auto-fix issues
uv run ruff check --fix .
```

### Adding Dependencies

```bash
# Production dependency
uv add package-name

# Development dependency
uv add --dev package-name

# Sync after adding
uv sync
```

## Common Tasks

### Test with Real Data

```bash
# Transform real data
uv run matrix transform data/alumnos_ser.csv -o test-output.csv -v

# Compare with expected output
diff test-output.csv data/upload-sn.csv
```

### Debug Issues

```bash
# Enable verbose logging
uv run matrix transform input.csv -v

# Check logs
tail -f logs/matrix.log
```

### IDE Setup (VSCode)

1. Open project in VSCode
2. Select Python interpreter: `.venv/bin/python`
3. Install recommended extensions:
   - Python
   - Pylance
   - Ruff

The [.vscode/settings.json](.vscode/settings.json) file is already configured.

## Project Structure

```
matrix/
├── src/matrix/           # Source code
│   ├── cli.py           # CLI commands
│   ├── transformer.py   # Main logic
│   ├── validators.py    # Validation functions
│   └── ...
├── tests/               # Unit tests
├── data/                # Input/output CSVs
├── logs/                # Application logs
└── pyproject.toml       # Configuration
```

## Troubleshooting

### Import Errors in IDE

VSCode should auto-detect the Python interpreter. If not:
1. Ctrl+Shift+P (Cmd+Shift+P on Mac)
2. "Python: Select Interpreter"
3. Choose `.venv/bin/python`

### Tests Failing

```bash
# Reinstall dependencies
uv sync --reinstall

# Clear cache
rm -rf .pytest_cache
uv cache clean

# Run tests again
uv run pytest
```

### CLI Not Working

```bash
# Reinstall in development mode
uv sync

# Try with full path
uv run python -m matrix.cli transform input.csv
```

## Next Steps

1. Read [README.md](README.md) for full documentation
2. Check [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for architecture details
3. Explore [tests/](tests/) for usage examples
4. Review [src/matrix/](src/matrix/) for implementation

## Getting Help

- Check logs: `logs/matrix.log`
- Run with verbose: `-v` flag
- View help: `uv run matrix --help`
- Test command: `uv run matrix transform --help`
