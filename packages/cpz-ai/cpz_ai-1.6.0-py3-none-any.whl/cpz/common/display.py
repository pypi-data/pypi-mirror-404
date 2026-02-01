"""
Display utilities for DataFrames with enhanced formatting
"""
from __future__ import annotations

from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


def display_dataframe_with_sticky_header(
    df: Any,  # pd.DataFrame, but lazy-loaded
    max_rows: int = 1000,
    max_height: str = "600px",
    show_index: bool = True,
) -> None:
    """
    Display a pandas DataFrame with a sticky/fixed header that stays visible while scrolling.
    
    This function outputs HTML with CSS that makes the table header stick to the top
    when scrolling through long tables. Works in Jupyter notebooks and many web-based
    execution environments that support HTML output.
    
    Args:
        df: The pandas DataFrame to display
        max_rows: Maximum number of rows to display (default: 1000)
        max_height: Maximum height of the table container before scrolling (default: "600px")
        show_index: Whether to show the DataFrame index column (default: True)
    
    Example:
        >>> from cpz.common.display import display_dataframe_with_sticky_header
        >>> df = client.download_csv_to_dataframe("user-data", "file.csv")
        >>> display_dataframe_with_sticky_header(df)
    """
    # Lazy-load pandas to avoid import errors if pandas isn't installed
    try:
        import pandas as pd
    except ImportError as e:
        raise ImportError(
            "pandas is required for display_dataframe_with_sticky_header. "
            "Install it with: pip install pandas"
        ) from e
    
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df)}")
    
    # Limit rows if needed
    display_df = df.head(max_rows) if len(df) > max_rows else df
    
    # Generate HTML table
    html_table = display_df.to_html(classes="cpz-sticky-table", index=show_index, escape=False)
    
    # Create HTML with CSS for sticky header
    html_output = f"""
    <style>
        .cpz-sticky-table-container {{
            max-height: {max_height};
            overflow-y: auto;
            overflow-x: auto;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .cpz-sticky-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0;
        }}
        .cpz-sticky-table thead {{
            position: sticky;
            top: 0;
            z-index: 10;
            background-color: #fff;
            box-shadow: 0 2px 2px -1px rgba(0, 0, 0, 0.4);
        }}
        .cpz-sticky-table th {{
            background-color: #f8f9fa;
            font-weight: bold;
            padding: 8px 12px;
            text-align: left;
            border-bottom: 2px solid #dee2e6;
            position: sticky;
            top: 0;
        }}
        .cpz-sticky-table td {{
            padding: 6px 12px;
            border-bottom: 1px solid #dee2e6;
        }}
        .cpz-sticky-table tr:hover {{
            background-color: #f5f5f5;
        }}
        .cpz-sticky-table thead tr:hover {{
            background-color: #f8f9fa;
        }}
    </style>
    <div class="cpz-sticky-table-container">
        {html_table}
    </div>
    """
    
    # Try to use IPython display if available (Jupyter notebooks)
    try:
        from IPython.display import HTML, display
        display(HTML(html_output))
    except ImportError:
        # Fallback: try to write HTML to a file or print instructions
        # In some environments, you might need to save and open the HTML
        print("HTML output with sticky header generated. If your environment supports HTML display,")
        print("the table should render with a sticky header. Otherwise, save the HTML to a file.")
        print("\nTo save as HTML file:")
        print("  with open('table.html', 'w') as f:")
        print("      f.write(html_output)")
        # Try to display anyway - some environments might support it
        try:
            import sys
            if hasattr(sys.stdout, 'write_html'):
                sys.stdout.write_html(html_output)
            else:
                # Last resort: print the HTML (might work in some web environments)
                print(html_output)
        except Exception:
            print("Could not display HTML. Your environment may not support HTML output.")


def display_dataframe_simple(df: pd.DataFrame, max_rows: int = 100) -> None:
    """
    Simple display function that outputs HTML with basic styling.
    Falls back to regular print if HTML display is not available.
    
    Args:
        df: The pandas DataFrame to display
        max_rows: Maximum number of rows to display
    """
    display_df = df.head(max_rows) if len(df) > max_rows else df
    
    try:
        from IPython.display import HTML, display
        html = display_df.to_html(classes="table table-striped", escape=False)
        display(HTML(html))
    except ImportError:
        # Fallback to regular display
        print(display_df)
