from planner.models import RawMessage, EventAction
from planner.intelligence.extract import parse_events

MSG = RawMessage(
    id="s1", source="sample", source_ref="t", sender="t",
    timestamp="2026-10-27T10:00:00+05:30",
    text="please submit Assignment 2 on normalization on the college portal by 2 November, 11:59 PM.",
)

GOOD = '''{"events":[{"action":"create","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-02T23:59:00+05:30","deadline_text":"by 2 November, 11:59 PM","evidence":"please submit Assignment 2 on normalization"}]}'''


def test_parses_one_event():
    events = parse_events(GOOD, MSG)
    assert len(events) == 1
    assert events[0].action == EventAction.CREATE
    assert events[0].title == "DBMS Assignment 2"
    assert events[0].source_message_id == "s1"


def test_empty_events():
    assert parse_events('{"events": []}', MSG) == []