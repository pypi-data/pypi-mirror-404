import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import jsonschema

from .loader import SchemaLoader
from .plugin import PluginLoader
from .utils import deep_merge

logger = logging.getLogger(__name__)

@dataclass
class ValidationError:
    """
    Represents a single validation error found in the data.

    Attributes:
        message: A human-readable error message.
        path: The path to the invalid element in the data (e.g., "samples.0.id").
    """
    message: str
    path: str

    def __str__(self) -> str:
        return f"[{self.path}] {self.message}"

class MetadataValidator:
    """
    Validates dictionary data against a JSON schema and optional custom plugins.
    """

    def __init__(self, 
                 schema_location: Optional[str] = None, 
                 schema_dict: Optional[Dict[str, Any]] = None,
                 extension_schema: Optional[Union[str, Dict[str, Any]]] = None,
                 plugins: Optional[List[str]] = None):
        """
        Initialize the validator.

        Args:
            schema_location: Path or URL to the base schema.
            schema_dict: Direct dictionary representation of the base schema.
            extension_schema: Path, URL, or dict of an extension schema to merge into the base.
            plugins: List of paths to python plugin files.

        Raises:
            ValueError: If neither schema_location nor schema_dict is provided.
        """
        self.loader = SchemaLoader()
        self.plugin_functions: List[Callable[[Dict[str, Any]], List[str]]] = []
        
        # 1. Load Base Schema
        if schema_dict:
            self.schema = schema_dict
        elif schema_location:
            self.schema = self.loader.load_schema(schema_location)
        else:
            raise ValueError("Either 'schema_location' or 'schema_dict' must be provided.")
            
        # 2. Apply Extension Schema
        if extension_schema:
            try:
                self._apply_extension(extension_schema)
            except Exception as e:
                logger.error("Failed to merge extension schema: %s", e)
                raise ValueError("Invalid extension schema configuration") from e

        # 3. Load Plugins
        if plugins:
            self._load_plugins(plugins)

    def _apply_extension(self, extension: Union[str, Dict[str, Any]]):
        """Helper to merge extension schema."""
        if isinstance(extension, (str, Path)):
            ext_dict = self.loader.load_schema(str(extension))
        elif isinstance(extension, dict):
            ext_dict = extension
        else:
            raise ValueError("extension_schema must be a path string or dictionary")
        
        logger.debug("Merging extension schema into base schema.")
        self.schema = deep_merge(self.schema, ext_dict)

    def _load_plugins(self, plugins: List[str]):
        """Helper to load plugins."""
        for p_path in plugins:
            try:
                func = PluginLoader.load_plugin(p_path)
                self.plugin_functions.append(func)
                logger.info("Loaded plugin: %s", p_path)
            except Exception as e:
                logger.error("Failed to load plugin '%s': %s", p_path, e)
                raise

    def validate(self, data: Dict[str, Any]) -> List[ValidationError]:
        """
        Validates data against the loaded schema and any registered plugins.

        Args:
            data: The dictionary data to validate.

        Returns:
            A list of ValidationError objects. If empty, validation passed.
        """
        errors: List[ValidationError] = []

        # 1. Standard JSON Schema Validation
        try:
            validator = jsonschema.Draft7Validator(self.schema)
            for error in validator.iter_errors(data):
                path_str = ".".join(str(p) for p in error.path) if error.path else "root"
                errors.append(ValidationError(message=error.message, path=path_str))
        except Exception as e:
            logger.error("Schema validation infrastructure failed: %s", e)
            errors.append(ValidationError(message=f"Internal schema error: {e}", path="system"))

        # 2. Custom Plugin Validation
        # Plugins run even if schema fails, to catch business logic errors early.
        for plugin_func in self.plugin_functions:
            try:
                plugin_errors = plugin_func(data)
                if plugin_errors:
                    for msg in plugin_errors:
                        errors.append(ValidationError(message=msg, path="plugin"))
            except Exception as e:
                logger.error("Plugin execution failed: %s", e)
                errors.append(ValidationError(message=f"Plugin crashed: {e}", path="plugin"))
            
        if errors:
            logger.info("Validation failed with %d errors.", len(errors))
        else:
            logger.debug("Validation successful.")
            
        return errors

def validate_metadata(data: Dict[str, Any], schema: Dict[str, Any]) -> List[ValidationError]:
    """
    Helper function for quick one-off validation.

    Args:
        data: The data to validate.
        schema: The schema dictionary.

    Returns:
        A list of ValidationError objects.
    """
    return MetadataValidator(schema_dict=schema).validate(data)
