from enum import Enum
from pydantic import BaseModel, AwareDatetime

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
    