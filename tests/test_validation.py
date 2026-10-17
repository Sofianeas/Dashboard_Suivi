import pandas as pd
import pytest

from src.validation.schema import REQUIRED_SOURCE_COLUMNS, validate_source_schema
from src.validation.quality import quality_report
from src.validation.duplicates import duplicate_ticket_ids


def make_analytic(rows=None):
    data = {
        "ticket_id": [], "client_analytic": [], "problem_analytic": [],
        "priority_analytic": [], "resolution_minutes": [], "opened_at": [],
        "resolved_at": [], "exact_duplicate": [], "ticket_pk": [],
    }
    if rows:
        for row in rows:
            for key in data:
                data[key].append(row.get(key))
    return pd.DataFrame(data)


def test_schema_accepts_required_headers():
    validate_source_schema(REQUIRED_SOURCE_COLUMNS)


def test_schema_accepts_reordered_and_additional_headers():
    validate_source_schema(["extra", *reversed(REQUIRED_SOURCE_COLUMNS)])


def test_schema_reports_all_missing_headers():
    with pytest.raises(ValueError) as exc:
        validate_source_schema(["N° Ticket", "Client"])
    message = str(exc.value)
    assert "Date du ticket" in message
    assert "Technicien" in message


def test_quality_report_empty_frame_with_contract_returns_zero_counters():
    report = quality_report(make_analytic())
    assert report["rows"] == 0
    assert report["tickets"] == 0
    assert report["duplicate_ticket_ids_rows"] == 0
    assert report["exact_duplicate_rows"] == 0


def test_quality_report_counts_collisions_and_quality_anomalies():
    frame = make_analytic([
        {"ticket_id": "P1", "client_analytic": None, "problem_analytic": "Incident",
         "priority_analytic": "Haute", "resolution_minutes": 10, "opened_at": "2026-01-01",
         "resolved_at": "2026-01-01", "exact_duplicate": True, "ticket_pk": "pk-a"},
        {"ticket_id": "P1", "client_analytic": "Client A", "problem_analytic": None,
         "priority_analytic": None, "resolution_minutes": None, "opened_at": None,
         "resolved_at": None, "exact_duplicate": True, "ticket_pk": "pk-b"},
        {"ticket_id": "P2", "client_analytic": "Client A", "problem_analytic": "Incident",
         "priority_analytic": "Basse", "resolution_minutes": 5, "opened_at": "2026-01-02",
         "resolved_at": "2026-01-02", "exact_duplicate": False, "ticket_pk": "pk-c"},
    ])
    report = quality_report(frame)
    assert report == {
        "rows": 3, "tickets": 3, "unknown_clients": 1, "unknown_problems": 1,
        "invalid_priorities": 1, "invalid_durations": 1, "invalid_opened_at": 1,
        "invalid_resolved_at": 1, "duplicate_ticket_ids_rows": 2,
        "duplicate_ticket_ids_distinct": 1, "exact_duplicate_rows": 2,
        "exact_duplicate_distinct_records": 2,
    }


def test_quality_report_rejects_incomplete_analytic_schema_explicitly():
    with pytest.raises(ValueError, match="Colonnes analytiques manquantes"):
        quality_report(pd.DataFrame({"ticket_id": []}))


def test_duplicate_ticket_ids_returns_all_colliding_rows_without_mutation():
    frame = pd.DataFrame({"ticket_id": ["P1", "P1", "P2", "P3", "P3", "P3"],
                          "value": [1, 2, 3, 4, 5, 6]})
    before = frame.copy(deep=True)
    result = duplicate_ticket_ids(frame)
    assert result.index.tolist() == [0, 1, 3, 4, 5]
    pd.testing.assert_frame_equal(frame, before)
    assert list(result.columns) == list(frame.columns)


def test_duplicate_ticket_ids_returns_empty_frame_with_columns():
    frame = pd.DataFrame({"ticket_id": ["P1", "P2"], "value": [1, 2]})
    result = duplicate_ticket_ids(frame)
    assert result.empty
    assert list(result.columns) == list(frame.columns)


def test_duplicate_ticket_ids_current_pandas_null_behavior_is_characterized():
    frame = pd.DataFrame({"ticket_id": [None, None, "P1"], "value": [1, 2, 3]})
    result = duplicate_ticket_ids(frame)
    assert result.index.tolist() == [0, 1]
