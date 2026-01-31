"""
Cuneiform SDK Core

Core components for workflow function management and dataset processing.
"""

from .context import WorkflowContext
from .decorators import workflow_function, WorkflowFunction
from .metadata import (
    get_workflow_metadata, 
    is_workflow_function, 
    WorkflowRegistry, 
    get_global_registry,
    register_function,
    discover_functions
)
from .schema import (
    DatasetSchema, 
    ColumnSchema, 
    SchemaManager
)

__all__ = [
    # Context
    "WorkflowContext",
    
    # Decorators and metadata
    "workflow_function",
    "WorkflowFunction", 
    "get_workflow_metadata",
    "is_workflow_function",
    "WorkflowRegistry",
    "get_global_registry",
    "register_function", 
    "discover_functions",
    
    # Schema
    "DatasetSchema",
    "ColumnSchema",
    "SchemaManager"
]
