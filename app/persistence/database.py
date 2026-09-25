from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import sqlite3

from app.integrity.hashing import (
    GENESIS_HASH,
    calculate_record_hash,
    calculate_sha256,
    canonicalize_record,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "audit.db"


CREATE_AUDIT_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS audit_events (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    record_hash TEXT NOT NULL,
    archived INTEGER NOT NULL DEFAULT 0,
    archived_at TEXT
);
"""


def get_connection(database_path=None) -> sqlite3.Connection:
    if database_path is None:
        database_path = DATABASE_PATH

    database_path = Path(database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        database_path,
        timeout=10,
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys = ON;")
    connection.execute("PRAGMA busy_timeout = 10000;")

    return connection


def _ensure_schema(connection: sqlite3.Connection) -> None:
    columns = connection.execute(
        "PRAGMA table_info(audit_events)"
    ).fetchall()

    column_names = {column["name"] for column in columns}

    if "archived" not in column_names:
        connection.execute(
            """
            ALTER TABLE audit_events
            ADD COLUMN archived INTEGER NOT NULL DEFAULT 0
            """
        )

    if "archived_at" not in column_names:
        connection.execute(
            """
            ALTER TABLE audit_events
            ADD COLUMN archived_at TEXT
            """
        )


def initialize_database(database_path=None) -> None:
    if database_path is None:
        database_path = DATABASE_PATH

    with get_connection(database_path) as connection:
        connection.execute(CREATE_AUDIT_EVENTS_TABLE)
        _ensure_schema(connection)


def get_audit_events(database_path=None):
    if database_path is None:
        database_path = DATABASE_PATH

    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT
                record_id,
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash,
                record_hash,
                archived,
                archived_at
            FROM audit_events
            ORDER BY record_id ASC
            """
        ).fetchall()

    records = []

    for row in rows:
        record = dict(row)
        record["payload"] = json.loads(record["payload"])
        record["archived"] = bool(record["archived"])
        records.append(record)

    return records


def create_audit_event(
    event_type: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    payload: dict,
    database_path=None,
):
    timestamp = datetime.now(timezone.utc).isoformat()

    with transaction(database_path) as connection:
        previous_record = connection.execute(
            """
            SELECT record_hash
            FROM audit_events
            ORDER BY record_id DESC
            LIMIT 1
            """
        ).fetchone()

        previous_hash = (
            previous_record["record_hash"]
            if previous_record is not None
            else GENESIS_HASH
        )

        canonical_record = canonicalize_record(
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            timestamp=timestamp,
        )

        content_hash = calculate_sha256(canonical_record)

        record_hash = calculate_record_hash(
            previous_hash=previous_hash,
            canonical_record=canonical_record,
        )

        cursor = connection.execute(
            """
            INSERT INTO audit_events (
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash,
                record_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_type,
                actor_id,
                resource_type,
                resource_id,
                json.dumps(
                    payload,
                    sort_keys=True,
                    separators=(",", ":"),
                    ensure_ascii=False,
                ),
                timestamp,
                content_hash,
                previous_hash,
                record_hash,
            ),
        )

        record_id = cursor.lastrowid

    return {
        "record_id": record_id,
        "event_type": event_type,
        "actor_id": actor_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": payload,
        "timestamp": timestamp,
        "content_hash": content_hash,
        "previous_hash": previous_hash,
        "record_hash": record_hash,
        "archived": False,
        "archived_at": None,
    }


def archive_audit_event(
    record_id: int,
    database_path=None,
):
    if database_path is None:
        database_path = DATABASE_PATH

    archived_at = datetime.now(timezone.utc).isoformat()

    with transaction(database_path) as connection:
        cursor = connection.execute(
            """
            UPDATE audit_events
            SET archived = 1,
                archived_at = ?
            WHERE record_id = ?
            """,
            (archived_at, record_id),
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            """
            SELECT
                record_id,
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash,
                record_hash,
                archived,
                archived_at
            FROM audit_events
            WHERE record_id = ?
            """,
            (record_id,),
        ).fetchone()

    record = dict(row)
    record["payload"] = json.loads(record["payload"])
    record["archived"] = bool(record["archived"])

    return record


@contextmanager
def transaction(database_path=None):
    if database_path is None:
        database_path = DATABASE_PATH

    connection = get_connection(database_path)

    try:
        connection.execute("BEGIN IMMEDIATE")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()