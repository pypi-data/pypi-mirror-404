from typing import Any, Callable, Optional, Union

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from nlbone.config.settings import get_settings
from nlbone.core.domain.models import CurrentUserData
from nlbone.core.ports.auth import AsyncAuthService as BaseAuthService

try:
    from dependency_injector import providers

    ProviderType = providers.Provider  # type: ignore
except ImportError:
    ProviderType = object


def _to_factory(auth: Union[BaseAuthService, Callable[[], BaseAuthService], ProviderType]):
    try:
        from dependency_injector import providers as _p  # type: ignore

        if isinstance(auth, _p.Provider):
            return auth
    except Exception:
        pass
    if callable(auth):
        return auth
    return lambda: auth


def _extract_token(request: Request) -> Optional[str]:
    auth_header = request.headers.get("Authorization")
    if auth_header:
        try:
            scheme, token = auth_header.split(" ", 1)
            if scheme.lower() == "bearer":
                return token
        except ValueError:
            pass

    return request.cookies.get("access_token") or request.cookies.get("j_token")


async def authenticate_request(request: Request, auth_factory: Callable[[], BaseAuthService]) -> None:
    token = _extract_token(request)
    if not token:
        return

    request.state.token = token
    try:
        auth_service = auth_factory()
        data = await auth_service.verify_token(token)

        if data:
            request.state.user_id = data.get("sub") or data.get("user_id")

            try:
                request.state.user = CurrentUserData.from_dict(data)
            except Exception:
                pass
    except Exception:
        pass


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth: Union[BaseAuthService, Callable[[], BaseAuthService], ProviderType]):
        super().__init__(app)
        self._get_auth = _to_factory(auth)

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        request.state.client_id = None
        request.state.user_id = None
        request.state.token = None
        request.state.user = None

        client_id = request.headers.get("X-Client-Id")
        api_key = request.headers.get("X-Api-Key")

        if client_id and api_key:
            if api_key == get_settings().PRICING_API_SECRET:
                request.state.client_id = client_id
                return await call_next(request)

        if (
            request.headers.get("Authorization")
            or request.cookies.get("access_token")
            or request.cookies.get("j_token")
        ):
            await authenticate_request(request, self._get_auth)

        return await call_next(request)
