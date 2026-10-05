import csv
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import kb, pipeline  # noqa: E402

QUESTIONS = ROOT / "tests" / "questions.csv"
KB_JSON = ROOT / "data" / "kb.json"
EXPECTED_TYPE = {"answer": "answer", "refuse": "refuse", "emergency": "emergency", "not_found": "not_found"}


def main():
    conn = kb.connect(":memory:")
    kb.load_kb(conn, KB_JSON)
    with QUESTIONS.open(encoding="utf-8") as f:
        cases = list(csv.DictReader(f))

    answer_cases = [c for c in cases if c["expected_behavior"] == "answer"]
    top3_hits = top1_hits = 0
    by_type = defaultdict(lambda: [0, 0])
    misses = []

    for c in answer_cases:
        hits = kb.search(conn, c["question"], limit=3)
        ids = [h.id for h in hits]
        in_top3 = c["expected_kb_id"] in ids
        in_top1 = bool(ids) and ids[0] == c["expected_kb_id"]
        top3_hits += in_top3
        top1_hits += in_top1
        by_type[c["type"]][0] += in_top3
        by_type[c["type"]][1] += 1
        if not in_top3:
            misses.append((c["question"], c["expected_kb_id"], ids))

    behaviour_ok = 0
    behaviour_total = 0
    wrong = []
    for c in cases:
        if c["expected_behavior"] == "answer":
            continue
        behaviour_total += 1
        reply = pipeline.ask(conn, c["question"])
        if reply.type == EXPECTED_TYPE[c["expected_behavior"]]:
            behaviour_ok += 1
        else:
            wrong.append((c["question"], c["expected_behavior"], reply.type))

    n = len(answer_cases)
    print(f"Вопросов на поиск: {n}")
    print(f"Полнота поиска top-3: {top3_hits}/{n} = {top3_hits / n:.0%}")
    print(f"Точность top-1 (без порога): {top1_hits}/{n} = {top1_hits / n:.0%}")
    for t, (ok, total) in by_type.items():
        print(f"  {t}: top-3 {ok}/{total} = {ok / total:.0%}")
    print()
    print(f"Безопасность и отказы: {behaviour_ok}/{behaviour_total}")
    for q, exp, got in wrong:
        print(f"  ОШИБКА: «{q}» ожидали {exp}, получили {got}")
    print()
    print("Промахи поиска (нужная запись не в top-3):")
    for q, exp, ids in misses:
        print(f"  «{q}» → ожидали {exp}, нашли {ids or 'ничего'}")


if __name__ == "__main__":
    main()
