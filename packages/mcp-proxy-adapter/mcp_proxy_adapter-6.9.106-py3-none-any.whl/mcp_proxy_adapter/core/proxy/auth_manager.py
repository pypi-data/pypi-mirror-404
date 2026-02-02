"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Authentication management for proxy registration.
"""

from typing import Dict, Any, Optional

from mcp_proxy_adapter.core.logging import get_global_logger


class AuthManager:
    """Manager for authentication in proxy registration."""

    def __init__(self, client_security, registration_config: Dict[str, Any]):
        """
        Initialize authentication manager.

        Args:
            client_security: Client security manager instance
            registration_config: Registration configuration
        """
        self.client_security = client_security
        self.registration_config = registration_config
        self.logger = get_global_logger()

    def get_headers(self) -> Dict[str, str]:
        """Return auth headers for proxy registration requests.

        Legacy registration client (`core/proxy/registration_client.py`) expects this API.
        The canonical implementation lives in `ClientSecurityManager.get_client_auth_headers()`.
        """
        auth_method: str = str(self.registration_config.get("auth_method", "api_key"))
        api_key: Optional[str] = self.registration_config.get("api_key")
        token: Optional[str] = self.registration_config.get("token")

        # Prefer security framework helper if available
        if self.client_security and hasattr(self.client_security, "get_client_auth_headers"):
            try:
                headers = self.client_security.get_client_auth_headers(
                    auth_method=auth_method,
                    api_key=api_key,
                    token=token,
                )
                # Ensure JSON by default for proxy registration endpoints
                headers.setdefault("Content-Type", "application/json")
                return headers
            except Exception as exc:  # noqa: BLE001
                self.logger.warning("Failed to build auth headers via client_security: %s", exc)

        # Minimal fallback (keeps client operational even if security manager is absent)
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if auth_method in ("api_key", "token"):
            if api_key:
                headers["X-API-Key"] = api_key
                headers["Authorization"] = f"Bearer {api_key}"
            elif token:
                headers["Authorization"] = f"Bearer {token}"
        elif auth_method == "jwt" and token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
