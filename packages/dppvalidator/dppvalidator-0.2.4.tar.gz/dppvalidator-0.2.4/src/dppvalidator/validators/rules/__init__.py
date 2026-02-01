"""Pluggable semantic validation rules."""

from dppvalidator.validators.rules.base import (
    CircularityContentRule,
    ConformityClaimRule,
    GranularitySerialNumberRule,
    GTINChecksumRule,
    HazardousMaterialRule,
    HSCodeRule,
    MassFractionSumRule,
    MaterialCodeRule,
    OperationalScopeRule,
    ValidityDateRule,
)

ALL_RULES = [
    MassFractionSumRule(),
    ValidityDateRule(),
    HazardousMaterialRule(),
    CircularityContentRule(),
    ConformityClaimRule(),
    GranularitySerialNumberRule(),
    OperationalScopeRule(),
    MaterialCodeRule(),
    HSCodeRule(),
    GTINChecksumRule(),
]

__all__ = [
    "ALL_RULES",
    "MassFractionSumRule",
    "ValidityDateRule",
    "HazardousMaterialRule",
    "CircularityContentRule",
    "ConformityClaimRule",
    "GranularitySerialNumberRule",
    "OperationalScopeRule",
    "MaterialCodeRule",
    "HSCodeRule",
    "GTINChecksumRule",
]
