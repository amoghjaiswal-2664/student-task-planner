import sqlite3
from planner.models import Task, TaskStatus
from planner.storage import init_db, add_task, get_task, list_tasks, update_task


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def make_task():
    return Task(
        title="DBMS Assignment 2",
        subject="DBMS",
        task_type="assignment",
        deadline="2026-11-02T23:59:00+05:30",
        deadline_text="by 2 November",
        source_message_ids=["s1", "s7"],
    )


def test_add_task_assigns_an_id():
    saved = add_task(make_db(), make_task())
    assert saved.id == 1


def test_task_round_trips_unchanged():
    conn = make_db()
    saved = add_task(conn, make_task())
    assert get_task(conn, saved.id) == saved


def test_missing_task_returns_none():
    assert get_task(make_db(), 99) is None


def test_task_without_deadline_round_trips():
    conn = make_db()
    saved = add_task(conn, Task(title="CN Assignment"))
    assert get_task(conn, saved.id).deadline is None


def test_list_tasks_in_order():
    conn = make_db()
    add_task(conn, Task(title="first"))
    add_task(conn, Task(title="second"))
    assert [t.title for t in list_tasks(conn)] == ["first", "second"]


def test_update_task_persists_changes():
    conn = make_db()
    saved = add_task(conn, make_task())
    changed = saved.model_copy(update={"status": TaskStatus.COMPLETED})
    update_task(conn, changed)
    assert get_task(conn, saved.id).status == TaskStatus.COMPLETED
    assert len(list_tasks(conn)) == 1