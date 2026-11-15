from typer.testing import CliRunner

from planner.cli import app
from planner.storage import connect, count_messages, list_review_items, list_tasks

runner = CliRunner()

CHAT = (
    "[11/1/26, 9:00:00 AM] A: Please submit Assignment 2 by 2 November, 11:59 PM.\n"
    "[11/5/26, 9:30:00 AM] B: Quiz 2 for Operating Systems on 5 November 10:00 AM\n"
    "[11/6/26, 10:00:00 AM] B: good morning everyone\n"
)

R1 = '{"events":[{"action":"create","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-02T23:59:00+05:30","deadline_text":"by 2 November, 11:59 PM","evidence":"submit Assignment 2"}]}'
R2 = '{"events":[{"action":"create","title":"OS Quiz 2","subject":"OS","task_type":"quiz","deadline":"2026-11-05T10:00:00+05:30","deadline_text":"5 November 10:00 AM","evidence":"Quiz 2 for Operating Systems"}]}'
R3 = '{"events":[{"action":"update","title":"DBMS Assignment 2","subject":"DBMS","task_type":"assignment","deadline":"2026-11-06T23:59:00+05:30","deadline_text":"6 November","evidence":"deadline extended to 6 November"}]}'


def setup(tmp_path, monkeypatch, chat=CHAT):
    chat_file = tmp_path / "chat.txt"
    chat_file.write_text(chat, encoding="utf-8")
    calls = []

    def fake_llm(prompt, system=None):
        calls.append(prompt)
        if "extended" in prompt:
            return R3
        if "Assignment 2" in prompt:
            return R1
        if "Quiz 2" in prompt:
            return R2
        return "no json"

    monkeypatch.setattr("planner.cli.make_llm", lambda: fake_llm)
    return str(chat_file), str(tmp_path / "t.db"), calls


def run_sync(db, *args):
    return runner.invoke(app, ["sync", *args], env={"PLANNER_DB": db, "COLUMNS": "200"})


def test_sync_creates_tasks(tmp_path, monkeypatch):
    path, db, calls = setup(tmp_path, monkeypatch)
    result = run_sync(db, path, "--group", "G")
    assert result.exit_code == 0
    assert "messages read: 3" in result.output
    assert "processed 3, already seen 0, failed 0" in result.output
    assert "created 2" in result.output
    conn = connect(db)
    assert sorted(t.title for t in list_tasks(conn)) == ["DBMS Assignment 2", "OS Quiz 2"]
    assert count_messages(conn) == 3
    assert len(calls) == 2


def test_second_sync_does_nothing(tmp_path, monkeypatch):
    path, db, calls = setup(tmp_path, monkeypatch)
    run_sync(db, path, "--group", "G")
    calls.clear()
    result = run_sync(db, path, "--group", "G")
    assert "processed 0, already seen 3" in result.output
    assert calls == []
    assert len(list_tasks(connect(db))) == 2


def test_missing_file(tmp_path, monkeypatch):
    _, db, _ = setup(tmp_path, monkeypatch)
    result = run_sync(db, str(tmp_path / "nope.txt"), "--group", "G")
    assert result.exit_code == 1
    assert "File not found" in result.output


def test_group_is_required(tmp_path, monkeypatch):
    path, db, _ = setup(tmp_path, monkeypatch)
    assert run_sync(db, path).exit_code == 2


def test_since_filters_older_messages(tmp_path, monkeypatch):
    path, db, _ = setup(tmp_path, monkeypatch)
    result = run_sync(db, path, "--group", "G", "--since", "2026-11-05")
    assert "messages read: 2" in result.output
    assert [t.title for t in list_tasks(connect(db))] == ["OS Quiz 2"]


BURST = (
    "[11/5/26, 9:30:00 AM] B: Quiz 2 for Operating Systems on 5 November 10:00 AM\n"
    "[11/5/26, 9:32:00 AM] B: Please submit Assignment 2 by 2 November, 11:59 PM.\n"
)


def test_bursts_are_merged_by_default(tmp_path, monkeypatch):
    path, db, _ = setup(tmp_path, monkeypatch, BURST)
    assert "messages read: 1" in run_sync(db, path, "--group", "G").output


def test_merge_can_be_turned_off(tmp_path, monkeypatch):
    path, db, _ = setup(tmp_path, monkeypatch, BURST)
    result = run_sync(db, path, "--group", "G", "--merge-minutes", "0")
    assert "messages read: 2" in result.output


def test_flagged_items_are_reported(tmp_path, monkeypatch):
    chat = "[11/5/26, 9:30:00 AM] A: DBMS Assignment 2 deadline extended to 6 November\n"
    path, db, _ = setup(tmp_path, monkeypatch, chat)
    result = run_sync(db, path, "--group", "G")
    assert "needs review 1" in result.output
    assert "python -m planner review" in result.output
    assert len(list_review_items(connect(db))) == 1