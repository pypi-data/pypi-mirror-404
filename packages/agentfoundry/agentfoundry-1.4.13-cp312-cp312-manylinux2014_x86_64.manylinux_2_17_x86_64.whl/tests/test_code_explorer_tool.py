import pytest
from unittest.mock import patch
from pathlib import Path
from agentfoundry.agents.tools.code_explorer_tool import code_explorer

@pytest.fixture
def workspace(tmp_path):
    # Create a dummy workspace
    (tmp_path / "file1.txt").write_text("Hello World\nLine 2")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("print('Hello World')\n# TODO: Fix this")
    (tmp_path / "src" / "utils.py").write_text("def util(): pass")
    return tmp_path

@pytest.fixture
def mock_cwd(workspace):
    with patch("agentfoundry.agents.tools.code_explorer_tool.Path.cwd", return_value=workspace):
        yield workspace

def test_list_root(mock_cwd):
    result = code_explorer(action="list")
    assert "entries" in result
    entries = result["entries"]
    assert "file1.txt" in entries
    assert "src" in entries

def test_list_subdir(mock_cwd):
    result = code_explorer(action="list", path="src")
    assert "entries" in result
    entries = result["entries"]
    assert "main.py" in entries
    assert "utils.py" in entries

def test_read_file(mock_cwd):
    result = code_explorer(action="read", path="file1.txt")
    assert "content" in result
    assert result["content"] == "Hello World\nLine 2"

def test_search(mock_cwd):
    result = code_explorer(action="search", pattern="Hello World")
    assert "matches" in result
    matches = result["matches"]
    assert len(matches) == 2
    # Check paths (relative to root)
    paths = sorted([m["path"] for m in matches])
    assert paths == ["file1.txt", "src/main.py"]

def test_search_limit(mock_cwd):
    result = code_explorer(action="search", pattern="Hello World", max_results=1)
    assert len(result["matches"]) == 1

def test_tree(mock_cwd):
    result = code_explorer(action="tree")
    assert "tree" in result
    tree = result["tree"]
    assert "file1.txt" in tree
    assert "src" in tree
    assert "main.py" in tree
    assert "utils.py" in tree

def test_invalid_path(mock_cwd):
    result = code_explorer(action="list", path="nonexistent")
    assert "error" in result
    assert "not found" in result["error"].lower()

def test_missing_path_read(mock_cwd):
    result = code_explorer(action="read")
    assert "error" in result
    assert "missing 'path'" in result["error"].lower()

def test_missing_pattern_search(mock_cwd):
    result = code_explorer(action="search")
    assert "error" in result
    assert "missing 'pattern'" in result["error"].lower()
