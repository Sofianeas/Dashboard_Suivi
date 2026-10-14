# ETL02 — Décisions d'architecture

## D-01 — Source de vérité de la durée

La colonne H `Temps de résolution (h)` est la source de vérité analytique,
sauf pour les tickets `P260604283` et `P260604317`, pour lesquels la colonne J
`Temps de résolution (min)` est la référence. Les timestamps F/G servent aux
dimensions temporelles et aux contrôles de qualité ; ils ne remplacent pas
la durée source.

## D-02 — Clé technique

`ticket_id` n'est pas garanti unique. `ticket_pk` est la clé technique
d'occurrence.

## D-03 — Doublons exacts

Les doublons exacts sont conservés dans l'historique mais exclus des KPI
via `kpi_eligible=False` / logique équivalente.

## D-04 — Collisions d'ID

Les collisions non exactes ne doivent pas être supprimées silencieusement.

## D-05 — Filtres dashboard

Les dimensions se combinent par AND.
`None`, chaîne vide, espaces et `ALL` signifient aucune restriction.
Les bornes de dates sont inclusives.
Une plage inversée est rejetée.

## D-06 — Frontend
Pas de framework JS ni de bibliothèque de graphiques à ce stade.
Séparation :
`app.js` orchestration,
`core/api.js` HTTP,
`core/state.js` état,
`core/ui.js` DOM/rendu.

## D-07 — Décision métier ponctuelle pour P260904149

Pour `P260904149` uniquement, les valeurs analytiques sont `L'addition`,
`Installation/Formation` et 4 minutes. Cette décision remplace les valeurs
analytiques mappées depuis les données brutes, sans les modifier. La date, les
horaires et la priorité restent issus du classeur. La durée brute, sa
provenance `business_validated` et le texte de décision sont conservés dans
l'export analytique. Les durées issues de la colonne J conservent aussi leur
valeur brute et la provenance `reference_column_j`.

Cette exception n'altère pas les mappings généraux des clients ou des
problématiques et ne constitue pas une règle de classification Centric pour
d'autres tickets.
