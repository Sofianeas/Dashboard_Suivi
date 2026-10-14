from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .config import AppConfig
from .routes import register_routes


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class WebApplication:
    def __init__(self, config: AppConfig | None = None):
        self.config = config or AppConfig()

    def create(self) -> FastAPI:
        application = FastAPI(
            title=self.config.title,
            version=self.config.version,
        )

        application.mount(
            "/static",
            StaticFiles(directory=PROJECT_ROOT / "app" / "static"),
            name="static",
        )

        templates = Jinja2Templates(directory=PROJECT_ROOT / "app" / "templates")
        register_routes(
            application,
            self.config,
            templates,
        )
        return application
