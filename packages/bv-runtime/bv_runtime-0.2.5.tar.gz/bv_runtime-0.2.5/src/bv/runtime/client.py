"""HTTP client for Bot Velocity Orchestrator (runtime SDK).

This module provides an authenticated HTTP client for the bv-runtime SDK.
Token refresh is handled by reloading the auth context from the runtime context
that was set by the runner.

URL handling follows the BaseUrlResolver convention:
- api_url in AuthContext includes the /api suffix
- All endpoint paths are relative to api_url (no /api prefix needed)
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
)
from bv.runtime.auth import AuthError, AuthContext, require_auth, load_auth_from_runtime_context
from bv.runtime.url_resolver import BaseUrlResolver
from . import context as runtime_context


logger = logging.getLogger("bv.runtime")


def _redact_tokens(text: str) -> str:
    """Redact potential tokens from error messages.
    
    Removes JWT-like strings and long hex strings that may be tokens.
    This prevents accidental token leakage in error logs.
    """
    if not text:
        return text
    # Redact JWT-like strings (header.payload.signature)
    text = re.sub(r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED]', text)
    # Redact hex tokens (32+ chars, typical for API tokens)
    text = re.sub(r'[a-f0-9]{32,}', '[REDACTED]', text, flags=re.IGNORECASE)
    return text


def _is_retryable_error(exc: BaseException) -> bool:
    """Determine if an exception is retryable.
    
    Retryable errors include:
    - Connection errors (network issues)
    - Timeout errors
    - 5xx server errors (transient server issues)
    """
    if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        # Retry on 5xx errors (server errors), but not 4xx (client errors)
        return exc.response.status_code >= 500
    return False


# Default retry configuration: 3 attempts with exponential backoff (1s, 2s, 4s)
_default_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_error),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)


class OrchestratorError(RuntimeError):
    """General orchestrator API error."""
    pass


class OrchestratorAuthError(OrchestratorError):
    """Raised when authentication fails (401/403).
    
    This signals that the token may need to be refreshed.
    """
    pass


@dataclass(frozen=True)
class OrchestratorResponse:
    status_code: int
    data: Any


class OrchestratorClient:
    """Authenticated HTTP client for BV Orchestrator (runtime SDK).
    
    Supports automatic token refresh on auth failure by reloading the
    auth context from the runtime context.
    """

    def __init__(
        self,
        *,
        auth_context: AuthContext | None = None,
        timeout_seconds: int = 30,
    ) -> None:
        self._timeout_seconds = timeout_seconds
        self._ctx = auth_context
        self._client = httpx.Client(timeout=float(timeout_seconds))
        self._auth_retry_attempted = False

    def _auth(self) -> AuthContext:
        if self._ctx is None:
            self._ctx = require_auth()
        return self._ctx
    
    def _refresh_auth(self) -> bool:
        """Try to refresh auth by reloading from runtime context.
        
        Returns True if auth was successfully refreshed.
        """
        if not runtime_context.is_runtime_initialized():
            return False
        
        try:
            logger.info("Auth failure detected, refreshing auth context")
            self._ctx = load_auth_from_runtime_context()
            return True
        except Exception as e:
            logger.warning("Failed to refresh auth context: %s", e)
            return False

    @property
    def base_url(self) -> str:
        """Get the API base URL (includes /api suffix).
        
        The api_url in AuthContext is derived using BaseUrlResolver,
        ensuring it always includes the /api suffix.
        """
        return self._auth().api_url.rstrip("/")

    def _headers(self) -> Dict[str, str]:
        ctx = self._auth()
        headers = {
            "Accept": "application/json",
        }
        # Robot authentication uses X-Robot-Token header
        if ctx.user and ctx.user.username and ctx.user.username.startswith("robot:"):
            if not ctx.access_token:
                raise OrchestratorAuthError(
                    "Robot token is empty. The runner may not have passed the token correctly. "
                    "Check that runtime_context.json contains a valid robot_token."
                )
            headers["X-Robot-Token"] = ctx.access_token
            token_preview = ctx.access_token[:8] + "..." if len(ctx.access_token) > 8 else "(short)"
            logger.debug("Using X-Robot-Token header: %s", token_preview)
        else:
            # User authentication uses Bearer token
            headers["Authorization"] = f"Bearer {ctx.access_token}"
        return headers
    
    def _execute_request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
    ) -> OrchestratorResponse:
        """Execute an HTTP request and handle response."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        
        try:
            resp = self._client.request(
                method.upper(),
                url,
                headers=self._headers(),
                params=params,
                json=json,
                data=data,
                files=files,
            )
        except httpx.RequestError as exc:
            raise OrchestratorError(f"Unable to reach Orchestrator at {self.base_url}: {exc}") from exc

        if resp.status_code == 401:
            raise OrchestratorAuthError(
                "Authentication failed (401). Token may be expired or invalid."
            )
        if resp.status_code == 403:
            # Try to extract detailed permission error message
            try:
                error_data = resp.json()
                detail = error_data.get("detail") if isinstance(error_data, dict) else None
                if detail:
                    # Redact potential tokens from error detail
                    detail = _redact_tokens(str(detail))
                    raise OrchestratorAuthError(f"Permission denied (403): {detail}")
            except OrchestratorAuthError:
                raise
            except Exception:
                pass
            raise OrchestratorAuthError("Permission denied (403)")

        data_out: Any
        try:
            data_out = resp.json()
        except Exception:
            data_out = resp.text

        if resp.status_code >= 400:
            message = None
            if isinstance(data_out, dict):
                message = data_out.get("detail") or data_out.get("message") or data_out.get("error")
            if not message:
                message = data_out if isinstance(data_out, str) else repr(data_out)
            # Redact potential tokens from error messages
            if isinstance(message, str):
                message = _redact_tokens(message)
            raise OrchestratorError(f"Orchestrator error {resp.status_code}: {message}")

        return OrchestratorResponse(status_code=resp.status_code, data=data_out)

    @_default_retry
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: Any = None,
        data: Any = None,
        files: Any = None,
    ) -> OrchestratorResponse:
        """Make an authenticated request to the orchestrator.
        
        On auth failure (401/403), attempts to refresh the auth context
        from the runtime context and retry once.
        """
        try:
            return self._execute_request(
                method, path, params=params, json=json, data=data, files=files
            )
        except OrchestratorAuthError as e:
            # Only try refresh once
            if self._auth_retry_attempted:
                logger.error("Auth failed after retry: %s", e)
                raise
            
            self._auth_retry_attempted = True
            
            # Try to refresh auth and retry
            if self._refresh_auth():
                logger.info("Auth refreshed, retrying request")
                try:
                    return self._execute_request(
                        method, path, params=params, json=json, data=data, files=files
                    )
                except OrchestratorAuthError:
                    logger.error("Auth failed after refresh retry")
                    raise
            
            # Refresh failed, re-raise original error
            raise

    def resolve_secret(self, name: str) -> str:
        """Resolve a secret's plaintext value via the runtime endpoint.
        
        Path is relative to api_base_url (no /api prefix needed).
        """
        resp = self.request("POST", "/runtime/secrets/resolve", json={"name": name})
        data_out = resp.data

        if isinstance(data_out, dict):
            if "value" in data_out:
                return str(data_out.get("value") or "")
            # Fallback: allow orchestrator to return raw string field name
            if len(data_out) == 1:
                try:
                    return str(next(iter(data_out.values())) or "")
                except Exception:
                    pass

        if isinstance(data_out, str):
            return data_out

        return str(data_out or "")

    def get_credential_metadata(self, name: str) -> dict[str, str]:
        """Fetch credential metadata (username only) without resolving the password.
        
        Path is relative to api_base_url (no /api prefix needed).
        """
        resp = self.request("GET", f"/runtime/credentials/{name}")
        data_out = resp.data

        username = ""
        if isinstance(data_out, dict):
            username = str(data_out.get("username") or "")
        else:
            username = str(data_out or "")

        return {"username": username}

