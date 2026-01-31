"""
Cuneiform SDK

Enterprise-grade Python SDK for data processing workflows with AWS Lambda-style interfaces.
"""

from .core.context import WorkflowContext
from .core.decorators import workflow_function, WorkflowFunction
from .core.metadata import get_workflow_metadata, is_workflow_function, WorkflowRegistry, get_global_registry
from .core.schema import DatasetSchema, ColumnSchema, SchemaManager
from .impl.duckdb_context import WorkflowRunContext
from .exceptions import CuneiformError, ValidationError, DatasetError, ContextError, FunctionRegistrationError

# Import scanner only if needed to avoid circular import issues
def get_scanner():
    """Get scanner components (lazy import)."""
    from .scanner import WorkflowFunctionScanner, FunctionAnalysis, DatasetDependency, SQLOperation
    return WorkflowFunctionScanner, FunctionAnalysis, DatasetDependency, SQLOperation

__version__ = "0.1.0"
__all__ = [
    # Core interfaces
    "WorkflowContext",
    "workflow_function", 
    "WorkflowFunction",
    
    # Metadata and discovery
    "get_workflow_metadata",
    "is_workflow_function",
    "WorkflowRegistry",
    "get_global_registry",
    
    # Schema management
    "DatasetSchema",
    "ColumnSchema", 
    "SchemaManager",
    
    # Implementations
    "WorkflowRunContext",
    
    # Exceptions
    "CuneiformError",
    "ValidationError", 
    "DatasetError",
    "ContextError",
    "FunctionRegistrationError",
    
    # Lazy imports
    "get_scanner"
]

# Auto-discovery helper
def setup_cli():
    """Setup CLI entry point."""
    from .cli import cli
    return cli
