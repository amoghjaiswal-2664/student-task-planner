from planner.models import RawMessage
from planner.intelligence.relevance import is_relevant


def make_msg(text, subject=None):
    return RawMessage(
        id="t",
        source="sample",
        source_ref="t",
        sender="t",
        timestamp="2026-10-30T10:00:00+05:30",
        text=text,
        subject=subject,
    )


def test_assignment_message_is_relevant():
    assert is_relevant(make_msg("Submit assignment 2 by Sunday")) is True


def test_chitchat_is_not_relevant():
    assert is_relevant(make_msg("good morning, canteen ka menu dekha?")) is False


def test_keyword_only_in_subject_is_relevant():
    msg = make_msg("please see attached", subject="Assignment 2 deadline")
    assert is_relevant(msg) is True


def test_hinglish_message_is_relevant():
    assert is_relevant(make_msg("lab file kal tak jama kar dena")) is True