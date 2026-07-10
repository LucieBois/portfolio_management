from collections.abc import Generator
from unittest.mock import patch

import pytest

from portfolio_management.clients.eodhd import EODHDClient
from portfolio_management.models import ExchangeModel

##
## HELPERS
##


def make_exchange_dict(
    code: str = "NYSE",
    name: str = "New York Stock Exchange",
) -> dict[str, object]:
    """Raw API dict as EODHD would return it, with PascalCase keys."""
    return {
        "Name": name,
        "Code": code,
        "OperatingMIC": f"MIC-{code}",
        "Country": "United States",
        "Currency": "USD",
        "CountryISO2": "US",
        "CountryISO3": "USA",
    }


class _FakeResponse:
    """Minimal requests.Response stub."""

    _body: list[dict[str, object]] | dict[str, object]
    _error: Exception | None

    def __init__(
        self,
        body: list[dict[str, object]] | dict[str, object],
        *,
        error: Exception | None = None,
    ) -> None:
        self._body = body
        self._error = error

    def raise_for_status(self) -> None:
        if self._error is not None:
            raise self._error

    def json(self) -> list[dict[str, object]] | dict[str, object]:
        return self._body


class _CapturingSession:
    """Fake requests.Session that records params from the last get() call."""

    _response: _FakeResponse

    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.last_params: dict[str, str | int] = {}

    def get(
        self, _url: str, params: dict[str, str | int] | None = None
    ) -> _FakeResponse:
        self.last_params = params or {}
        return self._response


class _StubGet:
    """Callable stub for EODHDClient._get with a fixed return value."""

    _body: list[dict[str, object]] | dict[str, object]

    def __init__(self, body: list[dict[str, object]] | dict[str, object]) -> None:
        self._body = body

    def __call__(
        self,
        endpoint: str,
        params: dict[str, str | int] | None = None,
    ) -> list[dict[str, object]] | dict[str, object]:
        return self._body


##
## FIXTURES
##


@pytest.fixture()
def client() -> Generator[EODHDClient, None, None]:
    """An EODHDClient with a stubbed API key and no real HTTP calls."""
    with patch("portfolio_management.clients.eodhd.ClientsSettings") as mock_settings:
        mock_settings.return_value.EODHD_API_KEY = "test-api-key"  # pyright: ignore[reportAny]
        yield EODHDClient()


##
## TESTS
##


class TestGet:
    def test_returns_parsed_json(self, client: EODHDClient) -> None:
        """_get returns the parsed JSON body on a successful response."""
        client.session = _CapturingSession(  # pyright: ignore[reportAttributeAccessIssue]
            _FakeResponse([{"key": "value"}])
        )

        result = client._get("some-endpoint")  # pyright: ignore[reportPrivateUsage]

        assert result == [{"key": "value"}]

    def test_injects_api_token_and_fmt(self, client: EODHDClient) -> None:
        """_get always appends api_token and fmt=json to params, preserving caller params."""
        session = _CapturingSession(_FakeResponse({}))
        client.session = session  # pyright: ignore[reportAttributeAccessIssue]

        params: dict[str, str | int] = {"from": "2020-01-01"}
        _ = client._get("some-endpoint", params=params)  # pyright: ignore[reportPrivateUsage]

        assert session.last_params["api_token"] == "test-api-key"
        assert session.last_params["fmt"] == "json"
        assert session.last_params["from"] == "2020-01-01"

    def test_raises_on_http_error(self, client: EODHDClient) -> None:
        """_get propagates any HTTPError raised by raise_for_status."""
        client.session = _CapturingSession(  # pyright: ignore[reportAttributeAccessIssue]
            _FakeResponse({}, error=Exception("404 Not Found"))
        )

        with pytest.raises(Exception, match="404 Not Found"):
            _ = client._get("bad-endpoint")  # pyright: ignore[reportPrivateUsage]


class TestGetExchanges:
    def test_returns_list_of_exchange_models(self, client: EODHDClient) -> None:
        """get_exchanges returns a typed list of ExchangeModel on a valid response."""
        raw: list[dict[str, object]] = [
            make_exchange_dict(),
            make_exchange_dict(code="LSE", name="London Stock Exchange"),
        ]
        client._get = _StubGet(raw)  # pyright: ignore[reportPrivateUsage]

        result = client.get_exchanges()

        assert len(result) == 2
        assert all(isinstance(m, ExchangeModel) for m in result)

    def test_exchange_fields_are_normalised(self, client: EODHDClient) -> None:
        """CleanStr fields are lowercased and whitespace-stripped by Pydantic."""
        client._get = _StubGet([make_exchange_dict()])  # pyright: ignore[reportPrivateUsage]

        result = client.get_exchanges()

        assert result[0].code == "nyse"
        assert result[0].currency == "usd"
        assert result[0].country_iso2 == "us"

    def test_raises_when_response_is_not_a_list(self, client: EODHDClient) -> None:
        """get_exchanges raises ValueError when the API unexpectedly returns a dict."""
        client._get = _StubGet({"error": "unexpected"})  # pyright: ignore[reportPrivateUsage]

        with pytest.raises(ValueError, match="expected a list of dicts"):
            _ = client.get_exchanges()
