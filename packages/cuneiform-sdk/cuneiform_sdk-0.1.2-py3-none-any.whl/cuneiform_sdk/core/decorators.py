"""
Workflow function decorators and metadata handling.
"""

import functools
import inspect
from typing import Callable, Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class WorkflowFunction:
    """Metadata container for workflow functions."""
    name: str
    description: Optional[str] = None
    version: Optional[str] = None
    tags: Optional[List[str]] = None
    func: Optional[Callable] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


def workflow_function(
    name: Optional[str] = None,
    description: Optional[str] = None,
    version: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Callable:
    """
    Decorator to mark functions as workflow functions with metadata.
    
    Args:
        name: Function name (defaults to actual function name)
        description: Function description
        version: Function version
        tags: List of tags for categorization
        
    Returns:
        Decorated function with workflow metadata
        
    Example:
        @workflow_function(
            name="process_customers",
            description="Process customer data",
            version="1.0.0",
            tags=["customers", "etl"]
        )
        def my_function(context: WorkflowContext, config: dict) -> dict:
            return {"status": "success"}
    """
    def decorator(func: Callable) -> Callable:
        # Use function name if no name provided
        func_name = name or func.__name__
        
        # Create metadata object
        metadata = WorkflowFunction(
            name=func_name,
            description=description,
            version=version,
            tags=tags or [],
            func=func
        )
        
        # Attach metadata to function
        func._workflow_metadata = metadata
        func._is_workflow_function = True
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        # Copy metadata to wrapper
        wrapper._workflow_metadata = metadata
        wrapper._is_workflow_function = True
        
        return wrapper
    
    return decorator
