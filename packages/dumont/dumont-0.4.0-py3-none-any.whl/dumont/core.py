"""Core Excel generation functions using pandas and xlwings."""

import pandas as pd
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, timedelta
import random


def generate_sample_data(rows: int = 100) -> pd.DataFrame:
    """Generate sample sales data for demonstration purposes.

    Args:
        rows: Number of rows to generate.

    Returns:
        DataFrame with sample sales data.
    """
    random.seed(42)

    categories = ["Electronics", "Clothing", "Food", "Books", "Home & Garden"]
    regions = ["North", "South", "East", "West", "Central"]
    products = {
        "Electronics": ["Laptop", "Phone", "Tablet", "Headphones", "Camera"],
        "Clothing": ["Shirt", "Pants", "Jacket", "Shoes", "Hat"],
        "Food": ["Snacks", "Beverages", "Frozen", "Dairy", "Produce"],
        "Books": ["Fiction", "Non-Fiction", "Technical", "Children", "Comics"],
        "Home & Garden": ["Furniture", "Tools", "Decor", "Plants", "Lighting"],
    }

    data = []
    base_date = datetime(2024, 1, 1)

    for _ in range(rows):
        category = random.choice(categories)
        product = random.choice(products[category])
        region = random.choice(regions)
        date = base_date + timedelta(days=random.randint(0, 364))
        quantity = random.randint(1, 50)
        unit_price = round(random.uniform(10, 500), 2)
        revenue = round(quantity * unit_price, 2)

        data.append({
            "Date": date,
            "Category": category,
            "Product": product,
            "Region": region,
            "Quantity": quantity,
            "Unit_Price": unit_price,
            "Revenue": revenue,
        })

    return pd.DataFrame(data)


def create_data_sheet(
    df: pd.DataFrame,
    writer: pd.ExcelWriter,
    sheet_name: str = "Data",
    format_as_table: bool = True,
) -> None:
    """Write a DataFrame to an Excel sheet.

    Args:
        df: DataFrame to write.
        writer: ExcelWriter object.
        sheet_name: Name of the sheet.
        format_as_table: Whether to format as Excel table.
    """
    df.to_excel(writer, sheet_name=sheet_name, index=False)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Auto-adjust column widths
    for idx, col in enumerate(df.columns):
        max_length = max(
            df[col].astype(str).map(len).max(),
            len(str(col))
        ) + 2
        worksheet.set_column(idx, idx, min(max_length, 50))


def create_pivot_table(
    df: pd.DataFrame,
    writer: pd.ExcelWriter,
    sheet_name: str = "Pivot",
    values: str = "Revenue",
    index: Union[str, List[str]] = "Category",
    columns: Optional[Union[str, List[str]]] = "Region",
    aggfunc: str = "sum",
) -> pd.DataFrame:
    """Create a pivot table and write it to an Excel sheet.

    Args:
        df: Source DataFrame.
        writer: ExcelWriter object.
        sheet_name: Name of the pivot sheet.
        values: Column to aggregate.
        index: Row grouping column(s).
        columns: Column grouping column(s).
        aggfunc: Aggregation function ('sum', 'mean', 'count', etc.).

    Returns:
        The pivot table DataFrame.
    """
    pivot_df = pd.pivot_table(
        df,
        values=values,
        index=index,
        columns=columns,
        aggfunc=aggfunc,
        margins=True,
        margins_name="Total",
    )

    # Round numeric values
    pivot_df = pivot_df.round(2)

    pivot_df.to_excel(writer, sheet_name=sheet_name)

    workbook = writer.book
    worksheet = writer.sheets[sheet_name]

    # Auto-adjust column widths for pivot
    for idx in range(len(pivot_df.columns) + 1):
        worksheet.set_column(idx, idx, 15)

    return pivot_df


