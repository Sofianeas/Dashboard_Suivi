from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

from app.api.reference_registry import register_reference_registry_routes
from app.api.routes import register_dashboard_routes

from .config import AppConfig


def register_routes(
    application: FastAPI,
    config: AppConfig,
    templates: Jinja2Templates,
) -> None:
    @application.get("/api/health")
    def health():
        return {"status": "ok"}

    @application.get("/", include_in_schema=False)
    def root(request: Request):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "request": request,
                "title": config.title,
                "version": config.version,
            },
        )

    register_dashboard_routes(application)
    register_reference_registry_routes(application)
