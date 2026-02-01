# entra_tool.py

import base64
import json
import logging
import re
from threading import Lock
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlsplit

import msal
import requests
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from pydantic import BaseModel, Field

try:
    from flask import has_request_context, session
except Exception:  # pragma: no cover
    session = None
    has_request_context = lambda: False  # type: ignore

from agentfoundry.utils.config import Config

# -------------------------------------------------------------------
# Logging setup
# -------------------------------------------------------------------
logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

# Load configuration for Microsoft Graph credentials
CONFIG = Config()
CLIENT_ID = CONFIG.get("MS.CLIENT_ID", None)
TENANT_ID = CONFIG.get("MS.TENANT_ID", None)
CLIENT_SECRET = CONFIG.get("MS.CLIENT_SECRET", None)
AUTHORITY = CONFIG.get("MS.AUTHORITY", f"https://login.microsoftonline.com/{TENANT_ID}" if TENANT_ID else None)

# Default delegated scopes for Graph (ensure Calendars.Read is requested)
raw_scope_config = CONFIG.get(
    "MS.GRAPH_SCOPES",
    "User.Read Calendars.Read",
)
GRAPH_SCOPES = [scope for scope in str(raw_scope_config).replace(",", " ").split() if scope]
# Determine if credentials are missing (tool will be disabled if so)
config_missing = not CLIENT_ID or not TENANT_ID or not CLIENT_SECRET

# Warn if credentials are missing (tool functionality will error on invocation)
if config_missing:
    logger.info("MS.CLIENT_ID, MS.TENANT_ID, and MS.CLIENT_SECRET must be set; entra_tool disabled.")
# Initialize MSAL cache and placeholders for lazy client initialization
_cache = msal.SerializableTokenCache()
_app = None
_lock = Lock()


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    """Decode a JWT payload without verification (best-effort for logging/caching)."""
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return {}
        padded = parts[1] + "=" * (-len(parts[1]) % 4)
        decoded = base64.urlsafe_b64decode(padded.encode("utf-8"))
        return json.loads(decoded.decode("utf-8"))
    except Exception:
        logger.debug("Failed to decode JWT payload for user assertion", exc_info=True)
        return {}


def _normalize_assertion(token: Optional[str]) -> Optional[str]:
    """Strip any Bearer prefix and surrounding whitespace from a token."""
    if not token:
        return token
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token.split(" ", 1)[1].strip()
    return token or None


def _is_graph_access_token(token: str, required_scopes: Optional[list[str]] = None) -> bool:
    """
    Check if the provided token is already a Microsoft Graph access token and carries required scopes.
    """
    try:
        payload = _decode_jwt_payload(token)
        aud = str(payload.get("aud") or "").lower()
        scopes_raw = str(payload.get("scp") or payload.get("scope") or "")
        scope_set = {s.lower() for s in scopes_raw.split()} if scopes_raw else set()
        req = {s.lower() for s in (required_scopes or []) if s and "default" not in s.lower()}
        # Standard Graph audience GUID and URLs
        if aud in ("00000003-0000-0000-c000-000000000000", "https://graph.microsoft.com"):
            if req and not req.issubset(scope_set):
                logger.info("Graph token missing required scopes; will exchange via OBO. missing=%s", sorted(req - scope_set))
                return False
            return True
        # Heuristic: scopes explicitly mention Graph or https://graph.microsoft.com/.default
        if "graph.microsoft.com" in scopes_raw.lower():
            if req and not req.issubset(scope_set):
                logger.info("Graph token (aud=?): missing required scopes; will exchange via OBO. missing=%s", sorted(req - scope_set))
                return False
            return True
    except Exception:
        return False
    return False


def _get_user_assertion_from_config(config: RunnableConfig | None) -> Optional[str]:
    """Extract the end-user bearer token (assertion) from the runnable config."""
    if not config:
        try:
            if has_request_context() and session:
                tok = session.get("graph_access_token")
                if tok:
                    return tok
        except Exception:
            pass
        return None
    cfg = config.get("configurable", {}) or {}
    return (
        cfg.get("entra_user_assertion")
        or cfg.get("ms_user_assertion")
        or cfg.get("user_assertion")
        or cfg.get("access_token")
    )


