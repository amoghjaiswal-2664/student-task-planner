import hashlib
import json
import sqlite3

from planner.intelligence.llm import complete


def _looks_valid(reply: str) -> bool:
    try:
        data = json.loads(reply[reply.find("{"): reply.rfind("}") + 1])
    except ValueError:
        return False
    return isinstance(data, dict) and "events" in data


def make_cached_llm(conn: sqlite3.Connection, llm=complete):
    conn.execute("CREATE TABLE IF NOT EXISTS llm_cache (key TEXT PRIMARY KEY, reply TEXT NOT NULL)")
    conn.commit()

    def cached(prompt: str, system: str | None = None) -> str:
        key = hashlib.sha1(f"{system}\n---\n{prompt}".encode("utf-8")).hexdigest()
        row = conn.execute("SELECT reply FROM llm_cache WHERE key = ?", (key,)).fetchone()
        if row is not None:
            return row[0]
        reply = llm(prompt, system)
        if _looks_valid(reply):
            conn.execute("INSERT OR REPLACE INTO llm_cache (key, reply) VALUES (?, ?)", (key, reply))
            conn.commit()
        return reply

    return cached