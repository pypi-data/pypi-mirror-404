#!/usr/bin/env python
import os
import subprocess
from setuptools import find_packages, setup, Extension
from Cython.Build import cythonize

# Persist Cython's cache across builds so unchanged modules aren't re-cythonized
CYTHON_CACHE_DIR = os.environ.get(
    "CYTHON_CACHE_DIR",
    os.path.join(os.path.dirname(__file__), ".cython_cache"),
)
os.makedirs(CYTHON_CACHE_DIR, exist_ok=True)
os.environ.setdefault("CYTHON_CACHE_DIR", CYTHON_CACHE_DIR)
CYTHON_FORCE_REBUILD = os.environ.get("CYTHON_FORCE_REBUILD", "0") == "1"
SKIP_CYTHON = os.environ.get("SKIP_CYTHON", "0") == "1"


def get_git_tag():
    """
    Resolve the version from git tags, preferring the highest semantic version
    (vX.Y.Z) rather than the most recent annotated tag (git describe can favor
    older annotated tags on the same commit).
    """
    candidates: list[str] = []
    try:
        cmd = ["git", "tag", "--list", "v*", "--sort=-v:refname"]
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
        if out:
            candidates = out.splitlines()
    except subprocess.CalledProcessError:
        candidates = []

    tag = candidates[0] if candidates else None

    if not tag:
        try:
            tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                stderr=subprocess.STDOUT
            ).decode().strip()
        except subprocess.CalledProcessError:
            tag = None

    if tag:
        return tag.lstrip('v')

    # Fallback to VERSION file if present (for sdist installs without .git)
    version_file = os.path.join(os.path.dirname(__file__), 'VERSION')
    if os.path.exists(version_file):
        with open(version_file, 'r') as vf:
            return vf.read().strip().lstrip('v')
    return "0.0.0"


def get_cython_sources(base_dir: str) -> list[str]:
    sources: list[str] = []
    # Normalize the ignore path for the current OS
    ignore_path = os.path.join("agentfoundry", "agents", "tools")
    # Exclude Pydantic models from compilation to avoid runtime errors
    ignore_files = {
        "agent_config.py",
        "openai_llm.py",
        "gemini_llm.py",
        "grok_llm.py", 
        "grok_chatxai_logging.py"
    } 
    
    for dirpath, _, filenames in os.walk(base_dir):
        # Skip the tools directory so those files remain pure Python
        # (required for LangChain's introspection/decorators to work)
        if ignore_path in dirpath:
            continue

        for filename in filenames:
            if filename == "__init__.py" or filename in ignore_files:
                continue
            if filename.endswith((".py", ".pyx")):
                sources.append(os.path.join(dirpath, filename))
    
    print(f"DEBUG: Cython sources found: {len(sources)}")
    if any("agent_config.py" in s for s in sources):
        print("CRITICAL WARNING: agent_config.py IS included in compilation list!")
    else:
        print("DEBUG: agent_config.py is correctly excluded.")
        
    return sources


def create_extensions(base_dir: str) -> list[Extension]:
    extensions: list[Extension] = []
    for source in get_cython_sources(base_dir):
        module_name, _ = os.path.splitext(source.replace(os.sep, '.'))
        extensions.append(Extension(module_name, [source]))
    return extensions


def to_c_path(source: str) -> str:
    root, _ = os.path.splitext(source)
    return os.path.join("build_cython", *root.split(os.sep)) + ".c"


def build_ext_modules(base_dir: str) -> list[Extension]:
    extensions = create_extensions(base_dir)
    if SKIP_CYTHON:
        # Reuse previously generated C files (no re-cythonization).
        for ext in extensions:
            ext.sources = [to_c_path(src) for src in ext.sources]
        return extensions

    return cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "emit_code_comments": False,
            "linetrace": False,
            "binding": False,
        },
        build_dir="build_cython",
        force=CYTHON_FORCE_REBUILD,
        cache=True,
    )


ext_modules = build_ext_modules("agentfoundry")

# ------------------------------------------------------------------
# Helper to read runtime requirements from requirements.txt so that the
# list only ever needs to be maintained in one place.
# ------------------------------------------------------------------


def read_requirements(path: str = "requirements.txt") -> list:
    """Return a list of requirement strings from *path* (ignoring comments)."""

    req_file = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(req_file):
        return []

    with open(req_file, "r", encoding="utf-8") as fp:
        return [
            line.strip()
            for line in fp
            if line.strip() and not line.startswith("#")
        ]

dist_name = "agentfoundry"
if os.getenv("AGENTFOUNDRY_ENFORCE_LICENSE", "1") == "0":
    dist_name += "-nolicense"

setup(
    name=dist_name,
    version=get_git_tag(),
    ext_modules=ext_modules,
    packages=find_packages(include=["agentfoundry*"]),
    install_requires=read_requirements(),
    include_package_data=True,
    exclude_package_data={
        "": ["*.py", "*.pyc"],
    },
    package_data={
        # Root package
        "agentfoundry": ["__init__.py", "*.so", "*.pyd", "agentfoundry.pem", "agentfoundry.lic"],
        
        # Sub-packages (Compiled)
        "agentfoundry.agents": ["__init__.py", "*.so", "*.pyd"],
        "agentfoundry.chroma": ["__init__.py", "*.so", "*.pyd"],
        "agentfoundry.code_gen": ["__init__.py", "*.so", "*.pyd"],
        "agentfoundry.llm": ["__init__.py", "*.so", "*.pyd", "openai_llm.py", "gemini_llm.py", "grok_llm.py", "grok_chatxai_logging.py"],
        "agentfoundry.license": ["__init__.py", "*.so", "*.pyd", "public.pem"],
        "agentfoundry.registry": ["__init__.py", "*.so", "*.pyd"],
        # utils contains agent_config.py which must remain pure Python
        "agentfoundry.utils": ["__init__.py", "*.so", "*.pyd", "agent_config.py"],
        
        # Tools (Pure Python - NOT compiled)
        # We explicitly include *.py here because the global exclude_package_data
        # excludes them by default.
        "agentfoundry.agents.tools": ["__init__.py", "*.py", "*.so", "*.pyd"],
        
        # Resources
        "agentfoundry.resources": ["default_agentfoundry.toml"],
    },
    zip_safe=False,
)
