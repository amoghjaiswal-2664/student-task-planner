from datetime import datetime, timedelta

from typer.testing import CliRunner

from planner.cli import app
from planner.intelligence.priority import is_stale
from planner.models import Task
from planner.storage import add_task, connect, init_db

runner = CliRunner()
NOW = datetime.fromisoformat("2026-11-10T12:00:00+05:30")


def make_task(title, task_type="assignment", due=None, status="active"):
    return Task(title=title, task_type=task_type, deadline=due, status=status)


def db_with(tmp_path, *tasks):
    path = str(tmp_path / "t.db")
    conn = connect(path)
    init_db(conn)
    for t in tasks:
        add_task(conn, t)
    conn.close()
    return path


def run(db, *args):
    env = {"PLANNER_DB": db, "PLANNER_NOW": NOW.isoformat(), "COLUMNS": "220"}
    return runner.invoke(app, ["priorities", *args], env=env)


def sample_db(tmp_path):
    return db_with(
        tmp_path,
        make_task("Overdue recent", due=NOW - timedelta(days=2)),
        make_task("Exam soon", "exam", due=NOW + timedelta(hours=5)),
        make_task("Quiz later", "quiz", due=NOW + timedelta(days=10)),
        make_task("Ancient task", due=NOW - timedelta(days=30)),
        make_task("No date task", "other"),
        make_task("Done task", "exam", due=NOW + timedelta(hours=1), status="completed"),
    )


def test_is_stale():
    assert is_stale(make_task("a", due=NOW - timedelta(days=8)), NOW) is True
    assert is_stale(make_task("a", due=NOW - timedelta(days=6)), NOW) is False
    assert is_stale(make_task("a", due=NOW + timedelta(days=1)), NOW) is False
    assert is_stale(make_task("a"), NOW) is False


def test_orders_by_score_and_hides_stale(tmp_path):
    out = run(sample_db(tmp_path)).output
    order = [out.index(t) for t in ("Overdue recent", "Exam soon", "Quiz later", "No date task")]
    assert order == sorted(order)
    assert "Ancient task" not in out
    assert "Done task" not in out
    assert "stale tasks hidden: 1" in out
    assert "--all" in out


def test_all_flag_includes_stale_tasks(tmp_path):
    out = run(sample_db(tmp_path), "--all").output
    assert "Ancient task" in out
    assert "stale tasks hidden" not in out


def test_every_row_explains_itself(tmp_path):
    out = run(sample_db(tmp_path)).output
    assert "overdue by 2.0 days" in out
    assert "importance of exam" in out
    assert "no deadline known" in out


def test_limit_truncates_the_list(tmp_path):
    out = run(sample_db(tmp_path), "--limit", "2").output
    assert "Overdue recent" in out and "Exam soon" in out
    assert "Quiz later" not in out
    assert "showing 2 of 4" in out


def test_empty_database(tmp_path):
    out = run(db_with(tmp_path)).output
    assert "No active tasks" in out


def test_only_stale_tasks(tmp_path):
    db = db_with(tmp_path, make_task("Ancient task", due=NOW - timedelta(days=30)))
    out = run(db).output
    assert "Nothing current to work on" in out
    assert "stale tasks hidden: 1" in out