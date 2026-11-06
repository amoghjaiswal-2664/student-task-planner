from datetime import datetime, timedelta
from planner.models import Task
from planner.intelligence.priority import score_task

NOW = datetime.fromisoformat("2026-11-01T12:00:00+05:30")


def task(task_type="assignment", due_in_hours=None, effort=2.0):
    deadline = NOW + timedelta(hours=due_in_hours) if due_in_hours is not None else None
    return Task(title="x", task_type=task_type, deadline=deadline, estimated_effort_hours=effort)


def test_due_in_hours_scores_high():
    score, reasons = score_task(task("assignment", due_in_hours=5), NOW)
    assert score == 97.0  # 80 + 15 + 2
    assert len(reasons) == 3


def test_overdue_exam():
    score, reasons = score_task(task("exam", due_in_hours=-3), NOW)
    assert score == 132.0  # 100 + 30 + 2
    assert any("overdue" in r for r in reasons)


def test_no_deadline():
    score, reasons = score_task(task("other"), NOW)
    assert score == 17.0  # 10 + 5 + 2
    assert any("no deadline" in r for r in reasons)


def test_urgency_bands():
    # assert score_task(task("assignment", due_in_hours=30), NOW)[0] == 77.0    # 60 + 15 + 2
    assert score_task(task("assignment", due_in_hours=30), NOW)[0] == 57.0    # 40 + 15 + 2
    assert score_task(task("quiz", due_in_hours=72), NOW)[0] == 62.0          # 40 + 20 + 2
    assert score_task(task("online class", due_in_hours=240, effort=4), NOW)[0] == 34.0  # 20 + 10 + 4


def test_effort_is_capped_at_eight():
    assert score_task(task("other", effort=20), NOW)[0] == 23.0  # 10 + 5 + 8