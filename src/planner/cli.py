import os

import typer
from rich.console import Console
from rich.table import Table

from planner.review import apply_review_item, dismiss_review_item, review_label
from planner.storage import connect, get_task, init_db, list_review_items, list_tasks
from collections import Counter
from datetime import datetime
from pathlib import Path

from planner.intelligence.cache import make_cached_llm  
from planner.models import DecisionAction
from planner.sources.whatsapp import IST, load_whatsapp_file
from planner.sync import sync_messages
from planner.intelligence.priority import STALE_AFTER, is_stale, rank_tasks


app = typer.Typer(help="College task planner", no_args_is_help=True)


def open_db():
    conn = connect(os.environ.get("PLANNER_DB", "planner.db"))
    init_db(conn)
    return conn


@app.command()
def tasks():
    """List every stored task."""
    conn = open_db()
    all_tasks = list_tasks(conn)
    if not all_tasks:
        typer.echo("No tasks yet. Run a sync first.")
        return
    table = Table(title="Tasks")
    for column in ("ID", "Title", "Type", "Deadline", "Status"):
        table.add_column(column)
    for t in all_tasks:
        deadline = t.deadline.strftime("%Y-%m-%d %H:%M") if t.deadline else "-"
        table.add_row(str(t.id), t.title, t.task_type.value, deadline, t.status.value)
    Console().print(table)


@app.command()
def review():
    """Show messages the system was not sure about."""
    conn = open_db()
    items = list_review_items(conn)
    if not items:
        typer.echo("Nothing to review.")
        return
    for item in items:
        for line in review_label(item, conn):
            typer.echo(line)
        typer.echo("")
    typer.echo("Resolve one with: python -m planner resolve ID --apply-to TASK_ID   or   --dismiss")


@app.command()
def resolve(
    item_id: int,
    apply_to: int | None = typer.Option(None, "--apply-to", help="Task id this message belongs to"),
    dismiss: bool = typer.Option(False, "--dismiss", help="Ignore this message"),
):
    """Resolve one review item."""
    if (apply_to is None) == (not dismiss):
        typer.echo("Give exactly one of --apply-to or --dismiss.", err=True)
        raise typer.Exit(code=1)

    conn = open_db()
    item = next((i for i in list_review_items(conn) if i.id == item_id), None)
    if item is None:
        typer.echo(f"No pending review item #{item_id}.", err=True)
        raise typer.Exit(code=1)

    if dismiss:
        dismiss_review_item(conn, item)
        typer.echo(f"Dismissed review item #{item.id}.")
        return

    if get_task(conn, apply_to) is None:
        typer.echo(f"No task #{apply_to}.", err=True)
        raise typer.Exit(code=1)
    apply_review_item(conn, item, apply_to)
    typer.echo(f"Applied review item #{item.id} to task #{apply_to}.")

def make_llm():
    cache_conn = connect(os.environ.get("PLANNER_CACHE_DB", "llm_cache.db"))
    return make_cached_llm(cache_conn)


@app.command()
def sync(
    path: str,
    group: str = typer.Option(..., "--group", help="Chat name, e.g. CSE-3A (part of the message ids, so keep it the same every time)"),
    since: datetime | None = typer.Option(None, "--since", formats=["%Y-%m-%d"], help="Only messages on or after this date"),
    merge_minutes: int = typer.Option(10, "--merge-minutes", help="Merge messages from one sender sent within this many minutes (0 = off)"),
):
    """Import a WhatsApp chat export and update the tasks."""
    if not Path(path).is_file():
        typer.echo(f"File not found: {path}", err=True)
        raise typer.Exit(code=1)

    conn = open_db()
    messages = load_whatsapp_file(
        path,
        group,
        since=since.replace(tzinfo=IST) if since else None,
        merge_gap_minutes=merge_minutes or None,
    )
    typer.echo(f"messages read: {len(messages)} ({path})")
    if not messages:
        return

    summary = sync_messages(conn, messages, llm=make_llm())
    counts = Counter(d.action for d in summary.decisions)
    typer.echo(
        f"processed {summary.messages_processed}, "
        f"already seen {summary.messages_seen}, failed {len(summary.failed)}"
    )
    typer.echo(
        f"created {counts[DecisionAction.CREATE]}, updated {counts[DecisionAction.UPDATE]}, "
        f"cancelled {counts[DecisionAction.CANCEL]}, duplicates {counts[DecisionAction.DUPLICATE]}, "
        f"needs review {counts[DecisionAction.NEEDS_REVIEW]}"
    )
    if summary.failed:
        typer.echo(f"{len(summary.failed)} messages failed and will be retried on the next sync.")
    pending = len(list_review_items(conn))
    if pending:
        typer.echo(f"{pending} items need review. Run: python -m planner review")

def current_time() -> datetime:
    value = os.environ.get("PLANNER_NOW")
    return datetime.fromisoformat(value) if value else datetime.now(IST)


@app.command()
def priorities(
    show_all: bool = typer.Option(False, "--all", help="Include stale tasks"),
    limit: int = typer.Option(10, "--limit", help="How many tasks to show"),
):
    """Show what to work on first, and why."""
    conn = open_db()
    now = current_time()
    ranked = rank_tasks(list_tasks(conn), now)
    if not ranked:
        typer.echo("No active tasks. Run a sync first.")
        return

    stale_count = sum(1 for r in ranked if is_stale(r.task, now))
    shown = ranked if show_all else [r for r in ranked if not is_stale(r.task, now)]

    if shown:
        table = Table(title="Priorities")
        for column in ("#", "Score", "ID", "Title", "Deadline", "Why"):
            table.add_column(column)
        for rank, r in enumerate(shown[:limit], start=1):
            deadline = r.task.deadline.strftime("%Y-%m-%d %H:%M") if r.task.deadline else "-"
            table.add_row(
                str(rank), f"{r.score:.1f}", str(r.task.id),
                r.task.title, deadline, "; ".join(r.reasons),
            )
        Console().print(table)
        if len(shown) > limit:
            typer.echo(f"showing {limit} of {len(shown)}")
    else:
        typer.echo("Nothing current to work on.")

    if stale_count and not show_all:
        typer.echo(
            f"stale tasks hidden: {stale_count} "
            f"(overdue more than {STALE_AFTER.days} days, use --all to show them)"
        )