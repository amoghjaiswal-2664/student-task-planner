from typer.testing import CliRunner

from planner.cli import app
from planner.models import RawMessage, Task, TaskStatus
from planner.storage import add_task, connect, get_task, init_db, save_message

runner = CliRunner()


def run(db, *args):
    return runner.invoke(app, list(args), env={"PLANNER_DB": db})


def make_db(tmp_path):
    path = str(tmp_path / "t.db")
    conn = connect(path)
    init_db(conn)
    save_message(conn, RawMessage(
        id="m1", source="whatsapp", source_ref="g:line-1", sender="Rohan",
        timestamp="2026-11-05T11:00:00+05:30",
        text="Submit assignment today\nUpload on Pod till 9 pm",
    ))
    task = add_task(conn, Task(
        title="DBMS Assignment 2", subject="DBMS", task_type="assignment",
        deadline="2026-11-06T23:00:00+05:30", deadline_text="6 November",
        source_message_ids=["m1", "m-missing"],
    ))
    conn.close()
    return path, task.id


def test_done_completes_an_active_task(tmp_path):
    path, task_id = make_db(tmp_path)
    result = run(path, "done", str(task_id))
    assert result.exit_code == 0
    assert "Marked task #1 as completed" in result.output
    assert get_task(connect(path), task_id).status == TaskStatus.COMPLETED


def test_done_twice_is_harmless(tmp_path):
    path, task_id = make_db(tmp_path)
    run(path, "done", str(task_id))
    result = run(path, "done", str(task_id))
    assert result.exit_code == 0
    assert "already completed" in result.output


def test_done_unknown_task(tmp_path):
    path, _ = make_db(tmp_path)
    result = run(path, "done", "99")
    assert result.exit_code == 1
    assert "No task #99" in result.output


def test_done_refuses_cancelled_task(tmp_path):
    path, _ = make_db(tmp_path)
    conn = connect(path)
    cancelled = add_task(conn, Task(title="Old quiz", status="cancelled"))
    conn.close()
    result = run(path, "done", str(cancelled.id))
    assert result.exit_code == 1
    assert "cancelled" in result.output
    assert get_task(connect(path), cancelled.id).status == TaskStatus.CANCELLED


def test_completed_tasks_leave_the_priorities_list(tmp_path):
    path, task_id = make_db(tmp_path)
    run(path, "done", str(task_id))
    result = run(path, "priorities")
    assert "No active tasks" in result.output


def test_show_prints_details_and_source_messages(tmp_path):
    path, task_id = make_db(tmp_path)
    out = run(path, "show", str(task_id)).output
    for expected in (
        "DBMS Assignment 2", "assignment", "DBMS", "active",
        "2026-11-06 23:00", "6 November", "from 2 message(s)",
        "2026-11-05 11:00", "whatsapp", "Rohan",
        "Submit assignment today", "Upload on Pod till 9 pm",
    ):
        assert expected in out


def test_show_marks_missing_messages(tmp_path):
    path, task_id = make_db(tmp_path)
    out = run(path, "show", str(task_id)).output
    assert "m-missing (message not stored)" in out


def test_show_unknown_task(tmp_path):
    path, _ = make_db(tmp_path)
    result = run(path, "show", "99")
    assert result.exit_code == 1
    assert "No task #99" in result.output


def test_show_task_without_deadline_or_subject(tmp_path):
    path, _ = make_db(tmp_path)
    conn = connect(path)
    bare = add_task(conn, Task(title="Bare task"))
    conn.close()
    out = run(path, "show", str(bare.id)).output
    assert "deadline: -" in out
    assert "subject: -" in out
    assert "from 0 message(s)" in out