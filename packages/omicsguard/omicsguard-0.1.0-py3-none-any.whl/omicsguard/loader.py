import logging
import shutil
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
import yaml

from .utils import load_yaml_or_json

logger = logging.getLogger(__name__)

# Standard Schema Registry: Maps friendly names to canonical URLs
SCHEMA_REGISTRY = {
    # Using JSON Schema draft-07 as a reliable placeholder since the official Phenopacket URL was 404ing during dev.
    "ga4gh-phenopacket-v2": "http://json-schema.org/draft-07/schema",
}

DEFAULT_CACHE_DIR = Path.home() / ".omicsguard" / "schemas"

class SchemaLoader:
    """
    Manages the retrieval and caching of JSON/YAML schemas from local paths, remote URLs, or the internal registry.
    """

    def __init__(self, cache_dir: Optional[Union[str, Path]] = None):
        """
        Args:
            cache_dir: Directory to store cached schemas. Defaults to ~/.omicsguard/schemas.
        """
        self.cache_dir = Path(cache_dir) if cache_dir else DEFAULT_CACHE_DIR
        self._ensure_cache_dir()
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _ensure_cache_dir(self):
        """Ensures the cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning("Failed to create cache directory %s: %s", self.cache_dir, e)

    def resolve_path(self, location: str) -> str:
        """Resolves a registry name to a URL, or returns the location as-is."""
        return SCHEMA_REGISTRY.get(location, location)

    def pull_schema(self, standard_name: str) -> Path:
        """
        Downloads a schema from the registry to the local cache.

        Args:
            standard_name: Key from SCHEMA_REGISTRY.

        Returns:
            Path to the downloaded file.

        Raises:
            ValueError: If standard_name is unknown.
            IOError: If download fails.
        """
        url = SCHEMA_REGISTRY.get(standard_name)
        if not url:
            raise ValueError(f"Unknown standard '{standard_name}'. Available: {list(SCHEMA_REGISTRY.keys())}")

        target_file = self.cache_dir / f"{standard_name}.json"
        logger.info("Pulling schema '%s' from %s", standard_name, url)

        try:
            with requests.get(url, stream=True, timeout=30) as response:
                response.raise_for_status()
                with open(target_file, 'wb') as f:
                    shutil.copyfileobj(response.raw, f)
            
            logger.info("Successfully cached schema at %s", target_file)
            return target_file
        except requests.RequestException as e:
            logger.error("Network error pulling schema '%s': %s", standard_name, e)
            raise IOError(f"Failed to download schema from {url}") from e
        except OSError as e:
            logger.error("File error saving schema '%s': %s", standard_name, e)
            raise IOError(f"Failed to save schema to {target_file}") from e

    def load_schema(self, location: str) -> Dict[str, Any]:
        """
        Loads a schema from the given location (Registry Name, URL, or File Path).
        Transparently handles caching for registry items.
        """
        # 1. Check Memory Cache
        if location in self._memory_cache:
            return self._memory_cache[location]

        # 2. Check Registry / Local Cache
        if location in SCHEMA_REGISTRY:
            cached_path = self.cache_dir / f"{location}.json"
            if cached_path.exists():
                logger.debug("Cache hit for '%s' at %s", location, cached_path)
                schema = self._load_local(cached_path)
            else:
                logger.info("Cache miss for '%s'. Attempting to pull...", location)
                try:
                    path = self.pull_schema(location)
                    schema = self._load_local(path)
                except IOError:
                    # Fallback to direct remote fetch if cache/write fails
                    logger.warning("Pull failed, falling back to ephemeral remote fetch.")
                    schema = self._load_remote(SCHEMA_REGISTRY[location])
        
        # 3. Check URL
        elif self._is_url(location):
            schema = self._load_remote(location)
            
        # 4. Local File
        else:
            schema = self._load_local(location)

        self._memory_cache[location] = schema
        return schema

    def _is_url(self, location: str) -> bool:
        try:
            result = urlparse(location)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    def _load_local(self, path: Union[str, Path]) -> Dict[str, Any]:
        return load_yaml_or_json(path)

    def _load_remote(self, url: str) -> Dict[str, Any]:
        try:
            logger.debug("Fetching remote schema: %s", url)
            with requests.get(url, timeout=15) as response:
                response.raise_for_status()
                # Simple content-type check
                ctype = response.headers.get('Content-Type', '').lower()
                if 'json' in ctype:
                    return response.json()
                return yaml.safe_load(response.text)
        except Exception as e:
            raise ValueError(f"Failed to fetch content from {url}: {e}") from e
