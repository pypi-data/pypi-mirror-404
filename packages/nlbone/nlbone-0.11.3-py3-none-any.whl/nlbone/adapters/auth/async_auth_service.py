from functools import lru_cache
from typing import Any, Optional, Set

import httpx

from nlbone.config.settings import get_settings
from nlbone.core.ports.auth import AsyncAuthService as BaseAuthService
from nlbone.utils.cache import cached
from nlbone.utils.http import normalize_https_base


class AsyncAuthService(BaseAuthService):
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self):
        s = get_settings()
        self.client_id = s.CLIENT_ID or s.KEYCLOAK_CLIENT_ID
        self.client_secret = s.CLIENT_SECRET.get_secret_value().strip()
        self._base_url = normalize_https_base(s.AUTH_SERVICE_URL.unicode_string(), enforce_https=False)
        self._timeout = float(s.HTTP_TIMEOUT_SECONDS)

    @classmethod
    def get_client(cls) -> httpx.AsyncClient:
        if cls._client is None or cls._client.is_closed:
            s = get_settings()
            cls._client = httpx.AsyncClient(
                timeout=float(s.HTTP_TIMEOUT_SECONDS),
                limits=httpx.Limits(
                    max_keepalive_connections=s.HTTPX_MAX_KEEPALIVE_CONNECTIONS,
                    max_connections=s.HTTPX_MAX_CONNECTIONS,
                ),
            )
        return cls._client

    @cached(ttl=15 * 60)
    async def verify_token(self, token: str) -> Optional[dict[str, Any]]:
        if not token:
            return None

        url = f"{self._base_url}/introspect"
        client = self.get_client()

        try:
            response = await client.post(url, data={"token": token})
            if response.status_code == 200:
                data = response.json()
                if data.get("active") is True:
                    return data
        except httpx.RequestError as e:
            pass

        return None

    async def has_access(self, token: str, permissions: list[str]) -> bool:
        data = await self.verify_token(token)
        if not data:
            return False

        allowed = set(data.get("allowed_permissions", []))
        required = {f"{self.client_id}#{perm}" for perm in permissions}

        return required.issubset(allowed)

    async def client_has_access(
        self, token: str, permissions: list[str], allowed_clients: Set[str] | None = None
    ) -> bool:
        return await self.has_access(token, permissions)

    async def get_client_id(self, token: str) -> Optional[str]:
        data = await self.verify_token(token)
        if data:
            username = data.get("preferred_username", "")
            if username.startswith("service-account"):
                return username
        return None

    async def is_client_token(self, token: str, allowed_clients: Set[str] | None = None) -> bool:
        data = await self.verify_token(token)
        if data:
            return data.get("preferred_username", "").startswith("service-account")
        return False

    async def get_client_token(self) -> dict | None:
        url = f"{self._base_url}/token"
        client = self.get_client()

        try:
            result = await client.post(
                url,
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
            if result.status_code == 200:
                return result.json()
        except httpx.RequestError:
            pass

        return None

    async def get_permissions(self, token: str) -> list[str]:
        data = await self.verify_token(token)
        return data.get("allowed_permissions", []) if data else []


@lru_cache(maxsize=1)
def get_async_auth_service() -> AsyncAuthService:
    return AsyncAuthService()
