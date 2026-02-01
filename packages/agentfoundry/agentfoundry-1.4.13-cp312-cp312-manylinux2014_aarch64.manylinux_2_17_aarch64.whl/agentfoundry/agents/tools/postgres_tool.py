import psycopg2
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class PostgresInput(BaseModel):
    """Input schema for the postgres_query_executor tool."""
    server: str = Field(..., description="The Python source code to write to disk")
    port: str = Field(..., description="The full path where the .py file will be saved")
    username: str = Field(..., description="The username to connect to the DB")
    password: str = Field(..., description="The password to connect to the DB")
    dbname: str = Field(..., description="The dbname to connect to the DB")
    query: str = Field(..., description="The query to be executed on the DB")


def postgres_query_executor(
        server: str,
        port: str,
        username: str,
        password: str,
        dbname: str,
        query: str

) -> str:
    """
    Execute a SQL query using connection parameters from a JSON string.

    Args:
        "server": "localhost\\SQLEXPRESS",
        "dbname": "master",
        "port": "port",
        "username": "sa",
        "password": "your_password",
        "query": "SQL Query to execute"
    Returns:
        str: Query result or error message.
    """
    try:
        conn = psycopg2.connect(
            host=server,
            port=port,
            user=username,
            password=password,
            dbname=dbname,
            sslmode="require"
        )
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return str(rows)
    except Exception as e:
        return f"Error executing query: {e}"


# Wrap the function as a LangChain Tool.
sqlite_tool = StructuredTool(
    name="postgres_server_query",
    func=postgres_query_executor,
    description=(
        "Executes a SQL query on a Postgres Server database using connection parameters provided in the parameters. "
        "Input must include both the SQL query and the connection configuration in the following format:"
        '  "host": str = "your_host_url,\n'
        '  "port": str = "your_port",\n'
        '  "user": str = "your_user",\n'
        '  "password": str = "your_pass",\n'
        '  "dbname": str = "your_dbs_name", \n'
        '  "query": str = "query to execute"'
        "Returns the query result as a string. This tool is intended for direct SQL execution where the user provides full context."
    ),
    args_schema=PostgresInput
)
