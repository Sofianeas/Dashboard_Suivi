from __future__ import annotations

import csv
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_DIR = PROJECT_ROOT / "data" / "reference_registry" / "data_007"

TICKET_COLUMNS = {
    "ticket_id",
    "message_evidence_rows",
    "data006_classification_recomputed",
    "analytical_reconciliation_status",
    "conflicting_or_ambiguous_evidence",
    "missing_analytic_fields",
}
LINK_COLUMNS = {
    "ticket_id",
    "message_event_id",
    "source_line",
    "timestamp_original",
    "sender_raw",
    "title_raw",
    "body_raw",
    "all_ticket_ids_in_message",
    "multiple_ticket_ids_in_message",
    "duration_like_text_not_validated",
    "status_like_text_not_validated",
}
MESSAGE_COLUMNS = {
    "event",
    "source_line",
    "timestamp_original",
    "sender",
    "title",
    "body",
}
AMBIGUITY_COLUMNS = {
    "ticket_id",
    "classification",
    "reason",
    "missing_or_unverified_fields",
}
REQUIRED_FILES = (
    "registre_tickets.csv",
    "registre_messages_tickets.csv",
    "messages_source.csv",
    "ambiguities_champs_absents.csv",
)
TICKET_ID_PATTERN = re.compile(r"P\d{9}")


class RegistryDataError(Exception):
    """The secondary registry is missing or fails its integrity checks."""


def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            if reader.fieldnames is None or not required_columns.issubset(
                reader.fieldnames
            ):
                raise RegistryDataError
            return list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        raise RegistryDataError from exc


@lru_cache(maxsize=1)
def _load_registry() -> dict[str, object]:
    try:
        manifest_path = REGISTRY_DIR / "SHA256SUMS.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected_hashes = manifest["files"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RegistryDataError from exc

    rows: dict[str, object] = {}
    for name in REQUIRED_FILES:
        path = REGISTRY_DIR / name
        expected_hash = expected_hashes.get(name)
        if not isinstance(expected_hash, dict):
            raise RegistryDataError
        expected_hash = expected_hash.get("sha256")
        if not isinstance(expected_hash, str):
            raise RegistryDataError
        try:
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        except OSError as exc:
            raise RegistryDataError from exc
        if actual_hash != expected_hash.upper():
            raise RegistryDataError

    try:
        tickets = _read_csv(REGISTRY_DIR / REQUIRED_FILES[0], TICKET_COLUMNS)
        links = _read_csv(REGISTRY_DIR / REQUIRED_FILES[1], LINK_COLUMNS)
        messages = _read_csv(REGISTRY_DIR / REQUIRED_FILES[2], MESSAGE_COLUMNS)
        ambiguities = _read_csv(REGISTRY_DIR / REQUIRED_FILES[3], AMBIGUITY_COLUMNS)
    except RegistryDataError:
        raise

    ticket_by_id: dict[str, dict[str, str]] = {}
    for ticket in tickets:
        ticket_id = ticket["ticket_id"]
        if not TICKET_ID_PATTERN.fullmatch(ticket_id) or ticket_id in ticket_by_id:
            raise RegistryDataError
        ticket_by_id[ticket_id] = ticket

    message_by_key: dict[tuple[str, str], dict[str, str]] = {}
    for message in messages:
        key = (message["event"], message["source_line"])
        if key in message_by_key:
            raise RegistryDataError
        message_by_key[key] = message

    links_by_ticket: dict[str, list[dict[str, str]]] = {}
    for link in links:
        key = (link["message_event_id"], link["source_line"])
        if link["ticket_id"] not in ticket_by_id or key not in message_by_key:
            raise RegistryDataError
        links_by_ticket.setdefault(link["ticket_id"], []).append(link)

    ambiguity_by_ticket: dict[str, dict[str, str]] = {}
    for ambiguity in ambiguities:
        ticket_id = ambiguity["ticket_id"]
        if ticket_id in ambiguity_by_ticket:
            raise RegistryDataError
        ambiguity_by_ticket[ticket_id] = ambiguity

    rows.update(
        tickets=ticket_by_id,
        links=links_by_ticket,
        messages=message_by_key,
        ambiguities=ambiguity_by_ticket,
    )
    return rows


def search_tickets(query: str, *, exact: bool = False, limit: int = 100) -> dict:
    registry = _load_registry()
    tickets = registry["tickets"]
    normalized_query = query.strip().casefold()
    matches = [
        row
        for ticket_id, row in tickets.items()
        if (
            ticket_id.casefold() == normalized_query
            if exact
            else normalized_query in ticket_id.casefold()
        )
    ]
    matches.sort(key=lambda row: row["ticket_id"])

    results = []
    for row in matches[:limit]:
        ticket_id = row["ticket_id"]
        ambiguity = registry["ambiguities"].get(ticket_id, {})
        results.append(
            {
                "ticket_id": ticket_id,
                "message_count": len(registry["links"].get(ticket_id, [])),
                "classification": row["data006_classification_recomputed"],
                "reconciliation_status": row["analytical_reconciliation_status"],
                "missing_fields": _split_fields(row["missing_analytic_fields"]),
                "ambiguity": (
                    ambiguity.get("reason")
                    or row["conflicting_or_ambiguous_evidence"]
                ),
            }
        )

    return {
        "query": query,
        "exact": exact,
        "total": len(matches),
        "truncated": len(matches) > limit,
        "results": results,
    }


def get_ticket_details(ticket_id: str) -> dict | None:
    registry = _load_registry()
    ticket = registry["tickets"].get(ticket_id)
    if ticket is None:
        return None

    ambiguity = registry["ambiguities"].get(ticket_id, {})
    messages = []
    for link in registry["links"].get(ticket_id, []):
        message = registry["messages"][
            (link["message_event_id"], link["source_line"])
        ]
        messages.append(
            {
                "event_id": link["message_event_id"],
                "source_line": link["source_line"],
                "timestamp": link["timestamp_original"],
                "timestamp_semantics": (
                    "Horodatage du message, pas une date de création du ticket."
                ),
                "sender": link["sender_raw"] or message["sender"],
                "title": link["title_raw"] or message["title"],
                "body": link["body_raw"] or message["body"],
                "linked_ticket_ids": link["all_ticket_ids_in_message"],
                "multiple_ticket_ids": (
                    link["multiple_ticket_ids_in_message"].casefold() == "true"
                ),
                "duration_text_unverified": link[
                    "duration_like_text_not_validated"
                ],
                "status_text_unverified": link["status_like_text_not_validated"],
            }
        )

    return {
        "ticket_id": ticket_id,
        "message_count": len(messages),
        "classification": ticket["data006_classification_recomputed"],
        "reconciliation_status": ticket["analytical_reconciliation_status"],
        "missing_fields": _split_fields(ticket["missing_analytic_fields"]),
        "ambiguity": (
            ambiguity.get("reason")
            or ticket["conflicting_or_ambiguous_evidence"]
        ),
        "messages": messages,
        "notice": (
            "Ces références proviennent de messages et ne sont pas des données "
            "métier vérifiées ni des indicateurs SLA."
        ),
    }


def _split_fields(value: str) -> list[str]:
    return [field for field in value.split(";") if field]
