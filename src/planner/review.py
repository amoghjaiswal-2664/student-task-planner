import sqlite3
from planner.models import Decision, DecisionAction, ReviewItem
from planner.storage import get_task, resolve_review_item
from planner.apply import apply_decision


def review_label(item: ReviewItem, conn: sqlite3.Connection) -> list[str]:
    decision = item.decision
    event = decision.event

    lines = [
        f"#{item.id}  {event.action.value}: {event.title}",
        f"  why flagged: {decision.reason}",
    ]
    if event.deadline is not None:
        lines.append(f"  message says: {event.deadline_text} -> {event.deadline.isoformat()}")
    if decision.task_id is not None:
        task = get_task(conn, decision.task_id)
        if task is not None:
            lines.append(f"  current task: {task.title}, deadline {task.deadline}")
    lines.append(f"  evidence: {event.evidence}")
    return lines


def apply_review_item(conn: sqlite3.Connection, item: ReviewItem, task_id: int) -> None:
    decision = Decision(
        action=DecisionAction.UPDATE,
        event=item.decision.event,
        task_id=task_id,
        reason="applied by you from the review queue",
    )
    apply_decision(conn, decision)
    resolve_review_item(conn, item.id)


def dismiss_review_item(conn: sqlite3.Connection, item: ReviewItem) -> None:
    resolve_review_item(conn, item.id)