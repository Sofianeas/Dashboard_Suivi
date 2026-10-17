# ETL02 — Spécification fonctionnelle synthétique

## Source et contrat des données

La source de référence du pipeline est le classeur Excel local. Les données
brutes sont conservées distinctes des données analytiques transformées.

### Schéma source

Le schéma source doit contenir les neuf colonnes déclarées dans
`src/validation/schema.py`. L'ordre des colonnes n'est pas significatif et les
colonnes supplémentaires sont tolérées. Une colonne obligatoire manquante
entraîne une `ValueError` qui identifie les colonnes manquantes.

La colonne `Temps de résolution (min)` est une dépendance conditionnelle de la
transformation : elle est requise si une ligne conservée concerne l'un des
tickets de référence `P260604283` ou `P260604317`. Elle n'est pas ajoutée aux
neuf colonnes obligatoires générales. Une valeur de référence invalide pour un
de ces tickets doit entraîner une erreur explicite identifiant le ticket.

### Contrat analytique du rapport qualité

`quality_report()` reçoit un DataFrame transformé contenant au minimum les
colonnes `ticket_id`, `client_analytic`, `problem_analytic`, `priority_analytic`,
`resolution_minutes`, `opened_at`, `resolved_at`, `exact_duplicate` et
`ticket_pk`. Une colonne requise absente doit produire une erreur explicite.
Un DataFrame vide avec ces colonnes est valide et donne des compteurs nuls.

Les indicateurs restent descriptifs et n'imposent pas à eux seuls une décision
d'acceptation ou de rejet de l'export :

- `rows` : nombre total de lignes ; `tickets` : lignes avec `ticket_id` non nul ;
- `unknown_clients`, `unknown_problems`, `invalid_priorities`, `invalid_durations`,
  `invalid_opened_at`, `invalid_resolved_at` : nombre de valeurs nulles dans
  chaque champ analytique correspondant ;
- `duplicate_ticket_ids_rows` : nombre de lignes appartenant à un groupe dont
  `ticket_id` est répété ; `duplicate_ticket_ids_distinct` : nombre d'identifiants
  distincts appartenant à ces groupes ;
- `exact_duplicate_rows` : nombre de lignes marquées `exact_duplicate` ;
  `exact_duplicate_distinct_records` : nombre de `ticket_pk` distincts parmi ces
  lignes.

### Identifiants et doublons

`ticket_id` est un identifiant métier qui n'est pas garanti unique ; `ticket_pk`
identifie une occurrence technique. `duplicate_ticket_ids()` renvoie toutes les
lignes dont l'identifiant est répété, sous forme d'une copie, sans supprimer ni
modifier de ligne. Une collision d'identifiant n'implique pas que les lignes
soient des doublons exacts. Les règles métier existantes sur l'exclusion des
doublons exacts des KPI et la conservation des collisions non exactes restent
applicables.

La politique relative aux identifiants nuls ou vides n'est pas redéfinie ici :
la transformation les filtre en amont. Le comportement de la fonction générique
sur ces valeurs est caractérisé par les tests et ne doit pas être modifié sans
une décision explicite.

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
