"""Custom exceptions for dobby transformation."""


class DobbyError(Exception):
    """Base exception for all dobby errors."""

    pass


class ValidationError(DobbyError):
    """Raised when data validation fails."""

    pass


class TransformationError(DobbyError):
    """Raised when data transformation fails."""

    pass


class FileProcessingError(DobbyError):
    """Raised when file reading or writing fails."""

    pass


class MissingColumnError(DobbyError):
    """Raised when required columns are missing from input."""

    pass