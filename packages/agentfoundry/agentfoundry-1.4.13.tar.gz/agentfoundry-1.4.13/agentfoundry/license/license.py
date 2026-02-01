__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "9/22/2023"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import os

from . import _license_core

_PKG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Logging (enable detailed logs with AGENTFOUNDRY_LICENSE_DEBUG=1)
logger = logging.getLogger(__name__)
_dbg_flag = os.getenv("AGENTFOUNDRY_LICENSE_DEBUG", "0").lower() in ("1", "true", "yes", "on")
if _dbg_flag and not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug("AGENTFOUNDRY_LICENSE_DEBUG enabled – verbose license logs active")


def _default_license_paths() -> list[str]:
    """Return candidate license file paths in priority order."""
    paths: list[str] = []
    # 1) Explicit env override
    env_path = os.getenv("AGENTFOUNDRY_LICENSE_FILE")
    if env_path:
        paths.append(os.path.expanduser(env_path))
    # 2) XDG config: ~/.config/agentfoundry/agentfoundry.lic
    xdg_home = os.getenv("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    paths.append(os.path.join(xdg_home, "agentfoundry", "agentfoundry.lic"))
    # 3) CWD convenience
    paths.append(os.path.join(os.getcwd(), "agentfoundry.lic"))
    # 4) Packaged fallback (site-packages/agentfoundry/agentfoundry.lic)
    paths.append(os.path.join(_PKG_DIR, "agentfoundry.lic"))
    logger.debug(f"Candidate license paths: {paths}")
    return paths


def _resolve_license_file() -> str:
    logger.debug("Resolving license file path…")
    for p in _default_license_paths():
        if p and os.path.exists(p):
            logger.info(f"Using license file: {p}")
            return p
    # Return the last path for error message clarity
    last = _default_license_paths()[-1]
    logger.warning(f"No license file found; last expected location: {last}")
    return last


LICENSE_FILE = _resolve_license_file()
PUBLIC_KEY_FILE = os.path.join(_PKG_DIR, "agentfoundry.pem")


def get_machine_id() -> str:
    mid = _license_core.current_machine_id().decode()
    logger.debug(f"Computed machine_id={mid}")
    print(f"Machine ID: {mid}")
    return mid


def verify_license() -> bool:
    logger.debug("verify_license: start")
    logger.debug(f"Resolved LICENSE_FILE={LICENSE_FILE}")
    try:
        ok, _ = _license_core.validate_license(LICENSE_FILE, PUBLIC_KEY_FILE, True)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        raise
    except RuntimeError as exc:
        logger.error(str(exc))
        raise

    logger.info("License validated successfully")
    return ok


def enforce_license():
    logger.debug("enforce_license: verifying…")
    ok = verify_license()
    logger.debug(f"enforce_license: verify_license -> {ok}")
    if not ok:
        logger.error("License invalid (verify_license returned False)")
        raise RuntimeError("Invalid, tampered, or expired AgentFoundry license.")
