"""Tests for transformer module."""

from pathlib import Path

import pandas as pd
import pytest

from dobby.exceptions import FileProcessingError, MissingColumnError
from dobby.models import TransformConfig
from dobby.transformer import StudentDataTransformer


@pytest.fixture
def sample_input_csv(tmp_path):
    """Create a sample input CSV file for testing."""
    csv_path = tmp_path / "input.csv"
    data = {
        "Rut": ["12345678", "23456789"],
        "Digito verificador": ["5", "K"],
        "Nombres": ["JUAN PABLO", "MARIA ELENA"],
        "Apellido Paterno": ["PEREZ", "GOMEZ"],
        "Apellido Materno": ["LOPEZ", "ROJAS"],
        "Sexo": ["M", "F"],
        "Fecha de Nacimiento": ["01-01-2010", "15-05-2011"],
        "Direccion": ["Calle 123, La Serena", "Avenida 456, Coquimbo"],
        "Comuna": [4101, 4102],
        "Grado": [7, 8],
        "Letra": ["A", "B"],
        "Email Estudiante": ["juan@test.com", "maria@test.com"],
        "Fecha de Matrícula": ["01-03-2024", "01-03-2024"],
        "Nombre Apoderado": ["PEDRO ANTONIO", "ANA MARIA"],
        "Apellido Paterno Apo.": ["PEREZ", "GOMEZ"],
        "Apellido Materno Apo.": ["SILVA", "CASTRO"],
        "Rut Apoderado": ["11111111-1", "22222222-2"],
        "Email Apoderado": ["pedro@test.com", "ana@test.com"],
        "Celular Apoderado": [987654321, 976543210],
        "Nombre Apoderado SPL": ["", ""],
        "Apellido Paterno Apo. SPL": ["", ""],
        "Apellido Materno Apo. SPL": ["", ""],
        "Rut Apoderado SPL": ["", ""],
        "Email Apoderado SPL": ["", ""],
        "Celular SPL": [None, None],
    }
    df = pd.DataFrame(data)
    df.to_csv(csv_path, sep=";", index=False, encoding="utf-8-sig")
    return csv_path


class TestStudentDataTransformer:
    """Tests for StudentDataTransformer class."""

    def test_load_csv(self, sample_input_csv):
        """Test CSV loading."""
        transformer = StudentDataTransformer()
        transformer.load_csv(sample_input_csv)
        assert transformer.df is not None
        assert len(transformer.df) == 2

    def test_load_csv_nonexistent_file(self, tmp_path):
        """Test loading non-existent file."""
        transformer = StudentDataTransformer()
        nonexistent = tmp_path / "nonexistent.csv"
        with pytest.raises(FileProcessingError):
            transformer.load_csv(nonexistent)

    def test_validate_input_columns_success(self, sample_input_csv):
        """Test successful column validation."""
        transformer = StudentDataTransformer()
        transformer.load_csv(sample_input_csv)
        transformer.validate_input_columns()

    def test_validate_input_columns_missing(self, tmp_path):
        """Test column validation with missing columns."""
        csv_path = tmp_path / "incomplete.csv"
        df = pd.DataFrame({"Rut": ["12345678"]})
        df.to_csv(csv_path, sep=";", index=False)

        transformer = StudentDataTransformer()
        transformer.load_csv(csv_path)
        with pytest.raises(MissingColumnError):
            transformer.validate_input_columns()

    def test_format_ruts(self, sample_input_csv):
        """Test RUT formatting."""
        transformer = StudentDataTransformer()
        transformer.load_csv(sample_input_csv)
        transformer.format_ruts()

        assert transformer.df is not None
        assert "12345678-5" in transformer.df["Rut"].values
        assert "23456789-K" in transformer.df["Rut"].values
        assert "Digito verificador" not in transformer.df.columns

    def test_split_names(self, sample_input_csv):
        """Test name splitting."""
        transformer = StudentDataTransformer()
        transformer.load_csv(sample_input_csv)
        transformer.split_names()

        assert transformer.df is not None
        assert "Primer Nombre Alumno" in transformer.df.columns
        assert "Segundo Nombre Alumno" in transformer.df.columns
        assert transformer.df["Primer Nombre Alumno"].iloc[0] == "JUAN"
        assert transformer.df["Segundo Nombre Alumno"].iloc[0] == "PABLO"

    def test_create_course_codes(self, sample_input_csv):
        """Test course code creation."""
        transformer = StudentDataTransformer()
        transformer.load_csv(sample_input_csv)
        transformer.create_course_codes()

        assert transformer.df is not None
        assert "curso_2024" in transformer.df.columns
        assert transformer.df["curso_2024"].iloc[0] == "7A"
        assert transformer.df["curso_2024"].iloc[1] == "8B"

    def test_transform_config_defaults(self):
        """Test default configuration."""
        config = TransformConfig()
        assert config.rbd == 574
        assert config.year == 2025
        assert config.local == "Principal"

    def test_transform_config_custom(self):
        """Test custom configuration."""
        config = TransformConfig(rbd=123, year=2026, local="Anexo")
        assert config.rbd == 123
        assert config.year == 2026
        assert config.local == "Anexo"

    def test_full_transform_pipeline(self, sample_input_csv, tmp_path):
        """Test complete transformation pipeline."""
        transformer = StudentDataTransformer()
        result = transformer.transform(sample_input_csv)

        assert result is not None
        assert len(result) == 2
        assert "rbd" in result.columns
        assert "year" in result.columns
        assert "nivel" in result.columns

        output_path = tmp_path / "output.csv"
        transformer.save_csv(output_path)
        assert output_path.exists()
