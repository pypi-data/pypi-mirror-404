# UNTP DPP Schema Files

This directory contains bundled JSON Schema files for the UN Transparency Protocol
(UNTP) Digital Product Passport (DPP) specification.

## Source

Schemas are sourced from the official UN/CEFACT vocabulary repository:

- **URL**: <https://test.uncefact.org/vocabulary/untp/dpp/>
- **Specification**: <https://untp.unece.org/specification/DigitalProductPassport>

## Included Schemas

| File                         | Version | Source URL                                                                           |
| ---------------------------- | ------- | ------------------------------------------------------------------------------------ |
| `untp-dpp-schema-0.6.1.json` | 0.6.1   | [Download](https://test.uncefact.org/vocabulary/untp/dpp/untp-dpp-schema-0.6.1.json) |

## License

The UNTP specification and schemas are published by UN/CEFACT under
open governance. See the [UNTP specification](https://untp.unece.org/)
for licensing details.

## Updates

To update schemas, use the `SchemaLoader.download_schema()` method or fetch
directly from the source URLs above.

```python
from dppvalidator.schemas import SchemaLoader

loader = SchemaLoader()
loader.download_schema("0.6.1", output_dir="./schemas/data")
```
