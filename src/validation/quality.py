"""Contrôles qualité du dataset analytique."""
from __future__ import annotations

import pandas as pd

REQUIRED_ANALYTIC_COLUMNS = (
    "ticket_id",
    "client_analytic",
    "problem_analytic",
    "priority_analytic",
    "resolution_minutes",
    "opened_at",
    "resolved_at",
    "exact_duplicate",
    "ticket_pk",
)


def quality_report(df: pd.DataFrame) -> dict[str, object]:
    """Return descriptive quality metrics for a transformed ticket dataset.

    The function reports anomalies; it does not decide whether an export is
    acceptable. The input must contain the complete analytic columns contract.
    An empty DataFrame with those columns is valid and returns zero counters.
    """
    missing = [column for column in REQUIRED_ANALYTIC_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Colonnes analytiques manquantes pour le rapport qualité: {missing}")

    duplicate_mask = df["ticket_id"].duplicated(keep=False)
    exact_mask = df["exact_duplicate"].fillna(False).astype(bool)
    return {
        "rows": len(df),
        "tickets": int(df["ticket_id"].notna().sum()),
        "unknown_clients": int(df["client_analytic"].isna().sum()),
        "unknown_problems": int(df["problem_analytic"].isna().sum()),
        "invalid_priorities": int(df["priority_analytic"].isna().sum()),
        "invalid_durations": int(df["resolution_minutes"].isna().sum()),
        "invalid_opened_at": int(df["opened_at"].isna().sum()),
        "invalid_resolved_at": int(df["resolved_at"].isna().sum()),
        "duplicate_ticket_ids_rows": int(duplicate_mask.sum()),
        "duplicate_ticket_ids_distinct": int(df.loc[duplicate_mask, "ticket_id"].nunique()),
        "exact_duplicate_rows": int(exact_mask.sum()),
        "exact_duplicate_distinct_records": int(df.loc[exact_mask, "ticket_pk"].nunique()),
    }
