from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from app.dashboard.filters import DashboardFilters


class DashboardFilterParams(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    client: str | None = None
    problem: str | None = None
    priority: str | None = None
    technician: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError(
                "date_from must be less than or equal to date_to."
            )
        return self

    def to_domain(self) -> DashboardFilters:
        return DashboardFilters(
            client=self.client,
            problem=self.problem,
            priority=self.priority,
            technician=self.technician,
            date_from=self.date_from,
            date_to=self.date_to,
        )


class DashboardKPI(BaseModel):
    ticket_count: int
    mean_resolution_minutes: float | None
    median_resolution_minutes: float | None


class ClientAnalysis(BaseModel):
    client: str
    ticket_count: int
    mean_resolution_minutes: float | None


class ProblemAnalysis(BaseModel):
    problem: str
    ticket_count: int
    mean_resolution_minutes: float | None


class PriorityAnalysis(BaseModel):
    priority: str
    ticket_count: int
    mean_resolution_minutes: float | None


class TechnicianAnalysis(BaseModel):
    technician: str
    ticket_count: int
    mean_resolution_minutes: float | None


class TemporalAnalysis(BaseModel):
    period: str
    ticket_count: int
    mean_resolution_minutes: float | None


class DashboardResponse(BaseModel):
    kpi: DashboardKPI
    clients: list[ClientAnalysis]
    problems: list[ProblemAnalysis]
    priorities: list[PriorityAnalysis]
    technicians: list[TechnicianAnalysis]
    temporal: list[TemporalAnalysis]
