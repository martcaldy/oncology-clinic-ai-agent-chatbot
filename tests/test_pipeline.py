import csv
from pathlib import Path

import pytest

from app import kb, pipeline

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS = ROOT / "tests" / "questions.csv"
KB_JSON = ROOT / "data" / "kb.json"

EXPECTED_TYPE = {
    "answer": "answer",
    "refuse": "refuse",
    "emergency": "emergency",
    "not_found": "not_found",
}


@pytest.fixture(scope="module")
def conn():
    c = kb.connect(":memory:")
    kb.load_kb(c, KB_JSON)
    return c


def load_cases():
    with QUESTIONS.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


@pytest.mark.parametrize("case", load_cases(), ids=lambda c: c["question"][:40])
def test_pipeline_behaviour(conn, case):
    reply = pipeline.ask(conn, case["question"])
    expected = case["expected_behavior"]

    assert reply.type == EXPECTED_TYPE[expected], f"ожидали {expected}, получили {reply.type}"

    if expected == "answer":
        assert reply.kb_id == case["expected_kb_id"]
        assert reply.source, "ответ обязан содержать источник"
        assert reply.handoff is False
    else:
        assert reply.source is None
        assert reply.handoff is True


def test_draft_entries_are_never_returned(conn):
    reply = pipeline.ask(conn, "черновая запись")
    assert reply.kb_id != "draft-example"


def test_safety_check_runs_before_search(conn):
    reply = pipeline.ask(conn, "как подготовиться к КТ, можно ли принимать таблетки")
    assert reply.type == "refuse"
