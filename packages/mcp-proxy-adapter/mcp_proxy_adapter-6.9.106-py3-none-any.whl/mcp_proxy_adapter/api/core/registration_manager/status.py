"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Global status management for registration.
"""

import asyncio
import threading
from typing import Any, Dict, Optional, Union

# Global registration status with mutex for thread-safe access
_registration_status_lock = asyncio.Lock()
_registration_status: bool = False

# Global registration snapshot (enables /health to report real state)
_registration_snapshot_lock = asyncio.Lock()
_registration_snapshot_lock_sync = threading.Lock()
_registration_snapshot: Dict[str, Any] = {
    "enabled": False,
    "registered": False,
    "proxy_url": None,
    "server_name": None,
    "server_url": None,
}
_registration_snapshot_sync: Dict[str, Any] = dict(_registration_snapshot)

_UNSET: Any = object()

# Global stop flag with mutex for thread-safe access
_stop_flag_lock = asyncio.Lock()
_stop_flag_lock_sync = threading.Lock()  # Synchronous lock for signal handlers
_stop_flag: bool = False


async def get_registration_status() -> bool:
    """Get current registration status (thread-safe with mutex)."""
    async with _registration_status_lock:
        return _registration_status


async def set_registration_status(status: bool) -> None:
    """Set registration status (thread-safe with mutex)."""
    async with _registration_status_lock:
        global _registration_status
        _registration_status = status


async def get_registration_snapshot() -> Dict[str, Any]:
    """Get current registration snapshot (thread-safe with mutex)."""
    async with _registration_snapshot_lock:
        # return a copy to avoid accidental mutations
        return dict(_registration_snapshot)


def get_registration_snapshot_sync() -> Dict[str, Any]:
    """Get current registration snapshot in sync context."""
    with _registration_snapshot_lock_sync:
        return dict(_registration_snapshot_sync)


async def set_registration_snapshot(
    *,
    enabled: Union[bool, Any] = _UNSET,
    registered: Union[bool, Any] = _UNSET,
    proxy_url: Union[Optional[str], Any] = _UNSET,
    server_name: Union[Optional[str], Any] = _UNSET,
    server_url: Union[Optional[str], Any] = _UNSET,
) -> None:
    """Update current registration snapshot (thread-safe with mutex)."""
    async with _registration_snapshot_lock:
        global _registration_snapshot
        if enabled is not _UNSET:
            _registration_snapshot["enabled"] = enabled
        if registered is not _UNSET:
            _registration_snapshot["registered"] = registered
        if proxy_url is not _UNSET:
            _registration_snapshot["proxy_url"] = proxy_url
        if server_name is not _UNSET:
            _registration_snapshot["server_name"] = server_name
        if server_url is not _UNSET:
            _registration_snapshot["server_url"] = server_url

    with _registration_snapshot_lock_sync:
        global _registration_snapshot_sync
        _registration_snapshot_sync = dict(_registration_snapshot)


async def get_stop_flag() -> bool:
    """Get current stop flag (thread-safe with mutex).
    
    Uses both async and sync locks for consistency with signal handlers.
    """
    async with _stop_flag_lock:
        with _stop_flag_lock_sync:
            return _stop_flag


async def set_stop_flag(stop: bool) -> None:
    """Set stop flag (thread-safe with mutex).
    
    Uses both async and sync locks for consistency.
    """
    async with _stop_flag_lock:
        with _stop_flag_lock_sync:
            global _stop_flag
            _stop_flag = stop


def set_stop_flag_sync(stop: bool) -> None:
    """Set stop flag synchronously (for signal handlers).
    
    This function can be called from signal handlers which run in sync context.
    Uses threading.Lock for thread-safe access to the flag.
    """
    # Use synchronous lock for thread-safe access
    with _stop_flag_lock_sync:
        global _stop_flag
        _stop_flag = stop
    
    # Also try to schedule async update if event loop is available
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop is running, schedule the async call for consistency
            asyncio.create_task(set_stop_flag(stop))
    except RuntimeError:
        # No event loop, flag already set with sync lock above
        pass

