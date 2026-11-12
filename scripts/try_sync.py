from datetime import datetime
from planner.intelligence.cache import make_cached_llm
from planner.intelligence.priority import rank_tasks
from planner.sources.whatsapp import IST, load_whatsapp_file
from planner.storage import connect, init_db, list_tasks
from planner.sync import sync_messages

SINCE = datetime(2026, 11, 1, tzinfo=IST)


cache_conn = connect("llm_cache.db")
llm = make_cached_llm(cache_conn)

conn = connect("planner.db")
init_db(conn)

messages = load_whatsapp_file("private/chat.txt", "CSE-3A", since=SINCE)
print(f"{len(messages)} messages since {SINCE.date()}")

summary = sync_messages(conn, messages, llm=llm)
print(
    f"processed={summary.messages_processed} "
    f"already_seen={summary.messages_seen} failed={len(summary.failed)}"
)
for d in summary.decisions:
    print(f"  {d.action.value:12} {d.event.title}  ({d.reason})")

print()
for r in rank_tasks(list_tasks(conn), datetime.now(IST)):
    print(f"{r.score:6.1f}  {r.task.title}  deadline={r.task.deadline}")
    for reason in r.reasons:
        print("        -", reason)