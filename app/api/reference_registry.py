from __future__ import annotations

import logging

from fastapi import APIRouter, FastAPI, HTTPException, Path, Query

from app.repositories.reference_registry import (
    RegistryDataError,
    get_ticket_details,
    search_tickets,
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reference-registry", tags=["reference-registry"])


def _registry_unavailable() -> HTTPException:
    logger.exception("Secondary ticket reference registry is unavailable.")
    return HTTPException(
        status_code=503,
        detail=(
            "Le registre secondaire est momentanément indisponible. "
            "Réessayez plus tard."
        ),
    )


@router.get("")
def search_reference_tickets(
    q: str = Query(min_length=1, max_length=32),
    exact: bool = False,
    limit: int = Query(default=100, ge=1, le=100),
):
    try:
        return search_tickets(q, exact=exact, limit=limit)
    except RegistryDataError:
        raise _registry_unavailable() from None


@router.get("/{ticket_id}")
def reference_ticket(
    ticket_id: str = Path(pattern=r"^P\d{9}$"),
):
    try:
        result = get_ticket_details(ticket_id)
    except RegistryDataError:
        raise _registry_unavailable() from None
    if result is None:
        raise HTTPException(status_code=404, detail="Identifiant introuvable.")
    return result


def register_reference_registry_routes(application: FastAPI) -> None:
    application.include_router(router)
