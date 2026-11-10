import json
import sqlite3
from planner.models import RawMessage, Task

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
TASKS_SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT,
    task_type TEXT NOT NULL,
    deadline TEXT,
    deadline_text TEXT,
    status TEXT NOT NULL,
    estimated_effort_hours REAL NOT NULL,
    source_message_ids TEXT NOT NULL
)
"""

TASK_COLUMNS = (
    "id, title, subject, task_type, deadline, deadline_text, "
    "status, estimated_effort_hours, source_message_ids"
)


def connect(path: str = "planner.db") -> sqlite3.Connection:
    return sqlite3.connect(path)


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(SCHEMA)
    conn.execute(TASKS_SCHEMA)
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

def _task_values(task: Task) -> tuple:
    return (
        task.title,
        task.subject,
        task.task_type.value,
        task.deadline.isoformat() if task.deadline else None,
        task.deadline_text,
        task.status.value,
        task.estimated_effort_hours,
        json.dumps(task.source_message_ids),
    )


def _row_to_task(row) -> Task:
    return Task(
        id=row[0],
        title=row[1],
        subject=row[2],
        task_type=row[3],
        deadline=row[4],
        deadline_text=row[5],
        status=row[6],
        estimated_effort_hours=row[7],
        source_message_ids=json.loads(row[8]),
    )


def add_task(conn: sqlite3.Connection, task: Task) -> Task:
    cursor = conn.execute(
        "INSERT INTO tasks (title, subject, task_type, deadline, deadline_text, "
        "status, estimated_effort_hours, source_message_ids) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        _task_values(task),
    )
    conn.commit()
    return task.model_copy(update={"id": cursor.lastrowid})


def get_task(conn: sqlite3.Connection, task_id: int) -> Task | None:
    row = conn.execute(
        f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = ?", (task_id,)
    ).fetchone()
    return None if row is None else _row_to_task(row)


def list_tasks(conn: sqlite3.Connection) -> list[Task]:
    rows = conn.execute(f"SELECT {TASK_COLUMNS} FROM tasks ORDER BY id").fetchall()
    return [_row_to_task(row) for row in rows]


def update_task(conn: sqlite3.Connection, task: Task) -> None:
    conn.execute(
        "UPDATE tasks SET title = ?, subject = ?, task_type = ?, deadline = ?, "
        "deadline_text = ?, status = ?, estimated_effort_hours = ?, "
        "source_message_ids = ? WHERE id = ?",
        _task_values(task) + (task.id,),
    )
    conn.commit()