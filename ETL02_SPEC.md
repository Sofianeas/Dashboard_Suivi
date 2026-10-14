# ETL02 — Spécification fonctionnelle synthétique

## Filtres

- Client
- Problème
- Priorité
- Technicien
- Date de début
- Date de fin

## Contrat HTTP

Les noms frontend `dateFrom` et `dateTo` sont transformés en
`date_from` et `date_to`.

Les valeurs `ALL`, vides et nulles sont omises de la query string.

Exemple :

`/api/dashboard/kpi?client=ETAM&priority=P1&date_from=2026-08-01`

## Réponses sans données

Un filtre sans résultat doit produire des KPI à zéro et des tableaux vides,
pas une erreur 404.
