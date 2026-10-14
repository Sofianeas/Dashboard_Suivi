# ETL03 — Design PostgreSQL

## Schémas

- `raw` : données brutes chargées.
- `core` : données transformées et validées.
- `mart` : vues analytiques destinées au dashboard.

## MART attendu

- `mart.v_ticket_kpi`
- `mart.v_client_analysis`
- `mart.v_problem_analysis`
- `mart.v_priority_analysis`
- `mart.v_technician_analysis`
- `mart.v_temporal_analysis`

## Règles

Les règles métier ETL doivent être appliquées avant les agrégations.
Les vues MART ne doivent pas réinterpréter la durée H.

Note de récupération : le DDL SQL exact de la dernière version n'était pas
présent dans le ZIP survivant. Revalider contre un dump ou les fichiers SQL
originaux avant déploiement PostgreSQL.
