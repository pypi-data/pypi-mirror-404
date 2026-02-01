import os
import traceback
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class CreatePythonFileInput(BaseModel):
    """Input schema for the create_python_file_structured tool."""
    code: str = Field(..., description="The Python source code to write to disk")
    file_path: str = Field(..., description="The full path where the .py file will be saved")


def create_python_file_structured(
        code: str,
        file_path: str) -> str:
    """
    Writes `code` to `file_path` and returns the path on success,
    or an error message on failure.
    """
    try:
        # Ensure containing directory exists
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)

        # Write out the code
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        return file_path
    except Exception as e:
        tb = traceback.format_exc()
        return f"Error writing python file: {e}\n{tb}"


python_file_writer_tool = StructuredTool(
    name="python_file_writer",
    description=(
        "Writes Python source code to a file. "
        "Takes a JSON object with:\n"
        "- code: the Python code to write\n"
        "- file_path: destination .py file path\n"
        "Returns the file_path on success or an error message."
    ),
    args_schema=CreatePythonFileInput,
    func=create_python_file_structured,
)
