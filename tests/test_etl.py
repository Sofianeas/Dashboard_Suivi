
import pandas as pd
import pytest

from src.transformation import pipeline
from src.transformation.dates import parse_datetime
from src.transformation.durations import parse_duration_minutes
from src.transformation.pipeline import transform_tickets


REFERENCE_TICKET = "P111111111"
BUSINESS_TICKET = "P222222222"
STANDARD_TICKET = "P333333333"


def make_ticket(
    ticket_id,
    *,
    client="CLIENT TEST",
    problem="Incident",
    priority="Moyenne",
    opened="23/06/2026 à 9h40",
    resolved="23/06/2026 à 10h00",
    duration="20min",
    reference_duration=None,
    technician="Sofiane Aoues",
):
    """Construit une ligne de ticket entièrement fictive."""
    return {
        "Date du ticket": "23/06/2026",
        "N° Ticket": ticket_id,
        "Client": client,
        "Problématique": problem,
        "Priorité": priority,
        "Date/Heure ouverture": opened,
        "Date/Heure résolution": resolved,
        "Temps de résolution (h)": duration,
        "Temps de résolution (min)": reference_duration,
        "Technicien": technician,
    }


@pytest.fixture
def synthetic_etl_data(monkeypatch):
    """Prépare des données synthétiques sans lire de fichier opérationnel."""
    monkeypatch.setattr(
        pipeline,
        "REFERENCE_DURATION_TICKETS",
        {REFERENCE_TICKET},
    )

    monkeypatch.setattr(
        pipeline,
        "BUSINESS_OVERRIDES",
        {
            BUSINESS_TICKET: {
                "client_analytic": "CLIENT TEST",
                "problem_analytic": "Installation/Formation",
                "resolution_minutes": 4.0,
                "business_decision": (
                    "Validation métier synthétique : 4 min"
                ),
            }
        },
    )

    tickets = pd.DataFrame(
        [
            make_ticket(
                REFERENCE_TICKET,
                duration="99min",
                reference_duration=19,
            ),
            make_ticket(
                BUSINESS_TICKET,
                client="CLIENT TEST",
                problem="Installation",
                duration="3min",
                opened="23/06/2026 à 15h00",
                resolved="23/06/2026 à 15h03",
            ),
            make_ticket(
                STANDARD_TICKET,
                client="CLIENT TEST",
                problem="Installation",
                duration="5min",
                opened="23/06/2026 à 11h00",
                resolved="23/06/2026 à 11h05",
            ),
        ]
    )

    clients = pd.DataFrame(
        [
            {
                "client_source_normalized": "CLIENT TEST",
                "client_analytic": "CLIENT TEST",
            }
        ]
    )

    problems = pd.DataFrame(
        [
            {
                "problem_source": "Incident",
                "problem_analytic": "Incident",
            },
            {
                "problem_source": "Installation",
                "problem_analytic": "Installation",
            },
        ]
    )

    return tickets, clients, problems


def test_duration_formats():
    assert parse_duration_minutes("0h19min") == 19
    assert parse_duration_minutes("41:14:00") == 2474
    assert parse_duration_minutes("15:18min") == 15
    assert parse_duration_minutes("6MIN") == 6


def test_date_formats():
    assert parse_datetime("23/06/2026 à 9h40").hour == 9
    assert parse_datetime("23/06/2026 à 10:44").minute == 44


def test_reference_duration_overrides_raw_duration(synthetic_etl_data):
    tickets, clients, problems = synthetic_etl_data

    result = transform_tickets(
        tickets, clients, problems
    ).set_index("ticket_id")

    assert result.loc[REFERENCE_TICKET, "resolution_minutes"] == 19
    assert result.loc[REFERENCE_TICKET, "resolution_minutes_raw"] == "99min"
    assert (
        result.loc[REFERENCE_TICKET, "resolution_minutes_reference_raw"]
        == 19
    )
    assert (
        result.loc[REFERENCE_TICKET, "resolution_minutes_origin"]
        == "reference_column_j"
    )


def test_business_override_preserves_raw_data(synthetic_etl_data):
    tickets, clients, problems = synthetic_etl_data

    result = transform_tickets(
        tickets, clients, problems
    ).set_index("ticket_id")

    target = result.loc[BUSINESS_TICKET]

    assert target["client_raw"] == "CLIENT TEST"
    assert target["problem_raw"] == "Installation"
    assert target["problem_analytic"] == "Installation/Formation"
    assert target["resolution_minutes_raw"] == "3min"
    assert target["resolution_minutes"] == 4
    assert target["resolution_minutes_origin"] == "business_validated"
    assert target["business_decision"] == (
        "Validation métier synthétique : 4 min"
    )

    unrelated = result.loc[STANDARD_TICKET]

    assert unrelated["problem_analytic"] == "Installation"
    assert unrelated["resolution_minutes"] == 5
    assert unrelated["resolution_minutes_origin"] == "explicit"


def test_reference_duration_column_is_required_for_target_ticket(
    synthetic_etl_data,
):
    tickets, clients, problems = synthetic_etl_data
    tickets = tickets.drop(columns=["Temps de résolution (min)"])

    with pytest.raises(
        ValueError,
        match="Colonne de référence des durées absente",
    ):
        transform_tickets(tickets, clients, problems)


@pytest.mark.parametrize("invalid_value", [None, "invalid", -1, float("inf")])
def test_invalid_reference_duration_raises(
    synthetic_etl_data,
    invalid_value,
):
    tickets, clients, problems = synthetic_etl_data

    tickets["Temps de résolution (min)"] = (
        tickets["Temps de résolution (min)"].astype(object)
    )

    target_row = tickets["N° Ticket"].eq(REFERENCE_TICKET)
    tickets.loc[target_row, "Temps de résolution (min)"] = invalid_value

    with pytest.raises(
        ValueError,
        match="Référence de durée en minutes invalide",
    ):
        transform_tickets(tickets, clients, problems)
