# Dumont

Excel file generation tool with data sheets, pivot tables, and charts.

## Try it Online

Use Dumont directly in your browser - no installation required:

**https://dumont-1npt.onrender.com**

## Installation

```bash
pip install dumont
```

## Features

- **Pivot Tables**: Configurable aggregations (sum, mean, count, min, max)
- **Charts**: Bar, line, pie, doughnut, scatter, area
- **Professional Formatting**: Green headers, borders, autofilter, freeze panes
- **Multiple Interfaces**: CLI, Python API, and Web UI

## CLI Usage

### Create a Chart

```bash
# Bar chart from sample data
dumont chart -o sales.png -t bar -x Category -y Revenue

# Pie chart from CSV
dumont chart -i data.csv -t pie -x Category -y Revenue -o chart.png

# Line chart with grouping
dumont chart -t line -x Category -y Revenue --group-by Region -o trend.png
```

### Export Excel with Charts

```bash
# Excel with data, pivot table, and bar chart
dumont export -o report.xlsx

# Excel with pie chart
dumont export -o report.xlsx --chart pie

# Excel without chart
dumont export -o report.xlsx --chart none

# From CSV input
dumont export -i data.csv -o report.xlsx --chart line
```

### Generate Excel (pivot only)

```bash
# With sample data
dumont generate -o sales_report.xlsx

# From CSV/Excel input
dumont generate -i data.csv -o report.xlsx

# Custom pivot configuration
dumont generate -o report.xlsx \
    --pivot-values Revenue \
    --pivot-index Category \
    --pivot-columns Region \
    --aggfunc sum
```

### Other Commands

```bash
# Preview sample data
dumont sample --rows 20

# Preview Excel file
dumont preview report.xlsx --sheet Data --rows 10

# Get file info
dumont info report.xlsx

# Start local web server
dumont serve
```

## Web UI

Dumont includes a browser-based spreadsheet interface.

### Online Version

Use it directly at: **https://dumont-1npt.onrender.com**

### Local Server

```bash
dumont serve
# Open http://127.0.0.1:8000
```

### Web UI Features

- **Spreadsheet Interface**: Excel-like grid with cell editing and keyboard navigation
- **Data Loading**: Load sample data or upload CSV/Excel files
- **Pivot Tables**: Create and preview pivot tables with configurable options
- **Charts**: Create interactive charts (bar, line, pie, doughnut, scatter, area)
- **Export**: Download formatted Excel files with data, pivot tables, and charts

## Python API

```python
from dumont import create_excel_with_charts, create_chart, generate_sample_data

# Create chart image
df = generate_sample_data(rows=100)
create_chart(
    df=df,
    output_path="sales_chart.png",
    chart_type="bar",
    x_axis="Category",
    y_axis="Revenue",
    aggfunc="sum",
)

# Create Excel with pivot and chart
create_excel_with_charts(
    output_path="report.xlsx",
    use_sample_data=True,
    pivot_values="Revenue",
    pivot_index="Category",
    pivot_columns="Region",
    charts=[{
        "chart_type": "bar",
        "x_axis": "Category",
        "y_axis": "Revenue",
        "aggfunc": "sum",
    }],
)

# Use your own DataFrame
import pandas as pd

df = pd.read_csv("my_data.csv")
create_excel_with_charts(
    output_path="report.xlsx",
    df=df,
    pivot_values="Sales",
    pivot_index="Product",
    pivot_columns="Quarter",
    charts=[{"chart_type": "line", "x_axis": "Product", "y_axis": "Sales"}],
)
```

## Output Structure

Generated Excel files contain:

1. **Data Sheet**: Raw data with formatting and autofilter
2. **Pivot Sheet**: Pivot table with totals row highlighted
3. **Charts Sheet**: Embedded chart images (when charts are included)

## Chart Types

| Type | Description |
|------|-------------|
| `bar` | Vertical bar chart |
| `line` | Line chart with markers |
| `pie` | Pie chart with percentages |
| `doughnut` | Doughnut chart |
| `scatter` | Scatter plot |
| `area` | Area chart |

## Requirements

- Python 3.8+
- pandas
- xlsxwriter
- click
- openpyxl
- matplotlib

## License

MIT