def get_on_behalf_of_token(user_assertion: str) -> str:
    """
    Exchange a user assertion (bearer token from the SPA) for a Graph token
    using the On-Behalf-Of flow. Relies on a confidential client credential.
    """
    # Ensure credentials are available and initialize MSAL client lazily
    if config_missing:
        raise RuntimeError("MS.CLIENT_ID, MS.TENANT_ID, and MS.CLIENT_SECRET must be set in your configuration.")
    normalized_assertion = _normalize_assertion(user_assertion)
    if not normalized_assertion:
        raise RuntimeError("User assertion is required for on-behalf-of token exchange.")

    # If the incoming token is already a Graph access token, skip OBO and use it directly.
    if _is_graph_access_token(normalized_assertion, GRAPH_SCOPES):
        logger.info("Received Graph access token; using directly without OBO exchange.")
        return normalized_assertion

    global _app
    if _app is None:
        _app = msal.ConfidentialClientApplication(
            client_id=CLIENT_ID,
            client_credential=CLIENT_SECRET,
            authority=AUTHORITY,
            token_cache=_cache,
        )
    with _lock:
        result = _app.acquire_token_on_behalf_of(
            user_assertion=normalized_assertion,
            scopes=GRAPH_SCOPES,
        )
        if "access_token" not in result:
            logger.error(f"OBO token error: {result}")
            raise RuntimeError(f"OBO token error: {result.get('error_description', result)}")
        claims = _decode_jwt_payload(normalized_assertion)
        user = claims.get("preferred_username") or claims.get("upn") or claims.get("oid") or "<unknown>"
        logger.info(f"Acquired Graph token on behalf of {user}")
        return result["access_token"]

# -------------------------------------------------------------------
# Input model
# -------------------------------------------------------------------
class EntraInput(BaseModel):
    method: str = Field(..., description="HTTP method: GET, POST, etc.")
    path: str = Field(..., description="Graph API path, e.g. 'me/messages'")
    query_params: dict = Field(default_factory=dict)
    body: dict = Field(default_factory=dict)
    user_assertion: Optional[str] = Field(
        default=None,
        description="Bearer token for the signed-in Microsoft 365 user (prefer passing via config.configurable['entra_user_assertion'])."
    )

