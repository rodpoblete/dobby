"""Pydantic models for data validation."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class StudentOutputRecord(BaseModel):
    """Model for output CSV record (SN system format)."""

    rbd: int = Field(description="School RBD identifier")
    year: int = Field(description="Academic year")
    nivel: str = Field(description="Grade level description")
    curso: str = Field(description="Course code (grade + letter)")
    local: str = Field(description="School location")
    fechaMatricula: date = Field(description="Enrollment date")
    estudiantePaterno: str = Field(description="Student paternal surname")
    estudianteMaterno: str = Field(description="Student maternal surname")
    estudianteNombre1: str = Field(description="Student first name")
    estudianteNombre2: Optional[str] = Field(None, description="Student second name")
    estudianteEmail: str = Field(description="Student email")
    sexo: str = Field(description="Student gender (M/F)")
    estudianteRun: str = Field(description="Student RUT with check digit")
    fechaNacimiento: date = Field(description="Student birth date")
    direccion: str = Field(description="Full address with commune")
    tutor1Nombre1: str = Field(description="Guardian 1 first name")
    tutor1Nombre2: Optional[str] = Field(None, description="Guardian 1 second name")
    tutor1Paterno: str = Field(description="Guardian 1 paternal surname")
    tutor1Materno: str = Field(description="Guardian 1 maternal surname")
    tutor1Run: str = Field(description="Guardian 1 RUT")
    tutor1Email: str = Field(description="Guardian 1 email")
    tutor1Celular: int = Field(description="Guardian 1 phone")
    tutor2Nombre1: Optional[str] = Field(None, description="Guardian 2 first name")
    tutor2Nombre2: Optional[str] = Field(None, description="Guardian 2 second name")
    tutor2Paterno: Optional[str] = Field(None, description="Guardian 2 paternal surname")
    tutor2Materno: Optional[str] = Field(None, description="Guardian 2 maternal surname")
    tutor2Run: Optional[str] = Field(None, description="Guardian 2 RUT")
    tutor2Email: Optional[str] = Field(None, description="Guardian 2 email")
    tutor2Celular: int = Field(0, description="Guardian 2 phone")

    @field_validator("sexo")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validate gender field."""
        if v not in ["M", "F"]:
            raise ValueError("Gender must be M or F")
        return v

    @field_validator("year")
    @classmethod
    def validate_year(cls, v: int) -> int:
        """Validate academic year is reasonable."""
        if v < 2000 or v > 2100:
            raise ValueError("Year must be between 2000 and 2100")
        return v

    @field_validator("tutor1Celular", "tutor2Celular")
    @classmethod
    def validate_phone(cls, v: int) -> int:
        """Validate phone number."""
        if v != 0 and (v < 900000000 or v > 999999999):
            raise ValueError("Phone must be 9 digits starting with 9, or 0")
        return v

    class Config:
        """Pydantic model configuration."""

        str_strip_whitespace = True
        validate_assignment = True


class TransformConfig(BaseModel):
    """Configuration for transformation process."""

    rbd: int = Field(default=574, description="School RBD identifier")
    year: int = Field(default=2025, description="Academic year")
    local: str = Field(default="Principal", description="School location")
    input_encoding: str = Field(default="utf-8-sig", description="Input CSV encoding")
    output_encoding: str = Field(default="utf-8-sig", description="Output CSV encoding")
    csv_separator: str = Field(default=";", description="CSV field separator")
    validate_rut: bool = Field(default=True, description="Validate RUT check digits")
    validate_email: bool = Field(default=True, description="Validate email formats")
    skip_invalid_rows: bool = Field(default=False, description="Skip rows with validation errors")

    class Config:
        """Pydantic model configuration."""

        validate_assignment = True
