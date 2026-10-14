# Dashboard Suivi Help Desk — ETL V1

Sprint ETL-01 : ingestion, parsing, mappings métier et validation sur l'historique.

## Lancer le dashboard
Depuis la racine du projet, installer les dépendances puis démarrer l'application :

```powershell
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Le dashboard récupéré lit `data/processed/tickets_v1.csv` et ne nécessite pas PostgreSQL.

## Source
- Google Sheets privé : `1SUemfD2NBhNAtciOBDjcW6UIJoovRSxo`
- `Suivi Tickets` : ligne 5 = en-têtes, données à partir de la ligne 6.
- Les lignes sans N° Ticket sont des séparateurs de journées et sont ignorées.
- `Listes!H:I` = mapping clients.
- `Listes!L:M` = mapping problématiques.

## Règles V1
- Durée analytique = colonne H, sauf pour `P260604283` et `P260604317`,
  pour lesquels la colonne J (`Temps de résolution (min)`) est la référence.
- F/G sont parsées pour les dimensions temporelles mais ne recalculent pas la durée.
- Priorités : Faible/Basse → Basse ; Moyen/Moyenne → Moyenne ; Elevé/Urgent → Haute.
- Techniciens : LOUBNA/Loubna → Loubna ; Sofiane AOUES/Sofiane Aoues → Sofiane Aoues.
- Les mappings Clients/Problématiques sont data-driven et case-insensitive sur la clé source.
- Exception ponctuelle `P260904149` : client analytique L'addition, problématique
  Installation/Formation et durée métier validée de 4 minutes. Les valeurs
  brutes et la décision appliquée sont conservées dans l'export ; les mappings
  des autres tickets restent inchangés.

## Contrôle du nouvel export
Depuis `Dashboard_Suivi` :

```powershell
python -m pytest -q
python -m src.pipeline.run --xlsx "data/raw/Suivi_HelpDesk1.xlsx" --output "data/processed/validation/new-export-20261010-171728/tickets_new_export.csv"
python -m src.validation.reference_audit "data/raw/Suivi_HelpDesk1.xlsx" --output "data/processed/validation/new-export-20261010-171728/reference_audit_new_export.json"
```

Remplacer les fichiers sous `data/processed/` uniquement après validation et
sauvegarde explicite des fichiers officiels.

## Google Sheets privé
Créer un compte de service Google, partager le classeur avec son adresse e-mail en lecture, puis :

```powershell
$env:GOOGLE_SERVICE_ACCOUNT_FILE="C:\chemin\service-account.json"
python -m src.pipeline.run --google --credentials $env:GOOGLE_SERVICE_ACCOUNT_FILE --output data/processed/tickets_v1.csv
```
