import sqlite3
from planner.models import RawMessage, DecisionAction, TaskStatus
from planner.storage import init_db, list_tasks, count_messages
from planner.sync import sync_messages


def make_db():
    conn = sqlite3.connect(":memory:")
    init_db(conn)
    return conn


def msg(id, ts, text, subject=None, source="whatsapp"):
    return RawMessage(
        id=id, source=source, source_ref="t", sender="t",
        timestamp=ts, subject=subject, text=text,
    )


M1 = msg("m1", "2026-10-27T10:00:00+05:30",
         "Please submit Assignment 2 by 2 November, 11:59 PM.",
         subject="DBMS Assignment 2", source="gmail")
M6 = msg("m6", "2026-10-28T14:20:00+05:30",
         "Quiz 2 for Operating Systems will be on 5 November at 10:00 AM.",
         subject="OS Quiz 2", source="gmail")
M7 = msg("m7", "2026-10-28T16:45:00+05:30",
         "Forwarded: Please submit Assignment 2 by 2 November, 11:59 PM.")
M5 = msg("m5", "2026-10-30T09:30:00+05:30",
         "DBMS Assignment 2 ki deadline extend ho gayi hai, ab 4 November tak submit kar sakte ho")
M8 = msg("m8", "2026-10-30T10:15:00+05:30",
         "OS quiz jo 5 Nov ko thi wo cancel ho gayi hai")
CHAT = msg("m4", "2026-10-29T09:05:00+05:30",
           "good morning everyone, canteen ka naya menu dekha?")
BAD = msg("bad", "2026-10-29T10:00:00+05:30", "please submit the BROKEN thing")

R1 = '{"events":[{"action":"create","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-02T23:59:00+05:30","deadline_text":"by 2 November, 11:59 PM","evidence":"submit Assignment 2"}]}'
R5 = '{"events":[{"action":"update","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-04T23:59:00+05:30","deadline_text":"4 November tak","evidence":"ab 4 November tak submit kar sakte ho"}]}'
R6 = '{"events":[{"action":"create","title":"OS Quiz 2","subject":"OS","task_type":"quiz","deadline":"2026-11-05T10:00:00+05:30","deadline_text":"5 November at 10:00 AM","evidence":"Quiz 2 for Operating Systems"}]}'
R7 = '{"events":[{"action":"create","title":"Assignment 2","subject":null,"task_type":"assignment","deadline":"2026-11-02T23:59:00+05:30","deadline_text":"by 2 November, 11:59 PM","evidence":"submit Assignment 2"}]}'
R8 = '{"events":[{"action":"cancel","title":"OS Quiz","subject":"OS","task_type":"quiz","deadline":null,"deadline_text":null,"evidence":"wo cancel ho gayi hai"}]}'

REPLIES = [
    ("Forwarded", R7),
    ("ab 4 November", R5),
    ("Please submit Assignment 2", R1),
    ("Operating Systems", R6),
    ("cancel ho gayi", R8),
]


def make_llm():
    calls = []

    def fake(prompt, system=None):
        calls.append(prompt)
        for key, reply in REPLIES:
            if key in prompt:
                return reply
        return "no json here"

    fake.calls = calls
    return fake


def test_create_flow():
    conn = make_db()
    summary = sync_messages(conn, [M1], llm=make_llm())
    tasks = list_tasks(conn)
    assert len(tasks) == 1
    assert tasks[0].deadline.isoformat() == "2026-11-02T23:59:00+05:30"
    assert summary.messages_processed == 1


def test_update_applies_even_when_messages_arrive_out_of_order():
    conn = make_db()
    sync_messages(conn, [M5, M1], llm=make_llm())
    tasks = list_tasks(conn)
    assert len(tasks) == 1
    assert tasks[0].deadline.isoformat() == "2026-11-04T23:59:00+05:30"
    assert tasks[0].source_message_ids == ["m1", "m5"]


def test_forward_is_recorded_as_duplicate():
    conn = make_db()
    summary = sync_messages(conn, [M1, M7], llm=make_llm())
    assert len(list_tasks(conn)) == 1
    assert list_tasks(conn)[0].source_message_ids == ["m1", "m7"]
    assert [d.action for d in summary.decisions] == [DecisionAction.CREATE, DecisionAction.DUPLICATE]


def test_cancellation_flow():
    conn = make_db()
    sync_messages(conn, [M6, M8], llm=make_llm())
    assert list_tasks(conn)[0].status == TaskStatus.CANCELLED


def test_running_sync_twice_does_nothing_the_second_time():
    conn = make_db()
    llm = make_llm()
    sync_messages(conn, [M1], llm=llm)
    summary = sync_messages(conn, [M1], llm=llm)
    assert summary.messages_seen == 1
    assert summary.messages_processed == 0
    assert len(llm.calls) == 1
    assert len(list_tasks(conn)) == 1


def test_irrelevant_message_is_saved_but_creates_nothing():
    conn = make_db()
    llm = make_llm()
    sync_messages(conn, [CHAT], llm=llm)
    assert count_messages(conn) == 1
    assert list_tasks(conn) == []
    assert llm.calls == []


def test_failed_message_is_reported_and_not_marked_seen():
    conn = make_db()
    summary = sync_messages(conn, [BAD, M1], llm=make_llm())
    assert summary.failed == ["bad"]
    assert count_messages(conn) == 1
    assert len(list_tasks(conn)) == 1


def test_update_with_no_matching_task_needs_review():
    conn = make_db()
    summary = sync_messages(conn, [M5], llm=make_llm())
    assert summary.decisions[0].action == DecisionAction.NEEDS_REVIEW
    assert list_tasks(conn) == []