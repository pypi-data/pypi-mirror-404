"""Execution context API for accessing job and runtime metadata.

This module provides APIs for accessing execution context during automation
execution, including job IDs, robot info, and environment metadata.

The context is initialized by the runner via set_runtime_context() before
the user's automation code runs. No environment variables are used.

Usage:
    from bv.runtime.context import get_execution_context, get_job_id
    
    # Get full execution context
    ctx = get_execution_context()
    print(f"Running job {ctx.execution_id} on robot {ctx.robot_name}")
    
    # Get specific values
    job_id = get_job_id()
    is_agent = is_agent_execution()
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable execution context with job and runtime metadata.
    
    Attributes:
        execution_id: Unique identifier for this job execution.
        robot_name: Name of the robot executing this job.
        machine_name: Name of the machine/host.
        orchestrator_url: Base URL of the orchestrator API.
        tenant_id: Tenant ID for multi-tenant scoping (if available).
        folder_id: Folder ID for folder-based scoping (if available).
        is_runner_mode: True if running in a runner, False if local dev.
    """
    execution_id: str
    robot_name: str
    machine_name: str
    orchestrator_url: str
    tenant_id: Optional[str] = None
    folder_id: Optional[str] = None
    is_runner_mode: bool = True
    project_type: Optional[str] = None


@dataclass
class RuntimeContextData:
    """Internal mutable storage for runtime context.
    
    This is used internally to store the context set by the runner.
    """
    base_url: str = ""
    robot_token: str = ""
    execution_id: str = ""
    robot_name: str = ""
    machine_name: str = ""
    tenant_id: Optional[str] = None
    folder_id: Optional[str] = None
    project_type: str = "rpa"
    initialized: bool = False


# Module-level storage for runtime context
# This replaces environment variable-based context passing
_runtime_context: RuntimeContextData = RuntimeContextData()
_runtime_context_path: Optional[Path] = None


def set_runtime_context(
    *,
    base_url: str,
    robot_token: str,
    execution_id: str,
    robot_name: str = "",
    machine_name: str = "",
    tenant_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    project_type: str = "rpa",
) -> None:
    """Initialize the runtime context.
    
    This function is called by the runner's bootstrap script to set up
    the execution context before the user's automation code runs.
    
    Args:
        base_url: Orchestrator API base URL.
        robot_token: Robot authentication token.
        execution_id: Unique job execution ID.
        robot_name: Name of the executing robot.
        machine_name: Name of the host machine.
        tenant_id: Optional tenant ID for multi-tenant scoping.
        folder_id: Optional folder ID for folder-based scoping.
        project_type: Type of project ("rpa" or "agent").
    """
    global _runtime_context
    _runtime_context = RuntimeContextData(
        base_url=base_url,
        robot_token=robot_token,
        execution_id=execution_id,
        robot_name=robot_name,
        machine_name=machine_name,
        tenant_id=tenant_id,
        folder_id=folder_id,
        project_type=project_type,
        initialized=True,
    )


def set_runtime_context_path(path: str) -> None:
    """Set the runtime context source file path for refresh."""
    global _runtime_context_path
    _runtime_context_path = Path(path).resolve()


def get_runtime_context_path() -> Optional[Path]:
    """Get the runtime context source file path, if set."""
    return _runtime_context_path


def refresh_runtime_context_from_file() -> bool:
    """Refresh runtime context from the source JSON file, if available.
    
    Returns:
        True if the context was refreshed, False otherwise.
    """
    path = _runtime_context_path
    if not path or not path.exists():
        return False
    try:
        data = path.read_text(encoding="utf-8")
        payload = __import__("json").loads(data)
        if not isinstance(payload, dict):
            return False
        set_runtime_context(
            base_url=str(payload.get("base_url") or ""),
            robot_token=str(payload.get("robot_token") or ""),
            execution_id=str(payload.get("execution_id") or ""),
            robot_name=str(payload.get("robot_name") or ""),
            machine_name=str(payload.get("machine_name") or ""),
            tenant_id=payload.get("tenant_id"),
            folder_id=payload.get("folder_id"),
            project_type=str(payload.get("project_type") or "rpa"),
        )
        return True
    except Exception:
        return False


def is_runtime_initialized() -> bool:
    """Check if the runtime context has been initialized.
    
    Returns:
        True if set_runtime_context() has been called, False otherwise.
    """
    return _runtime_context.initialized


def get_base_url() -> str:
    """Get the orchestrator base URL.
    
    Returns:
        The base URL string.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.base_url


def get_robot_token() -> str:
    """Get the robot authentication token.
    
    Returns:
        The robot token string.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.robot_token


def _require_runtime_initialized() -> None:
    """Ensure runtime context is initialized.
    
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    if not _runtime_context.initialized:
        raise RuntimeError(
            "Runtime context not initialized. "
            "This code must be run via the BV runner or 'bv run' command."
        )


def get_execution_context() -> ExecutionContext:
    """Get the current execution context.
    
    Returns:
        ExecutionContext with job and runtime metadata.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    
    return ExecutionContext(
        execution_id=_runtime_context.execution_id,
        robot_name=_runtime_context.robot_name,
        machine_name=_runtime_context.machine_name,
        orchestrator_url=_runtime_context.base_url,
        tenant_id=_runtime_context.tenant_id,
        folder_id=_runtime_context.folder_id,
        is_runner_mode=bool(_runtime_context.robot_token),
        project_type=_runtime_context.project_type,
    )


def get_execution_id() -> str:
    """Get the current job execution ID.
    
    Returns:
        The execution ID string, or empty string if not available.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.execution_id


def get_job_id() -> str:
    """Alias for get_execution_id() for convenience.
    
    Returns:
        The execution ID string.
    """
    return get_execution_id()


def get_robot_name() -> str:
    """Get the name of the robot executing this job.
    
    Returns:
        Robot name string, or empty string if not available.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.robot_name


def get_machine_name() -> str:
    """Get the name of the machine/host.
    
    Returns:
        Machine name string, or empty string if not available.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.machine_name


def get_tenant_id() -> Optional[str]:
    """Get the tenant ID for multi-tenant scoping.
    
    Returns:
        Tenant ID string, or None if not available.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.tenant_id


def get_folder_id() -> Optional[str]:
    """Get the folder ID for folder-based scoping.
    
    Returns:
        Folder ID string, or None if not available.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.folder_id


def is_runner_mode() -> bool:
    """Check if running in runner mode (vs local development).
    
    Returns:
        True if running in a runner, False if local dev mode.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return bool(_runtime_context.robot_token)


def is_agent_execution() -> bool:
    """Check if this is an agent-type execution.
    
    Returns:
        True if this is an agent execution, False for RPA.
        
    Raises:
        RuntimeError: If runtime context is not initialized.
    """
    _require_runtime_initialized()
    return _runtime_context.project_type == "agent"
