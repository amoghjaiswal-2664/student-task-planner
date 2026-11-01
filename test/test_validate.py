from planner.models import RawMessage, TaskEvent
from planner.intelligence.validate import evidence_in_message
from datetime import timedelta

MSG = RawMessage(
    id="s1", source="sample", source_ref="t", sender="t",
    timestamp="2026-10-27T10:00:00+05:30",
    subject="DBMS Assignment 2",
    text="Please submit Assignment 2 on normalization by 2 November,   11:59 PM.",
)


def make_event(evidence):
    return TaskEvent(
        action="create", title="DBMS Assignment 2",
        source_message_id="s1", evidence=evidence,
    )


def test_real_quote_passes():
    assert evidence_in_message(make_event("submit Assignment 2 on normalization"), MSG) is True


def test_case_and_spacing_ignored():
    assert evidence_in_message(make_event("PLEASE submit assignment 2 on normalization by 2 November, 11:59 PM."), MSG) is True


def test_invented_quote_fails():
    assert evidence_in_message(make_event("submit the report by Friday"), MSG) is False


def test_quote_from_subject_passes():
    assert evidence_in_message(make_event("DBMS Assignment 2"), MSG) is True