# showNginxLogs
Script Python pour traiter les logs NGINX et les envoyer par mail ou par Slack

## Configuration
Dupliquer le fichier `config.py.dist`, le renommer en `config.py` et remplir avec les bons paramétrages.

## Dépendances
À installer avec `pip[version de python]` (Ex. : `pip3.5` ou `pip`) :
- sh
- colorama
- pyinstaller (création d'un exécutable)

Commandes pip :
- Vérifier si les paquets sont à jour : `pip[version de python] list -o --format columns`
- Mettre à jour un paquet :`pip[version de python] install  --upgrade <SomePackage>`
- Mettre à jour tous les paquets à partir d'un fichier : `pip[version de python] install -r requirements.txt`
- Écrire dans un fichier les paquets installés et leur version : `pip[version de python] freeze > requirements.txt`

## Usage
- `python[version de python] Logs.py [nom du serveur]`
- `pyinstaller --onefile Logs.py`
