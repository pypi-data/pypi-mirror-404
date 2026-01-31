"""
Workflow metadata utilities and function discovery.
"""

import inspect
import importlib
import pkgutil
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path

from .decorators import WorkflowFunction


def get_workflow_metadata(func: Callable) -> Optional[WorkflowFunction]:
    """
    Extract workflow metadata from a decorated function.
    
    Args:
        func: Function to inspect
        
    Returns:
        WorkflowFunction metadata if present, None otherwise
    """
    return getattr(func, '_workflow_metadata', None)


def is_workflow_function(func: Callable) -> bool:
    """
    Check if a function is decorated as a workflow function.
    
    Args:
        func: Function to check
        
    Returns:
        True if function is a workflow function
    """
    return getattr(func, '_is_workflow_function', False)


class WorkflowRegistry:
    """Registry for discovering and managing workflow functions."""
    
    def __init__(self):
        self._functions: Dict[str, WorkflowFunction] = {}
    
    def register(self, func: Callable) -> None:
        """
        Register a workflow function.
        
        Args:
            func: Decorated workflow function
            
        Raises:
            ValueError: If function is not a workflow function
        """
        if not is_workflow_function(func):
            raise ValueError(f"Function {func.__name__} is not a workflow function")
        
        metadata = get_workflow_metadata(func)
        if metadata:
            self._functions[metadata.name] = metadata
    
    def get(self, name: str) -> Optional[WorkflowFunction]:
        """
        Get workflow function by name.
        
        Args:
            name: Function name
            
        Returns:
            WorkflowFunction if found, None otherwise
        """
        return self._functions.get(name)
    
    def list_functions(self) -> List[WorkflowFunction]:
        """
        List all registered workflow functions.
        
        Returns:
            List of registered functions
        """
        return list(self._functions.values())
    
    def list_names(self) -> List[str]:
        """
        List all registered function names.
        
        Returns:
            List of function names
        """
        return list(self._functions.keys())
    
    def find_by_tag(self, tag: str) -> List[WorkflowFunction]:
        """
        Find functions by tag.
        
        Args:
            tag: Tag to search for
            
        Returns:
            List of functions with the specified tag
        """
        return [
            func for func in self._functions.values()
            if tag in func.tags
        ]
    
    def discover_in_module(self, module_name: str) -> int:
        """
        Discover and register workflow functions in a module.
        
        Args:
            module_name: Name of module to scan
            
        Returns:
            Number of functions discovered
            
        Raises:
            ImportError: If module cannot be imported
        """
        try:
            module = importlib.import_module(module_name)
            count = 0
            
            for name in dir(module):
                obj = getattr(module, name)
                if inspect.isfunction(obj) and is_workflow_function(obj):
                    self.register(obj)
                    count += 1
            
            return count
        except ImportError as e:
            raise ImportError(f"Cannot import module {module_name}: {e}")
    
    def discover_in_package(self, package_name: str) -> int:
        """
        Recursively discover workflow functions in a package.
        
        Args:
            package_name: Name of package to scan
            
        Returns:
            Number of functions discovered
        """
        try:
            package = importlib.import_module(package_name)
            count = 0
            
            # Scan package modules
            if hasattr(package, '__path__'):
                for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
                    full_name = f"{package_name}.{modname}"
                    count += self.discover_in_module(full_name)
            
            return count
        except ImportError as e:
            raise ImportError(f"Cannot import package {package_name}: {e}")
    
    def discover_in_directory(self, directory: str, package_prefix: str = "") -> int:
        """
        Discover workflow functions in Python files within a directory.
        
        Args:
            directory: Directory path to scan
            package_prefix: Package prefix for imports
            
        Returns:
            Number of functions discovered
        """
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")
        
        count = 0
        for py_file in path.glob("**/*.py"):
            if py_file.name.startswith("__"):
                continue
            
            # Convert file path to module name
            relative_path = py_file.relative_to(path)
            module_parts = relative_path.with_suffix("").parts
            
            if package_prefix:
                module_name = f"{package_prefix}.{'.'.join(module_parts)}"
            else:
                module_name = '.'.join(module_parts)
            
            try:
                count += self.discover_in_module(module_name)
            except ImportError:
                # Skip files that can't be imported
                continue
        
        return count
    
    def clear(self) -> None:
        """Clear all registered functions."""
        self._functions.clear()


# Global registry instance
_global_registry = WorkflowRegistry()


def get_global_registry() -> WorkflowRegistry:
    """Get the global workflow function registry."""
    return _global_registry


def register_function(func: Callable) -> None:
    """Register a function in the global registry."""
    _global_registry.register(func)


def discover_functions(module_or_package: str) -> int:
    """Discover functions in the global registry."""
    try:
        return _global_registry.discover_in_module(module_or_package)
    except ImportError:
        return _global_registry.discover_in_package(module_or_package)
