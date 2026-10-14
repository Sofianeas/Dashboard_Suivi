from __future__ import annotations

REQUIRED_SOURCE_COLUMNS = [
    "Date du ticket", "N° Ticket", "Client", "Problématique", "Priorité",
    "Date/Heure ouverture", "Date/Heure résolution", "Temps de résolution (h)", "Technicien",
]


def validate_source_schema(columns) -> None:
    missing = [c for c in REQUIRED_SOURCE_COLUMNS if c not in columns]
    if missing:
        raise ValueError(f"Colonnes source manquantes: {missing}")
