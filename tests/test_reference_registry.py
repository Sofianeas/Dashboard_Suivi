from __future__ import annotations

from fastapi.testclient import TestClient

from app.repositories import reference_registry
from main import app


client = TestClient(app)


def test_registry_exact_search_returns_summary_without_sla_data():
    response = client.get(
        "/api/reference-registry",
        params={"q": "P260904012", "exact": "true"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["results"][0]["ticket_id"] == "P260904012"
    assert payload["results"][0]["message_count"] == 1
    assert payload["results"][0]["classification"] == "B"
    assert "ticket_date" in payload["results"][0]["missing_fields"]


def test_registry_partial_search_and_message_details_are_source_qualified():
    search = client.get(
        "/api/reference-registry",
        params={"q": "P2609040", "exact": "false"},
    )

    assert search.status_code == 200
    assert search.json()["total"] > 1
    assert all(
        result["ticket_id"].startswith("P2609040")
        for result in search.json()["results"]
    )

    detail = client.get("/api/reference-registry/P260904012")

    assert detail.status_code == 200
    payload = detail.json()
    assert payload["ticket_id"] == "P260904012"
    assert payload["message_count"] == 1
    assert payload["messages"][0]["event_id"] == "2"
    assert payload["messages"][0]["source_line"] == "10"
    assert payload["messages"][0]["timestamp"] == "17/09 2:54 PM"
    assert "pas une date de création" in payload["messages"][0][
        "timestamp_semantics"
    ]
    assert "Swap transporteur Etam" in payload["messages"][0]["title"]
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
