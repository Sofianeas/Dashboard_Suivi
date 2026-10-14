from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, FastAPI, HTTPException

from app.api.schemas import DashboardFilterParams
from app.dashboard.filters import DashboardFilters
from app.services.dashboard import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def get_service() -> DashboardService:
    return DashboardService()


def resolve_dashboard_filters(
    client: str | None = None,
    problem: str | None = None,
    priority: str | None = None,
    technician: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> DashboardFilters:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must be less than or equal to date_to.",
        )

    return DashboardFilterParams(
        client=client,
        problem=problem,
        priority=priority,
        technician=technician,
        date_from=date_from,
        date_to=date_to,
    ).to_domain()


@router.get("")
def dashboard(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_dashboard(filters)


@router.get("/kpi")
def kpi(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_kpi(filters)


@router.get("/clients")
def clients(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_clients(filters)


@router.get("/problems")
def problems(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_problems(filters)


@router.get("/priorities")
def priorities(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_priorities(filters)


@router.get("/technicians")
def technicians(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_technicians(filters)


@router.get("/temporal")
def temporal(
    filters: DashboardFilters = Depends(resolve_dashboard_filters),
    service: DashboardService = Depends(get_service),
):
    return service.get_temporal(filters)


def register_dashboard_routes(application: FastAPI) -> None:
    application.include_router(router)
