# Error Reference

This section documents all validation errors and warnings that dppvalidator can
produce across its five-layer validation architecture.

## Error Code Categories

| Prefix | Layer      | Description                          |
| ------ | ---------- | ------------------------------------ |
| SCH    | Schema     | JSON Schema structural validation    |
| MOD    | Model      | Pydantic model type validation       |
| JLD    | JSON-LD    | Context and term resolution errors   |
| SEM    | Semantic   | Business logic and cross-field rules |
| VOC    | Vocabulary | Controlled vocabulary and code lists |
| SIG    | Signature  | VC signature verification errors     |

## JSON-LD Rules (JLD)

| Code                | Severity | Description                                |
| ------------------- | -------- | ------------------------------------------ |
| [JLD001](JLD001.md) | Error    | `@context` must be present and valid       |
| [JLD002](JLD002.md) | Warning  | All terms must resolve during expansion    |
| [JLD003](JLD003.md) | Warning  | Custom terms should use proper namespacing |
| [JLD004](JLD004.md) | Warning  | Context resolution failure (network)       |

## Semantic Rules (SEM)

| Code                | Severity | Description                                         |
| ------------------- | -------- | --------------------------------------------------- |
| [SEM001](SEM001.md) | Warning  | Material mass fractions should sum to 1.0           |
| [SEM002](SEM002.md) | Error    | validFrom must be before validUntil                 |
| [SEM003](SEM003.md) | Error    | Hazardous materials require safety information      |
| [SEM004](SEM004.md) | Warning  | recycledContent should not exceed recyclableContent |
| [SEM005](SEM005.md) | Info     | At least one conformityClaim is recommended         |
| [SEM006](SEM006.md) | Warning  | Item-level passports require serial numbers         |
| [SEM007](SEM007.md) | Warning  | Emissions data should specify operational scope     |

## Vocabulary Rules (VOC)

| Code                | Severity | Description                                  |
| ------------------- | -------- | -------------------------------------------- |
| [VOC003](VOC003.md) | Warning  | Material code must be valid per UNECE Rec 46 |
| [VOC004](VOC004.md) | Warning  | HS code must be valid for product category   |
| [VOC005](VOC005.md) | Error    | GTIN must have valid check digit             |
