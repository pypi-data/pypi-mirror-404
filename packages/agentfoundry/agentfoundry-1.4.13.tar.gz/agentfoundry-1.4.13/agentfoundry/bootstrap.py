"""
Bootstrap executed *before* the heavy AgentFoundry modules load.

The helper must remain **pure-Python** – importing nothing that could
trigger the loading of compiled extensions (``.so``/``.pyd``).  Its sole
responsibility is to enforce licencing and verify a minimal runtime
environment before the rest of the package is allowed to initialise.
"""

from __future__ import annotations

import os
import sys

# *Only* import from the lightweight licence sub-package to avoid any
# accidental pull-in of heavy dependencies.
from agentfoundry.license.key_manager import KeyManager

__all__ = ["run"]


def run() -> None:  # noqa: D401
    """Validate the licence and guard mandatory environment variables.

    The function terminates the process (`sys.exit(1)`) if either check
    fails – preventing any further startup that might leak functionality
    to unlicensed or mis-configured environments.
    """

    # ------------------------------------------------------------------
    # 1. Licence validation
    # ------------------------------------------------------------------
    try:
        KeyManager().validate_license()  # exits on invalid licence
    except Exception as exc:  # pragma: no cover – fail hard
        sys.stderr.write(f"[AgentFoundry] Licence error: {exc}\n")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Optional environment guards
    # ------------------------------------------------------------------
    required = (
        "OPENAI_API_KEY",
        # Extend this tuple with additional variables as needed.
    )

    missing = [v for v in required if v not in os.environ]
    if missing:  # pragma: no cover
        sys.stderr.write(f"[AgentFoundry] Missing env vars: {missing}\n")
        sys.exit(1)


# Allow quick smoke-testing via ``python -m agentfoundry.bootstrap``
if __name__ == "__main__":  # pragma: no cover
    run()
    print("AgentFoundry bootstrap completed successfully.")

