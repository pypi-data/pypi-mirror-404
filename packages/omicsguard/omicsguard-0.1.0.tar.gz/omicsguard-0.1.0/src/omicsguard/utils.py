import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

import yaml

logger = logging.getLogger(__name__)

def load_yaml_or_json(source: Union[str, Path]) -> Dict[str, Any]:
    """
    Parses JSON or YAML content from a file path or raw string.
    """
    content = ""
    # simple heuristic: if it looks like a path and exists, read it.
    # otherwise, assume it's raw content.
    try:
        path = Path(source)
        # Check max length to avoid stat-ing huge raw strings
        if len(str(source)) < 1024 and path.is_file():
            content = path.read_text(encoding="utf-8")
        else:
            content = str(source)
    except OSError:
        # If filesystem access fails (e.g. name too long), treat as content
        content = str(source)

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            return yaml.safe_load(content) or {}
        except yaml.YAMLError as e:
            raise ValueError("Input is neither valid JSON nor YAML") from e

def deep_merge(base: Dict[str, Any], extension: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merges two dictionaries. 
    Values in 'extension' override those in 'base'.
    
    Args:
        base: The base dictionary.
        extension: The dictionary to merge into the base.
        
    Returns:
        A new dictionary with merged content.
    """
    result = base.copy()
    for key, value in extension.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result
