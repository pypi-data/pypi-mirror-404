"""Multi-layer DPP validation module."""

from dppvalidator.validators.deep import (
    DeepValidationResult,
    DeepValidator,
    validate_deep,
)
from dppvalidator.validators.detection import detect_schema_version, is_dpp_document
from dppvalidator.validators.engine import ValidationEngine
from dppvalidator.validators.jsonld_semantic import (
    JSONLDValidator,
    validate_jsonld,
)
from dppvalidator.validators.model import ModelValidator
from dppvalidator.validators.protocols import AsyncValidator, SemanticRule, Validator
from dppvalidator.validators.results import (
    ValidationError,
    ValidationException,
    ValidationResult,
)
from dppvalidator.validators.schema import SchemaValidator
from dppvalidator.validators.semantic import SemanticValidator

__all__ = [
    # Detection
    "detect_schema_version",
    "is_dpp_document",
    # Engine
    "ValidationEngine",
    # Results
    "ValidationResult",
    "ValidationError",
    "ValidationException",
    # Validators
    "SchemaValidator",
    "ModelValidator",
    "SemanticValidator",
    "JSONLDValidator",
    "validate_jsonld",
    # Deep validation
    "DeepValidator",
    "DeepValidationResult",
    "validate_deep",
    # Protocols
    "Validator",
    "AsyncValidator",
    "SemanticRule",
]
