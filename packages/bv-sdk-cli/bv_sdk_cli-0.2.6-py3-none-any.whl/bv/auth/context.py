"""Authentication context for bv-sdk-cli.

This module provides authentication context management for the SDK CLI.
All credentials are stored in ~/.bv/auth.json. No environment variables
are used for authentication configuration.

URL handling follows the BaseUrlResolver convention:
- base_url: Frontend URL without /api suffix (the only persisted URL)
- api_url: Always derived from base_url by appending /api (never persisted)
"""
from __future__ import annotations

import json
import logging
import stat
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from bv.common.url_resolver import BaseUrlResolver


logger = logging.getLogger("bv.auth")


class AuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthUser:
    id: int | None
    username: str | None


@dataclass(frozen=True)
class AuthContext:
    """Authentication context with single canonical URL.
    
    Only base_url is stored. api_url is always derived on demand.
    """
    base_url: str
    access_token: str
    expires_at: datetime
    user: AuthUser
    machine_name: str

    @property
    def api_url(self) -> str:
        """Derive API URL on demand from base_url."""
        return BaseUrlResolver(self.base_url).api_base

    def is_expired(self) -> bool:
        now = datetime.now(timezone.utc)
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return now >= expires


def _auth_dir() -> Path:
    """Get the authentication directory (~/.bv)."""
    return (Path.home() / ".bv").resolve()


def auth_file_path() -> Path:
    return _auth_dir() / "auth.json"


def _parse_iso8601(value: str) -> datetime:
    raw = (value or "").strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _atomic_write_json(path: Path, data: Mapping[str, Any]) -> None:
    """Write JSON data to a file atomically with restrictive permissions.
    
    Sets file permissions to 0o600 (owner read/write only) for security.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    # Set restrictive permissions (owner read/write only)
    try:
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    except OSError:
        pass  # Windows may not support chmod


def save_auth_context(ctx: AuthContext) -> None:
    """Save authentication context to the auth file.
    
    Only stores base_url. api_url is never persisted - it is derived
    at runtime using BaseUrlResolver.
    """
    resolver = BaseUrlResolver(ctx.base_url)
    
    payload: dict[str, Any] = {
        "base_url": resolver.frontend_base,
        "access_token": ctx.access_token,
        "expires_at": ctx.expires_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "user": {
            "id": ctx.user.id,
            "username": ctx.user.username,
        },
        "machine_name": ctx.machine_name,
    }
    _atomic_write_json(auth_file_path(), payload)
    logger.debug("Auth context saved: base_url=%s", resolver.frontend_base)


def load_auth_context() -> AuthContext:
    """Load authentication context from the auth file.
    
    Fails fast if legacy config keys (api_url, ui_url, orchestrator_url)
    are detected - user must re-login.
    
    Returns:
        AuthContext loaded from ~/.bv/auth.json.
        
    Raises:
        AuthError: If not authenticated or legacy config detected.
    """
    path = auth_file_path()
    if not path.exists():
        raise AuthError("Not authenticated. Run 'bv auth login'")

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        raise AuthError(f"Invalid auth file at {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise AuthError(f"Invalid auth file at {path}: expected JSON object")

    # Fail fast if legacy keys are detected
    legacy_keys = {"api_url", "ui_url", "orchestrator_url"}
    found_legacy = legacy_keys & set(data.keys())
    if found_legacy:
        raise AuthError(
            f"Legacy config keys detected: {', '.join(sorted(found_legacy))}. "
            "Please re-login with 'bv auth login'"
        )

    # Only base_url is accepted
    base_url_raw = data.get("base_url")
    if not base_url_raw:
        raise AuthError("Missing base_url in auth file. Run 'bv auth login'")
    
    # Normalize using BaseUrlResolver
    resolver = BaseUrlResolver(str(base_url_raw))
    base_url = resolver.frontend_base
    
    logger.debug("Auth loaded: base_url=%s, api_url=%s", base_url, resolver.api_base)

    access_token = str(data.get("access_token") or "").strip()
    if not access_token:
        raise AuthError("Invalid auth file: missing access_token. Run 'bv auth login'")

    expires_raw = str(data.get("expires_at") or "").strip()
    if not expires_raw:
        raise AuthError("Invalid auth file: missing expires_at. Run 'bv auth login'")

    try:
        expires_at = _parse_iso8601(expires_raw)
    except Exception as exc:
        raise AuthError(f"Invalid auth file: expires_at is not ISO8601: {exc}") from exc

    user = data.get("user") if isinstance(data.get("user"), dict) else {}

    machine_name = data.get("machine_name")
    if machine_name is None and isinstance(data.get("machine"), dict):
        machine_name = data.get("machine", {}).get("name")
    machine_name = str(machine_name) if machine_name is not None else ""
    machine_name = machine_name.strip() or "<unknown>"

    user_id = user.get("id")
    if user_id is not None:
        try:
            user_id = int(user_id)
        except Exception:
            user_id = None

    return AuthContext(
        base_url=base_url,
        access_token=access_token,
        expires_at=expires_at,
        user=AuthUser(
            id=user_id,
            username=(str(user.get("username")) if user.get("username") is not None else None),
        ),
        machine_name=machine_name,
    )


def try_load_auth_context() -> tuple[AuthContext | None, str | None]:
    """Best-effort loader for diagnostics.

    Returns (context, error). Does not raise for common problems.
    """
    try:
        ctx = load_auth_context()
        return ctx, None
    except Exception as exc:
        return None, str(exc)


def logout() -> bool:
    """Delete the local auth file.

    Returns True if a file was deleted, False if it did not exist.
    """
    path = auth_file_path()
    if not path.exists():
        return False
    path.unlink()
    return True


def require_auth() -> AuthContext:
    """Load and validate the developer auth context.

    Raises clear errors for:
    - not logged in
    - legacy config detected
    - token expired
    """
    ctx = load_auth_context()
    if ctx.is_expired():
        raise AuthError("Token expired. Run 'bv auth login'")
    return ctx


# Backward-compatible alias for existing internal usage.
def get_auth_context() -> AuthContext:
    return require_auth()
