from langchain_core.tools import Tool
import subprocess
import tempfile
import traceback
import re
import os


def execute_python_code(result: str) -> str:
    """Executes Python code stored as a string."""
    match = re.search(r"```(?:python)?\s*([\s\S]*?)```", result)
    result = match.group(1) if match else result
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix='.py', delete=False) as script:
            script.write(result)
            script_path = script.name
        output = subprocess.run(['python', script_path], capture_output=True, text=True, timeout=15)
        return output.stdout if output.returncode == 0 else output.stderr
    except Exception as e:
        tb = traceback.format_exc()
        return f"Error running python code: {e}\n{tb}"
    finally:
        try:
            os.remove(script_path)
        except OSError:
            pass


python_code_executer = Tool(
    name="python_code_runner",
    func=execute_python_code,
    description=(
        "This tool executes Python code that is provided as a string. It saves the string into a temporary file and "
        "then uses subprocess to execute the code. It will return the output of the script if it runs successfully, "
        "the error from the subprocess or Python code execution, or any other exception and traceback as a string. "
        "This is a very sensitive tool - do not execute any code that can compromise the system itself and if any "
        "file modifying code, such as updating a CSV, should save a new file and not overwrite the original file."
    )
)