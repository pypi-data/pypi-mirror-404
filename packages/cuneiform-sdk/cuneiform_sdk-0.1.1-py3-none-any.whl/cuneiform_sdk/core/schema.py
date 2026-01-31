"""
Dataset schema validation system.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass
import pandas as pd

from ..exceptions import ValidationError


@dataclass
class ColumnSchema:
    """Schema definition for a dataset column."""
    name: str
    type: str
    nullable: bool = True
    description: Optional[str] = None

    def validate_value(self, value: Any) -> bool:
        """
        Validate a single value against this column schema.
        
        Args:
            value: Value to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if pd.isna(value):
            if not self.nullable:
                raise ValidationError(f"Column {self.name} cannot be null")
            return True

        # Type validation mapping
        type_validators = {
            'int64': lambda x: isinstance(x, (int, pd.Int64Dtype)) or pd.api.types.is_integer_dtype(type(x)),
            'float64': lambda x: isinstance(x, (float, int)) or pd.api.types.is_numeric_dtype(type(x)),
            'string': lambda x: isinstance(x, str),
            'bool': lambda x: isinstance(x, bool),
            'timestamp': lambda x: pd.api.types.is_datetime64_any_dtype(type(x)) or isinstance(x, pd.Timestamp),
            'date': lambda x: pd.api.types.is_datetime64_any_dtype(type(x)) or isinstance(x, (pd.Timestamp, pd.Timedelta)),
        }

        validator = type_validators.get(self.type.lower())
        if validator and not validator(value):
            raise ValidationError(f"Column {self.name} expected {self.type}, got {type(value)}")

        return True


@dataclass
class DatasetSchema:
    """Schema definition for a complete dataset."""
    name: str
    columns: List[ColumnSchema]
    description: Optional[str] = None
    version: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetSchema':
        """
        Create schema from dictionary representation.
        
        Args:
            data: Schema dictionary
            
        Returns:
            DatasetSchema instance
        """
        columns = [
            ColumnSchema(
                name=col['name'],
                type=col['type'],
                nullable=col.get('nullable', True),
                description=col.get('description')
            )
            for col in data.get('columns', [])
        ]

        return cls(
            name=data['name'],
            columns=columns,
            description=data.get('description'),
            version=data.get('version')
        )

    @classmethod
    def from_yaml_file(cls, file_path: Union[str, Path]) -> 'DatasetSchema':
        """
        Load schema from YAML file.
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            DatasetSchema instance
            
        Raises:
            ValidationError: If file cannot be loaded or parsed
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"Schema file {file_path} does not exist")

        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
            return cls.from_dict(data)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML in schema file {file_path}: {e}")
        except Exception as e:
            raise ValidationError(f"Error loading schema file {file_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert schema to dictionary representation.
        
        Returns:
            Schema dictionary
        """
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'columns': [
                {
                    'name': col.name,
                    'type': col.type,
                    'nullable': col.nullable,
                    'description': col.description
                }
                for col in self.columns
            ]
        }

    def to_yaml_file(self, file_path: Union[str, Path]) -> None:
        """
        Save schema to YAML file.
        
        Args:
            file_path: Path to save file
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)

        print(f"📄 Schema saved to: {path.resolve()}")

    def get_column(self, name: str) -> Optional[ColumnSchema]:
        """
        Get column schema by name.
        
        Args:
            name: Column name
            
        Returns:
            ColumnSchema if found, None otherwise
        """
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """
        Validate a pandas DataFrame against this schema.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required columns
        schema_columns = {col.name for col in self.columns}
        df_columns = set(df.columns)

        missing_columns = schema_columns - df_columns
        if missing_columns:
            errors.append(f"Missing columns: {', '.join(missing_columns)}")

        extra_columns = df_columns - schema_columns
        if extra_columns:
            errors.append(f"Unexpected columns: {', '.join(extra_columns)}")

        # Validate column data types and constraints
        for col_schema in self.columns:
            if col_schema.name not in df.columns:
                continue

            series = df[col_schema.name]

            # Check nullable constraint
            if not col_schema.nullable and series.isna().any():
                errors.append(f"Column {col_schema.name} contains null values but is not nullable")

            # Basic type validation
            try:
                self._validate_series_type(series, col_schema)
            except ValidationError as e:
                errors.append(str(e))

        return errors

    def _validate_series_type(self, series: pd.Series, col_schema: ColumnSchema) -> None:
        """Validate pandas Series type against column schema."""
        expected_type = col_schema.type.lower()

        # Skip validation for empty series or all-null series
        if len(series) == 0 or series.isna().all():
            return

        # Get non-null values for type checking
        non_null_series = series.dropna()

        if expected_type == 'int64':
            if not pd.api.types.is_integer_dtype(series.dtype):
                raise ValidationError(f"Column {col_schema.name} expected integer type, got {series.dtype}")
        elif expected_type == 'float64':
            if not pd.api.types.is_numeric_dtype(series.dtype):
                raise ValidationError(f"Column {col_schema.name} expected numeric type, got {series.dtype}")
        elif expected_type == 'string':
            if not pd.api.types.is_object_dtype(series.dtype) and not pd.api.types.is_string_dtype(series.dtype):
                raise ValidationError(f"Column {col_schema.name} expected string type, got {series.dtype}")
        elif expected_type == 'bool':
            if not pd.api.types.is_bool_dtype(series.dtype):
                raise ValidationError(f"Column {col_schema.name} expected boolean type, got {series.dtype}")
        elif expected_type in ['timestamp', 'date']:
            if not pd.api.types.is_datetime64_any_dtype(series.dtype):
                raise ValidationError(f"Column {col_schema.name} expected datetime type, got {series.dtype}")

    @classmethod
    def infer_from_dataframe(cls, df: pd.DataFrame, name: str, description: Optional[str] = None) -> 'DatasetSchema':
        """
        Infer schema from a pandas DataFrame.
        
        Args:
            df: DataFrame to analyze
            name: Dataset name
            description: Optional description
            
        Returns:
            Inferred DatasetSchema
        """
        columns = []

        for col_name in df.columns:
            series = df[col_name]
            dtype = series.dtype
            nullable = bool(series.isna().any())

            # Map pandas dtypes to schema types
            if pd.api.types.is_integer_dtype(dtype):
                col_type = 'int64'
            elif pd.api.types.is_float_dtype(dtype):
                col_type = 'float64'
            elif pd.api.types.is_bool_dtype(dtype):
                col_type = 'bool'
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                col_type = 'timestamp'
            else:
                col_type = 'string'

            columns.append(ColumnSchema(
                name=col_name,
                type=col_type,
                nullable=nullable
            ))

        return cls(
            name=name,
            columns=columns,
            description=description
        )


