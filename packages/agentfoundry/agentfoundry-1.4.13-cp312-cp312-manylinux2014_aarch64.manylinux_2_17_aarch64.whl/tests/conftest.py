# Ensure tests import the local agentfoundry package rather than an installed version
import os, sys

# Prepend project root (one level up) so that imports resolve to local code
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("AGENTFOUNDRY_ENFORCE_LICENSE", "0")
os.environ.setdefault("AF_DISABLE_OPENAI_EMBEDDINGS", "1")

def pytest_configure(config):
    """Unregister conflicting plugins so pytest can collect tests as usual."""
    for name in ("helpconfig", "langsmith"):
        try:
            config.pluginmanager.unregister(name=name)
        except Exception:
            pass
