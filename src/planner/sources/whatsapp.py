import hashlib
import re
from datetime import datetime, timedelta, timezone

from planner.models import RawMessage, Source

IST = timezone(timedelta(hours=5, minutes=30))

HEADER = re.compile(r"^\[(\d{1,2})/(\d{1,2})/(\d{2}), (\d{1,2}):(\d{2}):(\d{2}) (AM|PM)\] (.*)$")
MEDIA_ONLY = re.compile(r"^(\[Forwarded\] )?<[a-z ]+ omitted>$", re.IGNORECASE)


def _clean(text: str) -> str:
    # Exports contain invisible characters that break regex matching.
    return text.replace("\u200e", "").replace("\u202f", " ").replace("\u00a0", " ")


def _make_id(group: str, timestamp: datetime, sender: str, body: str) -> str:
    # No line number in the hash, so re-importing a longer export of the
    # same chat produces the same ids and never duplicates anything.
    raw = f"{group}|{timestamp.isoformat()}|{sender}|{body}"
    return "wa-" + hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def parse_whatsapp_export(text: str, group: str, tz=IST) -> list[RawMessage]:
    entries = []
    current = None

    for line_no, line in enumerate(_clean(text).splitlines(), start=1):
        match = HEADER.match(line)
        if match:
            current = None
            month, day, yy, hour, minute, second, ampm, rest = match.groups()
            sender, sep, body = rest.partition(": ")
            if not sep:
                continue  # system line, e.g. "Messages and calls are end-to-end encrypted"
            hour24 = int(hour) % 12 + (12 if ampm == "PM" else 0)
            timestamp = datetime(
                2000 + int(yy), int(month), int(day),
                hour24, int(minute), int(second), tzinfo=tz,
            )
            current = {"line": line_no, "timestamp": timestamp, "sender": sender, "text": body}
            entries.append(current)
        elif current is not None:
            # No timestamp: this line continues the previous message.
            current["text"] += "\n" + line

    messages = []
    for entry in entries:
        body = entry["text"].strip()
        if not body or MEDIA_ONLY.match(body):
            continue
        messages.append(
            RawMessage(
                id=_make_id(group, entry["timestamp"], entry["sender"], body),
                source=Source.WHATSAPP,
                source_ref=f"{group}:line-{entry['line']}",
                sender=entry["sender"],
                timestamp=entry["timestamp"],
                text=body,
            )
        )
    return messages


def load_whatsapp_file(path: str, group: str) -> list[RawMessage]:
    with open(path, encoding="utf-8-sig") as f:
        return parse_whatsapp_export(f.read(), group)