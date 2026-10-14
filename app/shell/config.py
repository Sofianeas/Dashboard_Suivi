from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    title: str = "IRIS Dashboard Help Desk"
    version: str = "0.1.0"
