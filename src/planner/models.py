from enum import Enum
from pydantic import BaseModel, AwareDatetime, model_validator, Field

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

class TaskStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    id: int | None = None
    title: str
    subject: str | None = None
    task_type: TaskType = TaskType.OTHER
    deadline: AwareDatetime | None = None
    deadline_text: str | None = None
    status: TaskStatus = TaskStatus.ACTIVE
    estimated_effort_hours: float = Field(default=2.0, gt=0)
    source_message_ids: list[str] = Field(default_factory=list)

class DecisionAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    CANCEL = "cancel"
    DUPLICATE = "duplicate"
    NEEDS_REVIEW = "needs_review"

class Decision(BaseModel):
    action: DecisionAction
    event: TaskEvent
    task_id: int | None = None
    reason: str 