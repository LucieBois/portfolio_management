from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session
from typer.testing import CliRunner

from portfolio_management.cli.seed_db import app, seed
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
            assert row.distributive == asset.distributive

    def test_idempotent_second_run_skips_existing(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """Running seed_db twice does not duplicate rows and exits cleanly."""
        engine, uri = db

        _ = runner.invoke(app, ["--db-uri", uri])  # first run
        result = runner.invoke(app, ["--db-uri", uri])  # second run

        assert result.exit_code == 0

        with Session(engine) as session:
            count = len(session.scalars(select(AssetsORM)).all())
        assert count == len(BASE_ASSETS)

    def test_partial_seed_only_inserts_missing_assets(
        self, runner: CliRunner, db: tuple[Engine, str]
    ):
        """If one asset already exists, all assets are still correctly seeded."""
        engine, uri = db

        pre_existing = BASE_ASSETS[0]
        with Session(engine) as session:
            session.add(
                AssetsORM(
                    name=pre_existing.name,
                    isin=pre_existing.isin,
                    esg=pre_existing.esg,
                    defense=pre_existing.defense,
                    oil=pre_existing.oil,
                    distributive=pre_existing.distributive,
                )
            )
            session.commit()

        result = runner.invoke(app, ["--db-uri", uri])

        assert result.exit_code == 0
        assert (
            f"Successfully seeded {len(BASE_ASSETS)} new base assets" in result.output
        )

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


def test_seed_upserts_existing_asset(tmp_path: Path):
    """An asset already in the DB is updated when BASE_ASSETS changes."""
    engine, _ = make_db(tmp_path)

    # Pre-seed with a stale version of the first asset
    stale = BASE_ASSETS[0]
    with Session(engine) as session:
        session.add(
            AssetsORM(
                name="Stale Name",
                isin=stale.isin,
                esg=not stale.esg,
                defense=0.99,
                oil=0.99,
                distributive=not stale.distributive,
            )
        )
        session.commit()

    # Run seed — should upsert and correct the stale values
    with Session(engine) as session:
        _ = seed(session)

    with Session(engine) as session:
        row = session.scalars(
            select(AssetsORM).where(AssetsORM.isin == stale.isin)
        ).one()

    assert row.name == stale.name
    assert row.esg == stale.esg
    assert row.defense == stale.defense
    assert row.oil == stale.oil
    assert row.distributive == stale.distributive
