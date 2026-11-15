import sqlite3
from planner.models import Decision, RawMessage, TaskEvent
from planner.storage import init_db, add_review_item, list_review_items, resolve_review_item
from planner.sync import sync_messages

R5 = '{"events":[{"action":"update","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-04T23:59:00+05:30","deadline_text":"4 November tak","evidence":"ab 4 November tak submit kar sakte ho"}]}'
M5 = RawMessage(
    id="m5", source="whatsapp", source_ref="t", sender="t",
    timestamp="2026-10-30T09:30:00+05:30",
    text="DBMS Assignment 2 ki deadline extend ho gayi hai, ab 4 November tak submit kar sakte ho",
)


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def decision(title="DBMS Assignment 2", source="s5"):
    event = TaskEvent(action="update", title=title, source_message_id=source, evidence="x")
    return Decision(action="needs_review", event=event, reason="no existing task matches")


def test_added_item_is_listed_as_pending():
    conn = make_db()
    assert add_review_item(conn, decision()) is True
    items = list_review_items(conn)
    assert len(items) == 1
    assert items[0].status == "pending"


def test_decision_round_trips_unchanged():
    conn = make_db()
    d = decision()
    add_review_item(conn, d)
    assert list_review_items(conn)[0].decision == d


def test_same_decision_is_stored_once():
    conn = make_db()
    add_review_item(conn, decision())
    assert add_review_item(conn, decision()) is False
    assert len(list_review_items(conn)) == 1


def test_different_decisions_are_both_stored():
    conn = make_db()
    add_review_item(conn, decision("A", "s1"))
    add_review_item(conn, decision("B", "s2"))
    assert len(list_review_items(conn)) == 2


def test_resolved_items_leave_the_pending_list():
    conn = make_db()
    add_review_item(conn, decision())
    resolve_review_item(conn, list_review_items(conn)[0].id)
    assert list_review_items(conn) == []
    assert len(list_review_items(conn, status="resolved")) == 1


def test_sync_stores_needs_review_decisions():
    conn = make_db()
    sync_messages(conn, [M5], llm=lambda prompt, system=None: R5)
    items = list_review_items(conn)
    assert len(items) == 1
    assert items[0].decision.event.source_message_id == "m5"