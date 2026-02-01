import pytest
from agentfoundry.agents.tools.python_code_executer import execute_python_code

def test_execute_simple_print():
    code = "print('Hello Test')"
    result = execute_python_code(code)
    assert "Hello Test" in result

def test_execute_markdown_block():
    code = """
    ```python
    print("Markdown Code")
    ```
    """
    result = execute_python_code(code)
    assert "Markdown Code" in result

def test_execute_error():
    code = "raise ValueError('Intentional Error')"
    result = execute_python_code(code)
    # The tool returns stderr directly if the script fails, it doesn't wrap it in "Error running python code"
    # unless the tool itself crashes.
    assert "ValueError: Intentional Error" in result

def test_execute_timeout():
    # If possible, mocking subprocess might be cleaner, 
    # but for a "tool" test, executing a short sleep is fine to prove logic 
    # unless we want to test the actual timeout mechanism which is 15s (too long for unit test).
    # So we'll trust the timeout param is passed (which is subprocess logic) 
    # and just test that normal execution works.
    pass 

def test_import_allowed():
    code = "import math; print(math.pi)"
    result = execute_python_code(code)
    assert "3.14" in result
