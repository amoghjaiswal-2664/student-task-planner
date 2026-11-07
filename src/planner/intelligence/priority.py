from datetime import datetime
from planner.models import Task, TaskType, RankedTask, TaskStatus

IMPORTANCE = {
    TaskType.EXAM: 30,
    TaskType.QUIZ: 20,
    TaskType.ASSIGNMENT: 15,
    TaskType.ONLINE_CLASS: 10,
    TaskType.OTHER: 5,
}


def score_task(task: Task, now: datetime) -> tuple[float, list[str]]:
    """
    Calculate a priority score for a task.

    Higher scores indicate higher priority.

    Returns:
        A tuple containing:
        - Priority score
        - Exactly three explanations (urgency, importance, effort)
    """
    reasons = []

    if task.deadline is None:
        urgency = 10
        reasons.append("no deadline known (+10)")
    else:
        hours_left = (task.deadline - now).total_seconds() / 3600
        if hours_left < 0:
            urgency = 100
            overdue_hours = abs(hours_left)
            if overdue_hours >= 24:
                overdue_reason = f"overdue by {overdue_hours / 24:.1f} days"
            else:
                overdue_reason = f"overdue by {overdue_hours:.1f} hours"
            reasons.append(f"{overdue_reason} (+100)")
        elif hours_left <= 1:
            urgency = 90
            reasons.append(f"due in {hours_left:.1f} hours (+90)")
        elif hours_left <= 6:
            urgency = 80
            reasons.append(f"due in {hours_left:.1f} hours (+80)")
        elif hours_left <= 24:
            urgency = 60
            reasons.append(f"due in {hours_left:.1f} hours (+60)")
        elif hours_left <= 72:
            urgency = 40
            reasons.append(f"due in {hours_left:.1f} hours (+40)")
        else:
            urgency = 20
            reasons.append(f"due in {hours_left:.1f} hours (+20)")

    importance = IMPORTANCE.get(task.task_type, IMPORTANCE[TaskType.OTHER])
    reasons.append(f"importance of {task.task_type.value} (+{importance})")

    effort = min(task.estimated_effort_hours, 8)
    reasons.append(f"estimated effort of {effort} hours (+{effort})")

    return urgency + importance + effort, reasons

def rank_tasks(tasks: list[Task], now: datetime) -> list[RankedTask]:
    
    ranked_tasks = []
    for task in tasks:
        if task.status != TaskStatus.ACTIVE:
            continue
        score, reasons = score_task(task, now)
        ranked_tasks.append(RankedTask(task=task, score=score, reasons=reasons))
    return   sorted(ranked_tasks, key=lambda r: (-r.score, r.task.deadline is None, r.task.deadline, r.task.title))
    # return ranked_tasks
