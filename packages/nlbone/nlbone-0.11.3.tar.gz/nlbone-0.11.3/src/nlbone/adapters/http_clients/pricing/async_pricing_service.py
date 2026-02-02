from decimal import Decimal
from typing import Dict, Literal, Optional

import httpx

from nlbone.adapters.auth.async_token_provider import AsyncClientTokenProvider
from nlbone.adapters.http_clients import CalculatePriceIn, CalculatePriceOut
from nlbone.adapters.http_clients.pricing.pricing_service import PricingError
from nlbone.config.settings import get_settings
from nlbone.utils.http import normalize_https_base


class AsyncPricingService:
    def __init__(
        self,
        token_provider: AsyncClientTokenProvider,
        base_url: Optional[str] = None,
        timeout_seconds: Optional[float] = None,
        client: Optional[httpx.AsyncClient] = None,
    ) -> None:
        s = get_settings()
        self._token_provider = token_provider
        self._base_url = normalize_https_base(base_url or str(s.PRICING_SERVICE_URL), enforce_https=False)
        self._timeout = httpx.Timeout(timeout_seconds or float(s.HTTP_TIMEOUT_SECONDS), connect=5.0)
        self._client = client or httpx.AsyncClient(
            timeout=self._timeout,
            verify=True if s.ENV == "prod" else False,
            limits=httpx.Limits(
                max_keepalive_connections=s.HTTPX_MAX_KEEPALIVE_CONNECTIONS, max_connections=s.HTTPX_MAX_CONNECTIONS
            ),
        )

    async def calculate(
        self, items: list[CalculatePriceIn], response: Literal["list", "dict"] = "dict"
    ) -> CalculatePriceOut:
        payload = {"items": [i.model_dump(mode="json") for i in items]}

        response_obj = await self._client.post(
            f"{self._base_url}/price/calculate",
            params={"response": response},
            headers={"X-Api-Key": get_settings().PRICING_API_SECRET, "X-Client-Id": get_settings().KEYCLOAK_CLIENT_ID},
            # headers=auth_headers(await self._token_provider.get_access_token()),
            json=payload,
        )

        if response_obj.status_code not in (200, 204):
            raise PricingError(response_obj.status_code, response_obj.text)

        if response_obj.status_code == 204 or not response_obj.content:
            return CalculatePriceOut.model_validate(root=[])

        return CalculatePriceOut.model_validate(response_obj.json())

    async def exchange_rates(self) -> Dict[str, Decimal]:
        response_obj = await self._client.get(
            f"{self._base_url}/variables/key/exchange_rates",
            headers={"X-Api-Key": get_settings().PRICING_API_SECRET, "X-Client-Id": get_settings().KEYCLOAK_CLIENT_ID},
            # headers=auth_headers(await self._token_provider.get_access_token()),
        )

        if response_obj.status_code != 200:
            raise PricingError(response_obj.status_code, response_obj.text)

        values = response_obj.json().get("values", [])

        return {str(v["key"]): Decimal(str(v["value"])) for v in values}
