from pathlib import Path

import pytest
from sqlalchemy import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from portfolio_management.database import get_engine


@pytest.fixture(scope="module")
def create_engine() -> Engine:
    return get_engine("sqlite:///:memory:")


def test_engine_creation(create_engine: Engine):

    assert isinstance(create_engine, Engine)


def test_foreign_keys_enabled(create_engine: Engine):
    """Test that foreign keys are enabled by default in the SQLite engine."""

    # Engine creation should have triggered the PRAGMA statement to enable foreign keys
    with Session(create_engine) as session:
        _ = session.execute(text("CREATE TABLE parent (id INTEGER PRIMARY KEY);"))
        _ = session.execute(
            text(
                "CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER, FOREIGN KEY(parent_id) REFERENCES parent(id));"
            )
        )
        _ = session.execute(text("INSERT INTO parent (id) VALUES (1);"))
        _ = session.execute(text("INSERT INTO child (id, parent_id) VALUES (1, 1);"))

        # Attempting to insert a child with a non-existent parent should fail
        with pytest.raises(IntegrityError):
            _ = session.execute(
                text("INSERT INTO child (id, parent_id) VALUES (2, 999);")
            )


def test_journal_mode_wal(tmp_path: Path):
    """Test that the journal mode is set by default to WAL in the SQLite engine."""

    # Create a temporary file-backed database to test WAL
    db_path = tmp_path / "test.db"
    file_engine = get_engine(f"sqlite:///{db_path}")

    with Session(file_engine) as session:
        result = session.execute(text("PRAGMA journal_mode;"))
        journal_mode = result.scalar()
        assert journal_mode == "wal", (
            f"Expected journal mode to be 'wal', but got '{journal_mode}'"
        )
