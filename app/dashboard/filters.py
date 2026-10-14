from __future__ import annotations

from dataclasses import dataclass
from datetime import date

ALL_FILTER_VALUE = "ALL"


def normalize_dimension_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.casefold() == ALL_FILTER_VALUE.casefold():
        return None
    return normalized


@dataclass(frozen=True, slots=True)
class DashboardFilters:
    client: str | None = None
    problem: str | None = None
    priority: str | None = None
    technician: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "client", normalize_dimension_filter(self.client))
        object.__setattr__(self, "problem", normalize_dimension_filter(self.problem))
        object.__setattr__(self, "priority", normalize_dimension_filter(self.priority))
        object.__setattr__(self, "technician", normalize_dimension_filter(self.technician))
        if (
            self.date_from is not None
            and self.date_to is not None
            and self.date_from > self.date_to
        ):
            raise ValueError("date_from must be less than or equal to date_to.")

    @property
    def is_unfiltered(self) -> bool:
        return all(
            value is None
            for value in (
                self.client,
                self.problem,
                self.priority,
                self.technician,
                self.date_from,
                self.date_to,
            )
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "client": self.client,
            "problem": self.problem,
            "priority": self.priority,
            "technician": self.technician,
            "date_from": self.date_from,
            "date_to": self.date_to,
        }
