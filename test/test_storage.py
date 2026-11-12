import sqlite3
from planner.models import RawMessage
from planner.storage import init_db, save_message, get_message, count_messages

MSG = RawMessage(
    id="s1", source="gmail", source_ref="sample-email-1", sender="prof@college.edu",
    timestamp="2026-10-27T10:00:00+05:30",
    subject="DBMS Assignment 2",
    text="Please submit Assignment 2 by 2 November. Prof's notes attached.",
)


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def test_new_message_is_saved():
    conn = make_db()
    assert save_message(conn, MSG) is True
    assert count_messages(conn) == 1


def test_saving_same_message_twice_is_ignored():
    conn = make_db()
    save_message(conn, MSG)
    assert save_message(conn, MSG) is False
    assert count_messages(conn) == 1


def test_message_round_trips_unchanged():
    conn = make_db()
    save_message(conn, MSG)
    assert get_message(conn, "s1") == MSG


def test_missing_message_returns_none():
    assert get_message(make_db(), "nope") is None


def test_init_db_twice_is_safe():
    conn = make_db()
    init_db(conn)
    save_message(conn, MSG)
    init_db(conn)
    assert count_messages(conn) == 1