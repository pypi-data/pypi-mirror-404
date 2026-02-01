"""
code_parser.py

A module for parsing Python source code using the Abstract Syntax Tree (AST)
to extract structured information such as metadata, imports, functions, and classes.
"""

import ast
from typing import Any, Dict, List

import logging


class CodeParser:
    def __init__(self, code: str):
        """
        Initialize the CodeParser with the source code as a string.

        Args:
            code (str): The Python source code to parse.
        """
        self.logger = logging.getLogger(__name__)
        self.code = code
        self.logger.info("Initializing CodeParser")
        try:
            self.tree = ast.parse(code)
            self.logger.debug("Parsed AST tree successfully")
        except Exception as e:
            self.logger.error(f"Failed to parse code: {e}", exc_info=True)
            raise

    def get_metadata(self) -> Dict[str, Any]:
        """
        Extract top-level metadata variables (e.g. __author__, __version__) from the code.

        Returns:
            Dict[str, Any]: A dictionary of metadata names to their evaluated values.
        """
        self.logger.info("Extracting metadata from code")
        metadata = {}
        for node in self.tree.body:
            if isinstance(node, ast.Assign):
                # Look for simple assignments where the target is a Name.
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id
                    # Check for common metadata identifiers (start and end with __)
                    if var_name.startswith("__") and var_name.endswith("__"):
                        try:
                            value = ast.literal_eval(node.value)
                        except Exception:
                            value = None
                        metadata[var_name] = value
        return metadata

    def get_imports(self) -> List[str]:
        """
        Retrieve all imported module names in the code.

        Returns:
            List[str]: A list of unique module names that are imported.
        """
        self.logger.info("Extracting imports from code")
        imports = set()
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
        return list(imports)

    def get_functions(self) -> List[Dict[str, Any]]:
        """
        Extract all top-level function definitions along with their docstrings.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries each containing the function's name and docstring.
        """
        self.logger.info("Extracting functions from code")
        functions = []
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node)
                }
                functions.append(func_info)
        return functions

    def get_classes(self) -> List[Dict[str, Any]]:
        """
        Extract all top-level class definitions, including their docstrings and methods.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries each containing:
                - name: The class name.
                - docstring: The class docstring.
                - methods: A list of methods with their names and docstrings.
        """
        self.logger.info("Extracting classes from code")
        classes = []
        for node in self.tree.body:
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": ast.get_docstring(node),
                    "methods": []
                }
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "docstring": ast.get_docstring(item)
                        }
                        class_info["methods"].append(method_info)
                classes.append(class_info)
        return classes

    def parse(self) -> Dict[str, Any]:
        """
        Parse the source code and aggregate all extracted information.

        Returns:
            Dict[str, Any]: A dictionary with keys 'metadata', 'imports', 'functions', and 'classes'.
        """
        self.logger.info("Running full code parse")
        result = {
            "metadata": self.get_metadata(),
            "imports": self.get_imports(),
            "functions": self.get_functions(),
            "classes": self.get_classes()
        }
        self.logger.debug(f"Parse result: {result}")
        return result


def parse_file(file_path: str) -> Dict[str, Any]:
    """
    Read a Python source file, parse its content, and return the structured information.

    Args:
        file_path (str): The path to the Python source file.

    Returns:
        Dict[str, Any]: The parsed information from the file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    parser = CodeParser(code)
    return parser.parse()


if __name__ == "__main__":
    # Simple command-line interface for testing the parser.
    import sys
    import json

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            result = parse_file(file_path)
            print(json.dumps(result, indent=4))
        except Exception as e:
            print(f"Error parsing file '{file_path}': {e}")
    else:
        print("Usage: python code_parser.py <file_path>")
