"""Authentication context for bv-runtime SDK.

This module provides authentication context loading for both:
- Runner mode: Context is set via set_runtime_context() from the runner
- Developer mode: Context is loaded from ~/.bv/auth.json

No environment variables are used for authentication configuration.
All credentials are sourced from:
1. Runtime context (set by runner via set_runtime_context() API)
2. Auth file (~/.bv/auth.json for developer mode)
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Mapping

from bv.runtime.url_resolver import BaseUrlResolver


logger = logging.getLogger("bv.runtime")


class AuthError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthUser:
    id: int | None
    username: str | None


@dataclass(frozen=True)
class AuthContext:
    base_url: str
    api_url: str
    ui_url: str
    access_token: str
    expires_at: datetime
    user: AuthUser
    machine_name: str

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


def _normalize_base_url(url: str) -> str:
    """Normalize a base URL (strip trailing slashes).
    
    Args:
        url: The URL to normalize.
        
    Returns:
        Normalized URL without trailing slashes.
        
    Raises:
        AuthError: If the URL is empty or missing.
    """
    u = (url or "").strip()
    if not u:
        raise AuthError("Orchestrator URL is missing")
    return u.rstrip("/")


def _normalize_root_url(url: str) -> str:
    """Normalize a root URL (frontend URL without /api suffix).
    
    Uses BaseUrlResolver for consistent URL handling.
    
    Args:
        url: The URL to normalize.
        
    Returns:
        Normalized frontend URL without trailing slashes or /api suffix.
        
    Raises:
        AuthError: If the URL is empty or missing.
    """
    u = (url or "").strip()
    if not u:
        raise AuthError("Orchestrator URL is missing")
    return BaseUrlResolver(u).frontend_base


def _derive_api_url(url: str) -> str:
    """Derive the API base URL from a frontend URL.
    
    Uses BaseUrlResolver to ensure consistent URL derivation.
    
    Args:
        url: The frontend URL.
        
    Returns:
        API base URL with /api suffix.
        
    Raises:
        AuthError: If the URL is empty or missing.
    """
    u = (url or "").strip()
    if not u:
        raise AuthError("Orchestrator URL is missing")
    return BaseUrlResolver(u).api_base


def load_auth_from_runtime_context() -> AuthContext:
    """Load authentication from the runtime context (Runner mode).
    
    This is called when the runtime context has been initialized by the runner
    via the set_runtime_context() API.
    
    Returns:
        AuthContext loaded from the runtime context.
        
    Raises:
        AuthError: If the runtime context is not initialized.
    """
    from . import context as runtime_context
    
    if not runtime_context.is_runtime_initialized():
        raise AuthError("Runtime context not initialized")
    
    # Best-effort refresh from context file (if available)
    try:
        runtime_context.refresh_runtime_context_from_file()
    except Exception:
        pass
    
    base_url = runtime_context.get_base_url()
    robot_token = runtime_context.get_robot_token()
    robot_name = runtime_context.get_robot_name()
    machine_name = runtime_context.get_machine_name()
    
    if not base_url:
        raise AuthError("Runtime context: base_url is missing")
    if not robot_token:
        raise AuthError("Runtime context: robot_token is missing")
    
    # Use BaseUrlResolver to derive URLs consistently
    resolver = BaseUrlResolver(base_url)
    frontend_base = resolver.frontend_base
    api_base = resolver.api_base
    
    logger.debug("Runtime context URLs resolved: frontend=%s, api=%s", frontend_base, api_base)
    
    return AuthContext(
        base_url=frontend_base,
        api_url=api_base,
        ui_url=frontend_base,
        access_token=robot_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=365),  # Long-lived robot token
        user=AuthUser(id=None, username=f"robot:{robot_name or 'unknown'}"),
        machine_name=machine_name or "runner-machine",
    )


def load_auth_from_file() -> AuthContext:
    """Load authentication from the auth file (Developer mode).
    
    Returns:
        AuthContext loaded from ~/.bv/auth.json.
        
    Raises:
        AuthError: If the auth file is missing or invalid.
    """
    path = auth_file_path()
    if not path.exists():
        raise AuthError(
            "Not authenticated. Run 'bv auth login' to authenticate."
        )

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as exc:
        raise AuthError(f"Invalid auth file at {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise AuthError(f"Invalid auth file at {path}: expected JSON object")

    # New schema (preferred): only base_url is stored
    base_url_raw = data.get("base_url")
    api_url_raw = data.get("api_url")
    ui_url_raw = data.get("ui_url")

    # Backward compat: older schema used orchestrator_url.
    if base_url_raw is None and data.get("orchestrator_url") is not None:
        base_url_raw = data.get("orchestrator_url")

    # Determine the source URL for deriving all URLs
    source_url = base_url_raw or api_url_raw or ui_url_raw
    if not source_url:
        raise AuthError("Invalid auth file: missing base_url. Run 'bv auth login'")
    
    # Use BaseUrlResolver to derive consistent URLs
    resolver = BaseUrlResolver(str(source_url))
    base_url = resolver.frontend_base
    api_url = resolver.api_base
    ui_url = resolver.frontend_base
    
    logger.debug("Auth file URLs resolved: frontend=%s, api=%s", base_url, api_url)

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
        api_url=api_url,
        ui_url=ui_url,
        access_token=access_token,
        expires_at=expires_at,
        user=AuthUser(
            id=user_id,
            username=(str(user.get("username")) if user.get("username") is not None else None),
        ),
        machine_name=machine_name,
    )


def load_auth_context() -> AuthContext:
    """Load authentication context.
    
    Tries in order:
    1. Runtime context (set by runner via set_runtime_context())
    2. Auth file (~/.bv/auth.json for Developer mode)
    
    No environment variables are used for authentication.
    
    Returns:
        AuthContext from the first available source.
        
    Raises:
        AuthError: If no authentication source is available.
    """
    # 1. Check if runtime context is initialized (Runner mode)
    from . import context as runtime_context
    
    if runtime_context.is_runtime_initialized():
        return load_auth_from_runtime_context()
    
    # 2. Fall back to auth file (Developer mode)
    return load_auth_from_file()


def require_auth() -> AuthContext:
    """Load and validate the auth context.
    
    Raises clear errors for:
    - not authenticated (no runtime context and no auth file)
    - token expired (file-based auth only)
    
    Returns:
        Validated AuthContext.
    """
    ctx = load_auth_context()
    # Only check expiration for file-based auth (Runner tokens don't expire in this context)
    if ctx.user and ctx.user.username and not ctx.user.username.startswith("robot:"):
        if ctx.is_expired():
            raise AuthError("Token expired. Run 'bv auth login'")
    return ctx
