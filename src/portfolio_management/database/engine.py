import logging
import sqlite3
from functools import lru_cache

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.pool import ConnectionPoolEntry

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_engine(db_uri: str, echo: bool = False) -> Engine:
    """Returns a SQLAlchemy engine"""
    # Log
    logger.info(f"Creating engine for database {db_uri}")

    # Create engine
    engine = create_engine(
        url=db_uri,
        echo=echo,
        connect_args={"check_same_thread": False},
    )

    def sqlite_pragma(
        dbapi_connection: sqlite3.Connection, _connection_record: ConnectionPoolEntry
    ) -> None:
        cursor = dbapi_connection.cursor()

        try:
            _ = cursor.execute("PRAGMA foreign_keys=ON;")
            _ = cursor.execute("PRAGMA journal_mode=WAL;")
            _ = cursor.execute("PRAGMA synchronous=NORMAL;")
        finally:
            cursor.close()

    event.listen(engine, "connect", sqlite_pragma)

    return engine
