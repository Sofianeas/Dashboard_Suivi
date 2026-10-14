# Reconstituer PostgreSQL localement sous Windows

Ce guide correspond à l'installation des **binaires PostgreSQL** (ZIP), et non à l'installateur graphique EDB. Ouvrir un terminal CMD ou PowerShell et adapter le chemin de `bin` à l'emplacement réel de PostgreSQL.

## 1. Vérifier les binaires
Dans un nouveau CMD :

```bat
postgres -V
psql -V
initdb --version
pg_ctl --version
```

Si une commande n'est pas reconnue, soit le dossier `bin` n'est pas dans `PATH`, soit il faut appeler l'exécutable avec son chemin complet, par exemple `C:\chemin\vers\pgsql\bin\psql.exe`.

## 2. Initialiser le répertoire de données (une seule fois)

Dans CMD :

```bat
if not exist "%APPDATA%\pgsql\mydata" mkdir "%APPDATA%\pgsql\mydata"
initdb -D "%APPDATA%\pgsql\mydata" -U postgres -W -E UTF8 -A scram-sha-256
```

Saisir un mot de passe local fort et le conserver dans un gestionnaire de mots de passe. Ne pas communiquer ce mot de passe.

**Important :** ne relancez pas `initdb` sur un répertoire déjà initialisé. Cela ne sert pas à démarrer le serveur et peut échouer si le répertoire contient déjà un cluster.

## 3. Démarrer le serveur

```bat
pg_ctl -D "%APPDATA%\pgsql\mydata" -l "%APPDATA%\pgsql\postgres.log" -o "-p 5432" start
```

Vérifier :

```bat
pg_isready -h 127.0.0.1 -p 5432
```

Résultat attendu : le serveur accepte les connexions. Si `pg_isready` n'est pas reconnu, utiliser le chemin complet vers `pg_isready.exe`.

## 4. Se connecter et créer la base

```bat
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

Dans l'invite `psql`, exécuter :

```sql
SELECT version();
SELECT current_user;
CREATE DATABASE dashboard_suivi ENCODING 'UTF8';
\q
```

Puis se connecter à la base créée :

```bat
psql -h 127.0.0.1 -p 5432 -U postgres -d dashboard_suivi
```

Créer les schémas utilisés par le projet :

```sql
CREATE SCHEMA raw;
CREATE SCHEMA core;
CREATE SCHEMA mart;
\dn
\q
```

Si la base existe déjà, ne pas rejouer `CREATE DATABASE`; se connecter à cette base et vérifier les schémas avec `\dn`.

## 5. Arrêter le serveur

```bat
pg_ctl -D "%APPDATA%\pgsql\mydata" stop
```

Ce guide concerne la récupération de la base PostgreSQL historique. L'application FastAPI récupérée lit le CSV `data/processed/tickets_v1.csv` et ne nécessite pas de démarrer PostgreSQL.

## 6. Connexion depuis Python : ne pas deviner le driver

L'archive récupérée est la version ETL V1 et ne contient pas la couche de connexion PostgreSQL du Dashboard complet. Avant d'ajouter un driver ou un `.env`, il faut restaurer/valider les modules de connexion et de chargement attendus par la version complète. Ne pas mettre le mot de passe dans le code source ni dans Git.

## 7. Vérification du projet récupéré
Depuis le dossier `Dashboard_Suivi` avec l'environnement Python activé :

```powershell
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.pipeline.run --xlsx "data/raw/Suivi_HelpDesk1 (6).xlsx" --output data/processed/tickets_v1.csv
```

Cette étape vérifie la récupération ETL V1, pas encore l'application FastAPI ni le chargement PostgreSQL.
