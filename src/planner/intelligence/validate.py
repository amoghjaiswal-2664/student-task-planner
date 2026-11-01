from planner.models import RawMessage, TaskEvent
from datetime import timedelta
def normalize(text: str) -> str:
    return " ".join(text.lower().split())
        

def evidence_in_message(event: TaskEvent, msg: RawMessage) -> bool:
    
    text = (msg.subject or " ")+ " " + msg.text
    return normalize(event.evidence) in normalize(text)

def deadline_is_sane(event: TaskEvent, msg: RawMessage) -> bool:
    if event.deadline is None:
        return True
    if event.deadline<msg.timestamp:
        return False
    if event.deadline>msg.timestamp+timedelta(days=180):
        return False
    else:
        return True