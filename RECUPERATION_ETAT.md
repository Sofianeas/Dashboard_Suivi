# État de récupération — Dashboard_Suivi

## Contenu récupéré
- Code ETL V1 extrait de l'archive de départ disponible.
- Classeur source `data/raw/Suivi_HelpDesk1 (6).xlsx`.
- Pipeline ETL exécuté et validé : 592 lignes produites.
- Tests disponibles exécutés : `3 passed`.

## Limite importante
Cette archive est la meilleure récupération vérifiable à partir des fichiers encore disponibles. Elle ne constitue pas une copie exacte de la dernière version complète du Dashboard_Suivi : les sources de la couche FastAPI, les scripts SQL 01–07, certains tests et les artefacts ETL02 v2 ne sont pas tous présents dans l'archive de départ récupérée. Ils ne sont donc pas recréés artificiellement ici.

## Résultat ETL récupéré
- 592 lignes source avec identifiant de ticket.
- 586 identifiants distincts.
- 4 lignes exactes en doublon (12 lignes appartiennent à des groupes d'identifiants répétés selon le rapport V1).
- 1 horodatage de résolution invalide.
- Fichier généré : `data/processed/tickets_v1.csv`.

Ne pas considérer le rapport V1 comme le rapport qualité ETL02 V2 précédemment validé.
