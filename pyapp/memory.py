import sqlite3
import time
from typing import List, Tuple, Optional


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            user_id TEXT,
            role TEXT CHECK(role IN ('human','ai')),
            content TEXT,
            ts INTEGER
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS preferences (
            user_id TEXT,
            item TEXT,
            ts INTEGER
        )
        """
    )
    return conn


def append_message(db_path: str, user_id: str, role: str, content: str) -> None:
    conn = _get_conn(db_path)
    conn.execute(
        "INSERT INTO messages(user_id, role, content, ts) VALUES (?, ?, ?, ?)",
        (user_id, role, content, int(time.time())),
    )
    conn.commit()
    conn.close()


def get_history(
    db_path: str,
    user_id: str,
    limit: int = 16,
    ttl_seconds: Optional[int] = None,
) -> List[Tuple[str, str]]:
    cutoff = None
    if ttl_seconds and ttl_seconds > 0:
        cutoff = int(time.time()) - ttl_seconds
    conn = _get_conn(db_path)
    if cutoff:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? AND ts>=? ORDER BY ts DESC LIMIT ?",
            (user_id, cutoff, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE user_id=? ORDER BY ts DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    conn.close()
    # Return in chronological order (oldest first)
    return list(reversed(rows))


def count_context(db_path: str, user_id: str, ttl_seconds: Optional[int] = None) -> int:
    cutoff = None
    if ttl_seconds and ttl_seconds > 0:
        cutoff = int(time.time()) - ttl_seconds
    conn = _get_conn(db_path)
    if cutoff:
        row = conn.execute(
            "SELECT COUNT(1) FROM messages WHERE user_id=? AND ts>=?",
            (user_id, cutoff),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(1) FROM messages WHERE user_id=?",
            (user_id,),
        ).fetchone()
    conn.close()
    return int(row[0] if row and row[0] is not None else 0)


def add_preference(db_path: str, user_id: str, item: str, max_items: int = 5) -> None:
    conn = _get_conn(db_path)
    # Deduplicate
    existing = conn.execute(
        "SELECT item FROM preferences WHERE user_id=?",
        (user_id,),
    ).fetchall()
    existing_items = [r[0] for r in existing]
    if item not in existing_items:
        conn.execute(
            "INSERT INTO preferences(user_id, item, ts) VALUES (?, ?, ?)",
            (user_id, item, int(time.time())),
        )
    # enforce max_items by removing oldest beyond limit
    rows = conn.execute(
        "SELECT rowid FROM preferences WHERE user_id=? ORDER BY ts DESC",
        (user_id,),
    ).fetchall()
    if len(rows) > max_items:
        to_delete = rows[max_items:]
        for (rowid,) in to_delete:
            conn.execute("DELETE FROM preferences WHERE rowid=?", (rowid,))
    conn.commit()
    conn.close()


def clear_preferences(db_path: str, user_id: str) -> None:
    conn = _get_conn(db_path)
    conn.execute("DELETE FROM preferences WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_preferences(db_path: str, user_id: str) -> List[str]:
    conn = _get_conn(db_path)
    rows = conn.execute(
        "SELECT item FROM preferences WHERE user_id=? ORDER BY ts DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]