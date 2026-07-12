from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from portfolio_management.cli.get_exchanges import app, get_exchanges
from portfolio_management.database import Base, ExchangesORM, get_engine
from portfolio_management.database.repos import ExchangesRepository
from portfolio_management.models import ExchangeModel

##
## HELPERS
##


def make_db(tmp_path: Path) -> tuple[Engine, str]:
    """Return a fresh in-process SQLite engine and its URI (no lru_cache clash)."""
    db_path = tmp_path / "test_get_exchanges.db"
    uri = f"sqlite:///{db_path}"
    engine = get_engine(uri)
    Base.metadata.create_all(engine)
    return engine, uri


def make_exchange(
    code: str = "NYSE",
    name: str = "New York Stock Exchange",
) -> ExchangeModel:
    """An ExchangeModel as EODHDClient.get_exchanges would return it."""
    return ExchangeModel(
        Name=name,
        Code=code,
        OperatingMIC=f"MIC-{code}",
        Country="United States",
        Currency="USD",
        CountryISO2="US",
        CountryISO3="USA",
    )


SAMPLE_EXCHANGES: list[ExchangeModel] = [
    make_exchange(),
    make_exchange(code="LSE", name="London Stock Exchange"),
]


class _StubEODHDClient:
    """Stub for EODHDClient that returns fixed exchanges and counts calls."""

    exchanges: list[ExchangeModel]
    get_exchanges_calls: int

    def __init__(self, exchanges: list[ExchangeModel]) -> None:
        self.exchanges = exchanges
        self.get_exchanges_calls = 0

    def get_exchanges(self) -> list[ExchangeModel]:
        self.get_exchanges_calls += 1
        return self.exchanges


##
## FIXTURES
##


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def db(tmp_path: Path) -> Generator[tuple[Engine, str], None, None]:
    """Yields (engine, uri) for a fresh, empty database per test.

    Patches DatabaseSettings so the CLI resolves its URI to this test database.
    """
    engine, uri = make_db(tmp_path)
    with patch(
        "portfolio_management.cli.get_exchanges.DatabaseSettings"
    ) as mock_settings:
        mock_settings.return_value.DB_URI = uri  # pyright: ignore[reportAny]
        yield engine, uri


@pytest.fixture()
def eodhd_stub() -> Generator[_StubEODHDClient, None, None]:
    """Patches EODHDClient so get_exchanges returns SAMPLE_EXCHANGES, no HTTP."""
    stub = _StubEODHDClient(SAMPLE_EXCHANGES)
    with patch(
        "portfolio_management.cli.get_exchanges.EODHDClient", return_value=stub
    ):
        yield stub


##
## TESTS
##


class TestGetExchanges:
    def test_upserts_fetched_exchanges_into_repo(
        self, tmp_path: Path, eodhd_stub: _StubEODHDClient
    ) -> None:
        """get_exchanges persists every exchange fetched from EODHD via the repo."""
        engine, _ = make_db(tmp_path)
        repo = ExchangesRepository(engine=engine)

        get_exchanges(exchange_repo=repo)

        assert eodhd_stub.get_exchanges_calls == 1
        with Session(engine) as session:
            codes = {r.code for r in session.scalars(select(ExchangesORM)).all()}
        assert codes == {e.code for e in SAMPLE_EXCHANGES}


class TestMainCommand:
    def test_persists_exchanges_to_database(
        self,
        runner: CliRunner,
        db: tuple[Engine, str],
        eodhd_stub: _StubEODHDClient,
    ) -> None:
        """Running the command stores every fetched exchange in the database."""
        engine, _ = db

        result = runner.invoke(app, [])

        assert result.exit_code == 0
        assert eodhd_stub.get_exchanges_calls == 1
        with Session(engine) as session:
            codes = {r.code for r in session.scalars(select(ExchangesORM)).all()}
        assert codes == {e.code for e in SAMPLE_EXCHANGES}

    def test_uri_is_resolved_from_settings(
        self,
        runner: CliRunner,
        db: tuple[Engine, str],
        eodhd_stub: _StubEODHDClient,
    ) -> None:
        """Without --dry-run the command reads its URI from DatabaseSettings."""
        _, uri = db
        with patch(
            "portfolio_management.cli.get_exchanges.DatabaseSettings"
        ) as mock_settings:
            mock_settings.return_value.DB_URI = uri  # pyright: ignore[reportAny]
            result = runner.invoke(app, [])

        assert result.exit_code == 0
        assert eodhd_stub.get_exchanges_calls == 1
        mock_settings.assert_called_once()

    @pytest.mark.parametrize("flag", ["--dry-run", "-d"])
    def test_dry_run_does_not_touch_configured_database(
        self,
        flag: str,
        runner: CliRunner,
        db: tuple[Engine, str],
        eodhd_stub: _StubEODHDClient,
    ) -> None:
        """--dry-run uses an in-memory DB and never persists to the configured one."""
        engine, _ = db

        result = runner.invoke(app, [flag])

        assert result.exit_code == 0
        assert eodhd_stub.get_exchanges_calls == 1
        with Session(engine) as session:
            rows = session.scalars(select(ExchangesORM)).all()
        assert rows == []

    def test_dry_run_ignores_settings(
        self, runner: CliRunner, eodhd_stub: _StubEODHDClient
    ) -> None:
        """--dry-run never resolves the DB URI from DatabaseSettings."""
        with patch(
            "portfolio_management.cli.get_exchanges.DatabaseSettings"
        ) as mock_settings:
            result = runner.invoke(app, ["--dry-run"])

        assert result.exit_code == 0
        assert eodhd_stub.get_exchanges_calls == 1
        mock_settings.assert_not_called()
