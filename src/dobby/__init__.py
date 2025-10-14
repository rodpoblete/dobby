"""Dobby - Student Enrollment Data Transformer"""

__version__ = "0.1.0"

from .exceptions import (
    FileProcessingError,
    DobbyError,
    MissingColumnError,
    TransformationError,
    ValidationError,
)
from .models import StudentOutputRecord, TransformConfig
from .transformer import StudentDataTransformer

__all__ = [
    "__version__",
    "DobbyError",
    "ValidationError",
    "TransformationError",
    "FileProcessingError",
    "MissingColumnError",
    "StudentOutputRecord",
    "TransformConfig",
    "StudentDataTransformer",
]