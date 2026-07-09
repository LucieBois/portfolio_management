import requests

from portfolio_management.core import ClientsSettings
from portfolio_management.models import ExchangeModel


class EODHDClient:
    BASE_URL: str = "https://eodhd.com/api"

    def __init__(self):
        self.API_KEY: str = ClientsSettings().EODHD_API_KEY
        self.session: requests.Session = requests.Session()

    def _get(
        self, endpoint: str, params: dict[str, str | int] | None = None
    ) -> list[dict[str, object]] | dict[str, object]:
        if not params:
            params = {}

        params["api_token"] = self.API_KEY
        params["fmt"] = "json"

        response = self.session.get(f"{self.BASE_URL}/{endpoint}", params=params)
        response.raise_for_status()

        return response.json()  # pyright: ignore[reportAny]

    def get_exchanges(self) -> list[ExchangeModel]:
        exchanges_response = self._get(endpoint="exchanges-list")

        if not isinstance(exchanges_response, list):
            raise ValueError(
                f"EODHC returned a list of exchanges as type {type(exchanges_response)}, while expected a list of dicts"
            )

        exchanges_models: list[ExchangeModel] = []
        for item in exchanges_response:
            item_model = ExchangeModel.model_validate(item)
            exchanges_models.append(item_model)

        return exchanges_models
