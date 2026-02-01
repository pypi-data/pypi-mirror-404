import json
import sqlite3

from langchain_core.tools import Tool


def query_sqlite_generic(input_str: str) -> str:
    """
    Connects to a SQLite database using a file path provided in the input JSON, executes the SQL query,
    and returns the fetched rows as a string.

    The input should be a JSON string with the following keys:
      - "file_path": full path to the SQLite database file.
      - "query": a syntactically correct SQL query to execute.

    Example input:
    {
        "file_path": "./quantumdrive/data/chinook.sqlite",
        "query": "SELECT c.Country, SUM(i.Total) AS TotalSpent FROM Customer c JOIN Invoice i ON c.CustomerId = i.CustomerId GROUP BY c.Country ORDER BY TotalSpent DESC LIMIT 3;"
    }
    """
    try:
        data = json.loads(input_str)
    except Exception as e:
        return f"Error parsing input JSON: {e}"

    file_path = data.get("file_path")
    query = data.get("query")

    if not file_path or not query:
        return "Error: Input must contain both 'file_path' and 'query' keys."

    try:
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return str(rows)
    except Exception as e:
        return f"Error executing query: {e}"


# Wrap the function as a LangChain Tool.
sqlite_tool = Tool(
    name="sqlite_query",
    func=query_sqlite_generic,
    description=(
        "Executes a SQL query on a SQLite database. "
        "Input must be a JSON string with keys 'file_path' (the database file path) and 'query' (the SQL query to execute). "
        "Returns the query result as a string."
    )
)

