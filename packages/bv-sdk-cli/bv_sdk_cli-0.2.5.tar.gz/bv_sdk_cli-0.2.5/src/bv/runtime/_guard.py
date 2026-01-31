"""Runtime guard to ensure SDK APIs are only used in proper context.

This module provides a guard function that checks if the runtime context
has been properly initialized before allowing SDK API calls.
"""
from __future__ import annotations


def require_bv_run() -> None:
    """Ensure the runtime context is initialized before SDK API calls.
    
    Raises:
        RuntimeError: If the runtime context has not been initialized.
    """
    from bv.runtime import context as runtime_context
    
    if not runtime_context.is_runtime_initialized():
        raise RuntimeError(
            "bv.runtime is only available when running via 'bv run'. "
            "Ensure the runtime context has been initialized."
        )
