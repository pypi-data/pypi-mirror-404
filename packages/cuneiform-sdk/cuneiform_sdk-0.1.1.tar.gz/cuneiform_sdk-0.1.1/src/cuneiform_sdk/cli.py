# Common dataset file extensions in priority order (CSV first)
DATASET_EXTENSIONS = ['.csv', '.parquet', '.pq']
"""
CLI tool for dataset management.

Provides commands for downloading, managing, and validating datasets
with schema generation and local testing support.
"""

import click
import pandas as pd
import requests
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
import os
import sys

# Handle imports more robustly
try:
    # Try relative imports first (when used as package)
    from ..core.schema import SchemaManager, DatasetSchema
    from ..impl.duckdb_context import WorkflowRunContext
    from ..core.metadata import WorkflowRegistry, get_global_registry
    from ..scanner import WorkflowFunctionScanner, FunctionAnalysis
    from ..exceptions import ValidationError, DatasetError
except ImportError:
    # Fallback for direct script execution
    current_dir = Path(__file__).parent
    if str(current_dir.parent) not in sys.path:
        sys.path.insert(0, str(current_dir.parent))

    from cuneiform_sdk.core.schema import SchemaManager, DatasetSchema
    from cuneiform_sdk.impl.duckdb_context import WorkflowRunContext
    from cuneiform_sdk.core.metadata import WorkflowRegistry, get_global_registry
    from cuneiform_sdk.scanner import WorkflowFunctionScanner, FunctionAnalysis
    from cuneiform_sdk.exceptions import ValidationError, DatasetError


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def cli(ctx, verbose):
    """Cuneiform SDK CLI - Dataset and workflow management tool."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose

    if verbose:
        import logging
        logging.basicConfig(level=logging.INFO)


@cli.group()
def dataset():
    """Dataset management commands."""
    pass


@cli.group()
def workflow():
    """Workflow function management commands."""
    pass


@cli.group()
def scanner():
    """Repository scanning and analysis commands."""
    pass


@dataset.command('download')
@click.argument('dataset_name')
@click.option('--url', help='URL to download dataset from')
@click.option('--format', default='parquet', type=click.Choice(['parquet', 'csv']), help='Dataset format')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
@click.option('--force', is_flag=True, help='Overwrite existing files')
@click.pass_context
def download_dataset(ctx, dataset_name: str, url: Optional[str], format: str, data_dir: str, schemas_dir: str, force: bool):
    """Download a dataset and create its schema."""
    try:
        data_path = Path(data_dir)
        schemas_path = Path(schemas_dir)

        # Create directories
        data_path.mkdir(exist_ok=True)
        schemas_path.mkdir(exist_ok=True)

        dataset_dir = data_path / dataset_name
        dataset_dir.mkdir(exist_ok=True)

        file_ext = '.parquet' if format == 'parquet' else '.csv'
        output_file = dataset_dir / f"{dataset_name}{file_ext}"

        if output_file.exists() and not force:
            click.echo(f"Dataset '{dataset_name}' already exists. Use --force to overwrite.")
            return

        if url:
            click.echo(f"Downloading dataset '{dataset_name}' from {url}")
            _download_file(url, output_file)
        else:
            # Create sample dataset for testing
            click.echo(f"Creating sample dataset '{dataset_name}'")
            _create_sample_dataset(dataset_name, output_file, format)

        # Generate schema
        click.echo(f"Generating schema for '{dataset_name}'")
        schema_manager = SchemaManager(str(schemas_path))
        schema = schema_manager.create_schema_from_file(
            dataset_name,
            output_file,
            f"Generated schema for {dataset_name}"
        )

        click.echo(f"Successfully created dataset '{dataset_name}':")
        click.echo(f"  Data: {output_file}")
        click.echo(f"  Schema: {schemas_path / f'{dataset_name}.yml'}")
        click.echo(f"  Columns: {len(schema.columns)}")

    except Exception as e:
        click.echo(f"Error downloading dataset: {e}", err=True)
        sys.exit(1)


@dataset.command('list')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
def list_datasets(data_dir: str, schemas_dir: str):
    """List all available datasets."""
    try:
        data_path = Path(data_dir)
        schema_manager = SchemaManager(schemas_dir)

        if not data_path.exists():
            click.echo("No data directory found.")
            return

        datasets = []

        # Find all dataset directories
        for item in data_path.iterdir():
            if item.is_dir():
                # Look for dataset files
                for ext in DATASET_EXTENSIONS:
                    dataset_file = item / f"{item.name}{ext}"
                    if dataset_file.exists():
                        has_schema = item.name in schema_manager.list_schemas()
                        datasets.append({
                            'name': item.name,
                            'file': str(dataset_file),
                            'format': ext[1:],
                            'size': _format_file_size(dataset_file.stat().st_size),
                            'has_schema': has_schema
                        })
                        break

        if not datasets:
            click.echo("No datasets found.")
            return

        click.echo("Available datasets:")
        click.echo()
        click.echo(f"{'Name':<20} {'Format':<10} {'Size':<10} {'Schema':<8} {'File'}")
        click.echo("-" * 80)

        for ds in datasets:
            schema_status = "✓" if ds['has_schema'] else "✗"
            click.echo(f"{ds['name']:<20} {ds['format']:<10} {ds['size']:<10} {schema_status:<8} {ds['file']}")

    except Exception as e:
        click.echo(f"Error listing datasets: {e}", err=True)


@dataset.command('validate')
@click.argument('dataset_name')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
def validate_dataset(dataset_name: str, data_dir: str, schemas_dir: str):
    """Validate a dataset against its schema."""
    try:
        schema_manager = SchemaManager(schemas_dir)

        # Find dataset file
        data_path = Path(data_dir) / dataset_name
        dataset_file = None

        for ext in DATASET_EXTENSIONS:
            candidate = data_path / f"{dataset_name}{ext}"
            if candidate.exists():
                dataset_file = candidate
                break

        if not dataset_file:
            click.echo(f"Dataset file for '{dataset_name}' not found in {data_path}")
            return

        click.echo(f"Validating dataset '{dataset_name}'...")

        errors = schema_manager.validate_dataset_file(dataset_name, dataset_file)

        if not errors:
            click.echo("✓ Dataset validation passed!")
        else:
            click.echo("✗ Dataset validation failed:")
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)

    except Exception as e:
        click.echo(f"Error validating dataset: {e}", err=True)
        sys.exit(1)


@dataset.command('schema')
@click.argument('dataset_name')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
@click.option('--create', is_flag=True, help='Create schema from dataset file')
@click.option('--data-dir', default='data', help='Data directory (for --create)')
def show_schema(dataset_name: str, schemas_dir: str, create: bool, data_dir: str):
    """Show or create dataset schema."""
    try:
        schema_manager = SchemaManager(schemas_dir)

        if create:
            # Create schema from dataset file
            data_path = Path(data_dir) / dataset_name
            dataset_file = None

            for ext in DATASET_EXTENSIONS:
                candidate = data_path / f"{dataset_name}{ext}"
                if candidate.exists():
                    dataset_file = candidate
                    break

            if not dataset_file:
                click.echo(f"Dataset file for '{dataset_name}' not found in {data_path}")
                return

            schema = schema_manager.create_schema_from_file(dataset_name, dataset_file)
            click.echo(f"Created schema for '{dataset_name}'")
        else:
            # Load existing schema
            schema = schema_manager.load_schema(dataset_name)

        # Display schema
        click.echo(f"\nSchema for '{dataset_name}':")
        if schema.description:
            click.echo(f"Description: {schema.description}")
        if schema.version:
            click.echo(f"Version: {schema.version}")

        click.echo("\nColumns:")
        click.echo(f"{'Name':<20} {'Type':<15} {'Nullable':<10} {'Description'}")
        click.echo("-" * 70)

        for col in schema.columns:
            nullable = "Yes" if col.nullable else "No"
            desc = col.description or ""
            click.echo(f"{col.name:<20} {col.type:<15} {nullable:<10} {desc}")

    except Exception as e:
        click.echo(f"Error with schema: {e}", err=True)
        sys.exit(1)


@dataset.command('test')
@click.argument('dataset_name')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--output-dir', default='output', help='Output directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
def test_dataset(dataset_name: str, data_dir: str, output_dir: str, schemas_dir: str):
    """Test dataset loading and basic operations."""
    try:
        click.echo(f"Testing dataset '{dataset_name}'...")

        with WorkflowRunContext(data_dir, output_dir, schemas_dir) as ctx:
            # Load dataset
            ctx.load_dataset(dataset_name)
            click.echo(f"✓ Successfully loaded dataset '{dataset_name}'")

            # Basic statistics
            result = ctx.sql(f"SELECT COUNT(*) as row_count FROM {dataset_name}").fetchone()
            row_count = result[0] if result else 0

            columns = ctx.sql(f"DESCRIBE {dataset_name}").fetchall()
            col_count = len(columns)

            click.echo(f"  Rows: {row_count:,}")
            click.echo(f"  Columns: {col_count}")

            # Show sample data
            sample = ctx.sql(f"SELECT * FROM {dataset_name} LIMIT 5").fetchdf()
            click.echo(f"\nSample data:")
            click.echo(sample.to_string(index=False))

            # Test conversion to DataFrame
            df = ctx.to_dataframe(dataset_name)
            click.echo(f"\n✓ DataFrame conversion successful ({len(df)} rows)")

            click.echo(f"\n✓ All tests passed for dataset '{dataset_name}'")

    except Exception as e:
        click.echo(f"✗ Test failed: {e}", err=True)
        sys.exit(1)


@workflow.command('list')
@click.option('--module', help='Python module to scan for workflow functions')
@click.option('--package', help='Python package to scan for workflow functions')
def list_workflows(module: Optional[str], package: Optional[str]):
    """List discovered workflow functions."""
    try:
        registry = get_global_registry()

        if module:
            count = registry.discover_in_module(module)
            click.echo(f"Discovered {count} functions in module '{module}'")
        elif package:
            count = registry.discover_in_package(package)
            click.echo(f"Discovered {count} functions in package '{package}'")

        functions = registry.list_functions()

        if not functions:
            click.echo("No workflow functions found.")
            return

        click.echo("\nWorkflow Functions:")
        click.echo(f"{'Name':<25} {'Version':<10} {'Tags':<20} {'Description'}")
        click.echo("-" * 80)

        for func in functions:
            tags = ', '.join(func.tags) if func.tags else ""
            desc = func.description or ""
            version = func.version or ""
            click.echo(f"{func.name:<25} {version:<10} {tags:<20} {desc}")

    except Exception as e:
        click.echo(f"Error listing workflows: {e}", err=True)


@workflow.command('info')
@click.argument('function_name')
@click.option('--module', help='Python module to scan for workflow functions')
def workflow_info(function_name: str, module: Optional[str]):
    """Show detailed information about a workflow function."""
    try:
        registry = get_global_registry()

        if module:
            registry.discover_in_module(module)

        func = registry.get(function_name)
        if not func:
            click.echo(f"Workflow function '{function_name}' not found.")
            return

        click.echo(f"Workflow Function: {func.name}")
        click.echo(f"Description: {func.description or 'None'}")
        click.echo(f"Version: {func.version or 'None'}")
        click.echo(f"Tags: {', '.join(func.tags) if func.tags else 'None'}")

        if func.func:
            import inspect
            sig = inspect.signature(func.func)
            click.echo(f"Signature: {func.name}{sig}")

            if func.func.__doc__:
                click.echo(f"\nDocumentation:")
                click.echo(func.func.__doc__)

    except Exception as e:
        click.echo(f"Error getting workflow info: {e}", err=True)


def _download_file(url: str, output_path: Path) -> None:
    """Download file from URL."""
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def _create_sample_dataset(name: str, output_path: Path, format: str) -> None:
    """Create a sample dataset for testing."""
    # Generate sample data based on dataset name
    if 'customer' in name.lower():
        data = {
            'id': range(1, 101),
            'name': [f'Customer {i}' for i in range(1, 101)],
            'email': [f'customer{i}@example.com' for i in range(1, 101)],
            'created_at': pd.date_range('2023-01-01', periods=100)
        }
    elif 'product' in name.lower():
        data = {
            'id': range(1, 51),
            'name': [f'Product {i}' for i in range(1, 51)],
            'price': [10.0 + i * 2.5 for i in range(1, 51)],
            'category': ['Electronics', 'Clothing', 'Books'] * 17
        }
    else:
        # Generic sample data
        data = {
            'id': range(1, 21),
            'value': [i * 10 for i in range(1, 21)],
            'label': [f'Item {i}' for i in range(1, 21)],
            'timestamp': pd.date_range('2023-01-01', periods=20)
        }

    df = pd.DataFrame(data)

    if format == 'parquet':
        df.to_parquet(output_path, index=False)
    else:
        df.to_csv(output_path, index=False)


def _format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"


@scanner.command('scan')
@click.option('--repo', default='.', help='Repository path to scan')
@click.option('--output', default='scan_report.json', help='Output file for scan report')
@click.option('--manifests-dir', default='functions', help='Directory to save function manifests')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
def scan_repository(repo: str, output: str, manifests_dir: str, data_dir: str, schemas_dir: str):
    """Scan repository for workflow functions and analyze dependencies."""
    try:
        click.echo(f"🔍 Scanning repository: {repo}")

        scanner = WorkflowFunctionScanner(data_dir, schemas_dir)
        functions = scanner.scan_directory(Path(repo))

        if not functions:
            click.echo("No workflow functions found.")
            return

        click.echo(f"Found {len(functions)} workflow functions")

        # Generate manifests
        manifests_path = Path(manifests_dir)
        manifests_path.mkdir(exist_ok=True)

        for func in functions:
            manifest_file = scanner.generate_function_manifest(func, manifests_path)
            click.echo(f"Generated manifest: {manifest_file}")

        # Generate repository report
        report = scanner.generate_repository_report(functions, Path(output))

        click.echo(f"\n📊 Scan Results:")
        click.echo(f"  Functions: {report['summary']['total_functions']}")
        click.echo(f"  Input datasets: {report['summary']['total_input_datasets']}")
        click.echo(f"  Output datasets: {report['summary']['total_output_datasets']}")
        click.echo(f"  Missing datasets: {report['summary']['missing_datasets']}")
        click.echo(f"  Functions with issues: {report['summary']['functions_with_issues']}")

        if report['summary']['missing_datasets'] > 0:
            click.echo(f"\n⚠️  Missing datasets:")
            for dataset in report['datasets']['missing']:
                click.echo(f"    - {dataset}")

        click.echo(f"\n📄 Report saved to: {output}")
        click.echo(f"📄 Manifests saved to: {manifests_dir}/")

    except Exception as e:
        click.echo(f"Error scanning repository: {e}", err=True)
        sys.exit(1)


@scanner.command('validate')
@click.option('--repo', default='.', help='Repository path to scan')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
@click.option('--fail-on-missing', is_flag=True, help='Exit with error if datasets are missing')
def validate_dependencies(repo: str, data_dir: str, schemas_dir: str, fail_on_missing: bool):
    """Validate workflow function dependencies."""
    try:
        scanner = WorkflowFunctionScanner(data_dir, schemas_dir)
        functions = scanner.scan_directory(Path(repo))

        if not functions:
            click.echo("No workflow functions found.")
            return

        total_issues = 0
        missing_datasets = set()

        click.echo("🔍 Validating dependencies...\n")

        for func in functions:
            click.echo(f"Function: {func.name}")

            if not func.issues:
                click.echo("  ✅ No issues found")
            else:
                for issue in func.issues:
                    if issue['type'] == 'missing_dataset':
                        missing_datasets.add(issue['dataset'])
                        click.echo(f"  ❌ {issue['message']} (line {issue['line']})")
                    else:
                        click.echo(f"  ⚠️  {issue['message']} (line {issue['line']})")
                total_issues += len(func.issues)
            click.echo()

        click.echo(f"Validation Summary:")
        click.echo(f"  Total functions: {len(functions)}")
        click.echo(f"  Total issues: {total_issues}")
        click.echo(f"  Missing datasets: {len(missing_datasets)}")

        if missing_datasets:
            click.echo(f"\nMissing datasets:")
            for dataset in sorted(missing_datasets):
                click.echo(f"  - {dataset}")

        if fail_on_missing and missing_datasets:
            click.echo(f"\n❌ Validation failed due to missing datasets")
            sys.exit(1)
        elif total_issues == 0:
            click.echo(f"\n✅ All validations passed!")

    except Exception as e:
        click.echo(f"Error validating dependencies: {e}", err=True)
        sys.exit(1)


@scanner.command('missing')
@click.option('--repo', default='.', help='Repository path to scan')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
@click.option('--format', default='table', type=click.Choice(['table', 'json', 'yaml']), help='Output format')
def show_missing_datasets(repo: str, data_dir: str, schemas_dir: str, format: str):
    """Show missing datasets report."""
    try:
        scanner = WorkflowFunctionScanner(data_dir, schemas_dir)
        functions = scanner.scan_directory(Path(repo))

        # Collect missing datasets and which functions need them
        missing_info = {}

        for func in functions:
            for issue in func.issues:
                if issue['type'] == 'missing_dataset':
                    dataset = issue['dataset']
                    if dataset not in missing_info:
                        missing_info[dataset] = []
                    missing_info[dataset].append(func.name)

        if not missing_info:
            click.echo("✅ No missing datasets found!")
            return

        if format == 'table':
            click.echo("Missing Datasets Report:\n")
            click.echo(f"{'Dataset':<20} {'Required By':<30} {'Functions'}")
            click.echo("-" * 80)

            for dataset, functions in missing_info.items():
                func_list = ', '.join(functions)
                click.echo(f"{dataset:<20} {len(functions)} function(s) {func_list}")

        elif format == 'json':
            import json
            click.echo(json.dumps(missing_info, indent=2))

        elif format == 'yaml':
            import yaml
            click.echo(yaml.dump({'missing_datasets': missing_info}, default_flow_style=False))

    except Exception as e:
        click.echo(f"Error generating missing datasets report: {e}", err=True)
        sys.exit(1)


@scanner.command('analyze-function')
@click.argument('function_name')
@click.option('--repo', default='.', help='Repository path to scan')
@click.option('--data-dir', default='data', help='Data directory')
@click.option('--schemas-dir', default='datasets', help='Schemas directory')
def analyze_function(function_name: str, repo: str, data_dir: str, schemas_dir: str):
    """Analyze a specific workflow function in detail."""
    try:
        scanner = WorkflowFunctionScanner(data_dir, schemas_dir)
        functions = scanner.scan_directory(Path(repo))

        # Find the function
        target_func = None
        for func in functions:
            if func.name == function_name:
                target_func = func
                break

        if not target_func:
            click.echo(f"Function '{function_name}' not found.")
            available = [f.name for f in functions]
            if available:
                click.echo(f"Available functions: {', '.join(available)}")
            return

        # Display detailed analysis
        click.echo(f"Function Analysis: {target_func.name}")
        click.echo("=" * 50)
        click.echo(f"File: {target_func.file_path}:{target_func.line}")
        click.echo(f"Description: {target_func.description or 'None'}")
        click.echo(f"Version: {target_func.version or 'None'}")
        click.echo(f"Tags: {', '.join(target_func.tags) if target_func.tags else 'None'}")
        click.echo(f"Signature: {target_func.signature}")

        # Dependencies
        inputs = [d for d in target_func.dependencies if d.type == 'input']
        outputs = [d for d in target_func.dependencies if d.type == 'output']

        click.echo(f"\nInput Dependencies ({len(inputs)}):")
        for dep in inputs:
            status = "✅" if dep.exists else "❌"
            schema_status = "📋" if dep.schema_valid else "⚠️" if dep.schema_valid is False else "❓"
            click.echo(f"  {status} {schema_status} {dep.name} (from {dep.source}, line {dep.line})")

        click.echo(f"\nOutput Dependencies ({len(outputs)}):")
        for dep in outputs:
            click.echo(f"  📤 {dep.name} ({dep.format or 'unknown format'}) (from {dep.source}, line {dep.line})")

        # SQL Operations
        if target_func.sql_operations:
            click.echo(f"\nSQL Operations ({len(target_func.sql_operations)}):")
            for i, op in enumerate(target_func.sql_operations, 1):
                click.echo(f"  {i}. {op.operation_type} (line {op.line})")
                if op.inputs:
                    click.echo(f"     Inputs: {', '.join(op.inputs)}")
                if op.outputs:
                    click.echo(f"     Outputs: {', '.join(op.outputs)}")
                if op.error:
                    click.echo(f"     ⚠️ Error: {op.error}")

        # Issues
        if target_func.issues:
            click.echo(f"\nIssues ({len(target_func.issues)}):")
            for issue in target_func.issues:
                severity_icon = "❌" if issue['severity'] == 'error' else "⚠️"
                click.echo(f"  {severity_icon} {issue['message']} (line {issue['line']})")
        else:
            click.echo(f"\n✅ No issues found!")

    except Exception as e:
        click.echo(f"Error analyzing function: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
