from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path


SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def get_connection(database_path: Path | str) -> sqlite3.Connection:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize_database(database_path: Path | str) -> None:
    with closing(get_connection(database_path)) as connection:
        with connection:
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
