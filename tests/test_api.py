from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.api.routes import get_service
from app.dashboard.filters import DashboardFilters
from app.repositories.dashboard import DashboardRepository
from app.services.dashboard import DashboardService
from main import app


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATION_CSV = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "validation"
    / "new-export-20261010"
    / "tickets_new_export.csv"
)


def _reference_kpi(frame: pd.DataFrame) -> dict[str, int | float | None]:
    retained = frame.loc[~frame["exact_duplicate"].astype(bool)]
    durations = pd.to_numeric(
        retained["resolution_minutes"], errors="coerce"
    ).dropna()
    return {
        "ticket_count": len(retained),
        "mean_resolution_minutes": (
            float(durations.mean()) if not durations.empty else None
        ),
        "median_resolution_minutes": (
            float(durations.median()) if not durations.empty else None
        ),
    }


@pytest.fixture
def dashboard_client():
    if not VALIDATION_CSV.is_file():
        pytest.fail(f"Validation CSV not found: {VALIDATION_CSV}")

    service = DashboardService(DashboardRepository(VALIDATION_CSV))
    app.dependency_overrides[get_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.pop(get_service, None)


def test_dashboard_page_renders_interactive_results_surface(dashboard_client):
    client, _ = dashboard_client

    response = client.get("/")

    assert response.status_code == 200
    assert "Dashboard en construction" not in response.text
    for element_id in (
        "filter-client",
        "filter-problem",
        "filter-priority",
        "filter-technician",
        "filter-date-from",
        "filter-date-to",
        "kpi-ticket-count",
        "kpi-resolution-mean",
        "kpi-resolution-median",
        "chart-temporal",
        "chart-clients",
        "chart-problems",
        "chart-priorities",
        "chart-technicians",
        "dashboard-retry",
        "filter-catalog-status",
        "filter-catalog-retry",
    ):
        assert f'id="{element_id}"' in response.text
    for filter_id in (
        "filter-client",
        "filter-problem",
        "filter-priority",
        "filter-technician",
    ):
        assert f'id="{filter_id}" disabled' in response.text


def test_http_global_kpi_matches_service_and_independent_calculation(
    dashboard_client,
):
    client, service = dashboard_client
    frame = pd.read_csv(VALIDATION_CSV)
    expected = _reference_kpi(frame)

    response = client.get("/api/dashboard/kpi")

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json() == service.get_kpi(DashboardFilters())


def test_http_high_priority_kpi_matches_service_and_independent_calculation(
    dashboard_client,
):
    client, service = dashboard_client
    frame = pd.read_csv(VALIDATION_CSV)
    high_priority = frame.loc[frame["priority_analytic"].eq("Haute")]
    expected = _reference_kpi(high_priority)

    response = client.get("/api/dashboard/kpi", params={"priority": "Haute"})

    assert response.status_code == 200
    assert response.json() == expected
    assert response.json() == service.get_kpi(DashboardFilters(priority="Haute"))


def test_http_dashboard_combines_dimension_and_date_filters(dashboard_client):
    client, service = dashboard_client
    frame = pd.read_csv(VALIDATION_CSV)
    candidates = frame.loc[
        ~frame["exact_duplicate"].astype(bool)
        & frame["client_analytic"].notna()
        & frame["problem_analytic"].notna()
        & frame["priority_analytic"].notna()
        & frame["technician_analytic"].notna()
        & frame["ticket_date"].notna()
    ]
    row = candidates.iloc[0]
    selected_date = date.fromisoformat(str(row["ticket_date"]))
    filters = DashboardFilters(
        client=row["client_analytic"],
        problem=row["problem_analytic"],
        priority=row["priority_analytic"],
        technician=row["technician_analytic"],
        date_from=selected_date,
        date_to=selected_date,
    )

    response = client.get(
        "/api/dashboard/kpi",
        params={
            "client": filters.client,
            "problem": filters.problem,
            "priority": filters.priority,
            "technician": filters.technician,
            "date_from": selected_date.isoformat(),
            "date_to": selected_date.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json() == service.get_kpi(filters)


def test_http_date_range_filter_accepts_valid_and_equal_bounds(dashboard_client):
    client, _ = dashboard_client

    valid_range = client.get(
        "/api/dashboard/kpi",
        params={"date_from": "2026-06-01", "date_to": "2026-06-30"},
    )
    equal_bounds = client.get(
        "/api/dashboard/kpi",
        params={"date_from": "2026-06-01", "date_to": "2026-06-01"},
    )

    assert valid_range.status_code == 200
    assert equal_bounds.status_code == 200


def test_http_date_range_filter_rejects_reversed_bounds_with_422(
    dashboard_client,
):
    client, _ = dashboard_client

    response = client.get(
        "/api/dashboard/kpi",
        params={"date_from": "2026-06-30", "date_to": "2026-06-01"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "date_from must be less than or equal to date_to."
    )


def test_http_date_range_filter_rejects_malformed_date_with_422(
    dashboard_client,
):
    client, _ = dashboard_client

    response = client.get(
        "/api/dashboard/kpi",
        params={"date_from": "not-a-date"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]


def test_http_dashboard_keeps_invalid_resolution_date_and_unmapped_rows_in_global_kpi(
    dashboard_client,
):
    client, service = dashboard_client
    frame = pd.read_csv(VALIDATION_CSV)
    retained = frame.loc[~frame["exact_duplicate"].astype(bool)]
    target = retained.loc[retained["ticket_id"].eq("P260701627")]
    unknown_clients = retained.loc[retained["client_analytic"].isna()]
    unknown_problems = retained.loc[retained["problem_analytic"].isna()]
    expected_client_group_count = int(
        retained.loc[retained["client_analytic"].notna(), "resolution_minutes"]
        .count()
    )
    expected_problem_group_count = int(
        retained.loc[retained["problem_analytic"].notna(), "resolution_minutes"]
        .count()
    )

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    body = response.json()
    invalid_resolution = target.loc[target["resolved_at"].isna()]
    assert len(target) == 2
    assert len(invalid_resolution) == 1
    assert invalid_resolution.iloc[0]["ticket_id"] == "P260701627"
    assert body["kpi"] == _reference_kpi(frame)
    assert body["kpi"] == service.get_dashboard(DashboardFilters())["kpi"]
    assert body["kpi"]["ticket_count"] == len(retained)
    assert len(unknown_clients) == 14
    assert len(unknown_problems) == 3
    assert sum(row["ticket_count"] for row in body["clients"]) == (
        expected_client_group_count
    )
    assert sum(row["ticket_count"] for row in body["problems"]) == (
        expected_problem_group_count
    )
    assert body == service.get_dashboard(DashboardFilters())
