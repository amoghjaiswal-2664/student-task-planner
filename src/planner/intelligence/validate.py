from planner.models import RawMessage, TaskEvent
def normalize(text: str) -> str:
    return " ".join(text.lower().split())
        

def evidence_in_message(event: TaskEvent, msg: RawMessage) -> bool:
    
    text = (msg.subject or " ")+ " " + msg.text
    return normalize(event.evidence) in normalize(text);