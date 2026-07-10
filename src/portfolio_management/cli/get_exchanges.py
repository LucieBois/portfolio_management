import logging
from typing import Annotated

import typer
from sqlalchemy import Engine
from typer import Option

from portfolio_management.clients.eodhd import EODHDClient
from portfolio_management.core.settings import DatabaseSettings
from portfolio_management.database import Base, get_engine
from portfolio_management.database.repos import ExchangesRepository
from portfolio_management.models import ExchangeModel

logger = logging.getLogger(__name__)

app = typer.Typer(help="Query all possible exchanges from EODHD")


def get_exchanges(exchange_repo: ExchangesRepository) -> None:
    """Fetch all exchanges from EODHD and store them in the database"""

    # Get exchanges from EODHD
    exchanges: list[ExchangeModel] = EODHDClient().get_exchanges()

    logger.info(f"Fetched {len(exchanges)} exchanges from EODHD")

    # Store exchanges in the database
    exchange_repo.upsert_exchanges(exchanges)


@app.command()
# Add dry-run option to the command
def main(
    dry_run: Annotated[
        bool,
        Option(
            "--dry-run",
            "-d",
            help="If set, will not store exchanges in the database",
        ),
    ] = False,
) -> None:
    """Fetch all exchanges from EODHD and store them in the database"""

    # Get the appropriate database URI
    if dry_run:
        logger.info(
            "Dry run mode enabled. Exchanges will not be stored in the database."
        )
        db_uri = "sqlite:///:memory:"
    else:
        db_uri = DatabaseSettings().DB_URI

    # Create the database engine
    engine: Engine = get_engine(db_uri)

    # Create the tables if they don't exist
    Base.metadata.create_all(engine)

    # Create the repository
    exchange_repo: ExchangesRepository = ExchangesRepository(engine=engine)

    # Fetch and store exchanges
    get_exchanges(exchange_repo=exchange_repo)
