from datetime import datetime, timedelta
from planner.models import Task
from planner.intelligence.priority import rank_tasks

NOW = datetime.fromisoformat("2026-11-01T12:00:00+05:30")


def task(title, task_type="assignment", due_in_hours=None, status="active"):
    deadline = NOW + timedelta(hours=due_in_hours) if due_in_hours is not None else None
    return Task(title=title, task_type=task_type, deadline=deadline, status=status)


def titles(ranked):
    return [r.task.title for r in ranked]


def test_orders_by_score():
    tasks = [
        task("quiz without date", "quiz"),
        task("assignment", "assignment", 5),
        task("exam", "exam", 5),
    ]
    assert titles(rank_tasks(tasks, NOW)) == ["exam", "assignment", "quiz without date"]


def test_inactive_tasks_are_excluded():
    tasks = [task("done", "exam", 5, status="completed"), task("open", "quiz", 5)]
    assert titles(rank_tasks(tasks, NOW)) == ["open"]


def test_tie_broken_by_earlier_deadline():
    tasks = [task("later", "assignment", 20), task("sooner", "assignment", 10)]
    assert titles(rank_tasks(tasks, NOW)) == ["sooner", "later"]


def test_tie_without_deadlines_uses_title():
    tasks = [task("b task", "other"), task("a task", "other")]
    assert titles(rank_tasks(tasks, NOW)) == ["a task", "b task"]


def test_each_result_has_reasons():
    ranked = rank_tasks([task("x", "exam", 5)], NOW)
    assert len(ranked[0].reasons) == 3
    assert ranked[0].score > 0


def test_empty_list():
    assert rank_tasks([], NOW) == []