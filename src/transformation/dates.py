"""Parsing robuste des dates/heures françaises du suivi."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any

MONTHS = {"janvier":1,"février":2,"mars":3,"avril":4,"mai":5,"juin":6,"juillet":7,"août":8,"septembre":9,"octobre":10,"novembre":11,"décembre":12}


def parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s*[àa]\s*", " ", text, flags=re.IGNORECASE)
    text = text.replace("h", ":")
    text = re.sub(r":(\d{2})(?!\d)", r":\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    # Historique: certaines cellules utilisent "14/10" pour l'heure 14:10.
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2})/(\d{2})", text)
    if m:
        d, mo, y, h, minute = map(int, m.groups())
        return datetime(y, mo, d, h, minute)

    # Tolérance aux heures compactes de type "1643" = 16:43.
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{2})(\d{2})", text)
    if m:
        d, mo, y, h, minute = map(int, m.groups())
        return datetime(y, mo, d, h, minute)

    # Tolérance aux heures sans zéro initial et aux chaînes mixtes.
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2})(?::(\d{1,2}))?)?", text)
    if m:
        d, mo, y = map(int, m.group(1,2,3)); h = int(m.group(4) or 0); minute = int(m.group(5) or 0)
        return datetime(y, mo, d, h, minute)
    raise ValueError(f"Date/heure inconnue: {value!r}")


def opening_hour(value: datetime | None) -> int | None:
    return value.hour if value else None


def day_opening(value: datetime | None) -> str | None:
    return value.strftime("%A") if value else None
