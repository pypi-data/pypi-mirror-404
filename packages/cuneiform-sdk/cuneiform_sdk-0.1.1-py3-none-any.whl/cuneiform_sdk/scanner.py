"""
Repository scanner for workflow function analysis and dependency discovery.

Uses AST parsing and SQLGlot for comprehensive analysis of workflow functions,
their dataset dependencies, and schema requirements.
"""

import ast
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import importlib.util
import inspect

import sqlglot
from sqlglot import parse_one, expressions
from sqlglot.expressions import Select, Create, Insert, Update, Table, CTE

try:
    from .core.metadata import get_workflow_metadata, is_workflow_function
    from .core.schema import SchemaManager, DatasetSchema
    from .exceptions import ValidationError
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))

    from core.metadata import get_workflow_metadata, is_workflow_function
    from core.schema import SchemaManager, DatasetSchema
    from exceptions import ValidationError


@dataclass
class DatasetDependency:
    """Represents a dataset dependency for a workflow function."""
    name: str
    type: str  # 'input' or 'output'
    source: str  # How it was detected (e.g., 'context.load_dataset', 'SQL FROM clause')
    line: int
    required: bool = True
    exists: Optional[bool] = None
    schema_valid: Optional[bool] = None
    format: Optional[str] = None


@dataclass
class SQLOperation:
    """Represents a SQL operation found in workflow function."""
    sql: str
    line: int
    inputs: List[str]
    outputs: List[str]
    operation_type: str
    error: Optional[str] = None


@dataclass
class FunctionAnalysis:
    """Complete analysis result for a workflow function."""
    name: str
    file_path: str
    line: int
    description: Optional[str]
    version: Optional[str]
    tags: List[str]
    signature: str
    dependencies: List[DatasetDependency]
    sql_operations: List[SQLOperation]
    issues: List[Dict[str, Any]]


class SQLAnalyzer:
    """SQLGlot-based SQL query analyzer for extracting table dependencies."""

    def __init__(self, dialect: str = "duckdb"):
        self.dialect = dialect

    def analyze_sql_query(self, sql_query: str, line: int = 0) -> SQLOperation:
        """
        Parse SQL using SQLGlot to extract table dependencies.

        Args:
            sql_query: SQL query string
            line: Line number where SQL appears

        Returns:
            SQLOperation with inputs, outputs, and metadata
        """
        try:
            # Clean and prepare SQL
            sql_clean = sql_query.strip()
            if not sql_clean:
                return SQLOperation(sql_query, line, [], [], "empty")

            # Parse with SQLGlot
            parsed = parse_one(sql_clean, dialect=self.dialect)
            if not parsed:
                return SQLOperation(sql_query, line, [], [], "parse_failed", "Could not parse SQL")

            inputs = self._extract_input_tables(parsed)
            outputs = self._extract_output_tables(parsed)
            operation_type = self._classify_operation(parsed)

            return SQLOperation(
                sql=sql_query,
                line=line,
                inputs=list(inputs),
                outputs=list(outputs),
                operation_type=operation_type
            )

        except Exception as e:
            return SQLOperation(
                sql=sql_query,
                line=line,
                inputs=[],
                outputs=[],
                operation_type="error",
                error=str(e)
            )

    def _extract_input_tables(self, parsed) -> Set[str]:
        """Extract all tables being read from."""
        inputs = set()

        # Get CTE names to exclude them from inputs
        cte_names = set()
        for cte in parsed.find_all(CTE):
            if hasattr(cte, 'args') and 'alias' in cte.args:
                alias_node = cte.args['alias']
                if hasattr(alias_node, 'this'):
                    # Convert Identifier to string
                    cte_name = str(alias_node.this) if hasattr(alias_node.this, '__str__') else alias_node.this
                    cte_names.add(cte_name)

        # Extract inputs from the main query (excluding CTEs)
        if hasattr(parsed, 'find'):
            # For CREATE TABLE AS SELECT, get inputs from the SELECT part
            if isinstance(parsed, Create) and hasattr(parsed, 'expression'):
                select_part = parsed.expression
                if select_part:
                    inputs.update(self._get_tables_from_select(select_part, cte_names))
            elif isinstance(parsed, Select):
                inputs.update(self._get_tables_from_select(parsed, cte_names))

        # Handle CTEs - extract inputs from their internal queries
        for cte in parsed.find_all(CTE):
            if hasattr(cte, 'this') and cte.this:
                inputs.update(self._get_tables_from_select(cte.this, cte_names))

        return inputs

    def _get_tables_from_select(self, select_node, cte_names: Set[str]) -> Set[str]:
        """Extract table names from a SELECT statement, excluding CTE names."""
        tables = set()

        # Get tables from FROM clause
        if hasattr(select_node, 'find_all'):
            for table in select_node.find_all(Table):
                table_name = str(table.name) if hasattr(table.name, '__str__') else table.name
                if table_name not in cte_names:
                    tables.add(table_name)

        return tables

    def _extract_output_tables(self, parsed) -> Set[str]:
        """Extract all tables being created or modified."""
        outputs = set()

        # CREATE TABLE statements
        if isinstance(parsed, Create):
            if parsed.this and hasattr(parsed.this, 'name'):
                outputs.add(parsed.this.name)

        # INSERT INTO statements
        elif isinstance(parsed, Insert):
            if parsed.this and hasattr(parsed.this, 'name'):
                outputs.add(parsed.this.name)

        # UPDATE statements
        elif isinstance(parsed, Update):
            if parsed.this and hasattr(parsed.this, 'name'):
                outputs.add(parsed.this.name)

        return outputs

    def _classify_operation(self, parsed) -> str:
        """Classify the type of SQL operation."""
        if isinstance(parsed, Create):
            return "create_table"
        elif isinstance(parsed, Insert):
            return "insert"
        elif isinstance(parsed, Update):
            return "update"
        elif isinstance(parsed, Select):
            return "select"
        else:
            return type(parsed).__name__.lower()


