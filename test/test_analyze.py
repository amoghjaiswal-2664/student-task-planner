import pytest
from planner.models import RawMessage
from planner.intelligence.analyze import analyze_message

MSG = RawMessage(
    id="s1", source="sample", source_ref="t", sender="t",
    timestamp="2026-10-27T10:00:00+05:30",
    text="Please submit Assignment 2 by 2 November, 11:59 PM.",
)

CHAT = RawMessage(
    id="s4", source="sample", source_ref="t", sender="t",
    timestamp="2026-10-27T10:00:00+05:30",
    text="good morning, canteen ka menu dekha?",
)

GOOD = '{"events":[{"action":"create","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-02T23:59:00+05:30","deadline_text":"by 2 November, 11:59 PM","evidence":"submit Assignment 2"}]}'
INVENTED = '{"events":[{"action":"create","title":"Report","evidence":"submit the report by Friday"}]}'
PAST_DEADLINE = '{"events":[{"action":"create","title":"DBMS Assignment 2","deadline":"2020-01-01T23:59:00+05:30","deadline_text":"by 2 November","evidence":"submit Assignment 2"}]}'


def make_llm(*replies):
    calls = []

    def fake(prompt, system=None):
        calls.append(prompt)
        return replies[min(len(calls) - 1, len(replies) - 1)]

    fake.calls = calls
    return fake


def test_irrelevant_message_skips_llm():
    llm = make_llm(GOOD)
    assert analyze_message(CHAT, llm=llm) == []
    assert llm.calls == []


def test_good_output_gives_one_event():
    events = analyze_message(MSG, llm=make_llm(GOOD))
    assert len(events) == 1
    assert events[0].title == "DBMS Assignment 2"


def test_invented_evidence_is_dropped():
    assert analyze_message(MSG, llm=make_llm(INVENTED)) == []


def test_impossible_deadline_is_cleared_but_event_kept():
    events = analyze_message(MSG, llm=make_llm(PAST_DEADLINE))
    assert len(events) == 1
    assert events[0].deadline is None
    assert events[0].deadline_text is None


def test_retries_once_after_bad_output():
    llm = make_llm("sorry, no", GOOD)
    assert len(analyze_message(MSG, llm=llm)) == 1
    assert len(llm.calls) == 2


def test_fails_loudly_after_two_bad_outputs():
    with pytest.raises(ValueError):
        analyze_message(MSG, llm=make_llm("nope", "still nope"))