from planner.models import Task, TaskEvent
from planner.intelligence.matching import title_number, find_candidates


def task(id, title, subject=None, task_type="assignment", status="active"):
    return Task(id=id, title=title, subject=subject, task_type=task_type, status=status)


def event(title, subject=None, task_type="assignment"):
    return TaskEvent(
        action="update", title=title, subject=subject, task_type=task_type,
        source_message_id="s", evidence="x",
    )


def ids(found):
    return [t.id for t in found]


def test_title_number():
    assert title_number("DBMS Assignment 2") == 2
    assert title_number("CS101 Assignment 2") == 2
    assert title_number("OS Quiz") is None


def test_same_task_with_unknown_subject_matches():
    tasks = [task(1, "DBMS Assignment 2", "DBMS")]
    assert ids(find_candidates(event("Assignment 2"), tasks)) == [1]


def test_same_subject_matches_ignoring_case():
    tasks = [task(1, "DBMS Assignment 2", "DBMS")]
    assert ids(find_candidates(event("DBMS Assignment 2", "dbms"), tasks)) == [1]


def test_different_number_does_not_match():
    tasks = [task(1, "DBMS Assignment 2", "DBMS")]
    assert find_candidates(event("DBMS Assignment 3", "DBMS"), tasks) == []


def test_different_subject_does_not_match():
    tasks = [task(1, "DBMS Assignment 2", "DBMS")]
    assert find_candidates(event("OS Assignment 2", "OS"), tasks) == []


def test_event_without_number_matches_numbered_task():
    tasks = [task(1, "OS Quiz 2", "OS", task_type="quiz")]
    assert ids(find_candidates(event("OS Quiz", "OS", "quiz"), tasks)) == [1]


def test_different_type_does_not_match():
    tasks = [task(1, "OS Quiz 2", "OS", task_type="quiz")]
    assert find_candidates(event("OS Assignment 2", "OS"), tasks) == []


def test_inactive_tasks_are_ignored():
    tasks = [
        task(1, "DBMS Assignment 2", "DBMS", status="completed"),
        task(2, "DBMS Assignment 2", "DBMS", status="cancelled"),
    ]
    assert find_candidates(event("DBMS Assignment 2", "DBMS"), tasks) == []


def test_ambiguous_returns_all_candidates():
    tasks = [task(1, "DBMS Assignment 2", "DBMS"), task(2, "OS Assignment 2", "OS")]
    assert ids(find_candidates(event("Assignment 2"), tasks)) == [1, 2]