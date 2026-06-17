from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from portfolio_management.cli.seed_db import app
from portfolio_management.core import BASE_ASSETS
from portfolio_management.database import AssetsORM, Base, get_engine

##
## HELPERS
##


def make_db(tmp_path: Path):
    """Return a fresh in-process SQLite engine and its URI (no lru_cache clash)."""
    db_path = tmp_path / "test_seed.db"
    uri = f"sqlite:///{db_path}"
    engine = get_engine(uri)
    Base.metadata.create_all(engine)
    return engine, uri


##
## FIXTURES
##


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def db(tmp_path: Path):
    """Yields (engine, uri) for a fresh, empty database per test."""
    engine, uri = make_db(tmp_path)
    yield engine, uri


##
## TESTS
##


class TestSeedDbCommand:
    def test_seeds_all_base_assets_on_empty_db(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """Running seed_db on an empty database inserts all BASE_ASSETS."""
        engine, uri = db

        result = runner.invoke(app, ["--db-uri", uri])

        assert result.exit_code == 0
        assert (
            f"Successfully seeded {len(BASE_ASSETS)} new base assets" in result.output
        )

        with Session(engine) as session:
            rows = session.scalars(select(AssetsORM)).all()

        assert len(rows) == len(BASE_ASSETS)

    def test_seeded_assets_match_base_assets(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """Every BASE_ASSETS entry is correctly persisted (isin, name, esg, defense, oil)."""
        engine, uri = db
        _ = runner.invoke(app, ["--db-uri", uri])

        with Session(engine) as session:
            rows = {r.isin: r for r in session.scalars(select(AssetsORM)).all()}

        for asset in BASE_ASSETS:
            assert asset.isin in rows, f"ISIN {asset.isin} not found in DB"
            row = rows[asset.isin]
            assert row.name == asset.name
            assert row.esg == asset.esg
            assert row.defense == pytest.approx(asset.defense)  # pyright: ignore[reportUnknownMemberType]
            assert row.oil == pytest.approx(asset.oil)  # pyright: ignore[reportUnknownMemberType]

    def test_idempotent_second_run_skips_existing(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """Running seed_db twice does not duplicate rows and exits cleanly."""
        engine, uri = db

        _ = runner.invoke(app, ["--db-uri", uri])  # first run
        result = runner.invoke(app, ["--db-uri", uri])  # second run

        assert result.exit_code == 0
        assert "already fully seeded" in result.output

        with Session(engine) as session:
            count = len(session.scalars(select(AssetsORM)).all())

        assert count == len(BASE_ASSETS)

    def test_partial_seed_only_inserts_missing_assets(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """If one asset already exists, only the remaining ones are inserted."""
        engine, uri = db

        # Pre-seed only the first asset directly
        pre_existing = BASE_ASSETS[0]
        with Session(engine) as session:
            session.add(
                AssetsORM(
                    name=pre_existing.name,
                    isin=pre_existing.isin,
                    esg=pre_existing.esg,
                    defense=pre_existing.defense,
                    oil=pre_existing.oil,
                )
            )
            session.commit()

        result = runner.invoke(app, ["--db-uri", uri])

        assert result.exit_code == 0
        expected_count = len(BASE_ASSETS) - 1
        assert f"Successfully seeded {expected_count} new base assets" in result.output

        with Session(engine) as session:
            count = len(session.scalars(select(AssetsORM)).all())
        assert count == len(BASE_ASSETS)

    def test_output_mentions_db_uri(self, runner: CliRunner, db: tuple[Engine, str]):
        """The CLI echoes the DB URI it is connecting to."""
        _, uri = db
        result = runner.invoke(app, ["--db-uri", uri])
        assert uri in result.output

    def test_missing_db_uri_option_fails(self, runner: CliRunner):
        """Invoking without --db-uri should exit with a non-zero code."""
        result = runner.invoke(app, [])
        assert result.exit_code != 0
