
import logging
import sys
from pathlib import Path
from typing import Tuple

import click

from .loader import SchemaLoader, SCHEMA_REGISTRY
from .reporter import ValidationReporter
from .utils import load_yaml_or_json
from .validator import MetadataValidator, ValidationError

# Use stderr for logging to keep stdout clean for scriptability (true/false output)
logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_SCHEMA_PATH = Path(__file__).parent / "schemas" / "default.json"

@click.group()
def cli():
    """OmicsGuard: Serverless-Ready Metadata Validator for GA4GH Standards."""
    pass

@cli.command()
@click.option('--schema', help='Path, URL, or Standard Name (e.g., ga4gh-phenopacket-v2). Defaults to bundled schema.')
@click.option('--extend', help='Path/URL to an extension schema to merge with the base.')
@click.option('--data', required=True, help='Path to the data file (JSON/YAML) to validate.')
@click.option('--plugin', multiple=True, help='Path to Python file(s) with custom validation logic.')
@click.option('--output', help='Path to save the validation report (HTML/Markdown).')
def validate(schema: str, extend: str, data: str, plugin: Tuple[str], output: str):
    """
    Validate genomic metadata against a schema and optional custom rules.
    """
    # 1. Resolve Configuration
    schema_uri = schema or str(DEFAULT_SCHEMA_PATH)
    logger.debug("Configuration: Schema=%s, Extend=%s, Data=%s, Plugins=%s", schema_uri, extend, data, plugin)

    try:
        # 2. Load Data
        data_content = load_yaml_or_json(data)
    except (ValueError, OSError) as e:
        logger.error("Failed to load data file '%s': %s", data, e)
        sys.exit(1)

    try:
        # 3. Initialize Validator
        validator = MetadataValidator(
            schema_location=schema_uri, 
            extension_schema=extend,
            plugins=list(plugin)
        )
        
        # 4. Perform Validation
        errors = validator.validate(data_content)
        
        # 5. Generate Report (if requested)
        if output:
            try:
                ValidationReporter.generate_report(errors, output)
                logger.info("Report generated at %s", output)
            except Exception as e:
                logger.error("Failed to generate report: %s", e)

        # 6. Output Results
        if not errors:
            click.echo("true")
            sys.exit(0)
        else:
            click.echo("false")
            for err in errors:
                click.echo(f" - {err}", err=True)
            sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected internal error during validation.")
        sys.exit(1)

@cli.command()
@click.option('--standard', required=True, help=f'Standard to pull. Options: {", ".join(SCHEMA_REGISTRY.keys())}')
def pull(standard: str):
    """Download and cache a standard schema."""
    try:
        path = SchemaLoader().pull_schema(standard)
        click.echo(f"Successfully cached '{standard}' at {path}", err=True)
    except Exception as e:
        click.echo(f"Error pulling schema: {e}", err=True)
        sys.exit(1)

def main():
    cli()

if __name__ == '__main__':
    main()
