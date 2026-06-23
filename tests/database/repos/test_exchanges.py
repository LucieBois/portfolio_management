from pathlib import Path

import pytest

from portfolio_management.database import Base, get_engine
from portfolio_management.database.repos.exchanges import ExchangesRepository
from portfolio_management.models import ExchangeModel

##
## HELPERS
##


def make_exchange(
    code: str = "NYSE", name: str = "New York Stock Exchange"
) -> ExchangeModel:
    """Build an ExchangeModel with sensible defaults, overridable per field."""
    return ExchangeModel(
        name=name,
        code=code,
        operating_mic=f"MIC-{code}",
        country="united states",
        currency="usd",
        country_iso2="us",
        country_iso3="usa",
    )


##
## FIXTURES
##


@pytest.fixture()
def repo(tmp_path: Path) -> ExchangesRepository:
    """A repository backed by a fresh, empty SQLite database per test."""
    uri = f"sqlite:///{tmp_path / 'test_exchanges.db'}"
    Base.metadata.create_all(get_engine(uri))
    return ExchangesRepository(uri)


##
## TESTS
##


def test_get_all_exchanges_empty(repo: ExchangesRepository):
    """An empty database returns an empty list."""
    assert repo.get_all_exchanges() == []


def test_upsert_then_get_all_exchanges(repo: ExchangesRepository):
    """Upserted exchanges are read back with all fields preserved."""
    exchange = make_exchange()

    repo.upsert_exchanges([exchange])
    result = repo.get_all_exchanges()

    assert result == [exchange]


def test_upsert_updates_existing_exchange(repo: ExchangesRepository):
    """Upserting an exchange with an existing code updates it instead of duplicating."""
    repo.upsert_exchanges([make_exchange(name="Old Name")])
    repo.upsert_exchanges([make_exchange(name="New Name")])

    result = repo.get_all_exchanges()

    assert len(result) == 1
    assert result[0].name == "new name"
