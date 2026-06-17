import logging
from typing import Annotated

import typer
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from portfolio_management.core import BASE_ASSETS
from portfolio_management.database import AssetsORM, Base, get_engine

logger = logging.getLogger(__name__)

app = typer.Typer(help="Seed the database with basic assets")


def seed(session: Session) -> int:
    """Seed the database with base assets. Returns the number of newly inserted assets."""
    seeded_count = 0

    for asset in BASE_ASSETS:
        stmt = (
            sqlite_insert(AssetsORM)
            .values(
                name=asset.name,
                isin=asset.isin,
                esg=asset.esg,
                defense=asset.defense,
                oil=asset.oil,
            )
            .on_conflict_do_update(
                index_elements=[AssetsORM.isin],
                set_=dict(
                    name=asset.name,
                    esg=asset.esg,
                    defense=asset.defense,
                    oil=asset.oil,
                ),
            )
        )
        result = session.execute(stmt)
        assert isinstance(result, CursorResult)
        if result.rowcount == 1:
            seeded_count += 1

    session.commit()
    return seeded_count


@app.command()
def seed_db(db_uri: Annotated[str, typer.Option(help="Database URI to connect to")]):
    """Seed the database with base assets."""
    typer.echo(f"Connecting to database at {db_uri}...")
    engine = get_engine(db_uri)

    typer.echo("Creating database tables if they do not exist...")
    Base.metadata.create_all(engine)

    try:
        with Session(engine) as session:
            seeded_count = seed(session)
    except IntegrityError as e:
        logger.error(f"IntegrityError occurred: {e}")
        typer.secho(
            "Failed to seed the database due to an integrity error.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(code=1)

    if seeded_count > 0:
        typer.secho(
            f"Successfully seeded {seeded_count} new base assets!",
            fg=typer.colors.GREEN,
        )
    else:
        typer.secho("Database is already fully seeded.", fg=typer.colors.YELLOW)
