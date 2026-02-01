"""
Pure-Python fallback for AgentFoundry license verification.

This mirrors the logic in ``_license_core.pyx`` so that development and
non-compiled environments can import and validate licenses without requiring
the Cython-built extension.
"""

from __future__ import annotations

import base64
import json
import os
import platform
import uuid
from binascii import unhexlify
from datetime import datetime
import hashlib
import hmac

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


# Must match the value embedded in the Cython module
EXPECTED_PUBKEY_SHA256_HEX = "e660085c5efaca044b5b8469202e3b957a4987ed2ff08940a6ab784b69336933"
_EXPECTED_PUBKEY_SHA256 = unhexlify(EXPECTED_PUBKEY_SHA256_HEX)


def _load_license_json(license_path: str) -> dict:
    with open(license_path, "r", encoding="utf-8") as fp:
        return json.load(fp)


def _resolve_public_key_bytes(public_key_path: str) -> bytes:
    with open(public_key_path, "rb") as fp:
        data = fp.read()
    digest = hashlib.sha256(data).digest()
    if not hmac.compare_digest(digest, _EXPECTED_PUBKEY_SHA256):
        raise RuntimeError("Public key integrity check failed — unexpected fingerprint.")
    return data


def _current_machine_id() -> str:
    return f"{uuid.getnode()}{platform.node()}"


def validate_license(license_path: str, public_key_path: str, enforce_machine: bool = True) -> tuple[bool, bytes]:
    """
    Validate the license at ``license_path`` with ``public_key_path``.

    Returns ``(True, decryption_key_bytes)`` if validation succeeds; raises
    ``FileNotFoundError`` or ``RuntimeError`` on failure.
    """
    if not os.path.exists(license_path):
        raise FileNotFoundError(f"License file not found: {license_path}")
    if not os.path.exists(public_key_path):
        raise FileNotFoundError(f"Public key file not found: {public_key_path}")

    license_data = _load_license_json(license_path)
    content = license_data.get("content")
    signature_b64 = license_data.get("signature")
    if not isinstance(content, dict) or not signature_b64:
        raise RuntimeError("Invalid license format: missing content or signature")

    try:
        signature = base64.b64decode(signature_b64, validate=True)
    except Exception as exc:
        raise RuntimeError("Invalid license signature encoding") from exc

    public_key_bytes = _resolve_public_key_bytes(public_key_path)
    public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())

    content_str = json.dumps(content, sort_keys=True).encode()
    try:
        public_key.verify(
            signature,
            content_str,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH,
            ),
            hashes.SHA256(),
        )
    except Exception as exc:
        raise RuntimeError("Invalid, tampered, or expired AgentFoundry license.") from exc

    expiry = content.get("expiry")
    if not expiry:
        raise RuntimeError("License missing expiry field")
    try:
        exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
    except Exception as exc:
        raise RuntimeError("Invalid license expiry value") from exc
    if datetime.today().date() > exp_date:
        raise RuntimeError("AgentFoundry license has expired")

    lic_machine = content.get("machine_id")
    if enforce_machine and lic_machine not in (None, "", "*", "any", "unbound"):
        current_mid = _current_machine_id()
        if lic_machine != current_mid:
            raise RuntimeError("AgentFoundry license is not valid for this machine")

    decrypt_b64 = content.get("decryption_key")
    if not decrypt_b64:
        raise RuntimeError("License missing decryption key")
    try:
        key_bytes = base64.b64decode(decrypt_b64, validate=True)
    except Exception as exc:
        raise RuntimeError("Invalid decryption key encoding") from exc

    return True, key_bytes


def current_machine_id() -> bytes:
    """Expose the machine identifier used for machine binding (bytes)."""
    return _current_machine_id().encode()

