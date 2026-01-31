"""Command-line interface for Dumont Excel generator."""

import click
from pathlib import Path
from typing import Optional

from .core import (
    create_excel_with_pivot,
    create_excel_with_xlwings,
    generate_sample_data,
    read_excel_to_dataframe,
)


@click.group()
@click.version_option()
def cli():
    """Dumont - Excel file generation tool with pivot tables.

    Generate Excel files with data and pivot table sheets using pandas and xlwings.
    """
    pass


@cli.command()
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="output.xlsx",
    help="Output Excel file path (default: output.xlsx)",
)
@click.option(
    "-i", "--input",
    "input_file",
    type=click.Path(exists=True),
    help="Input CSV or Excel file to use as data source",
)
@click.option(
    "--data-sheet",
    default="Data",
    help="Name for the data sheet (default: Data)",
)
@click.option(
    "--pivot-sheet",
    default="Pivot",
    help="Name for the pivot sheet (default: Pivot)",
)
@click.option(
    "--pivot-values",
    default="Revenue",
    help="Column to aggregate in pivot table (default: Revenue)",
)
@click.option(
    "--pivot-index",
    default="Category",
    help="Row grouping column for pivot (default: Category)",
)
@click.option(
    "--pivot-columns",
    default="Region",
    help="Column grouping for pivot (default: Region)",
)
@click.option(
    "--aggfunc",
    type=click.Choice(["sum", "mean", "count", "min", "max"]),
    default="sum",
    help="Aggregation function (default: sum)",
)
@click.option(
    "--sample/--no-sample",
    default=True,
    help="Use sample data if no input file provided (default: True)",
)
@click.option(
    "--rows",
    type=int,
    default=100,
    help="Number of rows for sample data (default: 100)",
)
@click.option(
    "--engine",
    type=click.Choice(["pandas", "xlwings"]),
    default="pandas",
    help="Excel engine to use (default: pandas)",
)
@click.option(
    "--visible",
    is_flag=True,
    help="Show Excel window during xlwings creation",
)
def generate(
    output: str,
    input_file: Optional[str],
    data_sheet: str,
    pivot_sheet: str,
    pivot_values: str,
    pivot_index: str,
    pivot_columns: str,
    aggfunc: str,
    sample: bool,
    rows: int,
    engine: str,
    visible: bool,
):
    """Generate an Excel file with data and pivot table sheets.

    Examples:

        # Generate with sample data
        dumont generate -o sales_report.xlsx

        # Use custom input file
        dumont generate -i data.csv -o report.xlsx

        # Customize pivot table
        dumont generate -o report.xlsx --pivot-values Sales --pivot-index Product

        # Use xlwings engine with visible Excel
        dumont generate -o report.xlsx --engine xlwings --visible
    """
    df = None

    if input_file:
        click.echo(f"Reading data from: {input_file}")
        input_path = Path(input_file)
        if input_path.suffix.lower() == ".csv":
            import pandas as pd
            df = pd.read_csv(input_file)
        else:
            df = read_excel_to_dataframe(input_file)
        click.echo(f"Loaded {len(df)} rows")

    try:
        if engine == "xlwings":
            result_path = create_excel_with_xlwings(
                output_path=output,
                df=df,
                data_sheet_name=data_sheet,
                pivot_sheet_name=pivot_sheet,
                pivot_values=pivot_values,
                pivot_index=pivot_index,
                pivot_columns=pivot_columns,
                use_sample_data=sample and df is None,
                sample_rows=rows,
                visible=visible,
            )
        else:
            result_path = create_excel_with_pivot(
                output_path=output,
                df=df,
                data_sheet_name=data_sheet,
                pivot_sheet_name=pivot_sheet,
                pivot_values=pivot_values,
                pivot_index=pivot_index,
                pivot_columns=pivot_columns,
                pivot_aggfunc=aggfunc,
                use_sample_data=sample and df is None,
                sample_rows=rows,
            )

        click.echo(f"Excel file created: {result_path}")
        click.echo(f"  - Sheet '{data_sheet}': Raw data")
        click.echo(f"  - Sheet '{pivot_sheet}': Pivot table ({pivot_values} by {pivot_index} x {pivot_columns})")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.option(
    "--rows",
    type=int,
    default=10,
    help="Number of sample rows to show (default: 10)",
)
def sample(rows: int):
    """Show sample data that would be generated.

    Example:
        dumont sample --rows 20
    """
    df = generate_sample_data(rows=rows)
    click.echo("Sample data preview:")
    click.echo(df.to_string(index=False))


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option(
    "--sheet",
    help="Specific sheet to read",
)
@click.option(
    "--rows",
    type=int,
    default=10,
    help="Number of rows to display (default: 10)",
)
def preview(file: str, sheet: Optional[str], rows: int):
    """Preview contents of an Excel file.

    Example:
        dumont preview report.xlsx --sheet Data --rows 20
    """
    import pandas as pd

    try:
        if sheet:
            df = pd.read_excel(file, sheet_name=sheet)
            click.echo(f"Sheet: {sheet}")
        else:
            xl = pd.ExcelFile(file)
            click.echo(f"Available sheets: {', '.join(xl.sheet_names)}")
            df = pd.read_excel(file, sheet_name=0)
            click.echo(f"Showing first sheet: {xl.sheet_names[0]}")

        click.echo(f"Shape: {df.shape[0]} rows x {df.shape[1]} columns")
        click.echo()
        click.echo(df.head(rows).to_string(index=False))

    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("file", type=click.Path(exists=True))
def info(file: str):
    """Show information about an Excel file.

    Example:
        dumont info report.xlsx
    """
    import pandas as pd
    from pathlib import Path

    file_path = Path(file)
    click.echo(f"File: {file_path.name}")
    click.echo(f"Size: {file_path.stat().st_size / 1024:.1f} KB")

    try:
        xl = pd.ExcelFile(file)
        click.echo(f"Sheets: {len(xl.sheet_names)}")

        for sheet_name in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet_name)
            click.echo(f"  - {sheet_name}: {df.shape[0]} rows x {df.shape[1]} columns")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind to (default: 127.0.0.1)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind to (default: 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def serve(host: str, port: int, reload: bool):
    """Start the web UI server.

    Launches a mini Excel interface in the browser using sheet.js,
    connected to the dumont backend for Excel generation.

    Examples:

        # Start the server
        dumont serve

        # Start on a different port
        dumont serve --port 3000

        # Start with auto-reload for development
        dumont serve --reload
    """
    try:
        import uvicorn
    except ImportError:
        click.echo("Error: uvicorn is required for the web server.", err=True)
        click.echo("Install it with: pip install uvicorn fastapi python-multipart", err=True)
        raise click.Abort()

    click.echo(f"Starting Dumont Web UI server...")
    click.echo(f"Open http://{host}:{port} in your browser")
    click.echo("Press Ctrl+C to stop")

    uvicorn.run(
        "web.server:app",
        host=host,
        port=port,
        reload=reload,
    )


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
