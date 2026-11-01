from planner.models import RawMessage, TaskEvent
from planner.intelligence.relevance import is_relevant
from planner.intelligence.llm import complete
from planner.intelligence.extract import (
    SYSTEM_PROMPT,
    build_user_prompt,
    parse_events,
)
from planner.intelligence.validate import (
    evidence_in_message,
    deadline_is_sane,
)


def analyze_message(msg: RawMessage, llm=complete) -> list[TaskEvent]:

    if not is_relevant(msg):
        return []
    for attempt in range(2):
        raw = llm(build_user_prompt(msg), SYSTEM_PROMPT)

        try:
            events = parse_events(raw, msg)
            break

        except ValueError:
            if attempt == 1:
                raise

    kept = []

    for event in events:

        if not evidence_in_message(event, msg):
            continue

        if not deadline_is_sane(event, msg):
            event = event.model_copy(
                update={
                    "deadline": None,
                    "deadline_text": None,
                }
            )

        kept.append(event)

    return kept