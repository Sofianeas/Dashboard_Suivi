"""Transformation complète des tickets bruts vers le modèle analytique V1."""
from __future__ import annotations
import hashlib
import math
import pandas as pd
from .dates import parse_datetime, opening_hour, day_opening
from .durations import parse_duration_minutes
from .mappings import build_mapping, map_value, normalize_priority, normalize_technician
from ..validation.schema import validate_source_schema


REFERENCE_DURATION_COLUMN = "Temps de résolution (min)"
REFERENCE_DURATION_TICKETS = {"P260604283", "P260604317"}
BUSINESS_OVERRIDES = {
    "P260904149": {
        "client_analytic": "L'addition",
        "problem_analytic": "Installation/Formation",
        "resolution_minutes": 4.0,
        "business_decision": (
            "Validation métier : L'addition / Installation/Formation / 4 min"
        ),
    }
}


def _reference_duration_minutes(ticket_id: str, value: object) -> float:
    try:
        minutes = float(pd.to_numeric(value, errors="raise"))
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Référence de durée en minutes invalide pour le ticket "
            f"{ticket_id}: {value!r}"
        ) from exc

    if not math.isfinite(minutes) or minutes < 0:
        raise ValueError(
            f"Référence de durée en minutes invalide pour le ticket "
            f"{ticket_id}: {value!r}"
        )
    return minutes


def transform_tickets(raw: pd.DataFrame, clients_ref: pd.DataFrame, problems_ref: pd.DataFrame) -> pd.DataFrame:
    validate_source_schema(raw.columns)
    # Une ligne de séparation de journée = pas de N° Ticket. Elle est ignorée.
    df = raw[raw["N° Ticket"].notna() & raw["N° Ticket"].astype(str).str.strip().ne("")].copy()
    client_map = build_mapping(clients_ref, "client_source_normalized", "client_analytic")
    problem_map = build_mapping(problems_ref, "problem_source", "problem_analytic")

    df = df.rename(columns={
        "Date du ticket":"ticket_date", "N° Ticket":"ticket_id", "Client":"client_raw",
        "Problématique":"problem_raw", "Priorité":"priority_raw", "Date/Heure ouverture":"opened_raw",
        "Date/Heure résolution":"resolved_raw", "Temps de résolution (h)":"duration_raw", "Technicien":"technician_raw",
    })
    df["source_row_number"] = df.index + 6
    df["ticket_id"] = df["ticket_id"].astype(str).str.strip()
    def safe_date(value):
        try:
            return parse_datetime(value)
        except (TypeError, ValueError):
            return None

    df["opened_at"] = df["opened_raw"].map(safe_date)
    df["resolved_at"] = df["resolved_raw"].map(safe_date)
    target_duration_rows = df["ticket_id"].isin(REFERENCE_DURATION_TICKETS)
    if target_duration_rows.any() and REFERENCE_DURATION_COLUMN not in df.columns:
        raise ValueError(
            f"Colonne de référence des durées absente: {REFERENCE_DURATION_COLUMN}"
        )

    df["resolution_minutes"] = [
        _reference_duration_minutes(ticket_id, reference_value)
        if ticket_id in REFERENCE_DURATION_TICKETS
        else parse_duration_minutes(duration_value)
        for ticket_id, reference_value, duration_value in zip(
            df["ticket_id"],
            df[REFERENCE_DURATION_COLUMN] if target_duration_rows.any() else [None] * len(df),
            df["duration_raw"],
        )
    ]

    df["client_source_normalized"] = df["client_raw"].map(lambda x: str(x).strip().upper() if pd.notna(x) else None)
    df["client_analytic"] = df["client_raw"].map(lambda x: map_value(x, client_map)[0])
    df["problem_source_normalized"] = df["problem_raw"].map(lambda x: str(x).strip() if pd.notna(x) else None)
    df["problem_analytic"] = df["problem_raw"].map(lambda x: map_value(x, problem_map)[0])
    df["resolution_minutes_raw"] = df["duration_raw"]
    df["resolution_minutes_reference_raw"] = (
        df[REFERENCE_DURATION_COLUMN]
        if REFERENCE_DURATION_COLUMN in df.columns
        else None
    )
    df["resolution_minutes_origin"] = "explicit"
    df.loc[target_duration_rows, "resolution_minutes_origin"] = "reference_column_j"
    df.loc[df["resolution_minutes"].isna(), "resolution_minutes_origin"] = "unknown"
    df["business_decision"] = None
    for ticket_id, override in BUSINESS_OVERRIDES.items():
        ticket_rows = df["ticket_id"].eq(ticket_id)
        for column in ("client_analytic", "problem_analytic", "resolution_minutes"):
            df.loc[ticket_rows, column] = override[column]
        df.loc[ticket_rows, "resolution_minutes_origin"] = "business_validated"
        df.loc[ticket_rows, "business_decision"] = override["business_decision"]
    df["priority_analytic"] = df["priority_raw"].map(normalize_priority)
    df["technician_analytic"] = df["technician_raw"].map(normalize_technician)
    df["opening_hour"] = df["opened_at"].map(opening_hour)
    df["day_of_week"] = df["opened_at"].map(day_opening)
    business_cols = ["ticket_id", "ticket_date", "client_raw", "problem_raw", "priority_raw", "opened_raw", "resolved_raw", "duration_raw", "technician_raw"]
    df["ticket_pk"] = df[business_cols].fillna("").astype(str).agg("|".join, axis=1).map(lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest()[:20])
    df["exact_duplicate"] = df["ticket_pk"].duplicated(keep=False)
    df["ingestion_status"] = "OK"
    df.loc[df["exact_duplicate"], "ingestion_status"] = "WARNING_EXACT_DUPLICATE"
    df.loc[df["client_analytic"].isna(), "ingestion_status"] = "WARNING_UNKNOWN_CLIENT"
    df.loc[df["problem_analytic"].isna(), "ingestion_status"] = "WARNING_UNKNOWN_PROBLEM"
    df.loc[df["priority_analytic"].isna(), "ingestion_status"] = "WARNING_UNKNOWN_PRIORITY"
    df.loc[df["resolution_minutes"].isna(), "ingestion_status"] = "ERROR_INVALID_DURATION"

    cols = ["ticket_pk","source_row_number","ticket_id","ticket_date","client_raw","client_source_normalized","client_analytic",
            "problem_raw","problem_source_normalized","problem_analytic","priority_raw","priority_analytic",
            "technician_raw","technician_analytic","opened_at","resolved_at","resolution_minutes",
            "opening_hour","day_of_week","exact_duplicate","ingestion_status",
            "resolution_minutes_raw","resolution_minutes_reference_raw",
            "resolution_minutes_origin","business_decision"]
    return df[cols].reset_index(drop=True)
