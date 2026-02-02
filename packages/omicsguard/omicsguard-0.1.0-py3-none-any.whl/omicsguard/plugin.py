import importlib.util
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

class PluginLoader:
    """
    Loads custom validation plugins from Python files.
    """
    
    @staticmethod
    def load_plugin(plugin_path: str) -> Callable[[Dict[str, Any]], List[str]]:
        """
        Loads a python file and expects a 'validate' function.
        
        Args:
            plugin_path: Path to the python file.
            
        Returns:
            The validate function from the module.
            
        Raises:
            ImportError: If the file cannot be loaded.
            AttributeError: If 'validate' function is missing.
        """
        path = Path(plugin_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Plugin file not found: {plugin_path}")
            
        module_name = path.stem
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            raise ImportError(f"Could not load spec for plugin: {plugin_path}")
            
        module = importlib.util.module_from_spec(spec)
        # Avoid polluting sys.modules globally if possible, but for plugins it's often accepted.
        # However, keeping it isolated is cleaner for extensive testing.
        # sys.modules[module_name] = module 
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
             raise ImportError(f"Failed to execute plugin module: {e}") from e
             
        if not hasattr(module, 'validate'):
             raise AttributeError(f"Plugin '{plugin_path}' missing required 'validate(data)' function.")
             
        return module.validate
