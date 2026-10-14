"""Ingestion Google Sheets pour le dashboard Help Desk.

Le classeur cible peut rester privé. L'accès production est prévu via un
compte de service Google (credentials JSON) partagé sur le fichier Sheets.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pandas as pd

SPREADSHEET_ID = "1SUemfD2NBhNAtciOBDjcW6UIJoovRSxo"
TICKETS_RANGE = "Suivi Tickets!A5:Z"
CLIENT_MAPPING_RANGE = "Listes!H:I"
PROBLEM_MAPPING_RANGE = "Listes!L:M"


def _service_account_credentials(credentials_path: str | Path | None = None):
    from google.oauth2.service_account import Credentials

    path = Path(credentials_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", ""))
    if not path:
        raise ValueError("GOOGLE_SERVICE_ACCOUNT_FILE n'est pas défini.")
    if not path.exists():
        raise FileNotFoundError(f"Credentials Google introuvables: {path}")
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    return Credentials.from_service_account_file(str(path), scopes=scopes)


def _sheets_service(credentials_path: str | Path | None = None):
    from googleapiclient.discovery import build

    credentials = _service_account_credentials(credentials_path)
    return build("sheets", "v4", credentials=credentials, cache_discovery=False)


def read_range(
    range_name: str,
    *,
    spreadsheet_id: str = SPREADSHEET_ID,
    credentials_path: str | Path | None = None,
) -> list[list[Any]]:
    """Lit une plage Google Sheets avec le compte de service."""
    service = _sheets_service(credentials_path)
    response = (
        service.spreadsheets()
        .values()
        .get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueRenderOption="FORMATTED_VALUE",
        )
        .execute()
    )
    return response.get("values", [])


def load_tickets_sheet(
    *, spreadsheet_id: str = SPREADSHEET_ID, credentials_path: str | Path | None = None
) -> pd.DataFrame:
    """Retourne A:Z avec les noms de colonnes de la ligne 5."""
    values = read_range(TICKETS_RANGE, spreadsheet_id=spreadsheet_id, credentials_path=credentials_path)
    if not values:
        return pd.DataFrame()
    header = values[0]
    width = len(header)
    rows = [row + [None] * (width - len(row)) for row in values[1:]]
    rows = [row[:width] for row in rows]
    return pd.DataFrame(rows, columns=header)


def load_reference_mappings(
    *, spreadsheet_id: str = SPREADSHEET_ID, credentials_path: str | Path | None = None
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge les mappings Clients H:I et Problématiques L:M."""
    def frame(values: list[list[Any]], columns: tuple[str, str]) -> pd.DataFrame:
        if not values:
            return pd.DataFrame(columns=columns)
        header = values[0]
        rows = [r + [None] * (2 - len(r)) for r in values[1:]]
        return pd.DataFrame([r[:2] for r in rows], columns=header[:2]).rename(
            columns={header[0]: columns[0], header[1]: columns[1]}
        )

    clients = frame(read_range(CLIENT_MAPPING_RANGE, spreadsheet_id=spreadsheet_id, credentials_path=credentials_path),
                    ("client_source_normalized", "client_analytic"))
    problems = frame(read_range(PROBLEM_MAPPING_RANGE, spreadsheet_id=spreadsheet_id, credentials_path=credentials_path),
                     ("problem_source", "problem_analytic"))
    return clients, problems


def load_from_xlsx(path: str | Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Adaptateur historique de test: lit le classeur local sans dépendre de Sheets."""
    path = Path(path)
    tickets = pd.read_excel(path, sheet_name="Suivi Tickets", header=4, engine="openpyxl")
    clients = pd.read_excel(path, sheet_name="Listes", usecols="H:I", header=0, engine="openpyxl")
    problems = pd.read_excel(path, sheet_name="Listes", usecols="L:M", header=0, engine="openpyxl")
    clients.columns = ["client_source_normalized", "client_analytic"]
    problems.columns = ["problem_source", "problem_analytic"]
    return tickets, clients, problems
