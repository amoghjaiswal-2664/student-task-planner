import sqlite3
from planner.models import Decision, DecisionAction, Task, TaskStatus
from planner.storage import add_task, get_task, update_task


def with_source(task: Task, message_id: str) -> Task:
    ids = list(task.source_message_ids)
    if message_id not in ids:
        ids.append(message_id)
    return task.model_copy(update={"source_message_ids": ids})


def apply_decision(conn: sqlite3.Connection, decision: Decision) -> Task | None:
    event = decision.event

    if decision.action == DecisionAction.NEEDS_REVIEW:
        return None

    if decision.action == DecisionAction.CREATE:
        new_task = Task(
            title=event.title,
            subject=event.subject,
            task_type=event.task_type,
            deadline=event.deadline,
            deadline_text=event.deadline_text,
            source_message_ids=[event.source_message_id],
        )
        return add_task(conn, new_task)

    # update, cancel and duplicate all work on an existing task
    task = get_task(conn, decision.task_id)
    if task is None:
        raise ValueError(f"task {decision.task_id} not found")

    if decision.action == DecisionAction.UPDATE:
        changes = {}
        if event.deadline is not None:
            changes["deadline"] = event.deadline
            changes["deadline_text"] = event.deadline_text
        if task.subject is None and event.subject:
            changes["subject"] = event.subject
        task = task.model_copy(update=changes)
    elif decision.action == DecisionAction.CANCEL:
        task = task.model_copy(update={"status": TaskStatus.CANCELLED})
    # DUPLICATE: nothing to change except the source, recorded below

    task = with_source(task, event.source_message_id)
    update_task(conn, task)
    return task