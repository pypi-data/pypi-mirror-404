"""Logging API for bv-sdk-cli runtime.

This module provides structured logging that sends log messages to the
Orchestrator when running in Runner mode, or prints to console in dev mode.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from bv.runtime._guard import require_bv_run
from bv.runtime import context as runtime_context


class LogLevel(Enum):
    """Log level enumeration for structured logging."""
    TRACE = "TRACE"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"


def log_message(message: str, level: LogLevel) -> None:
    """Send a log message to Orchestrator (Runner mode) or print to console (dev mode).
    
    Args:
        message: The log message to send
        level: The log level (LogLevel enum value)
    
    Behavior:
        - Runner mode (has execution_id): Sends log to Orchestrator
        - Dev mode (no execution_id): Prints to console with [LEVEL] prefix
    """
    require_bv_run()
    
    if not isinstance(message, str):
        message = str(message)
    
    level_str = level.value if isinstance(level, LogLevel) else str(level).upper()
    
    # Get execution ID from runtime context
    execution_id = runtime_context.get_execution_id()
    
    if execution_id:
        # Runner mode: Send to Orchestrator
        _send_to_orchestrator(execution_id, message, level_str)
    else:
        # Dev mode: Print to console
        print(f"[{level_str}] {message}")


def _send_to_orchestrator(execution_id: str, message: str, level: str) -> None:
    """Send log message to Orchestrator job execution logs endpoint."""
    try:
        from bv.orchestrator.client import OrchestratorClient
        
        client = OrchestratorClient()
        timestamp = datetime.now(timezone.utc).isoformat()
        
        payload = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
        }
        
        # Best-effort: don't raise exceptions, just log errors
        # Path is relative to api_base_url (no /api prefix needed)
        try:
            client.request("POST", f"/job-executions/{execution_id}/logs", json=payload)
        except Exception:
            # In Runner mode, if sending fails, fall back to console
            # This prevents automation failures due to logging issues
            print(f"[{level}] {message} (failed to send to Orchestrator)")
    except Exception:
        # If we can't even initialize the client, just print
        print(f"[{level}] {message} (Orchestrator unavailable)")
