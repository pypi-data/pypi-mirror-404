import asyncio
import time
from typing import Optional

from nlbone.core.ports.auth import AsyncAuthService as BaseAuthService


class AsyncClientTokenProvider:
    """
    Caches Keycloak client-credentials token and refreshes before expiry.
    """

    def __init__(self, auth: BaseAuthService, *, skew_seconds: int = 30) -> None:
        self._auth = auth
        self._skew = skew_seconds
        self._lock = asyncio.Lock()
        self._token: Optional[str] = None  # access_token
        self._expires_at: float = 0.0  # epoch seconds

    def _needs_refresh(self) -> bool:
        return not self._token or time.time() >= (self._expires_at - self._skew)

    async def get_access_token(self) -> str:
        """
        Return a valid access token; refresh asynchronously if needed.
        """
        if not self._needs_refresh() and self._token:
            return self._token

        async with self._lock:
            if not self._needs_refresh() and self._token:
                return self._token

            data = await self._auth.get_client_token()

            if not data or "access_token" not in data:
                raise RuntimeError("Failed to retrieve access_token")

            access_token = data["access_token"]
            expires_in = int(data.get("expires_in", 15 * 60))

            self._token = access_token
            self._expires_at = time.time() + max(1, expires_in)

            return self._token

    async def get_auth_header(self) -> str:
        token = await self.get_access_token()
        return f"Bearer {token}"
