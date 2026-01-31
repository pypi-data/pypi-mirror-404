"""
Abstract WorkflowContext interface.

Defines the contract for workflow execution contexts with clear separation 
between interface and implementation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd

    
class WorkflowContext(ABC):
    """
    Abstract interface for workflow execution context.
    
    Provides dataset access, SQL execution, and I/O operations
    in a platform-agnostic way.
    """
    
    @abstractmethod
    def sql(self, query: str) -> Any:
        """
        Execute SQL query on loaded datasets.
        
        Args:
            query: SQL query string
            
        Returns:
            Query result object
        """
        pass
    
    @abstractmethod
    def table(self, table_name: str) -> Any:
        """
        Get reference to loaded table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table reference object
        """
        pass
    
    @abstractmethod
    def list_tables(self) -> List[str]:
        """
        List all available tables in the context.
        
        Returns:
            List of table names
        """
        pass
    
    @abstractmethod
    def load_dataset(self, table_name: str, file_path: Optional[str] = None) -> None:
        """
        Load dataset into context as a table.
        
        Args:
            table_name: Name to assign to the loaded table
            file_path: Optional path override for the dataset file
        """
        pass
    
    @abstractmethod
    def save_dataset(self, table_name: str, format: str = "parquet") -> Dict[str, Any]:
        """
        Save table as output dataset.
        
        Args:
            table_name: Name of table to save
            format: Output format (parquet, csv, etc.)
            
        Returns:
            Dictionary with 'output_path' and 'output_schema' keys
        """
        pass
    
    @abstractmethod
    def save_datasets(
        self, 
        table_names: List[str], 
        format: str = "parquet"
    ) -> Dict[str, str]:
        """
        Save multiple tables as output datasets.
        
        Args:
            table_names: List of table names to save
            format: Output format
            
        Returns:
            Mapping of table name to output path
        """
        pass
    
    @abstractmethod
    def get_dataframe(self, table_name: str, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Get dataset as pandas DataFrame, loading it first if not already loaded.
        
        Args:
            table_name: Name of the dataset/table
            file_path: Optional path override for the dataset file
            
        Returns:
            Pandas DataFrame
        """
        pass
    
    @abstractmethod
    def to_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        Convert table to pandas DataFrame.
        
        Args:
            table_name: Name of table to convert
            
        Returns:
            Pandas DataFrame
        """
        pass
    
    @abstractmethod
    def from_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Create table from pandas DataFrame.
        
        Args:
            df: Pandas DataFrame
            table_name: Name for the new table
        """
        pass
    
    @abstractmethod
    def set_variable(self, name: str, value: Any) -> None:
        """
        Set output variable.
        
        Args:
            name: Variable name
            value: Variable value
        """
        pass
    
    @abstractmethod
    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set multiple output variables.
        
        Args:
            variables: Dictionary of variable name/value pairs
        """
        pass
    
    @abstractmethod
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get input variable.
        
        Args:
            name: Variable name
            default: Default value if variable not found
            
        Returns:
            Variable value
        """
        pass
    
    @abstractmethod
    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message.
        
        Args:
            message: Message to log
            level: Log level (INFO, WARNING, ERROR, etc.)
        """
        pass