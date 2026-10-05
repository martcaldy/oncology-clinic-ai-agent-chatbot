import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from app.lemmatize import lemmatize

SCHEMA = """
CREATE TABLE IF NOT EXISTS kb (
    id TEXT PRIMARY KEY,
    question_variants TEXT NOT NULL,
    answer_text TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS kb_index USING fts5(id UNINDEXED, body);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    dialog_text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',
    answer_text TEXT
);
"""


@dataclass(frozen=True)
class Hit:
    id: str
    answer_text: str
    source: str
    score: float


def connect(path: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def load_kb(conn: sqlite3.Connection, json_path: Path) -> int:
    entries = json.loads(json_path.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM kb")
    conn.execute("DELETE FROM kb_index")
    loaded = 0
    for e in entries:
        conn.execute(
            "INSERT INTO kb (id, question_variants, answer_text, source, status) VALUES (?, ?, ?, ?, ?)",
            (e["id"], json.dumps(e["questions"], ensure_ascii=False), e["answer"], e["source"], e["status"]),
        )
        if e["status"] == "approved":
            body = " ".join(lemmatize(" ".join(e["questions"]) + " " + e["answer"]))
            conn.execute("INSERT INTO kb_index (id, body) VALUES (?, ?)", (e["id"], body))
            loaded += 1
    conn.commit()
    return loaded


STOPWORDS = {
    "как", "что", "где", "когда", "какой", "какие", "какая", "можно", "ли", "мне", "я",
    "про", "расскажи", "расскажите", "нужно", "надо", "у", "в", "на", "и", "или", "а", "о", "об",
}


def search(conn: sqlite3.Connection, query: str, limit: int = 3) -> list[Hit]:
    terms = {t for t in lemmatize(query) if t not in STOPWORDS}
    if not terms:
        return []
    match = " OR ".join(f'"{t}"' for t in terms)
    rows = conn.execute(
        """
        SELECT kb.id, kb.question_variants, kb.answer_text, kb.source, bm25(kb_index) AS score
        FROM kb_index JOIN kb ON kb.id = kb_index.id
        WHERE kb_index MATCH ? AND kb.status = 'approved'
        ORDER BY score
        LIMIT ?
        """,
        (match, limit * 5),
    ).fetchall()
    hits = []
    for r in rows:
        questions = " ".join(json.loads(r["question_variants"]))
        if terms & set(lemmatize(questions)):
            hits.append(Hit(r["id"], r["answer_text"], r["source"], r["score"]))
    return hits[:limit]


def create_ticket(conn: sqlite3.Connection, dialog_text: str) -> int:
    cur = conn.execute("INSERT INTO tickets (dialog_text) VALUES (?)", (dialog_text,))
    conn.commit()
    return cur.lastrowid


def list_tickets(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM tickets ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def answer_ticket(conn: sqlite3.Connection, ticket_id: int, answer: str) -> bool:
    cur = conn.execute(
        "UPDATE tickets SET answer_text = ?, status = 'answered' WHERE id = ?", (answer, ticket_id)
    )
    conn.commit()
    return cur.rowcount > 0
