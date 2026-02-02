from __future__ import annotations

from typing import Any, AsyncIterator, Optional

import httpx

from nlbone.adapters.auth.async_token_provider import AsyncClientTokenProvider
from nlbone.adapters.http_clients.uploadchi.uploadchi import UploadchiError, _filename_from_cd, _resolve_token
from nlbone.config.settings import get_settings
from nlbone.core.ports.files import AsyncFileServicePort
from nlbone.utils.http import auth_headers, build_list_query


class UploadchiAsyncClient(AsyncFileServicePort):
    def __init__(
        self,
        token_provider: Optional[AsyncClientTokenProvider] = None,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        s = get_settings()
        self._base_url = base_url or str(s.UPLOADCHI_BASE_URL)
        self._timeout = timeout_seconds or float(s.HTTP_TIMEOUT_SECONDS)
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            limits=httpx.Limits(
                max_keepalive_connections=s.HTTPX_MAX_KEEPALIVE_CONNECTIONS, max_connections=s.HTTPX_MAX_CONNECTIONS
            ),
            follow_redirects=True,
        )
        self._token_provider = token_provider

    async def aclose(self) -> None:
        await self._client.aclose()

    async def upload_file(
        self, file_bytes: bytes, filename: str, params: dict[str, Any] | None = None, token: str | None = None
    ) -> dict:
        tok = _resolve_token(token)
        files = {"file": (filename, file_bytes)}
        data = (params or {}).copy()
        r = await self._client.post(
            "/files", files=files, data=data, headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, await r.aread())
        return r.json()

    async def commit_file(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = await self._client.post(
            f"/files/{file_id}/commit", headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, await r.aread())

    async def rollback(self, file_id: str, token: str | None = None) -> None:
        if not token and not self._token_provider:
            raise UploadchiError(detail="token_provider is not provided", status=400)
        tok = _resolve_token(token)
        r = await self._client.post(
            f"/files/{file_id}/rollback", headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code not in (204, 200):
            raise UploadchiError(r.status_code, await r.aread())

    async def list_files(
        self,
        limit: int = 10,
        offset: int = 0,
        filters: dict[str, Any] | None = None,
        sort: list[tuple[str, str]] | None = None,
        token: str | None = None,
    ) -> dict:
        tok = _resolve_token(token)
        q = build_list_query(limit, offset, filters, sort)
        r = await self._client.get(
            "/files", params=q, headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, await r.aread())
        return r.json()

    async def get_file(self, file_id: str, token: str | None = None) -> dict:
        tok = _resolve_token(token)
        r = await self._client.get(
            f"/files/{file_id}", headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code >= 400:
            raise UploadchiError(r.status_code, await r.aread())
        return r.json()

    async def download_file(self, file_id: str, token: str | None = None) -> tuple[AsyncIterator[bytes], str, str]:
        tok = _resolve_token(token)
        r = await self._client.get(
            f"/files/{file_id}/download",
            headers=auth_headers(tok or await self._token_provider.get_access_token()),
            stream=True,
        )
        if r.status_code >= 400:
            body = await r.aread()
            raise UploadchiError(r.status_code, body.decode(errors="ignore"))
        filename = _filename_from_cd(r.headers.get("content-disposition"), fallback=f"file-{file_id}")
        media_type = r.headers.get("content-type", "application/octet-stream")

        async def _aiter() -> AsyncIterator[bytes]:
            try:
                async for chunk in r.aiter_bytes():
                    yield chunk
            finally:
                await r.aclose()

        return _aiter(), filename, media_type

    async def delete_file(self, file_id: str, token: str | None = None) -> None:
        tok = _resolve_token(token)
        r = await self._client.delete(
            f"/files/{file_id}", headers=auth_headers(tok or await self._token_provider.get_access_token())
        )
        if r.status_code not in (204, 200):
            body = await r.aread()
            raise UploadchiError(r.status_code, body.decode(errors="ignore"))
