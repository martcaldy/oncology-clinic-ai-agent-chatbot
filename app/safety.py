import re
from dataclasses import dataclass

EMERGENCY = re.compile(
    r"задыха|не могу дышать|кровотечени|потерял(а)? сознание|судорог|боль в груди|"
    r"инсульт|сильн\w* кровь",
    re.IGNORECASE,
)

MEDICAL_ADVICE = re.compile(
    r"дозировк|дозу|мг\b|таблетк|принима\w+|выпить|пить |можно ли есть|назначь|назначен|"
    r"диагноз|поставь|прогноз|сколько осталось|лекарств",
    re.IGNORECASE,
)

EMERGENCY_TEXT = (
    "Похоже, речь о состоянии, которое требует немедленной помощи. "
    "Вызовите скорую помощь: 103 или 112. Этот чат не предназначен для экстренных ситуаций."
)

ADVICE_TEXT = (
    "Вопросы о приёме лекарств, дозировках и диагнозе требуют решения лечащего врача. "
    "Бот не даёт медицинских назначений. Вы можете передать вопрос специалисту."
)


@dataclass(frozen=True)
class SafetyResult:
    kind: str
    text: str


def check(text: str) -> SafetyResult | None:
    if EMERGENCY.search(text):
        return SafetyResult("emergency", EMERGENCY_TEXT)
    if MEDICAL_ADVICE.search(text):
        return SafetyResult("refuse", ADVICE_TEXT)
    return None
