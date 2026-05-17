"""
Perzistentní paměť agenta — ukládá kontext přes SQLite.
Automaticky se přidává ke každé konverzaci s Claudem.
"""
import sqlite3, json, datetime, os

DB_PATH = os.environ.get("DB_PATH", "agent_memory.db")

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            role      TEXT,
            content   TEXT,
            ts        TEXT DEFAULT (datetime('now'))
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            key       TEXT PRIMARY KEY,
            value     TEXT,
            ts        TEXT DEFAULT (datetime('now'))
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS pending_actions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            action    TEXT,
            payload   TEXT,
            ts        TEXT DEFAULT (datetime('now'))
        )""")
    c.commit()
    return c

# ── Konverzační paměť ────────────────────────────────────────────────────────

def save_message(role: str, content: str):
    c = _conn()
    c.execute("INSERT INTO messages (role, content) VALUES (?,?)", (role, content))
    c.commit()
    c.close()

def get_history(limit: int = 20) -> list:
    """Vrátí posledních N zpráv jako list pro Claude messages."""
    c = _conn()
    rows = c.execute(
        "SELECT role, content FROM messages ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    c.close()
    return [{"role": r, "content": ct} for r, ct in reversed(rows)]

def clear_history():
    c = _conn()
    c.execute("DELETE FROM messages")
    c.commit()
    c.close()

# ── Trvalé fakty (pamatuj si X) ──────────────────────────────────────────────

def remember(key: str, value: str):
    c = _conn()
    c.execute("INSERT OR REPLACE INTO facts (key, value, ts) VALUES (?,?,datetime('now'))",
              (key, value))
    c.commit()
    c.close()

def recall(key: str) -> str | None:
    c = _conn()
    row = c.execute("SELECT value FROM facts WHERE key=?", (key,)).fetchone()
    c.close()
    return row[0] if row else None

def all_facts() -> dict:
    c = _conn()
    rows = c.execute("SELECT key, value FROM facts").fetchall()
    c.close()
    return {k: v for k, v in rows}

# ── Pending akce čekající na schválení ───────────────────────────────────────

def queue_action(action: str, payload: dict) -> int:
    c = _conn()
    cur = c.execute("INSERT INTO pending_actions (action, payload) VALUES (?,?)",
                    (action, json.dumps(payload, ensure_ascii=False)))
    c.commit()
    action_id = cur.lastrowid
    c.close()
    return action_id

def pop_action(action_id: int) -> dict | None:
    c = _conn()
    row = c.execute("SELECT action, payload FROM pending_actions WHERE id=?",
                    (action_id,)).fetchone()
    if row:
        c.execute("DELETE FROM pending_actions WHERE id=?", (action_id,))
        c.commit()
    c.close()
    if row:
        return {"action": row[0], "payload": json.loads(row[1])}
    return None
