import sqlite3
from planner.models import Decision, Task, TaskEvent
from planner.storage import (
    init_db, add_task, get_task, add_review_item, list_review_items,
)
from planner.review import review_label, apply_review_item, dismiss_review_item

DL1 = "2026-11-04T22:00:00+05:30"
DL2 = "2026-11-06T23:00:00+05:30"


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def flagged(conn, task_id=None):
    event = TaskEvent(
        action="create", title="CS3013 Course Proficiency Test-2", subject="CS3013",
        task_type="exam", deadline=DL2, deadline_text="ends 6 November 11 PM",
        source_message_id="m9", evidence="End Time 2026-11-06 23:00",
    )
    add_review_item(conn, Decision(
        action="needs_review", event=event, task_id=task_id,
        reason="task already has a different deadline",
    ))
    return list_review_items(conn)[0]


def existing_task(conn):
    return add_task(conn, Task(
        title="CS3013 Course Proficiency Test-2", subject="CS3013", task_type="exam",
        deadline=DL1, deadline_text="by 4 November", source_message_ids=["m1"],
    ))


def test_label_shows_reason_deadline_and_evidence():
    conn = make_db()
    task = existing_task(conn)
    text = "\n".join(review_label(flagged(conn, task.id), conn))
    assert "task already has a different deadline" in text
    assert "ends 6 November 11 PM" in text
    assert "End Time 2026-11-06 23:00" in text
    assert "CS3013 Course Proficiency Test-2" in text


def test_label_without_a_task_id_still_works():
    conn = make_db()
    assert len(review_label(flagged(conn), conn)) >= 3


def test_applying_updates_the_task_and_resolves_the_item():
    conn = make_db()
    task = existing_task(conn)
    item = flagged(conn, task.id)
    apply_review_item(conn, item, task.id)
    saved = get_task(conn, task.id)
    assert saved.deadline.isoformat() == DL2
    assert "m9" in saved.source_message_ids
    assert list_review_items(conn) == []


def test_dismissing_resolves_without_touching_the_task():
    conn = make_db()
    task = existing_task(conn)
    item = flagged(conn, task.id)
    dismiss_review_item(conn, item)
    assert get_task(conn, task.id).deadline.isoformat() == DL1
    assert list_review_items(conn) == []
    assert len(list_review_items(conn, status="resolved")) == 1