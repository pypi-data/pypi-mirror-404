# pandas_utils.py Documentation

## Overview
Pandas utilities module providing helper functions for DataFrame manipulation, including row filtering, column reordering, frame rollup operations, and hierarchical data structures.

## Functions

### `add_and_remove_from_frame(starting, to_add=None, to_drop=None, to_sort=False)`
Updates a DataFrame by adding/updating rows and removing others.
- **Parameters:**
  - `starting`: Base DataFrame
  - `to_add`: DataFrame with rows to add/update (optional)
  - `to_drop`: DataFrame with rows to remove (optional)
  - `to_sort`: If True, sorts result by index
- **Returns:** Updated DataFrame
- **Note:** Rows are uniquely identified by their index

### `filter_rows_from_frame(orig_frame, new_frame, columns)`
Filters out rows from orig_frame that exist in new_frame based on specified columns.
- **Parameters:**
  - `orig_frame`: Original DataFrame
  - `new_frame`: DataFrame containing rows to filter out
  - `columns`: Column(s) to use for matching (str or list)
- **Returns:** Filtered DataFrame
- **Note:** Assumes columns provided uniquely identify rows

### `replace_rows_from_frame(orig_frame, new_frame, columns)`
Replaces rows in orig_frame with those from new_frame based on specified columns.
- **Parameters:**
  - `orig_frame`: Original DataFrame
  - `new_frame`: DataFrame with replacement rows
  - `columns`: Column(s) to use for matching (str or list)
- **Returns:** DataFrame with replaced rows

### `get_first_value(frame, col, query=None, optional_value=None)`
Gets the first value from a specific column, optionally filtered by a query.
- **Parameters:**
  - `frame`: DataFrame to search
  - `col`: Column name to retrieve value from
  - `query`: Optional pandas query string to filter rows
  - `optional_value`: Value to return if no match found (default: np.nan)
- **Returns:** First value found or optional_value/np.nan

### `frame_regex_column_reorder(frame, *args, ignore_case=True, full_match=False, unmatched_at_end=False)`
Reorders DataFrame columns based on strings and regex patterns.
- **Parameters:**
  - `frame`: DataFrame to reorder
  - `*args`: List of strings or regex patterns for column matching
  - `ignore_case`: Case-insensitive matching (default: True)
  - `full_match`: Require full string match (default: False)
  - `unmatched_at_end`: Put unmatched columns at end (default: False)
- **Returns:** DataFrame with reordered columns

### `ordered_list_of_columns(frame, column_names_or_regex)`
Returns ordered list of column names matching strings or regex patterns.
- **Parameters:**
  - `frame`: DataFrame to search
  - `column_names_or_regex`: List of strings or regex patterns
- **Returns:** List of matching column names (duplicates removed)

### `rolled_up_frame(orig_frame, orig_groupby_cols, agg_cols, base_frame_name_col, add_total_line=True, show_grouping_columns=True, missing_name_override=None, extra_columns=None, name_col="display_name", keep_other_cols=False)`
Creates hierarchical rolled up DataFrame with multiple aggregation levels.
- **Parameters:**
  - `orig_frame`: Source DataFrame
  - `orig_groupby_cols`: Columns for grouping (min 2 required)
  - `agg_cols`: Columns to aggregate (sum)
  - `base_frame_name_col`: Column for display names in base frame
  - `add_total_line`: Add total summary row (default: True)
  - `show_grouping_columns`: Include groupby columns in output (default: True)
  - `missing_name_override`: Dict to override names for missing values
  - `extra_columns`: Additional columns to include
  - `name_col`: Name for display column (default: "display_name")
  - `keep_other_cols`: Keep non-aggregated columns (bool or list)
- **Returns:** Hierarchical DataFrame with rollup levels
- **Special Columns Added:**
  - `tg_key`: Unique key for each row
  - `tg_parent`: Parent row reference for hierarchy
  - `_level`: Hierarchy level (0=total, increasing for details)
  - `num_rows`: Count of aggregated rows (for non-base levels)

### `stringify_dataframe(df, float_precision=None, int_no_commas=None)`
Converts all DataFrame columns to formatted strings. Often used as preprocessing for markdown output.
- **Parameters:**
  - `df`: DataFrame to stringify
  - `float_precision`: Dict mapping column names to decimal precision (default: 0 for all floats)
  - `int_no_commas`: Set of integer column names to format without commas
- **Returns:** New DataFrame with all columns converted to strings
- **Formatting Rules:**
  - Datetime columns: Auto-detects date-only vs datetime format
    - Date-only (midnight times): `YYYY-MM-DD`
    - With time: `YYYY-MM-DD HH:MM:SS`
  - Integer columns: Comma-separated by default (e.g., `1,000`)
  - Float columns: Comma-separated with specified precision (default 0)
  - Other types: Converted to string

### `dataframe_to_markdown(df, float_precision=None, int_no_commas=None, colalign_override=None, stringify=True, index=False)`
Converts DataFrame to markdown format with automatic column alignment.
- **Parameters:**
  - `df`: DataFrame to convert
  - `float_precision`: Dict mapping column names to decimal precision (default: 0)
  - `int_no_commas`: Set of integer column names to format without commas
  - `colalign_override`: Dict mapping column names to alignment ('left', 'right', 'center')
  - `stringify`: Whether to stringify DataFrame first (default: True)
  - `index`: Whether to include index in output (default: False)
- **Returns:** Markdown formatted string
- **Requirements:** Requires `tabulate` package (`conda install tabulate`)
- **Note:** Default alignment is left for object columns, right for numeric columns

## Usage Examples

```python
from pandas_utils import get_first_value, rolled_up_frame
import pandas as pd

# Get first value from DataFrame
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
first_age = get_first_value(df, 'age', query='name == "Alice"')

# Create hierarchical rolled up frame
sales_df = pd.DataFrame({
    'region': ['North', 'North', 'South'],
    'product': ['A', 'B', 'A'],
    'salesperson': ['John', 'Jane', 'Bob'],
    'sales': [100, 150, 200]
})

rolled = rolled_up_frame(
    sales_df,
    orig_groupby_cols=['region', 'product'],
    agg_cols=['sales'],
    base_frame_name_col='salesperson',
    add_total_line=True
)
```