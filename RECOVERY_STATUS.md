# Dashboard_Suivi — Recovery package

Date de reconstruction: 2026-09-26

## Objectif

Cette archive reconstruit le dernier état connu du projet `Dashboard_Suivi`
à partir :
1. du ZIP encore disponible sur le poste ;
2. des contrats, décisions d'architecture, fichiers et tests confirmés
   dans l'historique de travail de la conversation.

## État connu avant la perte du PC

- Architecture Web : FastAPI + HTML/CSS/JavaScript.
- PostgreSQL 18.6 local, port 5432.
- Schémas PostgreSQL : `raw`, `core`, `mart`.
- Vues MART : `v_ticket_kpi`, `v_client_analysis`,
  `v_problem_analysis`, `v_priority_analysis`,
  `v_technician_analysis`, `v_temporal_analysis`.
- Contrat de filtres AF-005.1 :
  `client`, `problem`, `priority`, `technician`, `date_from`, `date_to`.
- AF-005.2-A validée : query builder frontend.
- AF-005.2-B validée : interface des six filtres.
- Dernier état de tests confirmé dans la conversation : **63 passed**.
- Prochaine étape prévue : AF-005.2-C, chargement/rendu du dashboard.

## Données historiques récupérées

Le ZIP fourni par l'utilisateur contient le CSV ETL validé :
`data/processed/tickets_v1.csv`.

Constats connus :
- 592 lignes avec ticket ID ;
- 586 IDs distincts ;
- 4 doublons exacts ;
- 588 lignes KPI éligibles après exclusion des doublons exacts ;
- `H — Temps de résolution (h)` reste la source de vérité de la durée.

## Limite de récupération

Les scripts SQL 01..07 et certains fichiers PostgreSQL de la dernière version
n'étaient pas présents dans le ZIP survivant et leur contenu exact n'est pas
intégralement reconstructible à partir de l'historique textuel seul.

Le dossier `app/` de cette archive est donc une **reconstruction fidèle des
contrats et de l'architecture validée**, pas une prétention à reproduire
octet par octet les fichiers perdus.

Avant de remettre la production PostgreSQL en service, il faudra revalider
le DDL et les vues MART à partir d'une sauvegarde PostgreSQL, d'un dump SQL,
d'un clone Git ou d'une copie des fichiers SQL d'origine.

## Lancement

Développement :

```powershell
uvicorn main:app --reload
```

`python main.py` ne démarre pas Uvicorn : `main.py` expose volontairement
l'objet ASGI `app`.

URL :
`http://127.0.0.1:8000/`

Documentation API :
`http://127.0.0.1:8000/docs`
