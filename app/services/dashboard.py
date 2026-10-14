from __future__ import annotations

from app.dashboard.filters import DashboardFilters
from app.repositories.dashboard import DashboardRepository


class DashboardService:
    def __init__(self, repository: DashboardRepository | None = None):
        self.repository = repository or DashboardRepository()

    def get_kpi(self, filters: DashboardFilters):
        return self.repository.get_kpi(filters)

    def get_clients(self, filters: DashboardFilters):
        return self.repository.get_clients(filters)

    def get_problems(self, filters: DashboardFilters):
        return self.repository.get_problems(filters)

    def get_priorities(self, filters: DashboardFilters):
        return self.repository.get_priorities(filters)

    def get_technicians(self, filters: DashboardFilters):
        return self.repository.get_technicians(filters)

    def get_temporal(self, filters: DashboardFilters):
        return self.repository.get_temporal(filters)

    def get_dashboard(self, filters: DashboardFilters):
        return {
            "kpi": self.get_kpi(filters),
            "clients": self.get_clients(filters),
            "problems": self.get_problems(filters),
            "priorities": self.get_priorities(filters),
            "technicians": self.get_technicians(filters),
            "temporal": self.get_temporal(filters),
        }
