from planner.models import Task, TaskEvent, DecisionAction
from planner.intelligence.matching import decide

DL1 = "2026-11-02T23:59:00+05:30"
DL2 = "2026-11-04T23:59:00+05:30"


def task(id, title, subject=None, task_type="assignment", deadline=None):
    return Task(id=id, title=title, subject=subject, task_type=task_type, deadline=deadline)


def event(action, title, subject=None, task_type="assignment", deadline=None):
    return TaskEvent(
        action=action, title=title, subject=subject, task_type=task_type,
        deadline=deadline, deadline_text="x" if deadline else None,
        source_message_id="s", evidence="x",
    )


def test_create_with_no_existing_tasks():
    d = decide(event("create", "DBMS Assignment 2", "DBMS", deadline=DL1), [])
    assert d.action == DecisionAction.CREATE
    assert d.task_id is None


def test_forward_with_same_deadline_is_duplicate():
    tasks = [task(1, "DBMS Assignment 2", "DBMS", deadline=DL1)]
    d = decide(event("create", "Assignment 2", deadline=DL1), tasks)
    assert d.action == DecisionAction.DUPLICATE
    assert d.task_id == 1


def test_create_without_deadline_is_duplicate():
    tasks = [task(1, "DBMS Assignment 2", "DBMS", deadline=DL1)]
    d = decide(event("create", "DBMS Assignment 2", "DBMS"), tasks)
    assert d.action == DecisionAction.DUPLICATE


def test_create_adding_missing_deadline_is_update():
    tasks = [task(1, "CN Assignment", "CN")]
    d = decide(event("create", "CN Assignment", "CN", deadline=DL1), tasks)
    assert d.action == DecisionAction.UPDATE
    assert d.task_id == 1


def test_create_with_conflicting_deadline_needs_review():
    tasks = [task(1, "DBMS Assignment 2", "DBMS", deadline=DL1)]
    d = decide(event("create", "DBMS Assignment 2", "DBMS", deadline=DL2), tasks)
    assert d.action == DecisionAction.NEEDS_REVIEW


def test_update_matches_existing_task():
    tasks = [task(1, "DBMS Assignment 2", "DBMS", deadline=DL1)]
    d = decide(event("update", "DBMS Assignment 2", "DBMS", deadline=DL2), tasks)
    assert d.action == DecisionAction.UPDATE
    assert d.task_id == 1


def test_update_with_no_match_needs_review():
    d = decide(event("update", "DBMS Assignment 2", "DBMS", deadline=DL2), [])
    assert d.action == DecisionAction.NEEDS_REVIEW


def test_cancel_matches_existing_task():
    tasks = [task(1, "OS Quiz 2", "OS", task_type="quiz", deadline=DL1)]
    d = decide(event("cancel", "OS Quiz", "OS", task_type="quiz"), tasks)
    assert d.action == DecisionAction.CANCEL
    assert d.task_id == 1


def test_cancel_with_no_match_needs_review():
    d = decide(event("cancel", "OS Quiz", "OS", task_type="quiz"), [])
    assert d.action == DecisionAction.NEEDS_REVIEW


def test_ambiguous_match_needs_review():
    tasks = [task(1, "DBMS Assignment 2", "DBMS"), task(2, "OS Assignment 2", "OS")]
    d = decide(event("update", "Assignment 2", deadline=DL2), tasks)
    assert d.action == DecisionAction.NEEDS_REVIEW