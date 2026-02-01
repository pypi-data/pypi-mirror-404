"""
code_validator.py

A module for validating Python source code.
It checks for:
    - Syntax correctness
    - Presence of required metadata (e.g. __author__, __version__)
    - Presence of docstrings in functions and classes
"""

import ast
from typing import Any, Dict, List, Tuple

import logging


class CodeValidator:
    def __init__(self, code: str):
        """
        Initialize the CodeValidator with the source code as a string.

        Args:
            code (str): The Python source code to validate.
        """
        self.logger = logging.getLogger(__name__)
        self.code = code
        self.tree = None
        self.syntax_error = None
        self.logger.info("Initializing CodeValidator")
        self._parse_code()

    def _parse_code(self) -> None:
        """
        Attempt to parse the code into an AST. If a syntax error occurs,
        store the error message.
        """
        self.logger.info("Parsing code to AST for syntax validation")
        try:
            self.tree = ast.parse(self.code)
            self.logger.debug("AST parsing successful")
        except SyntaxError as e:
            self.syntax_error = str(e)
            self.tree = None
            self.logger.warning(f"Syntax error during parsing: {self.syntax_error}")

    def validate_syntax(self) -> Tuple[bool, str]:
        """
        Validate that the code has correct syntax.

        Returns:
            Tuple[bool, str]: A tuple (is_valid, error_message). If valid, error_message is empty.
        """
        self.logger.info("Validating syntax")
        if self.tree is not None:
            self.logger.debug("Syntax is valid")
            return True, ""
        error_msg = self.syntax_error or "Unknown syntax error."
        self.logger.error(f"Syntax validation failed: {error_msg}")
        return False, error_msg

    def validate_metadata(self, required_keys: List[str] = None) -> List[str]:
        """
        Validate that required metadata variables are present in the code.
        By default, it requires __author__ and __version__.

        Args:
            required_keys (List[str], optional): List of required metadata keys.

        Returns:
            List[str]: A list of missing metadata keys.
        """
        self.logger.info("Validating metadata fields in code")
        if required_keys is None:
            required_keys = ["__author__", "__version__"]

        metadata = {}
        if self.tree:
            for node in self.tree.body:
                if isinstance(node, ast.Assign):
                    if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                        var_name = node.targets[0].id
                        if var_name.startswith("__") and var_name.endswith("__"):
                            try:
                                value = ast.literal_eval(node.value)
                            except Exception:
                                value = None
                            metadata[var_name] = value

        missing = [key for key in required_keys if key not in metadata]
        return missing

    def validate_docstrings(self) -> List[str]:
        """
        Validate that all top-level functions and classes have docstrings.
        Also checks that methods (except __init__) within classes have docstrings.

        Returns:
            List[str]: A list of warnings indicating missing docstrings.
        """
        self.logger.info("Validating docstrings in functions and classes")
        warnings = []
        if self.tree is None:
            self.logger.warning("Skipping docstring validation due to parse errors")
            return warnings

        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    warnings.append(f"Function '{node.name}' is missing a docstring.")
            elif isinstance(node, ast.ClassDef):
                if not ast.get_docstring(node):
                    warnings.append(f"Class '{node.name}' is missing a docstring.")
                # Check methods within the class (excluding __init__ as an example)
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name != "__init__":
                        if not ast.get_docstring(item):
                            warnings.append(f"Method '{node.name}.{item.name}' is missing a docstring.")
        return warnings

    def validate(self) -> Dict[str, Any]:
        """
        Run all validations and return a summary of results.

        Returns:
            Dict[str, Any]: A dictionary with keys:
                - syntax_valid: bool
                - syntax_error: str (if any)
                - missing_metadata: list of missing metadata keys
                - docstring_warnings: list of warnings for missing docstrings
        """
        self.logger.info("Starting full code validation")
        syntax_valid, syntax_error = self.validate_syntax()
        metadata_missing = self.validate_metadata() if syntax_valid else []
        docstring_warnings = self.validate_docstrings() if syntax_valid else []
        result = {
            "syntax_valid": syntax_valid,
            "syntax_error": syntax_error,
            "missing_metadata": metadata_missing,
            "docstring_warnings": docstring_warnings
        }
        self.logger.debug(f"Validation result: {result}")
        return result


def validate_file(file_path: str) -> Dict[str, Any]:
    """
    Validate a Python source file and return the validation results.

    Args:
        file_path (str): The path to the Python source file.

    Returns:
        Dict[str, Any]: The validation results.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()
    validator = CodeValidator(code)
    return validator.validate()


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        results = validate_file(file_path)
        print(json.dumps(results, indent=4))
    else:
        print("Usage: python code_validator.py <file_path>")
