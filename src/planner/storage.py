import sqlite3
from planner.models import RawMessage

SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_ref TEXT NOT NULL,
    sender TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    subject TEXT,
    text TEXT NOT NULL
)
"""


def connect(path: str = "planner.db") -> sqlite3.Connection:
    return sqlite3.connect(path)


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA)
    conn.commit()


def save_message(conn: sqlite3.Connection, msg: RawMessage) -> bool:
    cursor = conn.execute(
        "INSERT OR IGNORE INTO messages "
        "(id, source, source_ref, sender, timestamp, subject, text) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            msg.id,
            msg.source.value,
            msg.source_ref,
            msg.sender,
            msg.timestamp.isoformat(),
            msg.subject,
            msg.text,
        ),
    )
    conn.commit()
    return cursor.rowcount == 1


def get_message(conn: sqlite3.Connection, message_id: str) -> RawMessage | None:
    row = conn.execute(
        "SELECT id, source, source_ref, sender, timestamp, subject, text "
        "FROM messages WHERE id = ?",
        (message_id,),
    ).fetchone()
    if row is None:
        return None
    return RawMessage(
        id=row[0],
        source=row[1],
        source_ref=row[2],
        sender=row[3],
        timestamp=row[4],
        subject=row[5],
        text=row[6],
    )


def count_messages(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]