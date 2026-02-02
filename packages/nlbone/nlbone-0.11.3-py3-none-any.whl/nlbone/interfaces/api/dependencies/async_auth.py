import functools

from nlbone.adapters.auth.async_auth_service import get_async_auth_service
from nlbone.interfaces.api.exceptions import ForbiddenException, UnauthorizedException
from nlbone.utils.context import current_request

from .auth import bypass_authz, current_user_id


async def current_client_id() -> str:
    request = current_request()
    if client_id := await get_async_auth_service().get_client_id(request.state.token):
        return str(client_id)
    raise UnauthorizedException()


async def client_has_access_func(*, permissions=None):
    request = current_request()
    if not await get_async_auth_service().client_has_access(request.state.token, permissions=permissions):
        raise ForbiddenException(f"Forbidden {permissions}")
    return True


def client_has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await client_has_access_func(permissions=permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def user_authenticated(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not current_user_id():
            raise UnauthorizedException()
        return await func(*args, **kwargs)

    return wrapper


async def user_has_access_func(*, permissions=None):
    request = current_request()
    if not current_user_id():
        raise UnauthorizedException()
    if bypass_authz():
        return True
    if not await get_async_auth_service().has_access(request.state.token, permissions=permissions):
        raise ForbiddenException(f"Forbidden {permissions}")
    return True


def has_access(*, permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await user_has_access_func(permissions=permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def client_or_user_has_access_func(permissions=None, client_permissions=None):
    if bypass_authz():
        return True
    request = current_request()
    token = getattr(request.state, "token", None)
    if not token:
        raise UnauthorizedException()
    needed = client_permissions or permissions
    try:
        await client_has_access_func(permissions=needed)
    except Exception:
        await user_has_access_func(permissions=needed)


def client_or_user_has_access(*, permissions=None, client_permissions=None):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            await client_or_user_has_access_func(permissions=permissions, client_permissions=client_permissions)
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def is_permitted_user(permissions=None):
    async def check_permissions():
        try:
            if bypass_authz():
                return True
            request = current_request()
            if not current_user_id():
                raise UnauthorizedException()
            if not await get_async_auth_service().has_access(request.state.token, permissions=permissions):
                raise ForbiddenException(f"Forbidden {permissions}")
            return True
        except ForbiddenException:
            return False
        except UnauthorizedException:
            return False

    return check_permissions
