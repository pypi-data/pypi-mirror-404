import os
import tempfile
import zipfile
import traceback
from typing import List
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool


class UnzipFileInput(BaseModel):
    """Input schema for the unzip_file_structured tool."""
    zip_path: str = Field(..., description="The path to the zip file to be unzipped")


def unzip_file_structured(zip_path: str) -> List[str]:
    """
    Unzips `zip_path` into a temporary directory and returns a list of extracted file paths.
    """
    try:
        if not os.path.isfile(zip_path):
            return [f"Error: Zip file '{zip_path}' does not exist"]

        temp_dir = tempfile.mkdtemp(prefix="unzipped_")
        extracted_files = []

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(temp_dir)
            for root, _, files in os.walk(temp_dir):
                for file_name in files:
                    extracted_files.append(os.path.join(root, file_name))

        return extracted_files
    except Exception as e:
        tb = traceback.format_exc()
        return [f"Error unzipping file: {e}\n{tb}"]


unzip_file_tool = StructuredTool(
    name="unzip_file",
    description=(
        "Unzips a zip archive into a temporary directory. "
        "Takes a JSON object with:\n"
        "- zip_path: path to the .zip file\n"
        "Returns a list of paths of all extracted files, or an error message."
    ),
    args_schema=UnzipFileInput,
    func=unzip_file_structured,
)

# Alias tool name expected by allowed tool list
unzip_tool = StructuredTool.from_function(
    func=unzip_file_structured,
    name="unzip_tool",
    description="Unzip a .zip archive into a temporary folder and return extracted file paths.",
    args_schema=UnzipFileInput,
)
