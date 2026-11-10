import sqlite3
from pydantic import BaseModel, Field
from planner.models import Decision, RawMessage
from planner.intelligence.llm import complete
from planner.intelligence.analyze import analyze_message
from planner.intelligence.matching import decide
from planner.storage import get_message, save_message, list_tasks
from planner.apply import apply_decision


class SyncSummary(BaseModel):
    messages_seen: int = 0
    messages_processed: int = 0
    failed: list[str] = Field(default_factory=list)
    decisions: list[Decision] = Field(default_factory=list)

def sync_messages(conn: sqlite3.Connection, messages: list[RawMessage], llm=complete) -> SyncSummary:
    summary = SyncSummary()
    for msg in sorted(messages, key=lambda m: m.timestamp):
        if get_message(conn, msg.id) is not None:
            summary.messages_seen += 1
            continue
        try:
            events = analyze_message(msg, llm=llm)
        except ValueError:
            summary.failed.append(msg.id)
            continue
        for event in events:
            decision = decide(event, list_tasks(conn))
            apply_decision(conn, decision)
            summary.decisions.append(decision)
        save_message(conn, msg)
        summary.messages_processed += 1
    return summary