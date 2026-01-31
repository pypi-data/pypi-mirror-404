"""
DuckDB implementation of WorkflowContext.

Provides a robust, SQL-based data processing environment using DuckDB
as the execution engine with comprehensive error handling and logging.
"""

import os
import sys
import logging
import duckdb
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from kestra import Kestra

from ..core.context import WorkflowContext
from ..core.schema import SchemaManager
from ..exceptions import ContextError, DatasetError, ValidationError

# Common dataset file extensions in priority order (CSV first)
DATASET_EXTENSIONS = ['.csv', '.parquet', '.pq']


class WorkflowRunContext(WorkflowContext):
    """
    DuckDB-based implementation of WorkflowContext.

    Features:
    - In-memory SQL execution using DuckDB
    - Automatic dataset loading and validation
    - Schema management integration
    - Comprehensive error handling
    - Structured logging
    """

    def __init__(
            self,
            data_dir: str = "data",
            output_dir: str = "output",
            schemas_dir: str = "datasets",
            log_level: str = "INFO",
            connection: Optional[object] = None
    ):
        """
        Initialize workflow run context.

        Args:
            data_dir: Directory containing input datasets
            output_dir: Directory for output datasets
            schemas_dir: Directory containing schema files
            log_level: Logging level
            connection: Optional existing DuckDB connection
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.schemas_dir = Path(schemas_dir)

        # Create directories
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.schemas_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging(log_level)

        # Initialize DuckDB connection
        self.conn = connection or duckdb.connect(':memory:')

        # Initialize schema manager
        self.schema_manager = SchemaManager(str(self.schemas_dir))

        # Track loaded tables and variables
        self._loaded_tables: Dict[str, str] = {}  # table_name -> file_path
        self._variables: Dict[str, Any] = {}

        self.log("WorkflowRunContext initialized", "INFO")

    def _setup_logging(self, level: str) -> None:
        """Setup structured logging with separate handlers for INFO and ERROR."""
        self.logger = logging.getLogger(f"cuneiform.{self.__class__.__name__}")
        self.logger.setLevel(getattr(logging, level.upper()))

        if not self.logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            # Handler for INFO, DEBUG, and WARNING (stdout)
            info_handler = logging.StreamHandler(sys.stdout)
            info_handler.setLevel(logging.DEBUG)
            info_handler.setFormatter(formatter)
            info_handler.addFilter(lambda record: record.levelno < logging.ERROR)

            # Handler for ERROR and above (stderr)
            error_handler = logging.StreamHandler(sys.stderr)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)

            self.logger.addHandler(info_handler)
            self.logger.addHandler(error_handler)

    def sql(self, query: str):
        """
        Execute SQL query on loaded datasets.

        Args:
            query: SQL query string

        Returns:
            DuckDB query result

        Raises:
            ContextError: If query execution fails
        """
        try:
            self.log(f"Executing SQL: {query[:100]}{'...' if len(query) > 100 else ''}")
            result = self.conn.execute(query)
            self.log("SQL execution completed successfully")
            return result
        except Exception as e:
            error_msg = f"SQL execution failed: {e}"
            self.log(error_msg, "ERROR")
            raise ContextError(error_msg, error_code="SQL_EXECUTION_ERROR")

    def table(self, table_name: str):
        """
        Get reference to loaded table.

        Args:
            table_name: Name of the table

        Returns:
            DuckDB table relation

        Raises:
            ContextError: If table not found
        """
        if table_name not in self._loaded_tables:
            raise ContextError(
                f"Table '{table_name}' not loaded. Available tables: {list(self._loaded_tables.keys())}",
                error_code="TABLE_NOT_FOUND"
            )

        try:
            return self.conn.table(table_name)
        except Exception as e:
            raise ContextError(f"Failed to get table reference: {e}", error_code="TABLE_ACCESS_ERROR")

    def list_tables(self) -> List[str]:
        """
        List all available tables in the context.

        Returns:
            List of table names
        """
        return list(self._loaded_tables.keys())

    def load_dataset(self, table_name: str, file_path: Optional[str] = None) -> None:
        """
        Load dataset into context as a table.

        Args:
            table_name: Name to assign to the loaded table
            file_path: Optional path override for the dataset file

        Raises:
            DatasetError: If dataset loading fails
        """
        # Check if table is already loaded
        if table_name in self._loaded_tables:
            self.log(f"Dataset '{table_name}' already loaded, skipping")
            return

        try:
            # Determine file path
            if file_path:
                data_path = Path(file_path)
            else:
                # Look for dataset in data directory
                data_path = self._find_dataset_file(table_name)

            if not data_path.exists():
                raise DatasetError(f"Dataset file not found: {data_path}")

            self.log(f"Loading dataset '{table_name}' from {data_path}")

            # Validate against schema if available
            self._validate_dataset(table_name, data_path)

            # Load based on file type
            if data_path.suffix.lower() == '.csv':
                self._load_csv(table_name, data_path)
            elif data_path.suffix.lower() in ['.parquet', '.pq']:
                self._load_parquet(table_name, data_path)
            else:
                raise DatasetError(f"Unsupported file format: {data_path.suffix}")

            self._loaded_tables[table_name] = str(data_path)
            self.log(f"Successfully loaded dataset '{table_name}'")

        except Exception as e:
            error_msg = f"Failed to load dataset '{table_name}': {e}"
            self.log(error_msg, "ERROR")
            raise DatasetError(error_msg, error_code="DATASET_LOAD_ERROR")

    def _find_dataset_file(self, table_name: str) -> Path:
        """Find dataset file in data or output directories."""
        # Try different extensions in both data and output directories
        for directory in [self.data_dir, self.output_dir]:
            for ext in DATASET_EXTENSIONS:
                # Try direct match
                path = directory / f"{table_name}{ext}"
                if path.exists():
                    return path

                # Try in subdirectory
                subdir_path = directory / table_name / f"{table_name}{ext}"
                if subdir_path.exists():
                    return subdir_path

                # Try with timestamp pattern (for saved datasets)
                for file in directory.glob(f"{table_name}_*{ext}"):
                    if file.exists():
                        return file

        # Default to CSV if not found (since we prioritize CSV)
        return self.data_dir / f"{table_name}.csv"

    def _validate_dataset(self, table_name: str, file_path: Path) -> None:
        """Validate dataset against schema if available."""
        # Skip validation for derived datasets (those in output directory)
        if self.output_dir in file_path.parents or file_path.parent == self.output_dir:
            self.log(f"Skipping schema validation for derived dataset '{table_name}'")
            return

        try:
            errors = self.schema_manager.validate_dataset_file(table_name, file_path)
            if errors:
                self.log(f"Schema validation warnings for '{table_name}': {'; '.join(errors)}", "WARNING")
        except ValidationError:
            # No schema available - skip validation
            self.log(f"No schema found for '{table_name}' - skipping validation", "DEBUG")

    def _load_csv(self, table_name: str, file_path: Path) -> None:
        """Load CSV file into DuckDB."""
        # Create schema if table name contains dots
        if '.' in table_name:
            schema_name = table_name.split('.')[0]
            self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

        query = f"""
        CREATE OR REPLACE TABLE {table_name} AS 
        SELECT * FROM read_csv_auto('{file_path}')
        """
        self.conn.execute(query)

    def _load_parquet(self, table_name: str, file_path: Path) -> None:
        """Load Parquet file into DuckDB."""
        # Create schema if table name contains dots
        if '.' in table_name:
            schema_name = table_name.split('.')[0]
            self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

        query = f"""
        CREATE OR REPLACE TABLE {table_name} AS 
        SELECT * FROM read_parquet('{file_path}')
        """
        self.conn.execute(query)

    def save_dataset(self, table_name: str, format: str = "parquet") -> Dict[str, Any]:
        """
        Save table as output dataset.

        Args:
            table_name: Name of table to save
            format: Output format (parquet, csv)

        Returns:
            Dictionary with 'output_path' and 'output_schema' keys

        Raises:
            ContextError: If save operation fails
        """
        if table_name not in self._loaded_tables and not self._table_exists(table_name):
            raise ContextError(f"Table '{table_name}' not found", error_code="TABLE_NOT_FOUND")

        try:
            # Generate output file path
            if format.lower() == "csv":
                output_path = self.output_dir / f"{table_name}.csv"
                query = f"COPY (SELECT * FROM {table_name}) TO '{output_path}' (FORMAT CSV, HEADER)"
            else:  # Default to parquet
                output_path = self.output_dir / f"{table_name}.parquet"
                query = f"COPY (SELECT * FROM {table_name}) TO '{output_path}' (FORMAT PARQUET)"

            self.log(f"Saving table '{table_name}' to {output_path}")
            self.conn.execute(query)

            # Generate schema from saved file
            output_schema = self._generate_schema_from_file(table_name, output_path)

            # Save schema to JSON file
            schema_path = self.output_dir / f"{table_name}_schema.json"
            import json
            with open(schema_path, 'w') as f:
                json.dump(output_schema, f, indent=2)

            self.log(f"Successfully saved dataset to {output_path} and schema to {schema_path}")
            return {
                "output_path": str(output_path),
                "output_schema": output_schema
            }

        except Exception as e:
            error_msg = f"Failed to save dataset '{table_name}': {e}"
            self.log(error_msg, "ERROR")
            raise ContextError(error_msg, error_code="DATASET_SAVE_ERROR")

    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists in DuckDB."""
        try:
            # Use information_schema to check table existence
            if '.' in table_name:
                schema_name, table_only = table_name.split('.', 1)
                query = f"SELECT 1 FROM information_schema.tables WHERE table_schema = '{schema_name}' AND table_name = '{table_only}'"
            else:
                query = f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'"

            result = self.conn.execute(query).fetchone()
            return result is not None
        except:
            # Fallback to direct query
            try:
                self.conn.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
                return True
            except:
                return False

    def _generate_schema_from_file(self, table_name: str, file_path: Path) -> Dict[str, Any]:
        """Generate CanonicalSchema from parquet file."""
        try:
            # Get table schema from DuckDB
            schema_query = f"DESCRIBE {table_name}"
            schema_result = self.conn.execute(schema_query).fetchall()

            fields = []
            for row in schema_result:
                column_name = row[0]
                column_type = row[1]
                nullable = row[2] == 'YES' if len(row) > 2 else True

                # Map DuckDB types to canonical types
                canonical_type = self._map_duckdb_type_to_canonical(column_type)

                field = {
                    "name": column_name,
                    "originalName": column_name,
                    "type": canonical_type,
                    "nullable": nullable
                }
                fields.append(field)

            schema = {
                "name": table_name,
                "fields": fields,
                "options": {},
                "description": f"Generated schema for {table_name}"
            }

            self.log(f"Generated schema for '{table_name}' with {len(fields)} fields")
            return schema

        except Exception as e:
            self.log(f"Failed to generate schema: {e}", "WARNING")
            return {
                "name": table_name,
                "fields": [],
                "options": {},
                "description": f"Error generating schema for {table_name}"
            }

    def _map_duckdb_type_to_canonical(self, duckdb_type: str) -> str:
        """Map DuckDB data types to canonical types."""
        type_mapping = {
            'VARCHAR': 'string',
            'TEXT': 'string',
            'BOOLEAN': 'boolean',
            'INTEGER': 'int',
            'BIGINT': 'long',
            'DOUBLE': 'double',
            'REAL': 'float',
            'TIMESTAMP': 'timestamp',
            'DATE': 'date',
            'TIME': 'time'
        }

        # Handle array types
        if duckdb_type.endswith('[]'):
            return 'array'

        # Get base type (remove precision/scale info)
        base_type = duckdb_type.split('(')[0].upper()
        return type_mapping.get(base_type, 'string')

    def save_datasets(self, table_names: List[str], format: str = "parquet") -> Dict[str, str]:
        """
        Save multiple tables as output datasets.

        Args:
            table_names: List of table names to save
            format: Output format

        Returns:
            Mapping of table name to output path
        """
        results = {}
        for table_name in table_names:
            try:
                output_path = self.save_dataset(table_name, format)
                results[table_name] = output_path
            except Exception as e:
                self.log(f"Failed to save table '{table_name}': {e}", "ERROR")
                results[table_name] = f"ERROR: {e}"

        return results

    def get_dataframe(self, table_name: str, file_path: Optional[str] = None) -> pd.DataFrame:
        """
        Get dataset as pandas DataFrame, loading it first if not already loaded.

        Args:
            table_name: Name of the dataset/table
            file_path: Optional path override for the dataset file

        Returns:
            Pandas DataFrame

        Raises:
            DatasetError: If dataset loading fails
            ContextError: If conversion fails
        """
        # Load dataset if not already loaded
        if table_name not in self._loaded_tables:
            self.load_dataset(table_name, file_path)

        return self.to_dataframe(table_name)

    def to_dataframe(self, table_name: str) -> pd.DataFrame:
        """
        Convert table to pandas DataFrame.

        Args:
            table_name: Name of table to convert

        Returns:
            Pandas DataFrame

        Raises:
            ContextError: If conversion fails
        """
        if table_name not in self._loaded_tables and not self._table_exists(table_name):
            raise ContextError(f"Table '{table_name}' not found", error_code="TABLE_NOT_FOUND")

        try:
            self.log(f"Converting table '{table_name}' to DataFrame")
            result = self.conn.execute(f"SELECT * FROM {table_name}").fetchdf()
            self.log(f"Successfully converted table '{table_name}' ({len(result)} rows)")
            return result
        except Exception as e:
            error_msg = f"Failed to convert table to DataFrame: {e}"
            self.log(error_msg, "ERROR")
            raise ContextError(error_msg, error_code="DATAFRAME_CONVERSION_ERROR")

    def from_dataframe(self, df: pd.DataFrame, table_name: str) -> None:
        """
        Create table from pandas DataFrame.

        Args:
            df: Pandas DataFrame
            table_name: Name for the new table

        Raises:
            ContextError: If table creation fails
        """
        try:
            self.log(f"Creating table '{table_name}' from DataFrame ({len(df)} rows)")

            if '.' in table_name:
                # For schema-qualified names, create schema and use CREATE TABLE AS
                schema_name = table_name.split('.')[0]
                self.conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

                # conn.register() doesn't work with schema-qualified table names. DuckDB's register() method creates tables in the default schema only.
                # We need to use a different approach for schema-qualified tables
                # Register with a temporary name first
                temp_name = f"temp_{table_name.replace('.', '_')}"
                self.conn.register(temp_name, df)

                # Create the schema-qualified table
                self.conn.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM {temp_name}")

                # Drop the temporary view (register creates a view, not table)
                self.conn.execute(f"DROP VIEW {temp_name}")
            else:
                # For simple names, use register directly
                self.conn.register(table_name, df)

            self._loaded_tables[table_name] = f"dataframe_{table_name}"
            self.log(f"Successfully created table '{table_name}'")
        except Exception as e:
            error_msg = f"Failed to create table from DataFrame: {e}"
            self.log(error_msg, "ERROR")
            raise ContextError(error_msg, error_code="TABLE_CREATION_ERROR")

    def set_variable(self, name: str, value: Any) -> None:
        """
        Set output variable.

        Args:
            name: Variable name
            value: Variable value
        """
        self._variables[name] = value

        # Set Kestra variable if running in Kestra environment
        try:
            Kestra.outputs({name: value})
        except ImportError:
            # Kestra not available, skip
            pass
        except Exception as e:
            self.log(f"Warning: Could not set Kestra variable: {e}", "WARNING")

        self.log(f"Set variable '{name}' = {value}")

    def set_variables(self, variables: Dict[str, Any]) -> None:
        """
        Set multiple output variables.

        Args:
            variables: Dictionary of variable name/value pairs
        """
        self._variables.update(variables)

        # Set Kestra variables if running in Kestra environment
        try:
            Kestra.outputs(variables)
        except ImportError:
            # Kestra not available, skip
            pass
        except Exception as e:
            self.log(f"Warning: Could not set Kestra variables: {e}", "WARNING")

        for name, value in variables.items():
            self.log(f"Set variable '{name}' = {value}")

    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        Get input variable.

        Args:
            name: Variable name
            default: Default value if variable not found

        Returns:
            Variable value
        """
        value = self._variables.get(name, default)
        self.log(f"Retrieved variable '{name}' = {value}")
        return value

    def log(self, message: str, level: str = "INFO") -> None:
        """
        Log a message.

        Args:
            message: Message to log
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)

    def get_context_info(self) -> Dict[str, Any]:
        """
        Get information about the current context state.

        Returns:
            Dictionary with context information
        """
        return {
            "loaded_tables": list(self._loaded_tables.keys()),
            "table_details": {
                name: {
                    "source_file": path,
                    "row_count": self._get_table_row_count(name)
                }
                for name, path in self._loaded_tables.items()
            },
            "variables": dict(self._variables),
            "data_dir": str(self.data_dir),
            "output_dir": str(self.output_dir),
            "schemas_dir": str(self.schemas_dir)
        }

    def _get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            result = self.conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
            return result[0] if result else 0
        except:
            return -1



    def close(self) -> None:
        """Close the DuckDB connection and cleanup resources."""
        try:
            if self.conn:
                self.conn.close()
                self.log("DuckDB connection closed")
        except Exception as e:
            self.log(f"Error closing connection: {e}", "WARNING")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