class SchemaManager:
    """Manager for dataset schemas with file system operations."""

    def __init__(self, schemas_dir: str = "datasets"):
        """
        Initialize schema manager.
        
        Args:
            schemas_dir: Directory to store schema files
        """
        self.schemas_dir = Path(schemas_dir)
        self.schemas_dir.mkdir(exist_ok=True)
        self._cache: Dict[str, DatasetSchema] = {}

    def save_schema(self, schema: DatasetSchema) -> Path:
        """
        Save schema to file system.
        
        Args:
            schema: Schema to save
            
        Returns:
            Path to saved file
        """
        file_path = self.schemas_dir / f"{schema.name}.yml"
        schema.to_yaml_file(file_path)
        self._cache[schema.name] = schema
        return file_path

    def load_schema(self, name: str) -> DatasetSchema:
        """
        Load schema from file system.
        
        Args:
            name: Dataset name
            
        Returns:
            Loaded schema
            
        Raises:
            ValidationError: If schema file doesn't exist
        """
        if name in self._cache:
            return self._cache[name]

        file_path = self.schemas_dir / f"{name}.yml"
        if not file_path.exists():
            raise ValidationError(f"Schema file for dataset '{name}' not found")

        schema = DatasetSchema.from_yaml_file(file_path)
        self._cache[name] = schema
        return schema

    def list_schemas(self) -> List[str]:
        """
        List all available schema names.
        
        Returns:
            List of schema names
        """
        schema_files = list(self.schemas_dir.glob("*.yml"))
        return [f.stem for f in schema_files]

    def delete_schema(self, name: str) -> bool:
        """
        Delete schema from file system.
        
        Args:
            name: Schema name to delete
            
        Returns:
            True if deleted, False if not found
        """
        file_path = self.schemas_dir / f"{name}.yml"
        if file_path.exists():
            file_path.unlink()
            self._cache.pop(name, None)
            return True
        return False

    def validate_dataset_file(self, name: str, file_path: Union[str, Path]) -> List[str]:
        """
        Validate a dataset file against its schema.
        
        Args:
            name: Dataset name
            file_path: Path to dataset file
            
        Returns:
            List of validation errors
        """
        try:
            schema = self.load_schema(name)
        except ValidationError:
            return [f"No schema found for dataset '{name}'"]

        # Load file based on extension
        path = Path(file_path)
        if not path.exists():
            return [f"Dataset file '{file_path}' not found"]

        try:
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(path)
            elif path.suffix.lower() in ['.parquet', '.pq']:
                df = pd.read_parquet(path)
            else:
                return [f"Unsupported file format: {path.suffix}"]

            return schema.validate_dataframe(df)
        except Exception as e:
            return [f"Error reading dataset file: {e}"]

    def create_schema_from_file(self, name: str, file_path: Union[str, Path], description: Optional[str] = None) -> DatasetSchema:
        """
        Create and save schema by inferring from a dataset file.
        
        Args:
            name: Dataset name
            file_path: Path to dataset file
            description: Optional description
            
        Returns:
            Created schema
            
        Raises:
            ValidationError: If file cannot be read
        """
        path = Path(file_path)
        if not path.exists():
            raise ValidationError(f"Dataset file '{file_path}' not found")

        try:
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(path)
            elif path.suffix.lower() in ['.parquet', '.pq']:
                df = pd.read_parquet(path)
            else:
                raise ValidationError(f"Unsupported file format: {path.suffix}")

            schema = DatasetSchema.infer_from_dataframe(df, name, description)
            self.save_schema(schema)
            return schema
        except Exception as e:
            raise ValidationError(f"Error creating schema from file: {e}")
