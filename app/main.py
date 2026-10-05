import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import kb, pipeline

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = os.environ.get("DB_PATH", str(ROOT / "data" / "app.db"))
KB_PATH = ROOT / "data" / "kb.json"
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Справочный чат-бот онкодиспансера (прототип)")
conn = kb.connect(DB_PATH)
kb.load_kb(conn, KB_PATH)


class AskIn(BaseModel):
    text: str


class HandoffIn(BaseModel):
    dialog_text: str


class AnswerIn(BaseModel):
    answer: str


@app.post("/api/ask")
def ask(body: AskIn):
    reply = pipeline.ask(conn, body.text)
    return {
        "type": reply.type,
        "text": reply.text,
        "source": reply.source,
        "handoff": reply.handoff,
    }


@app.post("/api/handoff")
def handoff(body: HandoffIn):
    ticket_id = kb.create_ticket(conn, body.dialog_text)
    return {"ticket_id": ticket_id, "status": "new"}


@app.get("/api/tickets")
def tickets():
    return kb.list_tickets(conn)


@app.post("/api/tickets/{ticket_id}/answer")
def answer(ticket_id: int, body: AnswerIn):
    if not kb.answer_ticket(conn, ticket_id, body.answer):
        raise HTTPException(status_code=404, detail="Обращение не найдено")
    return {"ticket_id": ticket_id, "status": "answered"}


@app.get("/")
def chat_page():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/operator")
def operator_page():
    return FileResponse(STATIC_DIR / "operator.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
