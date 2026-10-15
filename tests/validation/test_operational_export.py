
from pathlib import Path

import pandas as pd
import pytest

from src.ingestion.google_sheets import load_from_xlsx
from src.transformation.pipeline import transform_tickets


PROJECT_ROOT = Path(__file__).resolve().parents[2]
XLSX = PROJECT_ROOT / "data" / "raw" / "Suivi_HelpDesk1.xlsx"

pytestmark = pytest.mark.operational


@pytest.fixture
def operational_data():
    """Charge une copie fraîche de l'export pour chaque test."""
    if not XLSX.is_file():
        pytest.fail(f"Export opérationnel introuvable : {XLSX}")

    return load_from_xlsx(XLSX)


def test_current_export_dataset_contract(operational_data):
    tickets, clients, problems = operational_data
    result = transform_tickets(tickets, clients, problems)

    assert len(result) == 717
    assert result["ticket_id"].nunique() == 709
    assert result["exact_duplicate"].sum() == 4
    assert result["client_analytic"].isna().sum() == 13
    assert result["problem_analytic"].isna().sum() == 3
    assert result["priority_analytic"].isna().sum() == 0
    assert result["resolution_minutes"].notna().all()
    assert result["opened_at"].notna().sum() == 717
    assert result["resolved_at"].notna().sum() == 716
    assert set(result["priority_analytic"]) <= {
        "Basse", "Moyenne", "Haute"
    }
    assert set(result["technician_analytic"]) <= {
        "Loubna", "Sofiane Aoues"
    }


def test_reference_durations_override_only_the_two_known_tickets(
    operational_data,
):
    tickets, clients, problems = operational_data
    result = transform_tickets(
        tickets, clients, problems
    ).set_index("ticket_id")

    assert result.loc["P260604283", "resolution_minutes"] == 19
    assert result.loc["P260604317", "resolution_minutes"] == 21
    assert result.loc["P260604283", "resolution_minutes_raw"].hour == 16
    assert result.loc["P260604283", "resolution_minutes_raw"].minute == 0
    assert result.loc[
        "P260604283", "resolution_minutes_reference_raw"
    ] == 19
    assert result.loc[
        "P260604283", "resolution_minutes_origin"
    ] == "reference_column_j"
    assert result.loc[
        "P260604317", "resolution_minutes_origin"
    ] == "reference_column_j"
    assert result.loc[
        "P260604023", "resolution_minutes"
    ] == pytest.approx(41.233333)
    assert result.loc["P260604229", "resolution_minutes"] == 35
    assert result.loc["P260604268", "resolution_minutes"] == 30


def test_reference_duration_column_is_required_for_target_tickets(
    operational_data,
):
    tickets, clients, problems = operational_data
    tickets = tickets.drop(columns=["Temps de résolution (min)"])

    with pytest.raises(
        ValueError, match="Colonne de référence des durées absente"
    ):
        transform_tickets(tickets, clients, problems)


def test_ticket_business_override_preserves_raw_data_and_does_not_change_other_installations(
    operational_data,
):
    tickets, clients, problems = operational_data
    result = transform_tickets(
        tickets, clients, problems
    ).set_index("ticket_id")

    target = result.loc["P260904149"]

    assert target["client_raw"] == "L'addition"
    assert target["client_analytic"] == "L'addition"
    assert target["problem_raw"] == "Installation"
    assert target["problem_analytic"] == "Installation/Formation"
    assert target["resolution_minutes_raw"] == "3min"
    assert pd.isna(target["resolution_minutes_reference_raw"])
    assert target["resolution_minutes"] == 4
    assert target["resolution_minutes_origin"] == "business_validated"
    assert target["business_decision"] == (
        "Validation métier : L'addition / Installation/Formation / 4 min"
    )
    assert str(target["ticket_date"].date()) == "2026-09-17"
    assert (
        target["opened_at"].strftime("%Y-%m-%d %H:%M:%S")
        == "2026-09-17 15:00:00"
    )
    assert (
        target["resolved_at"].strftime("%Y-%m-%d %H:%M:%S")
        == "2026-09-17 15:03:00"
    )
    assert target["priority_analytic"] == "Basse"

    assert result["business_decision"].notna().sum() == 1
    assert (
        result["resolution_minutes_origin"]
        .eq("business_validated")
        .sum()
        == 1
    )

    unrelated_installation = result.loc["P260604398"]

    assert unrelated_installation["client_analytic"] == "ADOPT"
    assert unrelated_installation["problem_analytic"] == "Installation"
    assert unrelated_installation["resolution_minutes"] == 5
    assert (
        unrelated_installation["resolution_minutes_origin"] == "explicit"
    )


@pytest.mark.parametrize("invalid_value", [None, "invalid"])
def test_invalid_reference_duration_raises_for_target_ticket(
    operational_data, invalid_value
):
    tickets, clients, problems = operational_data
    tickets["Temps de résolution (min)"] = (
        tickets["Temps de résolution (min)"].astype(object)
    )

    target_row = (
        tickets["N° Ticket"].astype(str).str.strip().eq("P260604283")
    )
    tickets.loc[
        target_row, "Temps de résolution (min)"
    ] = invalid_value

    with pytest.raises(
        ValueError,
        match="Référence de durée en minutes invalide.*P260604283",
    ):
        transform_tickets(tickets, clients, problems)
