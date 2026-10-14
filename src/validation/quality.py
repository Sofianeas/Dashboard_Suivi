"""Contrôles qualité du dataset analytique."""
from __future__ import annotations
import pandas as pd


def quality_report(df: pd.DataFrame) -> dict[str, object]:
    return {
        "rows": len(df),
        "tickets": int(df["ticket_id"].notna().sum()),
        "unknown_clients": int(df["client_analytic"].isna().sum()),
        "unknown_problems": int(df["problem_analytic"].isna().sum()),
        "invalid_priorities": int(df["priority_analytic"].isna().sum()),
        "invalid_durations": int(df["resolution_minutes"].isna().sum()),
        "invalid_opened_at": int(df["opened_at"].isna().sum()),
        "invalid_resolved_at": int(df["resolved_at"].isna().sum()),
        "duplicate_ticket_ids_rows": int(df["ticket_id"].duplicated(keep=False).sum()),
        "duplicate_ticket_ids_distinct": int(df.loc[df["ticket_id"].duplicated(keep=False), "ticket_id"].nunique()),
        "exact_duplicate_rows": int(df["exact_duplicate"].sum()),
        "exact_duplicate_distinct_records": int(df.loc[df["exact_duplicate"], "ticket_pk"].nunique()),
    }
