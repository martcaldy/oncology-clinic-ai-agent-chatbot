import sqlite3
from dataclasses import dataclass

from app import kb, safety

SCORE_THRESHOLD = -0.1

NOT_FOUND_TEXT = (
    "В утверждённой базе нет ответа на этот вопрос. "
    "Вы можете передать его специалисту."
)


@dataclass(frozen=True)
class Reply:
    type: str
    text: str
    source: str | None
    handoff: bool
    kb_id: str | None = None


def ask(conn: sqlite3.Connection, text: str) -> Reply:
    blocked = safety.check(text)
    if blocked:
        return Reply(blocked.kind, blocked.text, None, handoff=True)

    hits = kb.search(conn, text)
    if hits and hits[0].score <= SCORE_THRESHOLD:
        best = hits[0]
        return Reply("answer", best.answer_text, best.source, handoff=False, kb_id=best.id)

    return Reply("not_found", NOT_FOUND_TEXT, None, handoff=True)
