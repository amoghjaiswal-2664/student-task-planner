from typer.testing import CliRunner

from planner.cli import app
from planner.models import Decision, Task, TaskEvent
from planner.storage import (
    add_review_item, add_task, connect, get_task, init_db, list_review_items,
)

runner = CliRunner()
DL1 = "2026-11-04T22:00:00+05:30"
DL2 = "2026-11-06T23:00:00+05:30"


def run(db_path, *args):
    env = {"PLANNER_DB": db_path, "COLUMNS": "200"}
    return runner.invoke(app, list(args), env=env)


def empty_db(tmp_path):
    path = str(tmp_path / "t.db")
    conn = connect(path)
    init_db(conn)
    conn.close()
    return path


def seeded_db(tmp_path):
    path = empty_db(tmp_path)
    conn = connect(path)
    task = add_task(conn, Task(
        title="CS3013 Proficiency Test-2", subject="CS3013", task_type="exam",
        deadline=DL1, deadline_text="by 4 November", source_message_ids=["m1"],
    ))
    event = TaskEvent(
        action="create", title="CS3013 Proficiency Test-2", subject="CS3013",
        task_type="exam", deadline=DL2, deadline_text="ends 6 November",
        source_message_id="m9", evidence="End Time 2026-11-06 23:00",
    )
    add_review_item(conn, Decision(
        action="needs_review", event=event, task_id=task.id,
        reason="task already has a different deadline",
    ))
    conn.close()
    return path, task.id


def test_tasks_on_empty_database(tmp_path):
    result = run(empty_db(tmp_path), "tasks")
    assert result.exit_code == 0
    assert "No tasks yet" in result.output


def test_tasks_lists_stored_tasks(tmp_path):
    path, _ = seeded_db(tmp_path)
    result = run(path, "tasks")
    assert result.exit_code == 0
    assert "CS3013 Proficiency Test-2" in result.output
    assert "2026-11-04 22:00" in result.output
    assert "exam" in result.output
    assert "active" in result.output


def test_review_on_empty_database(tmp_path):
    result = run(empty_db(tmp_path), "review")
    assert result.exit_code == 0
    assert "Nothing to review" in result.output


def test_review_shows_flagged_items(tmp_path):
    path, _ = seeded_db(tmp_path)
    result = run(path, "review")
    assert result.exit_code == 0
    assert "task already has a different deadline" in result.output
    assert "End Time 2026-11-06 23:00" in result.output
    assert "resolve" in result.output


def test_resolve_apply_updates_the_task(tmp_path):
    path, task_id = seeded_db(tmp_path)
    item_id = list_review_items(connect(path))[0].id
    result = run(path, "resolve", str(item_id), "--apply-to", str(task_id))
    assert result.exit_code == 0
    conn = connect(path)
    assert get_task(conn, task_id).deadline.isoformat() == DL2
    assert list_review_items(conn) == []


def test_resolve_dismiss_leaves_the_task_alone(tmp_path):
    path, task_id = seeded_db(tmp_path)
    item_id = list_review_items(connect(path))[0].id
    result = run(path, "resolve", str(item_id), "--dismiss")
    assert result.exit_code == 0
    conn = connect(path)
    assert get_task(conn, task_id).deadline.isoformat() == DL1
    assert list_review_items(conn) == []


def test_resolve_needs_exactly_one_option(tmp_path):
    path, task_id = seeded_db(tmp_path)
    item_id = list_review_items(connect(path))[0].id
    neither = run(path, "resolve", str(item_id))
    both = run(path, "resolve", str(item_id), "--dismiss", "--apply-to", str(task_id))
    assert neither.exit_code == 1 and "exactly one" in neither.output
    assert both.exit_code == 1 and "exactly one" in both.output
    assert len(list_review_items(connect(path))) == 1


def test_resolve_unknown_item(tmp_path):
    path, _ = seeded_db(tmp_path)
    result = run(path, "resolve", "99", "--dismiss")
    assert result.exit_code == 1
    assert "No pending review item" in result.output


def test_resolve_unknown_task(tmp_path):
    path, _ = seeded_db(tmp_path)
    item_id = list_review_items(connect(path))[0].id
    result = run(path, "resolve", str(item_id), "--apply-to", "99")
    assert result.exit_code == 1
    assert "No task #99" in result.output
    assert len(list_review_items(connect(path))) == 1