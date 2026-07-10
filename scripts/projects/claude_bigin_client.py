"""
claude_bigin_client.py
======================
Thin REST client for Bigin COQL API.

Used by fetch_bigin_pipeline.py as its data layer — replaces the Claude MCP
bridge with a standalone Python HTTP client. This lets build_cashflow_json.py
fetch live Bigin data every time the dashboard is rendered, without needing
Claude Code's MCP session.

Credentials (Zoho OAuth 2.0):
  Set in a .env file at the repo root:

    BIGIN_CLIENT_ID=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BIGIN_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BIGIN_REFRESH_TOKEN=1000.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    BIGIN_DATA_CENTER=in          # 'in' for India accounts (zohoapis.in)
                                   # 'com' for US accounts  (zohoapis.com)

  How to get these:
    1. Go to https://api-console.zoho.in → "Server-based Applications"
    2. Create an app → copy Client ID + Client Secret
    3. Scope: ZohoBigin.modules.all,ZohoBigin.settings.READ
    4. Generate tokens → copy Refresh Token
    5. Paste into .env (never commit .env to git)

  If .env is missing or any key is absent:
    - coql_query() raises MissingBiginCredentials
    - build_cashflow_json.py catches this and falls back to the last cached
      bigin_pipeline_raw.json, logging a warning.

Usage:
    from claude_bigin_client import coql_query
    result = coql_query("SELECT id, Deal_Name FROM Pipelines WHERE ...")
    # Returns {"data": [...], "info": {...}}
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


# ── Credential loading ────────────────────────────────────────────────────────

class MissingBiginCredentials(RuntimeError):
    """Raised when Bigin OAuth credentials are not configured."""


def _load_env(env_path: Path | None = None) -> dict[str, str]:
    """Read .env from the repo root (two levels above scripts/projects/)."""
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent / ".env"
    env: dict[str, str] = {}
    if not env_path.exists():
        return env
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                env[key.strip()] = val.strip().strip('"').strip("'")
    return env


def _get_credentials() -> tuple[str, str, str, str]:
    """
    Return (client_id, client_secret, refresh_token, data_center).
    Priority: process env vars → .env file.
    """
    env = _load_env()

    def _get(key: str) -> str | None:
        return os.environ.get(key) or env.get(key)

    client_id     = _get("BIGIN_CLIENT_ID")
    client_secret = _get("BIGIN_CLIENT_SECRET")
    refresh_token = _get("BIGIN_REFRESH_TOKEN")
    data_center   = _get("BIGIN_DATA_CENTER") or "in"

    missing = [k for k, v in {
        "BIGIN_CLIENT_ID": client_id,
        "BIGIN_CLIENT_SECRET": client_secret,
        "BIGIN_REFRESH_TOKEN": refresh_token,
    }.items() if not v]

    if missing:
        raise MissingBiginCredentials(
            f"Missing Bigin credentials: {', '.join(missing)}. "
            f"Set them in the repo root .env file. "
            f"See scripts/projects/claude_bigin_client.py for instructions."
        )

    return client_id, client_secret, refresh_token, data_center  # type: ignore[return-value]


# ── Token cache (in-process, expires after 55 min) ───────────────────────────

_token_cache: dict = {}   # {"access_token": str, "expires_at": float, "dc": str}


def _get_access_token(client_id: str, client_secret: str, refresh_token: str,
                      data_center: str) -> str:
    """
    Exchange refresh token for an access token. Caches in-process for 55 min.
    Zoho tokens expire in 60 min; we refresh 5 min early.
    """
    now = time.time()
    if (_token_cache.get("access_token")
            and _token_cache.get("expires_at", 0) > now
            and _token_cache.get("dc") == data_center):
        return _token_cache["access_token"]

    base = "https://accounts.zoho.in" if data_center == "in" else "https://accounts.zoho.com"
    url = f"{base}/oauth/v2/token"

    payload = urllib.parse.urlencode({
        "grant_type":    "refresh_token",
        "client_id":     client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
    }).encode()

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Token refresh failed ({e.code}): {e.read().decode()}") from e

    if "access_token" not in body:
        raise RuntimeError(f"Token refresh error: {body}")

    _token_cache["access_token"] = body["access_token"]
    _token_cache["expires_at"]   = now + 55 * 60   # 55 min
    _token_cache["dc"]           = data_center

    return body["access_token"]


# ── COQL query ────────────────────────────────────────────────────────────────

def coql_query(select_query: str, page: int = 1, per_page: int = 200) -> dict:
    """
    Execute a Bigin COQL SELECT query and return all matching rows.

    Automatically paginates if Bigin returns a next-page token. Merges all
    pages into a single result dict:
        {"data": [...all rows...], "info": {...last page info...}}

    Args:
        select_query: COQL SELECT string (no trailing semicolon needed)
        page:         Starting page (1-based)
        per_page:     Rows per page (Bigin max: 200)

    Returns:
        dict with "data" (list of row dicts) and "info" (pagination metadata)

    Raises:
        MissingBiginCredentials: if credentials not configured
        RuntimeError: on HTTP errors or Bigin API error responses
    """
    client_id, client_secret, refresh_token, data_center = _get_credentials()
    access_token = _get_access_token(client_id, client_secret, refresh_token, data_center)

    api_base = (
        "https://www.zohoapis.in/bigin/v2"
        if data_center == "in"
        else "https://www.zohoapis.com/bigin/v2"
    )
    url = f"{api_base}/coql"

    all_rows: list = []
    current_page = page

    while True:
        body = json.dumps({
            "select_query": select_query,
            "page": current_page,
            "per_page": per_page,
        }).encode()

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Zoho-oauthtoken {access_token}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode()
            raise RuntimeError(
                f"Bigin COQL error (HTTP {e.code}): {err_body}\n"
                f"Query: {select_query[:200]}"
            ) from e

        # Bigin returns {"code": "SUCCESS", "data": [...], "info": {...}}
        # or {"code": "...", "message": "...", "status": "error"}
        if isinstance(result, dict) and result.get("status") == "error":
            raise RuntimeError(
                f"Bigin COQL error: {result.get('message', result)}\n"
                f"Query: {select_query[:200]}"
            )

        rows = result.get("data", [])
        info  = result.get("info", {})
        all_rows.extend(rows)

        # Paginate if more pages exist
        if info.get("more_records") and len(rows) == per_page:
            current_page += 1
        else:
            break

    return {"data": all_rows, "info": info}
