from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.dashboard.filters import DashboardFilters


_DEFAULT_CSV_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "processed"
    / "tickets_v1.csv"
)


class DashboardRepository:
    """Recovery implementation backed by the validated ETL CSV.

    The historical project used PostgreSQL/MART views. This repository keeps
    the recovered package usable even when PostgreSQL has not yet been
    restored; the database layer can be reconnected without changing the
    API contract.
    """

    def __init__(self, csv_path: str | Path = _DEFAULT_CSV_PATH):
        self.csv_path = Path(csv_path)
        self._df = pd.read_csv(self.csv_path)

    def _filtered(self, filters: DashboardFilters) -> pd.DataFrame:
        df = self._df.copy()
        df = df[df["exact_duplicate"].astype(bool) == False]  # noqa: E712

        if filters.client is not None:
            df = df[df["client_analytic"] == filters.client]
        if filters.problem is not None:
            df = df[df["problem_analytic"] == filters.problem]
        if filters.priority is not None:
            df = df[df["priority_analytic"] == filters.priority]
        if filters.technician is not None:
            df = df[df["technician_analytic"] == filters.technician]

        if filters.date_from is not None or filters.date_to is not None:
            dates = pd.to_datetime(df["ticket_date"], errors="coerce").dt.date
            if filters.date_from is not None:
                df = df[dates >= filters.date_from]
            if filters.date_to is not None:
                df = df[dates <= filters.date_to]

        return df

    @staticmethod
    def _stats(df: pd.DataFrame) -> dict[str, object]:
        values = pd.to_numeric(df["resolution_minutes"], errors="coerce").dropna()
        return {
            "ticket_count": int(len(df)),
            "mean_resolution_minutes": (
                float(values.mean()) if not values.empty else None
            ),
            "median_resolution_minutes": (
                float(values.median()) if not values.empty else None
            ),
        }

    def get_kpi(self, filters: DashboardFilters) -> dict[str, object]:
        return self._stats(self._filtered(filters))

    def _group(self, df, column, output_name):
        if df.empty:
            return []
        grouped = (
            df.groupby(column, dropna=False)["resolution_minutes"]
            .agg(["count", "mean"])
            .reset_index()
        )
        return [
            {
                output_name: row[column],
                "ticket_count": int(row["count"]),
                "mean_resolution_minutes": (
                    float(row["mean"]) if pd.notna(row["mean"]) else None
                ),
            }
            for _, row in grouped.iterrows()
            if pd.notna(row[column])
        ]

    def get_clients(self, filters):
        return self._group(self._filtered(filters), "client_analytic", "client")

    def get_problems(self, filters):
        return self._group(self._filtered(filters), "problem_analytic", "problem")

    def get_priorities(self, filters):
        return self._group(self._filtered(filters), "priority_analytic", "priority")

    def get_technicians(self, filters):
        return self._group(self._filtered(filters), "technician_analytic", "technician")

    def get_temporal(self, filters):
        df = self._filtered(filters)
        if df.empty:
            return []
        grouped = (
            df.assign(period=df["ticket_date"].astype(str))
            .groupby("period")["resolution_minutes"]
            .agg(["count", "mean"])
            .reset_index()
        )
        return [
            {
                "period": row["period"],
                "ticket_count": int(row["count"]),
                "mean_resolution_minutes": (
                    float(row["mean"]) if pd.notna(row["mean"]) else None
                ),
            }
            for _, row in grouped.iterrows()
        ]
