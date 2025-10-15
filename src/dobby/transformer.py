"""Student data transformation logic."""

import re
from pathlib import Path
from typing import Optional

import pandas as pd
from loguru import logger

from .constants import (
    COLUMN_RENAME_MAP,
    COMUNA_CODES,
    DEFAULT_LOCAL,
    DEFAULT_RBD,
    DEFAULT_YEAR,
    GRADE_LEVELS,
    OUTPUT_COLUMNS,
)
from .exceptions import FileProcessingError, MissingColumnError, TransformationError
from .models import TransformConfig
from .validators import clean_address, format_rut, validate_email, validate_rut


class StudentDataTransformer:
    """Transform student enrollment data from source format to SN system format."""

    def __init__(self, config: Optional[TransformConfig] = None):
        """
        Initialize transformer with configuration.

        Args:
            config: Transformation configuration. Uses defaults if not provided.
        """
        self.config = config or TransformConfig()
        self.df: Optional[pd.DataFrame] = None
        self.errors: list[dict] = []
        self.input_row_count: int = 0

    def load_csv(self, file_path: Path) -> None:
        """
        Load CSV file into dataframe.

        Args:
            file_path: Path to input CSV file

        Raises:
            FileProcessingError: If file cannot be read
        """
        try:
            logger.info(f"Loading CSV from {file_path}")
            self.df = pd.read_csv(
                file_path,
                sep=self.config.csv_separator,
                encoding=self.config.input_encoding,
            )
            self.input_row_count = len(self.df)
            logger.info(f"Loaded {self.input_row_count} rows and {len(self.df.columns)} columns")
        except Exception as e:
            raise FileProcessingError(f"Failed to read CSV file: {e}") from e

    def validate_input_columns(self) -> None:
        """
        Validate that required input columns exist.

        Raises:
            MissingColumnError: If required columns are missing
        """
        if self.df is None:
            raise TransformationError("No data loaded. Call load_csv first.")

        required_columns = [
            "Rut",
            "Digito verificador",
            "Nombres",
            "Apellido Paterno",
            "Apellido Materno",
            "Grado",
            "Letra",
            "Direccion",
            "Comuna",
        ]

        missing = [col for col in required_columns if col not in self.df.columns]
        if missing:
            raise MissingColumnError(f"Missing required columns: {missing}")

        logger.debug("Input column validation passed")

    def clean_addresses(self) -> None:
        """Clean address field by removing city names and commas."""
        if self.df is None:
            return

        logger.debug("Cleaning addresses")
        self.df["Direccion"] = self.df["Direccion"].apply(
            lambda x: clean_address(x) if pd.notna(x) else ""
        )

    def format_ruts(self) -> None:
        """Combine RUT number with check digit."""
        if self.df is None:
            return

        logger.debug("Formatting RUTs")
        self.df["Rut"] = (
            self.df["Rut"].astype(str)
            + "-"
            + self.df["Digito verificador"].astype(str)
        )
        self.df.drop(columns=["Digito verificador"], inplace=True)

        # Validate RUTs if configured
        if self.config.validate_rut:
            invalid_ruts = []
            for idx, rut in self.df["Rut"].items():
                if not validate_rut(str(rut)):
                    invalid_ruts.append((idx, rut))
                    self.errors.append({
                        "row": idx,
                        "field": "Rut",
                        "value": rut,
                        "error": "Invalid RUT check digit"
                    })

            if invalid_ruts:
                logger.warning(f"Found {len(invalid_ruts)} invalid RUTs")

    def split_names(self) -> None:
        """Split full names into first and second names."""
        if self.df is None:
            return

        logger.debug("Splitting names")

        # Split student names
        names = self.df["Nombres"].str.split(" ", n=1, expand=True)
        self.df["Primer Nombre Alumno"] = names[0]
        self.df["Segundo Nombre Alumno"] = names[1] if 1 in names.columns else None
        self.df.drop(columns=["Nombres"], inplace=True)

        # Split guardian names
        if "Nombre Apoderado" in self.df.columns:
            guardian_names = self.df["Nombre Apoderado"].str.split(" ", n=1, expand=True)
            self.df["Primer Nombre Apoderado"] = guardian_names[0]
            self.df["Segundo Nombre Apoderado"] = guardian_names[1] if 1 in guardian_names.columns else None
            self.df.drop(columns=["Nombre Apoderado"], inplace=True)

        # Split second guardian names
        if "Nombre Apoderado SPL" in self.df.columns:
            # Convert to string and handle NaN values
            self.df["Nombre Apoderado SPL"] = self.df["Nombre Apoderado SPL"].fillna("").astype(str)
            guardian2_names = self.df["Nombre Apoderado SPL"].str.split(" ", n=1, expand=True)
            self.df["Primer Nombre Apoderado SPL"] = guardian2_names[0]
            self.df["Segundo Nombre Apoderado SPL"] = guardian2_names[1] if 1 in guardian2_names.columns else None
            self.df.drop(columns=["Nombre Apoderado SPL"], inplace=True)

    def create_course_codes(self) -> None:
        """Create course codes by combining grade and letter."""
        if self.df is None:
            return

        logger.debug("Creating course codes")
        self.df["curso_2024"] = (
            self.df["Grado"].astype(str) + self.df["Letra"].astype(str)
        )

    def map_comuna_codes(self) -> None:
        """Map numeric commune codes to names."""
        if self.df is None:
            return

        logger.debug("Mapping commune codes")
        self.df["Comuna"] = self.df["Comuna"].replace(COMUNA_CODES)

    def create_full_addresses(self) -> None:
        """Combine address with commune."""
        if self.df is None:
            return

        logger.debug("Creating full addresses")
        self.df["full address"] = (
            self.df["Direccion"].astype(str)
            + ", "
            + self.df["Comuna"].astype(str)
        )
        self.df.drop(columns=["Direccion"], inplace=True)

    def convert_dates(self) -> None:
        """Convert date columns to proper format."""
        if self.df is None:
            return

        logger.debug("Converting dates")

        date_columns = ["Fecha de Nacimiento", "Fecha de Matrícula"]
        for col in date_columns:
            if col in self.df.columns:
                self.df[col] = pd.to_datetime(
                    self.df[col],
                    dayfirst=True,
                    format="mixed"
                ).dt.date

    def clean_phone_numbers(self) -> None:
        """Clean and format phone numbers."""
        if self.df is None:
            return

        logger.debug("Cleaning phone numbers")

        phone_columns = ["Celular Apoderado", "Celular SPL"]
        for col in phone_columns:
            if col in self.df.columns:
                # Validate and clean phone numbers
                for idx, phone in self.df[col].items():
                    # Handle NaN/None/empty
                    if pd.isna(phone) or phone == "" or phone is None:
                        self.df.at[idx, col] = 0
                        continue

                    # Convert to string
                    phone_str = str(phone).strip()

                    # Handle float notation (e.g., "932832346.0" -> "932832346")
                    if "." in phone_str:
                        try:
                            # Convert to float then to int to remove decimal part
                            phone_str = str(int(float(phone_str)))
                        except (ValueError, OverflowError):
                            pass

                    # Remove spaces, hyphens, and other common separators
                    phone_str = phone_str.replace(" ", "").replace("-", "").replace("+56", "")

                    # Remove non-digit characters
                    phone_str = "".join(c for c in phone_str if c.isdigit())

                    # If empty after cleaning, set to 0
                    if not phone_str:
                        self.df.at[idx, col] = 0
                        continue

                    # Convert to integer
                    phone_int = int(phone_str)

                    # Validate: 0 is valid (empty phone)
                    if phone_int == 0:
                        self.df.at[idx, col] = 0
                        continue

                    # Validate Chilean phone format (9 digits)
                    # Mobile: starts with 9 (900000000-999999999)
                    # Fixed: starts with 2,3,4,5,6,7 (200000000-799999999)
                    is_mobile = 900000000 <= phone_int <= 999999999
                    is_fixed = 200000000 <= phone_int <= 799999999

                    if is_mobile or is_fixed:
                        self.df.at[idx, col] = phone_int
                    else:
                        # Invalid phone (wrong format)
                        # Log warning and set to 0 to maintain data integrity
                        logger.warning(f"Row {idx}: Invalid phone in {col}: {phone} (cleaned: {phone_int}) -> setting to 0")
                        self.errors.append({
                            "row": idx,
                            "field": col,
                            "value": phone,
                            "error": f"Invalid phone: must be 9 digits (mobile 9XX... or fixed 2-7XX...)"
                        })
                        self.df.at[idx, col] = 0

    def add_metadata_columns(self) -> None:
        """Add RBD, year, nivel, and local columns."""
        if self.df is None:
            return

        logger.debug("Adding metadata columns")

        self.df.insert(0, "rbd", self.config.rbd)
        self.df.insert(1, "year", self.config.year)
        self.df.insert(2, "Nivel", "")
        self.df.insert(3, "local", self.config.local)

        # Set grade levels based on Grado column
        for grade, level in GRADE_LEVELS.items():
            self.df.loc[self.df["Grado"] == grade, "Nivel"] = level

    def uppercase_addresses(self) -> None:
        """Convert addresses to uppercase."""
        if self.df is None:
            return

        if "Direccion" in self.df.columns:
            logger.debug("Converting addresses to uppercase")
            self.df["Direccion"] = self.df["Direccion"].str.upper()

    def rename_columns(self) -> None:
        """Rename columns to output format."""
        if self.df is None:
            return

        logger.debug("Renaming columns")
        self.df.rename(columns=COLUMN_RENAME_MAP, inplace=True)

    def reorder_columns(self) -> None:
        """Reorder columns to match output schema and drop unused ones."""
        if self.df is None:
            return

        logger.debug("Reordering columns")

        # Keep only output columns that exist in dataframe
        existing_cols = [col for col in OUTPUT_COLUMNS if col in self.df.columns]
        self.df = self.df[existing_cols]

        # Drop Grado column if it still exists
        if "Grado" in self.df.columns:
            self.df.drop(columns=["Grado"], inplace=True)

    def validate_emails(self) -> None:
        """Validate email addresses if configured."""
        if not self.config.validate_email or self.df is None:
            return

        logger.debug("Validating email addresses")

        # Count email errors separately to report accurately
        email_error_count = 0
        email_columns = ["estudianteEmail", "tutor1Email", "tutor2Email"]
        for col in email_columns:
            if col in self.df.columns:
                for idx, email in self.df[col].items():
                    if pd.notna(email) and email and not validate_email(str(email)):
                        self.errors.append({
                            "row": idx,
                            "field": col,
                            "value": email,
                            "error": "Invalid email format"
                        })
                        email_error_count += 1

        if email_error_count > 0:
            logger.warning(f"Found {email_error_count} email validation errors")

    def transform(self, input_path: Path) -> pd.DataFrame:
        """
        Execute full transformation pipeline.

        Args:
            input_path: Path to input CSV file

        Returns:
            Transformed dataframe

        Raises:
            TransformationError: If transformation fails
        """
        try:
            logger.info("Starting transformation pipeline")

            self.load_csv(input_path)
            self.validate_input_columns()
            self.clean_addresses()
            self.uppercase_addresses()
            self.format_ruts()
            self.split_names()
            self.create_course_codes()
            self.map_comuna_codes()
            self.create_full_addresses()
            self.add_metadata_columns()
            self.convert_dates()
            self.clean_phone_numbers()
            self.rename_columns()
            self.reorder_columns()
            self.validate_emails()

            logger.info("Transformation completed successfully")

            if self.errors:
                logger.warning(f"Transformation completed with {len(self.errors)} validation warnings")

            if self.df is None:
                raise TransformationError(
                    "Dataframe not found after transformation pipeline."
                )

            return self.df

        except Exception as e:
            raise TransformationError(f"Transformation failed: {e}") from e

    def save_csv(self, output_path: Path) -> None:
        """
        Save transformed data to CSV.

        Args:
            output_path: Path to output CSV file

        Raises:
            FileProcessingError: If file cannot be written
        """
        if self.df is None:
            raise TransformationError("No data to save. Run transform first.")

        try:
            logger.info(f"Saving output to {output_path}")
            self.df.to_csv(
                output_path,
                sep=self.config.csv_separator,
                index=False,
                encoding=self.config.output_encoding,
            )
            logger.info(f"Saved {len(self.df)} rows to {output_path}")
        except Exception as e:
            raise FileProcessingError(f"Failed to write CSV file: {e}") from e
