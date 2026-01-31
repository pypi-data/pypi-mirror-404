"""Runtime context for local development (bv run).

This module provides a minimal runtime context for local development
when running automations via 'bv run'. It mirrors the context API
from bv-runtime package.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class RuntimeContextData:
    """Internal storage for runtime context."""
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
_runtime_context: RuntimeContextData = RuntimeContextData()


def set_runtime_context(
    *,
    base_url: str = "",
    robot_token: str = "",
    execution_id: str = "",
    robot_name: str = "",
    machine_name: str = "",
    tenant_id: Optional[str] = None,
    folder_id: Optional[str] = None,
    project_type: str = "rpa",
) -> None:
    """Initialize the runtime context for local development.
    
    This is called by 'bv run' to set up the context before running
    the user's automation code.
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


def is_runtime_initialized() -> bool:
    """Check if the runtime context has been initialized."""
    return _runtime_context.initialized


def get_base_url() -> str:
    """Get the orchestrator base URL."""
    return _runtime_context.base_url


def get_robot_token() -> str:
    """Get the robot authentication token."""
    return _runtime_context.robot_token


def get_execution_id() -> str:
    """Get the current execution ID."""
    return _runtime_context.execution_id


def get_robot_name() -> str:
    """Get the robot name."""
    return _runtime_context.robot_name


def get_machine_name() -> str:
    """Get the machine name."""
    return _runtime_context.machine_name


def get_tenant_id() -> Optional[str]:
    """Get the tenant ID."""
    return _runtime_context.tenant_id


def get_folder_id() -> Optional[str]:
    """Get the folder ID."""
    return _runtime_context.folder_id
