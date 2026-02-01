from pathlib import Path
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

import logging

logger = logging.getLogger(__name__)


class CodeExplorerInput(BaseModel):
    action: str = Field(
        ..., description="Action to perform: 'list', 'read', 'search', or 'tree'."
    )
    path: Optional[str] = Field(
        None, description="Path relative to the project root for 'list', 'read', or 'tree' actions."
    )
    pattern: Optional[str] = Field(
        None, description="Substring pattern to search for in code for 'search' action."
    )
    max_results: Optional[int] = Field(
        10, description="Maximum number of results to return for 'search' action."
    )


def code_explorer(
    action: str,
    path: Optional[str] = None,
    pattern: Optional[str] = None,
    max_results: int = 10,
) -> Dict[str, object]:
    """
    Explore the code base. Actions:
      - list: list files/directories at a given path (or project root if not specified)
      - read: return the content of a file at the given path
      - search: find lines containing the given pattern across the code base
      - tree: show a directory tree starting at the given path (or project root)
    """
    logger.info(
        f"CodeExplorer called with action={action}, path={path}, "
        f"pattern={pattern}, max_results={max_results}"
    )
    root = Path.cwd()
    try:
        if action == "list":
            target = root if path is None else root / path
            if not target.exists():
                return {"error": f"Path not found: {path}"}
            entries = [p.name for p in sorted(target.iterdir())]
            logger.debug(f"List entries at '{target}': {entries}")
            return {"entries": entries}

        if action == "read":
            if not path:
                return {"error": "Missing 'path' parameter for read action"}
            file_path = root / path
            if not file_path.exists() or not file_path.is_file():
                return {"error": f"File not found: {path}"}
            content = file_path.read_text(errors="ignore")
            logger.debug(f"Read file '{file_path}' ({len(content.splitlines())} lines)")
            return {"content": content}

        if action == "search":
            if not pattern:
                return {"error": "Missing 'pattern' parameter for search action"}
            matches: List[Dict] = []
            for file_path in root.rglob("*"):
                if not file_path.is_file():
                    continue
                try:
                    for lineno, line in enumerate(
                        file_path.read_text(errors="ignore").splitlines(), start=1
                    ):
                        if pattern in line:
                            matches.append(
                                {
                                    "path": str(file_path.relative_to(root)),
                                    "line": lineno,
                                    "text": line.strip(),
                                }
                            )
                            if len(matches) >= max_results:
                                break
                except Exception as e:
                    logger.warning(f"Failed to read '{file_path}': {e}")
                if len(matches) >= max_results:
                    break
            logger.debug(f"Search found {len(matches)} matches for pattern '{pattern}'")
            return {"matches": matches}

        if action == "tree":
            target = root if path is None else root / path
            if not target.exists() or not target.is_dir():
                return {"error": f"Directory not found: {path}"}
            tree_lines: List[str] = []

            def build_tree(dir_path: Path, prefix: str = ""):
                entries = sorted(dir_path.iterdir())
                for index, entry in enumerate(entries):
                    connector = "└── " if index == len(entries) - 1 else "├── "
                    tree_lines.append(prefix + connector + entry.name)
                    if entry.is_dir():
                        extension = "    " if index == len(entries) - 1 else "│   "
                        build_tree(entry, prefix + extension)

            build_tree(target)
            logger.debug(f"Directory tree at '{target}':\n" + "\n".join(tree_lines))
            return {"tree": "\n".join(tree_lines)}

        return {"error": f"Unknown action: {action}"}
    except Exception as ex:
        logger.error(f"Exception in code_explorer: {ex}", exc_info=True)
        return {"error": str(ex)}


code_explorer_tool = StructuredTool.from_function(
    func=code_explorer,
    name="code_explorer",
    description=code_explorer.__doc__,
    args_schema=CodeExplorerInput,
)