class WorkflowFunctionScanner:
    """Scanner for discovering and analyzing workflow functions in Python code."""

    def __init__(self, data_dir: str = "data", schemas_dir: str = "datasets", infer_schema: bool = False):
        self.data_dir = Path(data_dir)
        self.schemas_dir = Path(schemas_dir)
        self.output_data_dir = Path("examples/output")
        self.output_schemas_dir = Path("examples/output")
        self.infer_schema = infer_schema
        self.sql_analyzer = SQLAnalyzer()
        self.schema_manager = SchemaManager(str(schemas_dir))

    def scan_file(self, file_path, all_functions: List[FunctionAnalysis] = None) -> List[FunctionAnalysis]:
        """
        Scan a Python file for workflow functions and analyze dependencies.

        Args:
            file_path: Path to Python file (string or Path object)
            all_functions: List of all functions for cross-function validation

        Returns:
            List of function analyses
        """
        # Convert to Path object if it's a string
        if isinstance(file_path, str):
            file_path = Path(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source)
            functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if function has workflow decorator
                    if self._has_workflow_decorator(node):
                        analysis = self._analyze_function(node, file_path, source, all_functions)
                        functions.append(analysis)

            return functions

        except Exception as e:
            print(f"Error scanning file {file_path}: {e}")
            return []

    def scan_directory(self, directory) -> List[FunctionAnalysis]:
        """
        Recursively scan directory for workflow functions.

        Args:
            directory: Directory to scan (string or Path object)

        Returns:
            List of all function analyses found
        """
        # Convert to Path object if it's a string
        if isinstance(directory, str):
            directory = Path(directory)

        # First pass: collect all functions without cross-validation
        all_functions = []
        py_files = []

        for py_file in directory.rglob("*.py"):
            # Skip __pycache__ and test files
            if "__pycache__" in str(py_file) or py_file.name.startswith("test_"):
                continue
            py_files.append(py_file)
            all_functions.extend(self.scan_file(py_file))

        # Second pass: re-analyze with cross-function validation
        final_functions = []
        for py_file in py_files:
            final_functions.extend(self.scan_file(py_file, all_functions))

        return final_functions

    def _has_workflow_decorator(self, func_node: ast.FunctionDef) -> bool:
        """Check if function has @workflow or @workflow_function decorator."""
        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Name):
                if decorator.id in ('workflow', 'workflow_function'):
                    return True
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                if decorator.func.id in ('workflow', 'workflow_function'):
                    return True
        return False

    def _analyze_function(self, func_node: ast.FunctionDef, file_path: Path, source: str, all_functions: List[FunctionAnalysis] = None) -> FunctionAnalysis:
        """
        Analyze a workflow function for dependencies and metadata.

        Args:
            func_node: AST function node
            file_path: Path to source file
            source: Source code string
            all_functions: List of all functions for cross-function validation

        Returns:
            Complete function analysis
        """
        # Extract basic metadata
        name = func_node.name
        line = func_node.lineno

        # Get decorator metadata
        metadata = self._extract_decorator_metadata(func_node)

        # Extract function signature
        signature = self._extract_signature(func_node)

        # Find dataset dependencies and from_dataframe calls
        dependencies, from_dataframe_calls = self._extract_dependencies(func_node)

        # Analyze SQL operations
        sql_operations = self._extract_sql_operations(func_node)

        # Add SQL-derived dependencies (avoid duplicates)
        for sql_op in sql_operations:
            for input_table in sql_op.inputs:
                # Check if this dependency already exists
                existing = any(d.name == input_table and d.type == "input" for d in dependencies)
                if not existing:
                    dependencies.append(DatasetDependency(
                        name=input_table,
                        type="input",
                        source=f"SQL {sql_op.operation_type}",
                        line=sql_op.line
                    ))
            for output_table in sql_op.outputs:
                # Check if this dependency already exists
                existing = any(d.name == output_table and d.type == "output" for d in dependencies)
                if not existing:
                    dependencies.append(DatasetDependency(
                        name=output_table,
                        type="output",
                        source=f"SQL {sql_op.operation_type}",
                        line=sql_op.line
                    ))

        # Validate dependencies (pass all_functions for cross-function validation)
        issues = self._validate_dependencies(dependencies, all_functions)

        analysis = FunctionAnalysis(
            name=name,
            file_path=str(Path(file_path).resolve()),
            line=line,
            description=metadata.get('description'),
            version=metadata.get('version'),
            tags=metadata.get('tags', []),
            signature=signature,
            dependencies=dependencies,
            sql_operations=sql_operations,
            issues=issues
        )

        # Store from_dataframe calls for schema inference
        analysis._from_dataframe_calls = from_dataframe_calls

        return analysis

    def _extract_decorator_metadata(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Extract metadata from @workflow_function decorator."""
        metadata = {}

        for decorator in func_node.decorator_list:
            if isinstance(decorator, ast.Call):
                if (isinstance(decorator.func, ast.Name) and
                        decorator.func.id in ('workflow', 'workflow_function')):

                    # Extract keyword arguments
                    for keyword in decorator.keywords:
                        if keyword.arg == 'name' and isinstance(keyword.value, ast.Constant):
                            metadata['name'] = keyword.value.value
                        elif keyword.arg == 'description' and isinstance(keyword.value, ast.Constant):
                            metadata['description'] = keyword.value.value
                        elif keyword.arg == 'version' and isinstance(keyword.value, ast.Constant):
                            metadata['version'] = keyword.value.value
                        elif keyword.arg == 'tags' and isinstance(keyword.value, ast.List):
                            tags = []
                            for elt in keyword.value.elts:
                                if isinstance(elt, ast.Constant):
                                    tags.append(elt.value)
                            metadata['tags'] = tags

        return metadata

    def _extract_signature(self, func_node: ast.FunctionDef) -> str:
        """Extract function signature as string."""
        args = []
        for arg in func_node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                if isinstance(arg.annotation, ast.Name):
                    arg_str += f": {arg.annotation.id}"
                elif isinstance(arg.annotation, ast.Constant):
                    arg_str += f": {arg.annotation.value}"
            args.append(arg_str)

        # Extract return annotation
        returns = ""
        if func_node.returns:
            if isinstance(func_node.returns, ast.Name):
                returns = f" -> {func_node.returns.id}"
            elif isinstance(func_node.returns, ast.Constant):
                returns = f" -> {func_node.returns.value}"

        return f"{func_node.name}({', '.join(args)}){returns}"

    def _extract_dependencies(self, func_node: ast.FunctionDef) -> Tuple[List[DatasetDependency], Dict[str, int]]:
        """Extract dataset dependencies from function calls."""
        dependencies = []
        from_dataframe_calls = {}  # dataset_name -> line_number

        for node in ast.walk(func_node):
            # Look for context.load_dataset() calls
            if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'load_dataset'):

                if node.args and isinstance(node.args[0], ast.Constant):
                    dataset_name = node.args[0].value
                    dependencies.append(DatasetDependency(
                        name=dataset_name,
                        type="input",
                        source="context.load_dataset",
                        line=node.lineno
                    ))

            # Look for context.save_dataset() calls
            elif (isinstance(node, ast.Call) and
                  isinstance(node.func, ast.Attribute) and
                  node.func.attr == 'save_dataset'):

                if node.args and isinstance(node.args[0], ast.Constant):
                    dataset_name = node.args[0].value
                    format_arg = "parquet"  # default
                    if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                        format_arg = node.args[1].value

                    dependencies.append(DatasetDependency(
                        name=dataset_name,
                        type="output",
                        source="context.save_dataset",
                        line=node.lineno,
                        format=format_arg
                    ))

            # Look for context.to_dataframe() calls
            elif (isinstance(node, ast.Call) and
                  isinstance(node.func, ast.Attribute) and
                  node.func.attr == 'to_dataframe'):

                if node.args and isinstance(node.args[0], ast.Constant):
                    dataset_name = node.args[0].value
                    dependencies.append(DatasetDependency(
                        name=dataset_name,
                        type="input",
                        source="context.to_dataframe",
                        line=node.lineno
                    ))

            # Look for context.from_dataframe() calls for schema inference
            elif (isinstance(node, ast.Call) and
                  isinstance(node.func, ast.Attribute) and
                  node.func.attr == 'from_dataframe'):

                if len(node.args) > 1 and isinstance(node.args[1], ast.Constant):
                    dataset_name = node.args[1].value
                    # Store for schema inference but don't add as dependency
                    from_dataframe_calls[dataset_name] = node.lineno

        return dependencies, from_dataframe_calls

    def _extract_sql_operations(self, func_node: ast.FunctionDef) -> List[SQLOperation]:
        """Extract and analyze SQL operations from context.sql() calls."""
        sql_operations = []

        for node in ast.walk(func_node):
            if (isinstance(node, ast.Call) and
                    isinstance(node.func, ast.Attribute) and
                    node.func.attr == 'sql'):

                if node.args and isinstance(node.args[0], ast.Constant):
                    sql_query = node.args[0].value
                    sql_op = self.sql_analyzer.analyze_sql_query(sql_query, node.lineno)
                    sql_operations.append(sql_op)

        return sql_operations

    def _validate_dependencies(self, dependencies: List[DatasetDependency], all_functions: List[FunctionAnalysis] = None) -> List[Dict[str, Any]]:
        """Validate dataset dependencies against available data, schemas, and function outputs."""
        issues = []

        # Build set of datasets produced by workflow functions
        produced_datasets = set()
        if all_functions:
            for func in all_functions:
                for dep in func.dependencies:
                    if dep.type == "output":
                        produced_datasets.add(dep.name)

        for dep in dependencies:
            if dep.type == "input":
                # Check if dataset file exists OR is produced by another function
                dataset_exists = self._dataset_exists(dep.name)
                produced_by_function = dep.name in produced_datasets
                dep.exists = dataset_exists or produced_by_function

                if not dataset_exists and not produced_by_function:
                    issues.append({
                        "type": "missing_dataset",
                        "severity": "error",
                        "dataset": dep.name,
                        "message": f"Required input dataset '{dep.name}' not found",
                        "line": dep.line
                    })
                elif dataset_exists:
                    # Only validate schema for file-based datasets
                    schema_valid = self._validate_schema(dep.name)
                    dep.schema_valid = schema_valid

                    if not schema_valid:
                        issues.append({
                            "type": "schema_validation_failed",
                            "severity": "warning",
                            "dataset": dep.name,
                            "message": f"Schema validation failed for dataset '{dep.name}'",
                            "line": dep.line
                        })

        return issues

    def _dataset_exists(self, dataset_name: str) -> bool:
        """Check if dataset file exists in data directories."""
        # Check both examples/data and examples/output
        for data_dir in [self.data_dir, self.output_data_dir]:
            # First check subdirectory structure
            dataset_dir = data_dir / dataset_name
            if dataset_dir.exists():
                for ext in ['.parquet', '.pq', '.csv']:
                    if (dataset_dir / f"{dataset_name}{ext}").exists():
                        return True

            # Also check direct files in output directory
            for ext in ['.parquet', '.pq', '.csv']:
                if (data_dir / f"{dataset_name}{ext}").exists():
                    return True

        return False

    def _validate_schema(self, dataset_name: str) -> bool:
        """Validate dataset against its schema if available."""
        try:
            # Check if schema exists
            schema = self.schema_manager.load_schema(dataset_name)

            # Find dataset file in both data directories
            dataset_file = None
            for data_dir in [self.data_dir, self.output_data_dir]:
                # First check subdirectory structure
                dataset_dir = data_dir / dataset_name
                for ext in ['.parquet', '.pq', '.csv']:
                    candidate = dataset_dir / f"{dataset_name}{ext}"
                    if candidate.exists():
                        dataset_file = candidate
                        break

                # Also check direct files in output directory
                if not dataset_file:
                    for ext in ['.parquet', '.pq', '.csv']:
                        candidate = data_dir / f"{dataset_name}{ext}"
                        if candidate.exists():
                            dataset_file = candidate
                            break

                if dataset_file:
                    break

            if not dataset_file:
                return False

            # Validate
            errors = self.schema_manager.validate_dataset_file(dataset_name, dataset_file)
            return len(errors) == 0

        except Exception:
            return False

    def generate_function_manifest(self, analysis: FunctionAnalysis, output_dir: Path) -> Path:
        """
        Generate YAML manifest file for a workflow function.

        Args:
            analysis: Function analysis result
            output_dir: Directory to save manifest

        Returns:
            Path to generated manifest file
        """
        output_dir.mkdir(exist_ok=True)
        manifest_file = output_dir / f"{analysis.name}.yml"

        # Organize dependencies by type and sort by name for consistent ordering
        inputs = sorted([dep for dep in analysis.dependencies if dep.type == "input"], key=lambda x: x.name)
        outputs = sorted([dep for dep in analysis.dependencies if dep.type == "output"], key=lambda x: x.name)

        # Create manifest structure
        function_info = {
            "name": analysis.name,
            "description": analysis.description,
            "version": analysis.version,
            "tags": analysis.tags
        }

        # Add repo information if available
        if hasattr(analysis, 'repo_name') and analysis.repo_name:
            function_info["repo_name"] = analysis.repo_name
        if hasattr(analysis, 'repo_tag') and analysis.repo_tag:
            function_info["repo_tag"] = analysis.repo_tag

        # Helper function to parse schema info
        def parse_schema_info(schema_info):
            if schema_info and schema_info != " [no schema available]":
                if "[" in schema_info and ":" in schema_info:
                    start = schema_info.find("[") + 1
                    end = schema_info.find("]")
                    columns_text = schema_info[start:end] if start > 0 and end > start else schema_info.strip()

                    # Parse columns into list format - handle column names with commas
                    columns_list = []
                    if columns_text:
                        # Split by comma but be careful of column names that contain commas
                        # Look for pattern "name:type" where type is a known data type
                        import re
                        # Pattern to match column definitions: name:type
                        # Handle cases where column names contain commas
                        pattern = r'([^:]+?):(string|int64|float64|bool|timestamp)'
                        matches = re.findall(pattern, columns_text)
                        for name, col_type in matches:
                            # Clean up the name by removing leading/trailing whitespace and commas
                            clean_name = name.strip().lstrip(', ').strip()
                            columns_list.append({"name": clean_name, "type": col_type.strip()})

                    if "(inferred from DataFrame)" in schema_info:
                        source = "dataframe_inference"
                    elif "(inferred from SQL)" in schema_info:
                        source = "sql_inference"
                    else:
                        source = "schema_file"

                    return {
                        "source": source,
                        "columns": columns_list,
                        "description": f"Schema with {len(columns_list)} columns"
                    }
                elif "schema: inferred from SQL" in schema_info:
                    return {
                        "source": "sql_inference",
                        "columns": [],
                        "description": "Schema inferred from SQL operations"
                    }
                else:
                    return {
                        "source": "unknown",
                        "columns": [],
                        "description": "Schema information available but format unknown"
                    }
            else:
                return {
                    "source": "none",
                    "columns": [],
                    "description": "No schema information available"
                }

        # Generate output schemas
        output_schemas = {}
        for dep in outputs:
            schema_info = self.get_output_schema_info(dep.name, analysis.sql_operations, analysis, self.infer_schema)
            if schema_info == " [schema: from DataFrame]":
                df_schema = self._infer_dataframe_schema(dep.name, analysis)
                if df_schema and "[" in df_schema:
                    schema_info = df_schema
                else:
                    for sql_op in analysis.sql_operations:
                        if sql_op.operation_type == "select" and not sql_op.outputs:
                            columns = self._parse_sql_columns(f"CREATE TABLE temp AS {sql_op.sql}")
                            if columns:
                                column_types = [f"{col['name']}:{col['type']}" for col in columns if col['name']]
                                if column_types:
                                    schema_info = f" [{', '.join(column_types)}] (inferred from SQL)"
                                    break
            output_schemas[dep.name] = parse_schema_info(schema_info)

        # Generate input schemas
        input_schemas = {}
        for dep in inputs:
            if dep.exists:
                schema_info = self.get_output_schema_info(dep.name, [], None, self.infer_schema)
                input_schemas[dep.name] = parse_schema_info(schema_info)

        # Add schemas to dependencies (inputs and outputs are already sorted by name)
        inputs_with_schemas = []
        for dep in inputs:
            input_info = {
                "dataset": dep.name,
                "required": dep.required,
                "exists": dep.exists,
                "schema_valid": dep.schema_valid,
                "source": dep.source,
                "line": dep.line
            }
            if dep.name in input_schemas:
                input_info["schema"] = input_schemas[dep.name]
            inputs_with_schemas.append(input_info)

        outputs_with_schemas = []
        for dep in outputs:
            output_info = {
                "dataset": dep.name,
                "format": dep.format or "parquet",
                "source": dep.source,
                "line": dep.line
            }
            if dep.name in output_schemas:
                output_info["schema"] = output_schemas[dep.name]
            outputs_with_schemas.append(output_info)

        manifest = {
            "function": function_info,
            "entry_point": {
                "file": analysis.file_path,
                "line": analysis.line,
                "signature": analysis.signature
            },
            "dependencies": {
                "inputs": inputs_with_schemas,
                "outputs": outputs_with_schemas
            },
            "sql_operations": [
                {
                    "sql": op.sql,
                    "line": op.line,
                    "operation_type": op.operation_type,
                    "inputs": sorted(op.inputs),
                    "outputs": sorted(op.outputs),
                    "error": op.error
                }
                for op in sorted(analysis.sql_operations, key=lambda x: (x.inputs[0] if x.inputs else "", x.line))
            ],
            "validation": {
                "issues": analysis.issues,
                "status": "valid" if not analysis.issues else "has_issues"
            }
        }

        # Save manifest with custom YAML dumper to prevent HTML encoding
        class NoEscapeYamlDumper(yaml.SafeDumper):
            def represent_str(self, data):
                if '\n' in data:
                    return self.represent_scalar('tag:yaml.org,2002:str', data, style='|')
                return self.represent_scalar('tag:yaml.org,2002:str', data)

        NoEscapeYamlDumper.add_representer(str, NoEscapeYamlDumper.represent_str)

        with open(manifest_file, 'w', encoding='utf-8') as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False, allow_unicode=True, Dumper=NoEscapeYamlDumper)

        return manifest_file

    def generate_repository_report(self, functions: List[FunctionAnalysis], output_file: Path, with_schemas: bool = False) -> Dict[str, Any]:
        """
        Generate comprehensive repository analysis report.

        Args:
            functions: List of analyzed functions
            output_file: Path to save report
            with_schemas: Include schema information for output datasets

        Returns:
            Report dictionary
        """
        # Collect all datasets mentioned
        all_inputs = set()
        all_outputs = set()
        missing_datasets = set()
        output_schemas = {}

        # Detect duplicate function names using centralized logic
        duplicate_functions = self.detect_duplicate_functions(functions)

        # Process functions to collect dataset info
        for func in functions:
            for dep in func.dependencies:
                if dep.type == "input":
                    all_inputs.add(dep.name)
                    if dep.exists is False:
                        missing_datasets.add(dep.name)
                else:
                    all_outputs.add(dep.name)

        # Initialize report structure with calculated values
        report = {
            "scan_timestamp": "2024-01-15T10:30:00Z",
            "repository": str(Path.cwd()),
            "summary": {
                "total_functions": len(functions),
                "total_input_datasets": len(all_inputs),
                "total_output_datasets": len(all_outputs),
                "missing_datasets": len(missing_datasets),
                "functions_with_issues": len([f for f in functions if f.issues]),
                "duplicate_function_names": len(duplicate_functions)
            },
            "functions": [],
            "datasets": {
                "inputs_required": list(all_inputs),
                "outputs_generated": list(all_outputs),
                "missing": list(missing_datasets)
            },
            "duplicate_functions": duplicate_functions
        }

        # Process functions for report
        for func in functions:
            # Convert function to dict and add repo info near name and version
            func_dict = asdict(func)

            # Reorder to put repo info after name and version
            ordered_dict = {"name": func_dict["name"]}
            if hasattr(func, 'repo_name') and func.repo_name:
                ordered_dict["repo_name"] = func.repo_name
            if hasattr(func, 'repo_tag') and func.repo_tag:
                ordered_dict["repo_tag"] = func.repo_tag
            if "version" in func_dict:
                ordered_dict["version"] = func_dict["version"]

            # Add remaining fields
            for key, value in func_dict.items():
                if key not in ordered_dict:
                    ordered_dict[key] = value

            report["functions"].append(ordered_dict)

            # Handle schema info for output datasets if requested
            for dep in func.dependencies:
                if dep.type == "output" and with_schemas and dep.name not in output_schemas:
                    schema_info = self.get_output_schema_info(dep.name, func.sql_operations, func, self.infer_schema)
                    if schema_info and schema_info != " [no schema available]":
                        # Determine source and columns based on schema info content
                        if "schema: from DataFrame" in schema_info:
                            source = "dataframe"
                            columns = "from_dataframe"
                        elif "schema: inferred from SQL" in schema_info:
                            source = "sql_inference"
                            columns = "from_sql"
                        elif "[" in schema_info and ":" in schema_info:
                            # Parse actual column count from schema info
                            column_count = self._parse_column_count_from_schema_info(schema_info)
                            if "(inferred from DataFrame)" in schema_info:
                                source = "dataframe"
                            elif "(inferred from SQL)" in schema_info:
                                source = "sql_inference"
                            else:
                                source = "parsed"
                            columns = column_count if column_count > 0 else "available"
                        else:
                            source = "unknown"
                            columns = 0

                        output_schemas[dep.name] = {
                            "name": dep.name,
                            "description": "Schema information available",
                            "version": None,
                            "source": source,
                            "columns": columns
                        }
                    else:
                        output_schemas[dep.name] = {
                            "name": dep.name,
                            "description": "No schema information available",
                            "version": None,
                            "source": "unknown",
                            "columns": []
                        }

        # Add schema information if requested - use function-level schemas instead
        if with_schemas:
            # Count schemas from function-level data
            schema_count = 0
            for func_data in report['functions']:
                if 'output_schemas' in func_data:
                    schema_count += len([s for s in func_data['output_schemas'].values() if isinstance(s.get('columns'), int) and s.get('columns') > 0])
            report["summary"]["output_datasets_with_schemas"] = schema_count

        # Save report
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return report

    def detect_duplicate_functions(self, functions: List[FunctionAnalysis]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect duplicate function names across functions.

        Args:
            functions: List of analyzed functions

        Returns:
            Dictionary mapping function names to list of locations where they appear
        """
        function_names = {}
        duplicate_functions = {}

        for func in functions:
            if func.name in function_names:
                # This is a duplicate
                if func.name not in duplicate_functions:
                    # First time seeing this duplicate, add the original function too
                    original_func = function_names[func.name]
                    duplicate_functions[func.name] = [
                        {"file_path": original_func.file_path, "line": original_func.line},
                        {"file_path": func.file_path, "line": func.line}
                    ]
                else:
                    # Add this duplicate to the existing list
                    duplicate_functions[func.name].append({"file_path": func.file_path, "line": func.line})
            else:
                function_names[func.name] = func

        return duplicate_functions

    def _parse_column_count_from_schema_info(self, schema_info: str) -> int:
        """
        Parse column count from schema info string.

        Args:
            schema_info: Schema info string like " [method:string, option_tenor:string, ...+1 more]"

        Returns:
            Number of columns
        """
        if not schema_info or "[" not in schema_info:
            return 0

        # Handle special cases that don't have column counts
        if "schema: from DataFrame" in schema_info or "schema: inferred from SQL" in schema_info or "no schema available" in schema_info:
            return 0

        # Extract content between brackets
        content = schema_info.split("[")[1].split("]")[0]

        # Count explicit columns (those with colons)
        explicit_cols = len([part for part in content.split(",") if ":" in part and part.strip()])

        # Check for "...+N more" pattern
        if "...+" in content and "more" in content:
            try:
                more_part = [part for part in content.split(",") if "...+" in part][0]
                additional = int(more_part.split("+")[1].split(" ")[0])
                return explicit_cols + additional
            except:
                pass

        return explicit_cols if explicit_cols > 0 else 0

    def _infer_dataframe_schema(self, dataset_name: str, func_analysis: FunctionAnalysis) -> Optional[str]:
        """
        Try to infer DataFrame schema by looking for variable assignments and operations.

        Args:
            dataset_name: Name of the dataset
            func_analysis: Function analysis object

        Returns:
            Schema string if found, None otherwise
        """
        try:
            # Read the source file and parse it
            with open(func_analysis.file_path, 'r') as f:
                source = f.read()

            tree = ast.parse(source)

            # Find the function node
            func_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_analysis.name:
                    func_node = node
                    break

            if not func_node:
                return None

            # Look for DataFrame operations that might reveal column structure
            for node in ast.walk(func_node):
                # Look for column list assignments like df = df[['col1', 'col2', 'col3']]
                if isinstance(node, ast.Assign):
                    if (isinstance(node.value, ast.Subscript) and
                            isinstance(node.value.slice, ast.List)):
                        columns = []
                        for elt in node.value.slice.elts:
                            if isinstance(elt, ast.Constant):
                                columns.append(f"{elt.value}:string")
                        if columns:
                            return f" [{', '.join(columns)}] (inferred from DataFrame)"

                # Look for DataFrame method calls that might reveal schema
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    # Look for operations like df.groupby(['col1', 'col2'])
                    if node.func.attr in ['groupby', 'pivot_table', 'merge']:
                        if node.args:
                            for arg in node.args:
                                if isinstance(arg, ast.List):
                                    columns = []
                                    for elt in arg.elts:
                                        if isinstance(elt, ast.Constant):
                                            columns.append(f"{elt.value}:string")
                                    if columns:
                                        return f" [{', '.join(columns)}] (inferred from DataFrame)"

            # Look for specific patterns in the source code
            source_lines = source.split('\n')
            for i, line in enumerate(source_lines):
                # Look for column list patterns like ["method", "option_tenor", "swap_tenor", "value"]
                if dataset_name in line and '[' in line and ']' in line and '"' in line:
                    # Try to extract column names from the line
                    import re
                    pattern = r'\[([^\]]+)\]'
                    matches = re.findall(pattern, line)
                    for match in matches:
                        if '"' in match or "'" in match:
                            # Extract quoted strings
                            col_pattern = r'["\']([^"\'\']+)["\']'
                            columns = re.findall(col_pattern, match)
                            if columns:
                                col_types = [f"{col}:string" for col in columns]
                                return f" [{', '.join(col_types)}] (inferred from DataFrame)"

            return None

        except Exception:
            return None

    def _parse_sql_columns(self, sql: str) -> List[Dict[str, str]]:
        """
        Parse column information from CREATE TABLE SQL statement.

        Args:
            sql: SQL CREATE TABLE statement

        Returns:
            List of column dictionaries with name and type
        """
        try:
            # Use SQLGlot to parse the CREATE TABLE statement
            parsed = parse_one(sql, dialect="duckdb")
            if not parsed or not isinstance(parsed, Create):
                return []

            columns = []
            if hasattr(parsed, 'this') and hasattr(parsed.this, 'expressions'):
                for expr in parsed.this.expressions:
                    if hasattr(expr, 'this') and hasattr(expr, 'kind'):
                        col_name = str(expr.this)
                        col_type = str(expr.kind) if expr.kind else "unknown"
                        columns.append({"name": col_name, "type": col_type})

            # If we can't parse the schema definition, try to infer from SELECT
            if not columns and hasattr(parsed, 'expression') and parsed.expression:
                # For CREATE TABLE AS SELECT, try to infer from the SELECT columns
                select_expr = parsed.expression
                if hasattr(select_expr, 'expressions'):
                    for expr in select_expr.expressions:
                        col_name = ""
                        if hasattr(expr, 'alias') and expr.alias:
                            col_name = str(expr.alias)
                        elif hasattr(expr, 'this') and expr.this:
                            col_name = str(expr.this)
                        elif hasattr(expr, 'name') and expr.name:
                            col_name = str(expr.name)
                        else:
                            col_name = str(expr)[:20]  # Truncate long expressions

                        # Clean up column name
                        col_name = col_name.replace('"', '').replace('`', '').strip()
                        if col_name:  # Only add if we have a valid column name
                            columns.append({"name": col_name, "type": "inferred"})

            return columns

        except Exception:
            return []

    def get_output_schema_info(self, dataset_name: str, func_sql_operations: List[SQLOperation], func_analysis: FunctionAnalysis = None, infer_schema: bool = None) -> str:
        """
        Get schema information string for display purposes.

        Fallback logic:
        1. Try to load schema from schema manager
        2. Try to read from schema directory yaml files
        3. Try to infer from actual data files
        4. If infer_schema=True: Try to infer from SQL or dataframe operations
        5. Return 'no schema available' if all above failed

        Args:
            dataset_name: Name of the dataset
            func_sql_operations: SQL operations from the function
            func_analysis: Function analysis object with from_dataframe info
            infer_schema: Override instance setting for schema inference

        Returns:
            Schema information string for display
        """
        # Use parameter override or instance setting
        if infer_schema is None:
            infer_schema = self.infer_schema
        # 1. Try to load schema from schema manager
        try:
            schema = self.schema_manager.load_schema(dataset_name)
            column_types = [f"{col.name}:{col.type}" for col in schema.columns]
            return f" [{', '.join(column_types)}]"
        except:
            pass

        # 2. Try to read from schema directory yaml files (schema definitions)
        # Check both examples/datasets and examples/output
        # check examples/datasets first, in case user put output dataset schema there already
        # then check examples/output, which is generated by test/dry runner
        for schema_dir in [self.schemas_dir, self.output_schemas_dir]:
            try:
                dataset_yaml = schema_dir / f"{dataset_name}.yml"
                if dataset_yaml.exists():
                    with open(dataset_yaml, 'r', encoding='utf-8') as f:
                        yaml_data = yaml.safe_load(f)
                        if 'columns' in yaml_data:
                            columns = yaml_data['columns']
                            column_types = [f"{col['name']}:{col['type']}" for col in columns]
                            return f" [{', '.join(column_types)}]"
            except:
                continue

        # 3. Try to infer from actual data files
        # Check both examples/data and examples/output
        for data_dir in [self.data_dir, self.output_data_dir]:
            # First check subdirectory structure
            dataset_dir = data_dir / dataset_name
            if dataset_dir.exists():
                for ext in ['.parquet', '.pq', '.csv']:
                    dataset_file = dataset_dir / f"{dataset_name}{ext}"
                    if dataset_file.exists():
                        try:
                            schema = self.schema_manager.create_schema_from_file(dataset_name, dataset_file)
                            column_types = [f"{col.name}:{col.type}" for col in schema.columns]
                            return f" [{', '.join(column_types)}]"
                        except:
                            continue

            # Also check direct files in output directory
            for ext in ['.parquet', '.pq', '.csv']:
                dataset_file = data_dir / f"{dataset_name}{ext}"
                if dataset_file.exists():
                    try:
                        schema = self.schema_manager.create_schema_from_file(dataset_name, dataset_file)
                        column_types = [f"{col.name}:{col.type}" for col in schema.columns]
                        return f" [{', '.join(column_types)}]"
                    except:
                        continue

        # 4. Try to infer from SQL or dataframe operations (only if enabled)
        if infer_schema:
            # 4a. Try to infer from SQL operations
            for sql_op in func_sql_operations:
                if dataset_name in sql_op.outputs and sql_op.operation_type == "create_table":
                    columns = self._parse_sql_columns(sql_op.sql)
                    if columns:
                        column_types = [f"{col['name']}:{col['type']}" for col in columns if col['name']]
                        if column_types:  # Only return if we have valid column names
                            return f" [{', '.join(column_types)}]"
                    return " [schema: inferred from SQL]"

            # 4b. Check if this dataset has a from_dataframe call
            if func_analysis and hasattr(func_analysis, '_from_dataframe_calls'):
                if dataset_name in func_analysis._from_dataframe_calls:
                    # Try to infer schema from the DataFrame variable in the function
                    schema_info = self._infer_dataframe_schema(dataset_name, func_analysis)
                    if schema_info:
                        return schema_info
                    return " [schema: from DataFrame]"

        # 5. If all above failed, return 'no schema available'
        return " [no schema available]"
