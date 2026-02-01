"""External vocabulary loading and validation."""

from dppvalidator.vocabularies.cache import CacheEntry, VocabularyCache
from dppvalidator.vocabularies.code_lists import (
    get_hs_codes,
    get_material_codes,
    is_textile_hs_code,
    is_valid_gs1_digital_link,
    is_valid_hs_code,
    is_valid_material_code,
    validate_gtin,
)
from dppvalidator.vocabularies.loader import (
    VOCABULARIES,
    VocabularyDefinition,
    VocabularyLoader,
    get_bundled_country_codes,
    get_bundled_unit_codes,
)

__all__ = [
    # Loader
    "VocabularyLoader",
    "VocabularyDefinition",
    "VOCABULARIES",
    # Cache
    "VocabularyCache",
    "CacheEntry",
    # Bundled data accessors
    "get_bundled_country_codes",
    "get_bundled_unit_codes",
    # Code lists
    "get_material_codes",
    "get_hs_codes",
    "is_valid_material_code",
    "is_valid_hs_code",
    "is_textile_hs_code",
    "validate_gtin",
    "is_valid_gs1_digital_link",
]
