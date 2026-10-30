from planner.models import RawMessage
KEYWORDS = ["deadline", "submit", "assignment", "quiz","exam","project","due","extend","postpone","cancel","test","course proficiency","credit","jama", "karni hai", "dena hai", "karna hai", "last date", "kal tak", "aaj tak", "submission"]

def is_relevant(msg: RawMessage) -> bool:
    text = (msg.subject or " ")+ " " + msg.text
    lowercase_msg = text.lower()
    return any(k in lowercase_msg for k in KEYWORDS)