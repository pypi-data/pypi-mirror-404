"""Proxy registration helpers for JsonRpcClient.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

from __future__ import annotations

import logging
import re
import uuid as uuid_module
from typing import Any, Dict, List, Optional, Tuple, TYPE_CHECKING, Union, cast
from urllib.parse import urlparse

from mcp_proxy_adapter.client.jsonrpc_client.transport import JsonRpcTransport

if TYPE_CHECKING:
    from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient


class ProxyApiMixin(JsonRpcTransport):
    """Mixin providing proxy registration helpers."""

    def _maybe_validate_uuid(self, metadata: Optional[Dict[str, Any]]) -> None:
        """Validate metadata.uuid if present (UUID4 preferred, but not mandatory).

        UUID is expected to be provided in ``metadata["uuid"]`` by the server-side
        registration context builder. This mixin will move it to the root-level
        ``uuid`` field when talking to proxies.
        """
        if not metadata:
            return
        uuid_value = metadata.get("uuid")
        if not uuid_value:
            return
        try:
            uuid_obj = uuid_module.UUID(str(uuid_value))
            if uuid_obj.version != 4:
                logging.getLogger(__name__).warning(
                    "metadata.uuid is not UUID4 (version=%s): %s",
                    uuid_obj.version,
                    uuid_value,
                )
        except Exception:  # noqa: BLE001
            logging.getLogger(__name__).warning(
                "metadata.uuid is not a valid UUID string: %s", uuid_value
            )

    def _extract_and_validate_uuid(
        self, metadata: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """
        Extract UUID value from metadata and validate it (UUID4 preferred).

        Returns:
            UUID string or None when not provided.
        """
        if not metadata:
            return None
        uuid_value = metadata.get("uuid")
        if not uuid_value:
            return None
        # Reuse logging behavior from the validator (non-fatal)
        self._maybe_validate_uuid(metadata)
        return str(uuid_value)

    async def register_with_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> Dict[str, Any]:
        """Register with proxy using JsonRpcClient (no direct httpx usage)."""
        # Extract UUID from metadata (required by MCP-Proxy and adapter proxy)
        uuid_value = self._extract_and_validate_uuid(metadata)

        # Remove UUID from metadata; it must be passed at root level of the payload.
        clean_metadata = dict(metadata or {})
        clean_metadata.pop("uuid", None)

        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": server_url,
            "capabilities": capabilities or [],
            "metadata": clean_metadata,
        }
        if uuid_value:
            payload["uuid"] = uuid_value

        # Build register URL from proxy_url (OpenAPI: /register)
        # proxy_url can be base URL or already include /register.
        proxy_base = proxy_url.rstrip("/")
        register_url = (
            proxy_base if proxy_base.endswith("/register") else f"{proxy_base}/register"
        )

        # Determine if we should use configured client or create new JsonRpcClient
        # Use configured client if:
        # 1. No cert/verify override provided AND
        # 2. proxy_url matches base_url (same host/port/protocol)
        use_configured_client = (
            cert is None and verify is None and proxy_url.startswith(self.base_url)
        )

        logger = logging.getLogger(__name__)
        logger.info("🔍 [REGISTRATION] Starting registration process")
        logger.info("🔍 [REGISTRATION] Register URL: %s", register_url)
        logger.info("🔍 [REGISTRATION] Base URL: %s", self.base_url)
        logger.info(
            "🔍 [REGISTRATION] Server name: %s, Server URL: %s", server_name, server_url
        )
        import json

        logger.info("🔍 [REGISTRATION] Payload: %s", json.dumps(payload, indent=2))
        logger.info("🔍 [REGISTRATION] Cert: %s, Verify: %s", cert is not None, verify)
        logger.info(
            "🔍 [REGISTRATION] Use configured client: %s", use_configured_client
        )

        def _needs_legacy_uuid_retry(status_code: int, body_text: str) -> bool:
            # UUID is always sent at root level now; keep compatibility retry for older proxies.
            if status_code not in (400, 422):
                return False
            lower = (body_text or "").lower()
            return "uuid" in lower and ("required" in lower or "missing" in lower)

        def _build_legacy_uuid_payload() -> Optional[Dict[str, Any]]:
            # Legacy: keep UUID only in metadata (very old proxy variants).
            if not uuid_value:
                return None
            legacy = dict(payload)
            legacy.pop("uuid", None)
            legacy_metadata = dict(clean_metadata)
            legacy_metadata["uuid"] = str(uuid_value)
            legacy["metadata"] = legacy_metadata
            return legacy

        try:
            if use_configured_client:
                # Use configured client from JsonRpcTransport
                client = await self._get_client()
                response = await client.post(register_url, json=payload)
            else:
                # Create new JsonRpcClient with explicit settings
                # Extract protocol, host, port from proxy_url
                parsed = urlparse(proxy_base)
                client_protocol = parsed.scheme or "http"
                client_host = parsed.hostname or "localhost"
                client_port = parsed.port or (443 if client_protocol == "https" else 80)

                # Extract cert and key from override or self
                client_cert = None
                client_key = None
                client_ca = None
                if cert:
                    client_cert, client_key = cert
                elif self.cert:
                    client_cert, client_key = self.cert

                if isinstance(verify, str):
                    client_ca = verify
                elif verify is False:
                    client_ca = None
                elif isinstance(self.verify, str):
                    client_ca = self.verify
                else:
                    client_ca = None

                # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
                from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

                proxy_client = JsonRpcClient(
                    protocol=client_protocol,
                    host=client_host,
                    port=client_port,
                    cert=client_cert,
                    key=client_key,
                    ca=client_ca,
                )
                try:
                    # Use internal client from JsonRpcTransport
                    client = await proxy_client._get_client()
                    response = await client.post(register_url, json=payload)
                finally:
                    await proxy_client.close()

            # Handle response
            logger.info("🔍 [REGISTRATION] Response status: %s", response.status_code)
            logger.info(
                "🔍 [REGISTRATION] Response headers: %s", dict(response.headers)
            )
            try:
                response_text = response.text
                logger.info("🔍 [REGISTRATION] Response body: %s", response_text[:500])
            except Exception:
                pass

            # Handle response
            if response.status_code == 400:
                error_data = cast(Dict[str, Any], response.json())
                error_msg = error_data.get("error", "").lower()
                if "already registered" in error_msg:
                    # Retry registration after unregister
                    await self._retry_registration_after_unregister_via_client(
                        proxy_base,
                        register_url,
                        server_name,
                        server_url,
                        capabilities,
                        metadata,
                        error_data,
                        cert,
                        verify,
                    )

            if response.status_code >= 400:
                try:
                    error_data = cast(Dict[str, Any], response.json())
                    error_msg = error_data.get(
                        "error",
                        error_data.get("message", f"HTTP {response.status_code}"),
                    )
                    raise RuntimeError(f"Registration failed: {error_msg}")
                except (ValueError, KeyError):
                    # Heuristic fallback: retry with legacy uuid-at-root if server demands it
                    try:
                        if _needs_legacy_uuid_retry(
                            response.status_code, getattr(response, "text", "")
                        ):
                            legacy_payload = _build_legacy_uuid_payload()
                            if legacy_payload is not None:
                                logger.warning(
                                    "Proxy rejected OpenAPI payload (uuid required). Retrying with legacy uuid-at-root payload."
                                )
                                response2 = await client.post(
                                    register_url, json=legacy_payload
                                )
                                response2.raise_for_status()
                                return cast(Dict[str, Any], response2.json())
                    except Exception:  # noqa: BLE001
                        pass
                    response.raise_for_status()

            response.raise_for_status()
            result = cast(Dict[str, Any], response.json())
            return result
        except Exception as exc:  # noqa: BLE001
            if "Connection" in str(type(exc).__name__):
                error_msg = f"Connection failed to {register_url}"
                raise ConnectionError(error_msg) from exc
            elif "Timeout" in str(type(exc).__name__):
                raise TimeoutError(f"Request timeout to {register_url}") from exc
            else:
                raise ConnectionError(
                    f"HTTP error connecting to {register_url}: {exc}"
                ) from exc

    async def unregister_from_proxy(
        self,
        proxy_url: str,
        server_name: str,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> Dict[str, Any]:
        """Unregister from proxy using JsonRpcClient (no direct httpx usage)."""
        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": "",
            "capabilities": [],
            "metadata": {},
        }

        proxy_base = proxy_url.rstrip("/")
        unregister_url = (
            proxy_base
            if proxy_base.endswith("/unregister")
            else f"{proxy_base}/unregister"
        )

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert

        if isinstance(verify, str):
            client_ca = verify
        elif verify is False:
            client_ca = None
        elif isinstance(self.verify, str):
            client_ca = self.verify
        else:
            client_ca = None

        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.post(unregister_url, json=payload)
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def heartbeat_to_proxy(
        self,
        proxy_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        cert: Optional[Tuple[str, str]] = None,
        verify: Optional[Union[bool, str]] = None,
    ) -> None:
        """Send heartbeat to proxy using JsonRpcClient (no direct httpx usage).

        Args:
            proxy_url: Full URL to heartbeat endpoint (e.g., "http://host:port/proxy/heartbeat")
            server_name: Server identifier
            server_url: Server URL
            capabilities: Server capabilities
            metadata: Server metadata
            cert: Optional client certificate tuple (cert_file, key_file)
            verify: Optional SSL verification (bool or CA cert path)
        """
        uuid_value = self._extract_and_validate_uuid(metadata)
        clean_metadata = dict(metadata or {})
        clean_metadata.pop("uuid", None)

        payload: Dict[str, Any] = {
            "server_id": server_name,
            "server_url": server_url,
            "capabilities": capabilities or [],
            "metadata": clean_metadata,
        }
        if uuid_value:
            payload["uuid"] = uuid_value

        # OpenAPI supports timestamp (recommended for observability)
        import time

        payload["timestamp"] = int(time.time())

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_url)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert

        if isinstance(verify, str):
            client_ca = verify
        elif verify is False:
            client_ca = None
        elif isinstance(self.verify, str):
            client_ca = self.verify
        else:
            client_ca = None

        def _build_legacy_uuid_payload() -> Optional[Dict[str, Any]]:
            # Legacy: keep UUID only in metadata.
            if not uuid_value:
                return None
            legacy = dict(payload)
            legacy.pop("uuid", None)
            legacy_metadata = dict(clean_metadata)
            legacy_metadata["uuid"] = str(uuid_value)
            legacy["metadata"] = legacy_metadata
            return legacy

        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            response = await client.post(proxy_url, json=payload)
            if response.status_code in (400, 422):
                # Retry legacy uuid-at-root only when server complains
                try:
                    body_text = getattr(response, "text", "")
                    if "uuid" in (body_text or "").lower() and (
                        "required" in (body_text or "").lower()
                        or "missing" in (body_text or "").lower()
                    ):
                        legacy_payload = _build_legacy_uuid_payload()
                        if legacy_payload is not None:
                            response2 = await client.post(
                                proxy_url, json=legacy_payload
                            )
                            response2.raise_for_status()
                            return
                except Exception:  # noqa: BLE001
                    pass
            response.raise_for_status()
        finally:
            await proxy_client.close()

    async def list_proxy_servers(self, proxy_url: str) -> Dict[str, Any]:
        """List proxy servers using JsonRpcClient (no direct httpx usage)."""
        proxy_base = proxy_url.rstrip("/")

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Create JsonRpcClient for proxy
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            # OpenAPI: GET /list ; compatibility proxy: GET /servers
            response = await client.get(f"{proxy_base}/list")
            if response.status_code == 404:
                response = await client.get(f"{proxy_base}/servers")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def get_proxy_health(self, proxy_url: str) -> Dict[str, Any]:
        """Get proxy health using JsonRpcClient (no direct httpx usage)."""
        proxy_base = proxy_url.rstrip("/")

        # Extract protocol, host, port from proxy_url
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Create JsonRpcClient for proxy
        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()
            # OpenAPI: GET /health
            response = await client.get(f"{proxy_base}/health")
            response.raise_for_status()
            return cast(Dict[str, Any], response.json())
        finally:
            await proxy_client.close()

    async def _retry_registration_after_unregister_via_client(
        self,
        proxy_base: str,
        register_url: str,
        server_name: str,
        server_url: str,
        capabilities: Optional[List[str]],
        metadata: Optional[Dict[str, Any]],
        error_data: Dict[str, Any],
        cert: Optional[Tuple[str, str]],
        verify: Optional[Union[bool, str]],
    ) -> None:
        """Retry registration after unregister using JsonRpcClient."""
        match = re.search(
            r"already registered as ([^\s,]+)",
            error_data.get("error", ""),
            re.IGNORECASE,
        )
        if not match:
            return

        registered_server_key = match.group(1)
        original_server_id = (
            re.sub(r"_\d+$", "", registered_server_key)
            if "_" in registered_server_key
            else registered_server_key
        )

        # Extract protocol, host, port from proxy_base
        parsed = urlparse(proxy_base)
        client_protocol = parsed.scheme or "http"
        client_host = parsed.hostname or "localhost"
        client_port = parsed.port or (443 if client_protocol == "https" else 80)

        # Extract cert and key from override or self
        client_cert = None
        client_key = None
        client_ca = None
        if cert:
            client_cert, client_key = cert
        elif self.cert:
            client_cert, client_key = self.cert

        if isinstance(verify, str):
            client_ca = verify
        elif verify is False:
            client_ca = None
        elif isinstance(self.verify, str):
            client_ca = self.verify
        else:
            client_ca = None

        # Create JsonRpcClient for proxy (lazy import to avoid circular dependency)
        from mcp_proxy_adapter.client.jsonrpc_client import JsonRpcClient

        proxy_client = JsonRpcClient(
            protocol=client_protocol,
            host=client_host,
            port=client_port,
            cert=client_cert,
            key=client_key,
            ca=client_ca,
        )
        try:
            # Use internal client from JsonRpcTransport
            client = await proxy_client._get_client()

            # Unregister
            unregister_payload: Dict[str, Any] = {
                "server_id": original_server_id,
                "server_url": "",
                "capabilities": [],
                "metadata": {},
            }
            unregister_response = await client.post(
                f"{proxy_base}/unregister",
                json=unregister_payload,
            )
            if unregister_response.status_code != 200:
                return

            # Retry registration
            # Extract and validate UUID from metadata
            uuid_value = self._extract_and_validate_uuid(metadata)

            retry_payload: Dict[str, Any] = {
                "server_id": server_name,
                "server_url": server_url,
                "uuid": uuid_value,  # UUID at root level - REQUIRED
                "capabilities": capabilities or [],
                "metadata": metadata or {},
            }
            await client.post(register_url, json=retry_payload)
        finally:
            await proxy_client.close()
