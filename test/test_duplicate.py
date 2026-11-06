import pytest
from planner.models import Decision, DecisionAction, TaskEvent

EVENT = TaskEvent(
    action="create", title="DBMS Assignment 2",
    source_message_id="s1", evidence="x",
)


def test_create_decision_needs_no_task_id():
    d = Decision(action="create", event=EVENT, reason="no similar task exists")
    assert d.task_id is None
    assert d.action == DecisionAction.CREATE


def test_update_decision_carries_task_id():
    d = Decision(action="update", event=EVENT, task_id=7, reason="deadline changed")
    assert d.task_id == 7


def test_reason_is_required():
    with pytest.raises(ValueError):
        Decision(action="create", event=EVENT)


def test_invalid_action_rejected():
    with pytest.raises(ValueError):
        Decision(action="merge", event=EVENT, reason="x")