"""Package entry-point wrapper.

Executed when the user runs ``python -m agentfoundry`` or when a PyInstaller
binary launches the frozen application.  The module performs two distinct
phases:

1. Run the lightweight *bootstrap* checks (licence + critical env vars)
   without importing any sub-packages that might trigger the loading of
   compiled extensions.
2. Import and start the heavy-weight orchestration layer only after the
   environment has been validated.
"""

from __future__ import annotations

from agentfoundry.bootstrap import run as bootstrap_run

# ---------------------------------------------------------------------------
# Step-0 → licence + environment validation (no heavy imports yet)
# ---------------------------------------------------------------------------

bootstrap_run()

# ---------------------------------------------------------------------------
# Step-1 → it is now safe to import modules that may rely on C-extensions or
#          other expensive resources.
# ---------------------------------------------------------------------------

from agentfoundry.agents.orchestrator import Orchestrator  # noqa: E402  (delayed import)


def main() -> None:  # noqa: D401
    """Console entry-point delegated to the Orchestrator CLI."""

    # The real application might expose a richer interface (CLI args, server
    # mode, etc.).  For the scope of this wrapper we just start the interactive
    # CLI if present, otherwise we instantiate the orchestrator so that side
    # effects (such as model warm-up) are executed.

    orch = Orchestrator()

    start = getattr(orch, "start_cli", None)
    if callable(start):
        start()
    else:  # Fallback: simple informational message
        print("[AgentFoundry] Orchestrator initialised (no CLI exposed).")


if __name__ == "__main__":
    main()
