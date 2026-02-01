# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Validation Layer Architecture**: New `validators/layers.py` module with Strategy Pattern
  - `ValidationContext` dataclass for shared validation state
  - `ValidationLayer` abstract base class with 7 implementations
  - `SchemaLayer`, `ModelLayer`, `SemanticLayer`, `JsonLdLayer`,
    `VocabularyLayer`, `PluginLayer`, `SignatureLayer`
- **Schema Auto-Detection (Phase 0)**: `ValidationEngine` now defaults to `schema_version="auto"`
  - Detects version from `$schema`, `@context`, or `type` array
  - New `detect_schema_version()` and `is_dpp_document()` functions in `validators/detection.py`
- **JSON-LD Semantic Validation (Phase 1)**: PyLD-based expansion validation
  - `JSONLDValidator` class with `CachingDocumentLoader` for remote contexts
  - New error codes: JLD001-JLD004 for context and term validation
  - Enable with `ValidationEngine(validate_jsonld=True)`
- **Extended Code Lists (Phase 2)**: UNECE Rec 46, HS codes, GTIN validation
  - `validate_gtin()`, `is_valid_material_code()`, `is_valid_hs_code()` functions
  - GS1 Digital Link URL parsing and validation
  - 85 UNECE Rec 46 material codes, 156 textile HS codes (Chapters 50-63)
  - New rules: VOC003 (material codes), VOC004 (HS codes), VOC005 (GTIN checksum)
- **Verifiable Credential Verification (Phase 3)**: DID resolution and signature verification
  - `CredentialVerifier`, `DIDResolver`, `SignatureVerifier` classes in `verifier/` module
  - Support for `did:web` and `did:key` resolution
  - Ed25519, ES256, ES384 signature algorithms
  - Ed25519Signature2020, DataIntegrityProof, JsonWebSignature2020 proof types
  - New `ValidationResult` fields: `signature_valid`, `issuer_did`, `verification_method`
  - Enable with `ValidationEngine(verify_signatures=True)`
- **Deep/Recursive Validation (Phase 4)**: Supply chain traversal
  - `DeepValidator` class with async crawling, rate limiting, retry logic
  - Cycle detection for circular references
  - Configurable depth limits and link following paths
  - New `ValidationEngine.validate_deep()` async method
- `CredentialStatus` model for W3C VC v2 revocation checking
- `credentialStatus` field on `DigitalProductPassport`
- `Scope1`, `Scope2`, `Scope3` values to `OperationalScope` enum (GHG Protocol)
- SHA-256 integrity hash for schema v0.6.1
- `pytest-asyncio` for native async test support
- `CONTRIBUTING.md` with development guidelines
- Stable error code mapping (`PYDANTIC_ERROR_CODES`) for model validation

### Changed

- **Breaking**: `ValidationEngine()` now defaults to `schema_version="auto"`
- **Architecture**: Validation uses Strategy Pattern with pluggable layers
  - `validate()` refactored from 88 lines to 32 lines
  - Complexity reduced: C901 (15→0), PLR0912 (14→0)
- **CLI Refactoring**: Watch, init, and validate commands restructured
  - `watch.py`: Extracted `FileWatcher` and `WatchLoop` classes
  - `init.py`: Data-driven `FileSpec` pattern for scaffolding
  - `validate.py`: Extracted `_format_issue()` helper
- **Vocabulary Loader**: `_extract_values()` uses dispatch pattern
- Core dependencies simplified: `httpx`, `jsonschema`, `pyld`, `cryptography`, `PyJWT` now required
- Removed all `HAS_*` conditional checks from source code
- `has_vc_support()` now always returns `True`
- `operational_scope` is now optional in `EmissionsPerformance` (enables SEM007 rule)
- Replaced bare `except Exception` catches with specific exception types
- Consolidated error system: removed unused `EnhancedValidationError` class
- Version now read from `pyproject.toml` via `importlib.metadata`
- Async validation uses `asyncio.to_thread()` instead of deprecated API

### Fixed

- README plugin API example now matches actual `SemanticRule` protocol
- Model error codes are now deterministic (based on Pydantic error type)
- Unused imports and arguments cleaned up across verifier module
- Flaky `test_engine_never_crashes_on_binary` deadline increased to 500ms

## [0.1.0] - 2026-01-29

### Added

- Initial release
- `Material` model for fiber composition with ISO 2076 codes
- `SupplyChainNode` model for traceability
- `DigitalProductPassport` model following EU ESPR regulations
- JSON-LD export for Semantic Web compatibility
- Unit tests for all models and validators
- GitHub Actions CI/CD pipeline
- Pre-commit hooks with ruff
