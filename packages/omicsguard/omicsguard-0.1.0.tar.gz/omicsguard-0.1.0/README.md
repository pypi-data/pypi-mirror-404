# OmicsGuard

**OmicsGuard** is a lightweight, serverless-ready metadata validator designed for modern bioinformatics workflows. It ensures "Schema-on-Write" integrity for GA4GH standards (like Phenopackets) while allowing flexible organizational extensions and custom business logic.

## Key Features

- **Serverless Ready**: Designed to run in AWS Lambda, Google Cloud Functions, or lightweight containers.
- **GA4GH Standard Support**: Built-in registry for official schemas (e.g., `ga4gh-phenopacket-v2`).
- **Plugin System**: Inject custom business logic with simple Python functions.
- **Schema Extensions**: Layer organization-specific fields (e.g., `hospital_id`) on top of standard schemas.
- **Human-Readable Reports**: Generate HTML or Markdown reports for biologists and clinicians.
- **Smart Caching**: Automatically caches remote schemas to minimize network latency.

---

## Installation

## Installation

You can install OmicsGuard from PyPI or directly from the source.

### 1. From PyPI (Recommended)

```bash
pip install omicsguard
```

### 2. From Source

Useful for development or using the latest unreleased features.

```bash
git clone https://github.com/your-org/omicsguard.git
cd omicsguard
pip install .
```

## Usage

### 1. Basic Validation

Validate a JSON or YAML file against the default bundled standard (Phenopackets v2).

```bash
omicsguard validate --data patient_data.json
```

**Output**:
```text
true
```

### 2. Pulling Schemas

Download and cache official schemas from the registry to avoid repeated network calls.

```bash
omicsguard pull --standard ga4gh-phenopacket-v2
```

### 3. Custom Business Rules (Plugins)

Sometimes, structural validation isn't enough. Use Python plugins to enforce complex rules (e.g., "ID must start with `PROBAND-`").

**Create a plugin (`my_plugin.py`)**:
```python
def validate(data):
    errors = []
    if not data.get("id", "").startswith("PROBAND-"):
        errors.append("ID must start with 'PROBAND-'")
    return errors
```

**Run with plugin**:
```bash
omicsguard validate --data patient.json --plugin my_plugin.py
```

### 4. Schema Extensions

Add custom fields to a standard schema without forking it.

**Extension Schema (`hospital_fields.json`)**:
```json
{
  "properties": {
    "hospital_id": { "type": "string" }
  },
  "required": ["hospital_id"]
}
```

**Merge and Validate**:
```bash
omicsguard validate --data patient.json --extend hospital_fields.json
```

### 5. Generating Reports

Generate detailed reports for non-technical stakeholders.

```bash
# HTML Report
omicsguard validate --data patient.json --output report.html

# Markdown Report (great for CI/CD comments)
omicsguard validate --data patient.json --output report.md
```

## Configuration

OmicsGuard is 12-factor app compliant and can be configured via Environment Variables:

- `OMICSGUARD_SCHEMA_CACHE`: Directory to store cached schemas (Default: `~/.omicsguard/schemas`).

## Development

1. **Clone the repo**
   ```bash
   git clone https://github.com/your-org/omicsguard.git
   cd omicsguard
   ```

2. **Install dependencies**
   ```bash
   pip install -e .
   ```

3. **Run Tests**
   ```bash
   python -m unittest discover tests
   ```

## License

MIT License. See `LICENSE` for details.
