__author__ = "Chris Steel"
__copyright__ = "Copyright 2023, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "10/23/2023"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging

import os

from . import _license_core

# Logging (enable with AGENTFOUNDRY_LICENSE_DEBUG=1)
logger = logging.getLogger(__name__)
_dbg_flag = os.getenv("AGENTFOUNDRY_LICENSE_DEBUG", "0").lower() in ("1", "true", "yes", "on")
if _dbg_flag and not logger.handlers:
    handler = logging.StreamHandler()
    fmt = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    logger.debug("AGENTFOUNDRY_LICENSE_DEBUG enabled – verbose license logs active (key_manager)")


def _default_license_paths() -> list[str]:
    paths: list[str] = []
    env_path = os.getenv("AGENTFOUNDRY_LICENSE_FILE")
    if env_path:
        paths.append(os.path.expanduser(env_path))
    xdg_home = os.getenv("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    paths.append(os.path.join(xdg_home, "agentfoundry", "agentfoundry.lic"))
    paths.append(os.path.join(os.getcwd(), "agentfoundry.lic"))
    paths.append(os.path.join(os.path.dirname(__file__), "..", "agentfoundry.lic"))
    logger.debug(f"KeyManager candidate license paths: {paths}")
    return paths


def _resolve_license_file(path: str | None) -> str:
    if path and os.path.exists(path):
        return path
    for p in _default_license_paths():
        if os.path.exists(p):
            logger.info(f"KeyManager using license file: {p}")
            return p
    last = _default_license_paths()[-1]
    logger.warning(f"KeyManager could not find a license file; last expected: {last}")
    return last


def get_license_key(license_file=None, public_key_file=None):
    """
    Retrieve the decryption key from the RSA-signed license file.

    Args:
        license_file (str): Path to the license file.
        public_key_file (str): Path to the public key file.

    Returns:
        bytes: Decryption key for encrypted .so files, or None if verification fails.
    """
    license_file = _resolve_license_file(license_file)
    public_key_file = public_key_file or os.path.join(os.path.dirname(__file__), "..", "agentfoundry.pem")
    logger.debug(f"get_license_key: license_file={license_file} public_key_file={public_key_file}")
    try:
        logger.debug("KeyManager invoking compiled license validator…")
        _, key = _license_core.validate_license(license_file, public_key_file, True)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        raise
    except RuntimeError as exc:
        logger.error(str(exc))
        raise RuntimeError("Invalid, tampered, or expired AgentFoundry license.") from exc

    logger.info(f"KeyManager extracted decryption key ({len(key)} bytes)")
    return key


# ---------------------------------------------------------------------------
# Lightweight OO wrapper – maintained for backward compatibility with code
# paths that expect a *class* API (see ``agentfoundry.bootstrap.run``).
# ---------------------------------------------------------------------------


class KeyManager:  # noqa: D401
    """Small façade around :pyfunc:`get_license_key`.

    Historical versions of AgentFoundry exposed a ``KeyManager`` class with a
    ``validate_license`` method.  Some entry-points (e.g. the lightweight
    bootstrap) still import this symbol, therefore we re-introduce the minimal
    wrapper while keeping the functional implementation untouched.
    """

    def __init__(self, license_file: str | None = None, public_key_file: str | None = None):
        self._license_file = license_file
        self._public_key_file = public_key_file

    # The original public API – kept stable on purpose --------------------
    def validate_license(self) -> None:  # noqa: D401
        """Validate the current licence or raise ``RuntimeError``.

        The method performs *no* caching – callers worried about performance
        should implement their own memoisation layer.
        """

        # ``get_license_key`` already performs signature verification and
        # raises a helpful ``RuntimeError`` on failure.  We delegate the heavy
        # lifting and discard the actual key – the *bootstrap* only needs to
        # know whether the check succeeded.
        _ = get_license_key(self._license_file, self._public_key_file)



if __name__ == "__main__":
    # Example usage
    decryption_key = get_license_key(license_file="agentfoundry.lic", public_key_file="agentfoundry.pem")
    if decryption_key:
        print("Decryption key retrieved successfully.")
    else:
        print("Failed to retrieve decryption key.")
