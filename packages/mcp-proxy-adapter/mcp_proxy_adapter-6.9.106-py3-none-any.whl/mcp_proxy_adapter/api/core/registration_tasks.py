"""Async helper routines for proxy heartbeat and unregister flows.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from .registration_context import HeartbeatSettings, ProxyCredentials


async def _wait_for_server_listening(
    server_url: str,
    *,
    timeout_seconds: float,
    poll_interval_seconds: float,
    logger: Any,
) -> bool:
    """
    Wait until the local server starts listening on the advertised host/port.

    MCP-Proxy validates a server during registration by calling it immediately
    (command discovery via OpenAPI/get_methods). If we attempt registration too
    early (before Hypercorn starts listening), the proxy may cache an empty
    command set and registration will keep failing.

    This helper prevents that race by waiting for a TCP connection to succeed.
    It intentionally does not perform HTTP/TLS requests (works for http/https/mtls).
    """
    from urllib.parse import urlparse

    parsed = urlparse(server_url)
    host = parsed.hostname
    if not host:
        logger.warning("⚠️  Cannot parse host from server_url=%s", server_url)
        return False

    scheme = parsed.scheme or "http"
    default_port = 443 if scheme in ("https", "mtls") else 80
    port = parsed.port or default_port

    deadline = asyncio.get_running_loop().time() + max(0.0, timeout_seconds)
    while asyncio.get_running_loop().time() < deadline:
        try:
            reader, writer = await asyncio.open_connection(host, port)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # noqa: BLE001
                # Some transports may not support wait_closed(), ignore.
                pass
            return True
        except Exception:  # noqa: BLE001
            await asyncio.sleep(max(0.05, poll_interval_seconds))

    logger.warning(
        "⚠️  Server did not start listening in %.1fs: %s",
        timeout_seconds,
        server_url,
    )
    return False


def create_heartbeat_task(
    registration_manager: Any,
    proxy_url: str,
    server_name: str,
    server_url: str,
    capabilities: List[str],
    metadata: Dict[str, Any],
    settings: HeartbeatSettings,
    credentials: ProxyCredentials,
    logger: Any,
) -> asyncio.Task:
    """Create and return an asyncio Task that sends heartbeats.

    The heartbeat loop will:
    1. Check global registration status (with mutex)
    2. If not registered, attempt registration
    3. If registered, send heartbeat
    """

    interval = max(2, settings.interval)

    # Import here to avoid circular import
    from mcp_proxy_adapter.api.core.registration_manager import (
        set_registration_status,
        set_registration_snapshot,
        get_stop_flag,
    )

    async def heartbeat_loop() -> None:
        # Extract protocol, host, port from proxy_url for JsonRpcClient
        from urllib.parse import urlparse

        parsed = urlparse(proxy_url)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Extract cert and key from credentials if available
        client_cert = None
        client_key = None
        client_ca = None
        if credentials.cert:
            client_cert, client_key = credentials.cert
        if isinstance(credentials.verify, str):
            client_ca = credentials.verify

        # Lazy import to avoid circular dependency
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

        client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
            check_hostname=credentials.check_hostname,
        )
        try:
            # Avoid early registration race: wait until this server is actually listening.
            await _wait_for_server_listening(
                server_url,
                timeout_seconds=15.0,
                poll_interval_seconds=0.25,
                logger=logger,
            )
            while True:
                try:
                    # Check stop flag first (thread-safe with mutex)
                    should_stop = await get_stop_flag()
                    if should_stop:
                        logger.info("🛑 Stop flag set, stopping heartbeat loop")
                        break

                    if not getattr(registration_manager, "registered", False):
                        config_for_registration = getattr(
                            registration_manager, "_registration_config", None
                        )
                        if config_for_registration:
                            logger.info(
                                "📡 Attempting proxy registration before heartbeat"
                            )
                            try:
                                await registration_manager.register_with_proxy(
                                    config_for_registration
                                )
                            except Exception as exc:  # noqa: BLE001
                                logger.warning(
                                    "⚠️  Initial registration attempt failed: %s", exc
                                )
                                await asyncio.sleep(min(5, interval))
                                continue

                    heartbeat_url = settings.url
                    logger.info(
                        "💓 Sending heartbeat with registration payload to %s",
                        heartbeat_url,
                    )
                    try:
                        await client.heartbeat_to_proxy(
                            proxy_url=heartbeat_url,
                            server_name=server_name,
                            server_url=server_url,
                            capabilities=list(capabilities),
                            metadata=metadata,
                            cert=credentials.cert,
                            verify=credentials.verify,
                        )
                        registration_manager.registered = True
                        await set_registration_status(True)
                        await set_registration_snapshot(registered=True)
                        logger.info("💓 Heartbeat/registration acknowledged by proxy")
                        await asyncio.sleep(interval)
                    except Exception as exc:
                        registration_manager.registered = False
                        await set_registration_status(False)
                        await set_registration_snapshot(registered=False)
                        logger.warning("⚠️  Heartbeat/registration failed: %s", exc)
                        await asyncio.sleep(min(5, interval))
                except asyncio.CancelledError:
                    raise
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"Heartbeat/Registration error: {exc}")
                    await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.debug("Heartbeat loop cancelled")
            raise
        finally:
            await client.close()

    return asyncio.create_task(heartbeat_loop())


async def unregister_from_proxy(
    proxy_url: str,
    server_name: str,
    endpoint: str,
    credentials: ProxyCredentials,
    logger: Any,
) -> None:
    """Unregister adapter from proxy using provided credentials."""

    # Extract protocol, host, port from proxy_url for JsonRpcClient
    from urllib.parse import urlparse

    parsed = urlparse(proxy_url)
    client_protocol = parsed.scheme or "http"
    client_host = parsed.hostname or "localhost"
    client_port = parsed.port or (443 if client_protocol == "https" else 80)

    # Extract cert and key from credentials if available
    client_cert = None
    client_key = None
    client_ca = None
    if credentials.cert:
        client_cert, client_key = credentials.cert
    if isinstance(credentials.verify, str):
        client_ca = credentials.verify

    # Lazy import to avoid circular dependency
    from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

    client = JsonRpcClient(
        protocol=client_protocol,
        host=client_host,
        port=client_port,
        cert=client_cert,
        key=client_key,
        ca=client_ca,
        check_hostname=credentials.check_hostname,
    )
    try:
        full_url = f"{proxy_url}{endpoint}"
        await client.unregister_from_proxy(
            proxy_url=full_url,
            server_name=server_name,
            cert=credentials.cert,
            verify=credentials.verify,
        )
        logger.info("Unregistered from proxy: %s", server_name)
    finally:
        await client.close()
