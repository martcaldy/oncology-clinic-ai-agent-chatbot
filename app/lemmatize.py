import re
from functools import lru_cache

import pymorphy3

_morph = pymorphy3.MorphAnalyzer()
_WORD = re.compile(r"[а-яёa-z0-9]+", re.IGNORECASE)


@lru_cache(maxsize=10000)
def _lemma(word: str) -> str:
    return _morph.parse(word)[0].normal_form


def lemmatize(text: str) -> list[str]:
    return [_lemma(w) for w in _WORD.findall(text.lower())]
