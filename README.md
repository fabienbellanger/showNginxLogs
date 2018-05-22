# showNginxLogs
Script Python pour traiter les logs NGINX et les envoyer par mail ou par Slack

## Configuration
Dupliquer le fichier `config.py.dist`, le renommer en `config.py` et remplir avec les bons paramétrages.

## Dépendances
À installer avec `pip[version de python]` :
- sh
- colorama
- pyinstaller (création d'un exécutable)

## Usage
- `python[version de python] Logs.py [nom du serveur]`
- `pyinstaller --onefile Logs.py`
