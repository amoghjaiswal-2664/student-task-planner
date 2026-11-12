import re
from planner.models import Decision, DecisionAction, EventAction, Task, TaskEvent, TaskStatus

GENERIC_WORDS = {
    "assignment", "quiz", "test", "exam", "lab", "experiment", "project",
    "form", "slip", "class", "session", "submission", "feedback",
    "the", "a", "an", "of", "on", "for", "and", "to",
}

ALIASES = {"de": "digital electronics"}


def expand_aliases(text: str) -> str:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return " ".join(ALIASES.get(w, w) for w in words)


def topic_words(title: str) -> set[str]:
    words = re.findall(r"[a-z]+", expand_aliases(title))
    return set(words) - GENERIC_WORDS


def title_number(title: str) -> int | None:
    numbers = re.findall(r"\d+", title)
    if numbers:
        return int(numbers[-1])
    return None


def find_candidates(event: TaskEvent, tasks: list[Task]) -> list[Task]:
    candidates = []
    event_topics = topic_words(event.title)
    event_no = title_number(event.title)
    for task in tasks:
        if task.status != TaskStatus.ACTIVE:
            continue
        if event.task_type != task.task_type:
            continue
        if event.subject and task.subject and expand_aliases(event.subject) != expand_aliases(task.subject):
            continue
        task_no = title_number(task.title)
        if event_no is not None and task_no is not None and event_no != task_no:
            continue
        task_topics = topic_words(task.title)
        if event_topics and task_topics and event_topics.isdisjoint(task_topics):
            continue
        candidates.append(task)
    return candidates
def decide(event: TaskEvent, tasks: list[Task]) -> Decision:
    candidates = find_candidates(event, tasks)

    # Several tasks could fit: don't guess.
    if len(candidates) > 1:
        return Decision(
            action=DecisionAction.NEEDS_REVIEW,
            event=event,
            reason=f"{len(candidates)} existing tasks could match this message",
        )

    # Nothing matches.
    if len(candidates) == 0:
        if event.action == EventAction.CREATE:
            return Decision(
                action=DecisionAction.CREATE,
                event=event,
                reason="no existing task matches, so this is a new task",
            )
        return Decision(
            action=DecisionAction.NEEDS_REVIEW,
            event=event,
            reason=f"message asks to {event.action.value} a task, but no existing task matches",
        )

    # Exactly one task matches.
    task = candidates[0]

    if event.action == EventAction.CANCEL:
        return Decision(
            action=DecisionAction.CANCEL,
            event=event,
            task_id=task.id,
            reason=f"cancellation of '{task.title}'",
        )

    if event.action == EventAction.UPDATE:
        return Decision(
            action=DecisionAction.UPDATE,
            event=event,
            task_id=task.id,
            reason=f"update to '{task.title}'",
        )

    # A "create" event that matches an existing task: a repeat or forward.
    if event.deadline is None or event.deadline == task.deadline:
        return Decision(
            action=DecisionAction.DUPLICATE,
            event=event,
            task_id=task.id,
            reason=f"repeat of '{task.title}', nothing new",
        )

    if task.deadline is None:
        return Decision(
            action=DecisionAction.UPDATE,
            event=event,
            task_id=task.id,
            reason=f"'{task.title}' had no deadline, and this message gives one",
        )

    return Decision(
        action=DecisionAction.NEEDS_REVIEW,
        event=event,
        task_id=task.id,
        reason=f"'{task.title}' already has a different deadline, so this may be a change or a different task",
    )