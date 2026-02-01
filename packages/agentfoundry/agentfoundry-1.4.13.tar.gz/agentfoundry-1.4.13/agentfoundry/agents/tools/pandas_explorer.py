from langchain_core.tools import Tool
import pandas as pd
import io
import traceback


def summarize_csv(file_path: str) -> str:
    """
    Synchronously read the CSV at `file_path`, compute DataFrame info, descriptive stats,
    and missing‐value counts, then return a combined string summary.
    """
    try:
        # 1. Read CSV into DataFrame
        df = pd.read_csv(file_path)

        # 2. Capture df.info() output
        buf = io.StringIO()
        df.info(buf=buf)
        info_str = buf.getvalue()

        # 3. Compute descriptive statistics (include all dtypes)
        desc_df = df.describe(include='all')
        desc_str = desc_df.to_string()

        # 4. Compute missing‐value counts
        missing_series = df.isnull().sum()
        missing_str = missing_series.to_string()

        # 5. Compose the final summary
        summary = (
            f"DataFrame Info:\n{info_str}\n\n"
            f"Descriptive Statistics (all columns):\n{desc_str}\n\n"
            f"Missing Values per Column:\n{missing_str}"
        )
        return summary

    except Exception as e:
        tb = traceback.format_exc()
        return f"Error summarizing CSV '{file_path}': {e}\n{tb}"


csv_explorer_tool = Tool(
    name="summarize_csv",
    func=summarize_csv,
    description=(
        "Given the function argument 'file_path' which is a string containing a file path to a CSV, load it into a "
        "pandas DataFrame and return a text summary that includes column data types, row count, descriptive statistics"
        " for all columns, and missing‐value counts per column."
    )
)

# Alias tool name expected by allowed tool list
pandas_explorer = Tool(
    name="pandas_explorer",
    func=summarize_csv,
    description="Explore a CSV via pandas; returns schema, descriptive stats, and missing-value counts."
)
