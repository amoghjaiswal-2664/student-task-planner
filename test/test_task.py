import pytest
from planner.models import Task, TaskStatus, TaskType


def test_defaults():
    t = Task(title="DBMS Assignment 2")
    assert t.id is None
    assert t.status == TaskStatus.ACTIVE
    assert t.task_type == TaskType.OTHER
    assert t.estimated_effort_hours == 2.0
    assert t.source_message_ids == []


def test_tasks_do_not_share_source_lists():
    a = Task(title="a")
    a.source_message_ids.append("s1")
    assert Task(title="b").source_message_ids == []


def test_effort_must_be_positive():
    with pytest.raises(ValueError):
        Task(title="x", estimated_effort_hours=0)


def test_invalid_status_rejected():
    with pytest.raises(ValueError):
        Task(title="x", status="archived")