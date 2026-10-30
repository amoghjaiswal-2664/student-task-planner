from enum import Enum
from pydantic import BaseModel, AwareDatetime, model_validator

class Source(str, Enum):
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    SAMPLE = "sample"

class TaskType(str, Enum):
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    QUIZ = "quiz"
    ONLINE_CLASS = "online class"
    PROJECT = "project"
    OTHER = "other"

class RawMessage(BaseModel):
    id: str
    source: Source
    source_ref: str
    sender: str
    timestamp: AwareDatetime
    text: str
    subject: str | None = None

class EventAction(str,Enum):
    CREATE = "create"
    UPDATE = "update"
    CANCEL = "cancel"

class TaskEvent(BaseModel):
    action: EventAction
    title: str
    subject: str | None = None
    task_type: TaskType = TaskType.OTHER
    source_message_id: str
    evidence: str
    deadline: AwareDatetime | None = None
    deadline_text: str | None = None
    @model_validator(mode="after")
    def deadline_needs_text(self):
        if(self.deadline):
            if(self.deadline_text is None):
                raise ValueError("deadline was given without deadline_text")
        return self
