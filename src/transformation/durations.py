"""Parsing de la durée de résolution.

La colonne H est la source de vérité: F/G sont approximatives et ne servent
pas à recalculer la durée.
"""
from __future__ import annotations

import re
from datetime import timedelta, time
from typing import Any


def parse_duration_minutes(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, timedelta):
        # Excel peut stocker "41:14:00" comme 1 jour + 17:14 lorsque la
        # cellule est au format [hh]:mm:ss. Dans ce classeur, cela représente
        # 41 min 14 s, confirmé par la colonne J historique.
        if value.days >= 1:
            return value.total_seconds() / 3600
        return value.total_seconds() / 60
    if isinstance(value, time):
        return value.hour * 60 + value.minute + value.second / 60
    if isinstance(value, (int, float)):
        # Dans Excel/Sheets, une durée numérique peut être stockée en fraction de jour.
        return float(value) * 24 * 60 if 0 <= float(value) < 1 else float(value)

    text = str(value).strip().lower().replace(" ", "")
    text = text.replace(",", ".")
    # Dans l'historique, des valeurs comme "15:18min" ont été saisies
    # comme "15 minutes" avec un suffixe parasite. La colonne J de référence
    # confirme que la partie avant ":" est la minute analytique.
    m = re.fullmatch(r"(\d+):\d+min", text)
    if m:
        return float(m.group(1))

    total = 0.0
    found = False
    for pattern, multiplier in ((r"(\d+(?:\.\d+)?)h", 60), (r"(\d+(?:\.\d+)?)(?:min|mi)", 1), (r"(\d+(?:\.\d+)?)m\b", 1), (r"(\d+(?:\.\d+)?)s", 1/60)):
        m = re.search(pattern, text)
        if m:
            total += float(m.group(1)) * multiplier
            found = True
    if found:
        return total

    # Cas hh:mm:ss ou mm:ss.
    if re.fullmatch(r"\d{1,3}:\d{1,2}:\d{1,2}", text):
        h, m, s = map(int, text.split(":"))
        return h * 60 + m + s / 60
    if re.fullmatch(r"\d{1,3}:\d{1,2}", text):
        m, s = map(int, text.split(":"))
        return m + s / 60

    raise ValueError(f"Format de durée inconnu: {value!r}")
