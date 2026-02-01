# Validators API

Validation engine and result types for DPP validation.

## ValidationEngine

The main validation engine supporting five-layer validation.

::: dppvalidator.validators.ValidationEngine
options:
show_source: false
members:
\- __init__
\- validate

## ValidationResult

Result of a validation operation.

::: dppvalidator.validators.ValidationResult
options:
show_source: false

## ValidationError

A single validation error or warning.

::: dppvalidator.validators.ValidationError
options:
show_source: false

## Usage Example

```python
from dppvalidator.validators import ValidationEngine, ValidationResult

# Create engine with specific layers
engine = ValidationEngine(layers=["model", "semantic"])

# Validate data
result = engine.validate(
    {
        "id": "https://example.com/dpp/001",
        "issuer": {"id": "https://example.com/issuer", "name": "Acme Corp"},
    }
)

# Check result
if result.valid:
    print("Passport is valid!")
else:
    for error in result.errors:
        print(f"[{error.code}] {error.path}: {error.message}")

# Access validation metadata
print(f"Schema version: {result.schema_version}")
print(f"Validation time: {result.validation_time_ms:.2f}ms")
```

## Validation Layers

| Layer    | Description                |
| -------- | -------------------------- |
| schema   | JSON Schema validation     |
| model    | Pydantic model validation  |
| jsonld   | JSON-LD context validation |
| semantic | Business rule validation   |
| crypto   | Signature verification     |

## Error Codes

| Code   | Layer    | Description              |
| ------ | -------- | ------------------------ |
| SCH001 | schema   | Required field missing   |
| SCH002 | schema   | Invalid type             |
| MOD001 | model    | Model validation error   |
| JLD001 | jsonld   | Invalid context          |
| SEM001 | semantic | Invalid vocabulary value |
| SEM002 | semantic | Invalid date range       |
| SIG001 | crypto   | Invalid signature        |
