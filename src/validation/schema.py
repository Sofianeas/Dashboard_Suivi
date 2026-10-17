from __future__ import annotations

from collections.abc import Iterable

REQUIRED_SOURCE_COLUMNS = [
    "Date du ticket", "N° Ticket", "Client", "Problématique", "Priorité",
    "Date/Heure ouverture", "Date/Heure résolution", "Temps de résolution (h)", "Technicien",
]


def validate_source_schema(columns: Iterable[str]) -> None:
    """Validate required source headers without constraining order or extra columns."""
    available = set(columns)
    missing = [column for column in REQUIRED_SOURCE_COLUMNS if column not in available]
    if missing:
        raise ValueError(f"Colonnes source manquantes: {missing}")
