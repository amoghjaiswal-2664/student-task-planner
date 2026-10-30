from planner.models import RawMessage

SYSTEM_PROMPT = """You extract academic tasks from college messages (emails and WhatsApp, often Hinglish).

Return ONLY a JSON object, no other text, in this shape:
{"events": [{"action": "create|update|cancel", "title": "...", "subject": "course name only, like DBMS, OS or CN, or null", "task_type": "assignment|exam|quiz|online class|other", "deadline": "ISO 8601 with +05:30, or null", "deadline_text": "exact phrase from the message, or null", "evidence": "exact quote from the message"}]}

Rules:
- Extract only things a student must act on, or that change an earlier task. Greetings, chit-chat and pure information give {"events": []}.
- "create" = a new task, "update" = changes an earlier task (deadline moved, details changed), "cancel" = a task is cancelled.
- NEVER guess a deadline. If the message gives none, deadline and deadline_text must both be null.
- If it gives one, deadline_text is the exact words used, and deadline is that moment in ISO format, worked out from the message's sent time (for example "kal" means the day after it was sent). If only a date is given with no time, use 23:59.
- evidence must be copied word for word from the message.
- All times are IST (+05:30)."""

def build_user_prompt(msg:RawMessage)->str:
    lines = [
    f"Sent at: {msg.timestamp.isoformat()} ({msg.timestamp.strftime('%A')})",
    f"Source: {msg.source.value}",
    f"Sender: {msg.sender}",
    ]
    if msg.subject:
        lines.append(f"Subject: {msg.subject}")
    lines.append(f"Message: {msg.text}")
    return "\n".join(lines)