from datetime import datetime, timedelta
from planner.models import Task
from planner.intelligence.priority import score_task

NOW = datetime.fromisoformat("2026-11-01T12:00:00+05:30")


def task(task_type="assignment", due_in_hours=None):
    deadline = NOW + timedelta(hours=due_in_hours) if due_in_hours is not None else None
    return Task(title="x", task_type=task_type, deadline=deadline)


def test_due_in_hours_scores_high():
    score, reasons = score_task(task("assignment", due_in_hours=5), NOW)
    assert score == 95.0  # 80 + 15
    assert len(reasons) == 2


def test_overdue_exam():
    score, reasons = score_task(task("exam", due_in_hours=-3), NOW)
    assert score == 130.0  # 100 + 30
    assert any("overdue" in r for r in reasons)


def test_no_deadline():
    score, reasons = score_task(task("other"), NOW)
    assert score == 15.0  # 10 + 5
    assert any("no deadline" in r for r in reasons)


def test_urgency_bands():
    assert score_task(task("assignment", due_in_hours=30), NOW)[0] == 55.0   # 40 + 15
    assert score_task(task("quiz", due_in_hours=72), NOW)[0] == 60.0         # 40 + 20
    assert score_task(task("online class", due_in_hours=240), NOW)[0] == 30.0  # 20 + 10