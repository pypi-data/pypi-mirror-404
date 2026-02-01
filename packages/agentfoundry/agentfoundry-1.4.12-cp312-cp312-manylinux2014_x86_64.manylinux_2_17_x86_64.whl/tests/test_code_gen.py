import pytest
from agentfoundry.code_gen.code_parser import CodeParser
from agentfoundry.code_gen.code_validator import CodeValidator

# --- Test Data ---

VALID_CODE = '''
__author__ = "Test User"
__version__ = "1.0.0"

import os
from sys import path

def my_func(a, b):
    """This is a function."""
    return a + b

class MyClass:
    """This is a class."""
    def method(self):
        """This is a method."""
        pass
'''

INVALID_SYNTAX_CODE = """
def my_func(a, b)
    return a + b
"""

MISSING_METADATA_CODE = '''
import os

def foo():
    """Docstring."""
    pass
'''

MISSING_DOCSTRING_CODE = """
__author__ = "Me"
__version__ = "1.0"

def no_doc():
    pass

class NoDocClass:
    def method(self):
        pass
"""

# --- CodeParser Tests ---

def test_parser_init():
    parser = CodeParser(VALID_CODE)
    assert parser.tree is not None

def test_parser_metadata():
    parser = CodeParser(VALID_CODE)
    metadata = parser.get_metadata()
    assert metadata["__author__"] == "Test User"
    assert metadata["__version__"] == "1.0.0"

def test_parser_imports():
    parser = CodeParser(VALID_CODE)
    imports = parser.get_imports()
    assert "os" in imports
    assert "sys" in imports or "path" in imports # Depending on implementation details

def test_parser_functions():
    parser = CodeParser(VALID_CODE)
    funcs = parser.get_functions()
    assert len(funcs) == 1
    assert funcs[0]["name"] == "my_func"
    assert funcs[0]["docstring"] == "This is a function."

def test_parser_classes():
    parser = CodeParser(VALID_CODE)
    classes = parser.get_classes()
    assert len(classes) == 1
    assert classes[0]["name"] == "MyClass"
    assert classes[0]["docstring"] == "This is a class."
    assert len(classes[0]["methods"]) == 1
    assert classes[0]["methods"][0]["name"] == "method"

def test_parser_parse_all():
    parser = CodeParser(VALID_CODE)
    result = parser.parse()
    assert "metadata" in result
    assert "imports" in result
    assert "functions" in result
    assert "classes" in result

def test_parser_invalid_syntax():
    with pytest.raises(SyntaxError):
        CodeParser(INVALID_SYNTAX_CODE)

# --- CodeValidator Tests ---

def test_validator_valid_code():
    validator = CodeValidator(VALID_CODE)
    result = validator.validate()
    assert result["syntax_valid"] is True
    assert result["syntax_error"] == ""
    assert len(result["missing_metadata"]) == 0
    assert len(result["docstring_warnings"]) == 0

def test_validator_syntax_error():
    validator = CodeValidator(INVALID_SYNTAX_CODE)
    result = validator.validate()
    assert result["syntax_valid"] is False
    assert result["syntax_error"] != ""

def test_validator_missing_metadata():
    validator = CodeValidator(MISSING_METADATA_CODE)
    missing = validator.validate_metadata()
    assert "__author__" in missing
    assert "__version__" in missing

def test_validator_missing_docstrings():
    validator = CodeValidator(MISSING_DOCSTRING_CODE)
    warnings = validator.validate_docstrings()
    
    warning_texts = [w for w in warnings]
    assert any("Function 'no_doc' is missing a docstring" in w for w in warning_texts)
    assert any("Class 'NoDocClass' is missing a docstring" in w for w in warning_texts)
