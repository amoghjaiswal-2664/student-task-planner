import sqlite3
from planner.models import Decision, Task, TaskEvent, TaskStatus
from planner.storage import init_db, add_task, get_task, list_tasks
from planner.apply import apply_decision

DL1 = "2026-11-02T23:59:00+05:30"
DL2 = "2026-11-04T23:59:00+05:30"


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def event(action, subject="DBMS", deadline=None, source="s1"):
    return TaskEvent(
        action=action, title="DBMS Assignment 2", subject=subject,
        task_type="assignment", deadline=deadline,
        deadline_text="x" if deadline else None,
        source_message_id=source, evidence="x",
    )


def decision(action, ev, task_id=None):
    return Decision(action=action, event=ev, task_id=task_id, reason="test")


def existing_task(conn, subject="DBMS", sources=("s1",)):
    return add_task(conn, Task(
        title="DBMS Assignment 2", subject=subject, task_type="assignment",
        deadline=DL1, deadline_text="by 2 November", source_message_ids=list(sources),
    ))


def test_create_adds_a_task():
    conn = make_db()
    saved = apply_decision(conn, decision("create", event("create", deadline=DL1)))
    assert saved.id == 1
    assert saved.source_message_ids == ["s1"]
    assert saved.deadline is not None
    assert len(list_tasks(conn)) == 1


def test_update_changes_deadline_and_records_source():
    conn = make_db()
    task = existing_task(conn)
    apply_decision(conn, decision("update", event("update", deadline=DL2, source="s5"), task.id))
    saved = get_task(conn, task.id)
    assert saved.deadline.isoformat() == DL2
    assert saved.source_message_ids == ["s1", "s5"]
    assert len(list_tasks(conn)) == 1


def test_update_without_deadline_keeps_existing_one():
    conn = make_db()
    task = existing_task(conn)
    apply_decision(conn, decision("update", event("update", source="s5"), task.id))
    saved = get_task(conn, task.id)
    assert saved.deadline.isoformat() == DL1
    assert saved.deadline_text == "by 2 November"


def test_update_fills_missing_subject_but_never_overwrites():
    conn = make_db()
    no_subject = existing_task(conn, subject=None)
    has_subject = existing_task(conn, subject="OS")
    apply_decision(conn, decision("update", event("update", subject="DBMS"), no_subject.id))
    apply_decision(conn, decision("update", event("update", subject="DBMS"), has_subject.id))
    assert get_task(conn, no_subject.id).subject == "DBMS"
    assert get_task(conn, has_subject.id).subject == "OS"


def test_cancel_sets_status():
    conn = make_db()
    task = existing_task(conn)
    apply_decision(conn, decision("cancel", event("cancel", source="s8"), task.id))
    saved = get_task(conn, task.id)
    assert saved.status == TaskStatus.CANCELLED
    assert "s8" in saved.source_message_ids


def test_duplicate_only_records_the_source():
    conn = make_db()
    task = existing_task(conn)
    apply_decision(conn, decision("duplicate", event("create", deadline=DL1, source="s7"), task.id))
    saved = get_task(conn, task.id)
    assert saved.source_message_ids == ["s1", "s7"]
    assert saved.status == TaskStatus.ACTIVE
    assert len(list_tasks(conn)) == 1


def test_same_source_is_never_added_twice():
    conn = make_db()
    task = existing_task(conn)
    dup = decision("duplicate", event("create", source="s7"), task.id)
    apply_decision(conn, dup)
    apply_decision(conn, dup)
    assert get_task(conn, task.id).source_message_ids == ["s1", "s7"]


def test_needs_review_changes_nothing():
    conn = make_db()
    task = existing_task(conn)
    result = apply_decision(conn, decision("needs_review", event("update", source="s9"), task.id))
    assert result is None
    assert get_task(conn, task.id) == task