from planner.models import RawMessage, TaskEvent
from planner.intelligence.validate import deadline_is_sane

MSG = RawMessage(
    id="s1", source="sample", source_ref="t", sender="t",
    timestamp="2026-10-27T10:00:00+05:30",
    text="Submit by 2 November",
)


def make_event(deadline=None, deadline_text=None):
    return TaskEvent(
        action="create", title="x", source_message_id="s1", evidence="x",
        deadline=deadline, deadline_text=deadline_text,
    )


def test_no_deadline_is_fine():
    assert deadline_is_sane(make_event(), MSG) is True


def test_deadline_a_week_later_is_fine():
    event = make_event("2026-11-03T23:59:00+05:30", "by 3 November")
    assert deadline_is_sane(event, MSG) is True


def test_deadline_before_message_is_rejected():
    event = make_event("2026-10-20T23:59:00+05:30", "by 20 October")
    assert deadline_is_sane(event, MSG) is False


def test_deadline_years_away_is_rejected():
    event = make_event("2029-11-03T23:59:00+05:30", "by 3 November")
    assert deadline_is_sane(event, MSG) is False