# -------------------------------------------------------------------
# Core request
# -------------------------------------------------------------------
def make_entra_request(raw_input, *, config: RunnableConfig | None = None, user_assertion: str | None = None) -> dict:
    """
    Execute a delegated Graph request under /me using OBO auth.
    Accepts EntraInput or JSON/dict/string. The user assertion (bearer token)
    should be provided via config.configurable['entra_user_assertion'] when
    invoked from an agent workflow.
    """
    logger.info("make_entra_request invoked")

    def _path_query_from_url(url: str) -> tuple[Optional[str], dict]:
        try:
            parsed = urlsplit(url)
            raw_path = parsed.path.lstrip("/").strip()
            # Strip version prefixes if present
            for prefix in ("v1.0/", "beta/"):
                if raw_path.startswith(prefix):
                    raw_path = raw_path.split(prefix, 1)[1]
                    break
            query = dict(parse_qsl(parsed.query))
            return raw_path or None, query
        except Exception:
            return None, {}

    # 1) Normalize input
    if isinstance(raw_input, EntraInput):
        inp = raw_input
        logger.debug(f"Using passed EntraInput: {inp}")
    else:
        try:
            # If it's a simple string GET path, wrap it
            if isinstance(raw_input, str) and not raw_input.strip().startswith("{"):
                raw = raw_input.strip()
                verb_match = re.match(r"^(GET|POST|PUT|PATCH|DELETE)\\s+(.+)$", raw, flags=re.IGNORECASE)
                if verb_match:
                    method = verb_match.group(1).upper()
                    path = verb_match.group(2).strip()
                else:
                    method = "GET"
                    path = raw
                inp = EntraInput(method=method, path=path)
                logger.debug(f"Wrapped raw string into EntraInput: {inp}")
            else:
                data = json.loads(raw_input) if isinstance(raw_input, str) else raw_input
                if isinstance(data, dict):
                    # Map common aliases
                    if "query" in data and "query_params" not in data:
                        data = dict(data)
                        data["query_params"] = data.pop("query")
                    if "params" in data and "query_params" not in data:
                        data = dict(data)
                        data["query_params"] = data.pop("params")
                    if "queryParams" in data and "query_params" not in data:
                        data = dict(data)
                        data["query_params"] = data.pop("queryParams")
                    if "path" not in data:
                        if "url" in data:
                            inferred, inferred_query = _path_query_from_url(data["url"])
                            if inferred:
                                data = dict(data)
                                data["path"] = inferred
                                if inferred_query and not data.get("query_params"):
                                    data["query_params"] = inferred_query
                        if "endpoint" in data and "path" not in data:
                            inferred, inferred_query = _path_query_from_url(data["endpoint"])
                            if not inferred:
                                inferred = str(data["endpoint"]).lstrip("/")
                            if inferred:
                                data = dict(data)
                                data["path"] = inferred
                                if inferred_query and not data.get("query_params"):
                                    data["query_params"] = inferred_query
                        if "api" in data and "path" not in data:
                            inferred, inferred_query = _path_query_from_url(data["api"])
                            if not inferred:
                                inferred = str(data["api"]).lstrip("/")
                            if inferred:
                                data = dict(data)
                                data["path"] = inferred
                                if inferred_query and not data.get("query_params"):
                                    data["query_params"] = inferred_query
                    if "method" not in data:
                        data = dict(data)
                        data["method"] = "GET"
                inp = EntraInput(**data)
                logger.debug(f"Parsed JSON into EntraInput: {data}")
        except Exception as e:
            logger.error(f"Failed to parse input: {e}", exc_info=True)
            return {
                "error": (
                    "Invalid input for EntraInput: provide 'path', 'url', 'endpoint', or 'api'; "
                    "optional 'query'/'params'/'queryParams'/'query_params'; "
                    "HTTP 'method' (defaults to GET); body, and user_assertion as needed. "
                    f"Details: {e}"
                )
            }

    method = inp.method.upper()
    if method not in {"GET","POST","PUT","PATCH","DELETE"}:
        logger.error(f"Unsupported HTTP method: {method}")
        return {"error": f"Unsupported HTTP method: {method}"}

    # 2) Force /me prefix
    raw_path = inp.path.lstrip("/")
    if raw_path.startswith("users/") or raw_path.startswith("https://"):
        # Strip users/{UPN} or full URL
        # e.g. users/alice@mail/...  → remove prefix up to /v1.0/
        parts = raw_path.split("/v1.0/",1)
        raw_path = parts[-1]
        logger.debug(f"Stripped full users path to: {raw_path}")
    if not raw_path.startswith("me/"):
        raw_path = f"me/{raw_path}"
        logger.debug(f"Prefixed path with 'me/': {raw_path}")

    url = f"https://graph.microsoft.com/v1.0/{raw_path}"
    logger.info(f"Prepared URL: {method} {url}")

    # 3) Resolve user assertion and exchange for Graph token
    assertion = _normalize_assertion(inp.user_assertion or user_assertion or _get_user_assertion_from_config(config))
    if not assertion:
        return {"error": "User assertion missing. Provide a bearer token via config.configurable['entra_user_assertion']."}

    claims = _decode_jwt_payload(assertion) if assertion else {}
    aud_claim = str(claims.get("aud") or "").lower()
    scope_str = str(claims.get("scp") or claims.get("scope") or "")
    scope_set = {s.lower() for s in scope_str.split()} if scope_str else set()
    if "calendars.read" not in scope_set:
        logger.warning(f"calendars.read not in scope: {scope_str}. Adding...")
        scope_set.add("calendars.read")
    required_scopes = {s.lower() for s in GRAPH_SCOPES if s and ".default" not in s.lower()}
    backend_aud = str(CLIENT_ID or "").lower()
    logger.info(
        "entra_tool token meta: aud=%s scope_count=%d scopes=%s required=%s",
        aud_claim or "<missing>",
        len(scope_set),
        sorted(scope_set),
        sorted(required_scopes),
    )

    # Decide how to handle the incoming assertion
    if aud_claim in ("00000003-0000-0000-c000-000000000000", "https://graph.microsoft.com"):
        missing = required_scopes.difference(scope_set)
        if missing:
            return {
                "error": (
                    "The provided token is a Microsoft Graph token but is missing required scopes for this call. "
                    f"Missing scopes: {sorted(missing)}. Request the token with Calendars.Read and retry."
                )
            }
        logger.info("Using provided Graph access token directly (audience=Graph, required scopes present).")
        token = assertion
    elif backend_aud and aud_claim == backend_aud:
        try:
            token = get_on_behalf_of_token(assertion)
            logger.debug(f"Token length: {len(token)}")
        except Exception as e:
            return {"error": f"Token acquisition error: {e}"}
    else:
        reason = aud_claim or "<missing>"
        return {
            "error": (
                "User assertion has an unexpected audience for OBO. "
                f"Received aud='{reason}', expected your backend API '{backend_aud}' "
                "or a Graph token with Calendars.Read. "
                "Have the SPA request api://<backend-client-id>/user_impersonation (or /.default) "
                "and include Calendars.Read."
            )
        }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }

    # 4) Perform HTTP call
    logger.debug(f"Headers: {headers}")
    logger.debug(f"Query params: {inp.query_params}, Body: {inp.body}")
    resp = None
    try:
        resp = requests.request(
            method,
            url,
            headers=headers,
            params=inp.query_params or None,
            json=inp.body or None,
            timeout=15
        )
        logger.info(f"HTTP {method} → status {resp.status_code}")
        resp.raise_for_status()
        if resp.status_code == 204:
            return {"message": "Success − no content"}
        data = resp.json()
        logger.debug(f"Response JSON: {data}")
        return data
    except requests.exceptions.HTTPError as e:
        if resp:
            message = resp.text
        else:
            message = "No response body"
        logger.error(f"Graph API error: {e}: response: ({message})")
        return {"error": str(e), "status": resp.status_code, "body": resp.text}
    except Exception as e:
        logger.exception("Unexpected error")
        return {"error": str(e)}

# -------------------------------------------------------------------
# LangChain tool export
# -------------------------------------------------------------------
if not config_missing:
    @tool("entra_tool")
    def entra_tool(raw_input, config: RunnableConfig | None = None):
        """Calls Microsoft Graph under /me using on-behalf-of auth for the signed-in user."""
        return make_entra_request(raw_input, config=config)

    entra_tool.description = (
        "Calls Microsoft Graph under /me using on-behalf-of auth. "
        "Requires the caller to supply the signed-in user's bearer token via "
        "config.configurable['entra_user_assertion']."
    )
