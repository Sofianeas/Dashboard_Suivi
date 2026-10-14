
from __future__ import annotations

import csv
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.repositories import reference_registry
from main import app



@pytest.fixture
def synthetic_registry(tmp_path, monkeypatch):
    """Construit un registre fictif et isolé pour les tests."""
    registry_dir = tmp_path / "data_007"
    registry_dir.mkdir()

    datasets = {
        "registre_tickets.csv": (
            [
                "ticket_id",
                "message_evidence_rows",
                "data006_classification_recomputed",
                "analytical_reconciliation_status",
                "conflicting_or_ambiguous_evidence",
                "missing_analytic_fields",
            ],
            [
                {
                    "ticket_id": "P123456789",
                    "message_evidence_rows": "1",
                    "data006_classification_recomputed": "B",
                    "analytical_reconciliation_status": "synthetic_test",
                    "conflicting_or_ambiguous_evidence": "",
                    "missing_analytic_fields": "ticket_date",
                },
                {
                    "ticket_id": "P123456788",
                    "message_evidence_rows": "0",
                    "data006_classification_recomputed": "A",
                    "analytical_reconciliation_status": "synthetic_test",
                    "conflicting_or_ambiguous_evidence": "",
                    "missing_analytic_fields": "",
                },
            ],
        ),
        "registre_messages_tickets.csv": (
            [
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
            ],
            [
                {
                    "ticket_id": "P123456789",
                    "message_event_id": "2",
                    "source_line": "10",
                    "timestamp_original": "2026-01-15 10:30",
                    "sender_raw": "Expéditeur fictif",
                    "title_raw": "Message de test synthétique",
                    "body_raw": "Contenu fictif réservé aux tests.",
                    "all_ticket_ids_in_message": "P123456789",
                    "multiple_ticket_ids_in_message": "false",
                    "duration_like_text_not_validated": "",
                    "status_like_text_not_validated": "",
                }
            ],
        ),
        "messages_source.csv": (
            [
                "event",
                "source_line",
                "timestamp_original",
                "sender",
                "title",
                "body",
            ],
            [
                {
                    "event": "2",
                    "source_line": "10",
                    "timestamp_original": "2026-01-15 10:30",
                    "sender": "Expéditeur fictif",
                    "title": "Message de test synthétique",
                    "body": "Contenu fictif réservé aux tests.",
                }
            ],
        ),
        "ambiguities_champs_absents.csv": (
            [
                "ticket_id",
                "classification",
                "reason",
                "missing_or_unverified_fields",
            ],
            [],
        ),
    }

    hashes = {}

    for filename, (columns, rows) in datasets.items():
        path = registry_dir / filename

        with path.open(
            "w", encoding="utf-8-sig", newline=""
        ) as destination:
            writer = csv.DictWriter(
                destination,
                fieldnames=columns,
                lineterminator="\n",
            )
            writer.writeheader()
            writer.writerows(rows)

        hashes[filename] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest().upper()
        }

    manifest = {"files": hashes}
    (registry_dir / "SHA256SUMS.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        reference_registry, "REGISTRY_DIR", registry_dir
    )
    reference_registry._load_registry.cache_clear()

    try:
        yield registry_dir
    finally:
        reference_registry._load_registry.cache_clear()


client = TestClient(app)



def test_registry_exact_search_returns_summary_without_sla_data(
    synthetic_registry,
):
    response = client.get(
        "/api/reference-registry",
        params={"q": "P123456789", "exact": "true"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["results"][0]["ticket_id"] == "P123456789"
    assert payload["results"][0]["message_count"] == 1
    assert payload["results"][0]["classification"] == "B"
    assert "ticket_date" in payload["results"][0]["missing_fields"]




def test_registry_partial_search_and_message_details_are_source_qualified(
    synthetic_registry,
):
    search = client.get(
        "/api/reference-registry",
        params={"q": "P12345678", "exact": "false"},
    )

    assert search.status_code == 200
    assert search.json()["total"] == 2
    assert all(
        result["ticket_id"].startswith("P12345678")
        for result in search.json()["results"]
    )

    detail = client.get("/api/reference-registry/P123456789")

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["ticket_id"] == "P123456789"
    assert payload["message_count"] == 1
    assert payload["messages"][0]["event_id"] == "2"
    assert payload["messages"][0]["source_line"] == "10"
    assert payload["messages"][0]["timestamp"] == "2026-01-15 10:30"
    assert "pas une date de création" in (
        payload["messages"][0]["timestamp_semantics"]
    )
    assert payload["messages"][0]["title"] == "Message de test synthétique"
    assert "ne sont pas des données métier vérifiées" in payload["notice"]



def test_registry_search_handles_empty_results_and_invalid_requests():
    empty = client.get(
        "/api/reference-registry",
        params={"q": "P269999999", "exact": "true"},
    )
    missing = client.get("/api/reference-registry/P269999999")
    empty_query = client.get("/api/reference-registry", params={"q": ""})
    invalid_id = client.get("/api/reference-registry/not-a-ticket")

    assert empty.status_code == 200
    assert empty.json()["total"] == 0
    assert empty.json()["results"] == []
    assert missing.status_code == 404
    assert empty_query.status_code == 422
    assert invalid_id.status_code == 422


def test_registry_reports_unavailable_data_without_exposing_file_paths(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(reference_registry, "REGISTRY_DIR", tmp_path)
    reference_registry._load_registry.cache_clear()

    response = client.get(
        "/api/reference-registry",
        params={"q": "P260904012"},
    )

    reference_registry._load_registry.cache_clear()
    assert response.status_code == 503
    assert "momentanément indisponible" in response.json()["detail"]
    assert str(tmp_path) not in response.text


def test_dashboard_page_exposes_separate_reference_registry_navigation():
    response = client.get("/")

    assert response.status_code == 200
    assert 'data-app-view="reference-registry"' in response.text
    assert 'id="reference-registry-view"' in response.text
    assert "Hors indicateurs SLA" in response.text