def create_excel_with_pivot(
    output_path: Union[str, Path],
    df: Optional[pd.DataFrame] = None,
    data_sheet_name: str = "Data",
    pivot_sheet_name: str = "Pivot",
    pivot_values: str = "Revenue",
    pivot_index: Union[str, List[str]] = "Category",
    pivot_columns: Optional[Union[str, List[str]]] = "Region",
    pivot_aggfunc: str = "sum",
    use_sample_data: bool = False,
    sample_rows: int = 100,
) -> Path:
    """Create an Excel file with a data sheet and a pivot table sheet.

    Args:
        output_path: Path for the output Excel file.
        df: DataFrame to use. If None and use_sample_data is True, generates sample data.
        data_sheet_name: Name of the data sheet.
        pivot_sheet_name: Name of the pivot table sheet.
        pivot_values: Column to aggregate in pivot.
        pivot_index: Row grouping for pivot.
        pivot_columns: Column grouping for pivot.
        pivot_aggfunc: Aggregation function for pivot.
        use_sample_data: Generate sample data if df is None.
        sample_rows: Number of rows for sample data.

    Returns:
        Path to the created Excel file.
    """
    output_path = Path(output_path)

    if df is None:
        if use_sample_data:
            df = generate_sample_data(rows=sample_rows)
        else:
            raise ValueError("Either provide a DataFrame or set use_sample_data=True")

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        # Create data sheet
        create_data_sheet(df, writer, sheet_name=data_sheet_name)

        # Create pivot table sheet
        create_pivot_table(
            df,
            writer,
            sheet_name=pivot_sheet_name,
            values=pivot_values,
            index=pivot_index,
            columns=pivot_columns,
            aggfunc=pivot_aggfunc,
        )

    return output_path


def create_excel_with_xlwings(
    output_path: Union[str, Path],
    df: Optional[pd.DataFrame] = None,
    data_sheet_name: str = "Data",
    pivot_sheet_name: str = "Pivot",
    pivot_values: str = "Revenue",
    pivot_index: str = "Category",
    pivot_columns: str = "Region",
    use_sample_data: bool = False,
    sample_rows: int = 100,
    visible: bool = False,
) -> Path:
    """Create an Excel file using xlwings for more advanced features.

    This function uses xlwings to interact with Excel directly,
    enabling native Excel pivot tables and formatting.

    Args:
        output_path: Path for the output Excel file.
        df: DataFrame to use.
        data_sheet_name: Name of the data sheet.
        pivot_sheet_name: Name of the pivot table sheet.
        pivot_values: Column to aggregate in pivot.
        pivot_index: Row grouping for pivot.
        pivot_columns: Column grouping for pivot.
        use_sample_data: Generate sample data if df is None.
        sample_rows: Number of rows for sample data.
        visible: Whether to show Excel during creation.

    Returns:
        Path to the created Excel file.
    """
    try:
        import xlwings as xw
    except ImportError:
        raise ImportError("xlwings is required for this function. Install with: pip install xlwings")

    output_path = Path(output_path)

    if df is None:
        if use_sample_data:
            df = generate_sample_data(rows=sample_rows)
        else:
            raise ValueError("Either provide a DataFrame or set use_sample_data=True")

    # Create workbook with xlwings
    app = xw.App(visible=visible)
    try:
        wb = app.books.add()

        # Add data sheet
        data_sheet = wb.sheets[0]
        data_sheet.name = data_sheet_name
        data_sheet.range("A1").value = df

        # Auto-fit columns
        data_sheet.autofit()

        # Add pivot sheet with pandas pivot (xlwings native pivot requires Excel COM)
        pivot_df = pd.pivot_table(
            df,
            values=pivot_values,
            index=pivot_index,
            columns=pivot_columns,
            aggfunc="sum",
            margins=True,
            margins_name="Total",
        ).round(2)

        pivot_sheet = wb.sheets.add(name=pivot_sheet_name, after=data_sheet)
        pivot_sheet.range("A1").value = pivot_df
        pivot_sheet.autofit()

        # Format pivot table headers
        header_range = pivot_sheet.range("A1").expand("right")
        header_range.color = (66, 133, 244)  # Blue
        header_range.font.color = (255, 255, 255)  # White
        header_range.font.bold = True

        # Save and close
        wb.save(str(output_path))
        wb.close()

    finally:
        app.quit()

    return output_path


def read_excel_to_dataframe(
    file_path: Union[str, Path],
    sheet_name: Optional[str] = None,
) -> pd.DataFrame:
    """Read an Excel file into a DataFrame.

    Args:
        file_path: Path to the Excel file.
        sheet_name: Specific sheet to read. If None, reads first sheet.

    Returns:
        DataFrame with the Excel data.
    """
    return pd.read_excel(file_path, sheet_name=sheet_name)
