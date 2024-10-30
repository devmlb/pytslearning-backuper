# Pytslearning Backuper
Script Python pour télécharger l'intégralité des messages de chat présents dans Itslearning ainsi que les pièces-jointes.

## Fonctionnement
Une fenêtre est ouverte pour entrer ses informations de connexion et le cookie est ensuite automatiquement récupéré pour pouvoir faire des requêtes à l'API d'Itslearning.  
Les messages sont écrits dans des fichiers JSON nommés par l'id de la conversation, et un fichier `threads_list.json` répertorie toutes les conversations.  
Les pièces-jointes sont téléchargées dans des dossiers nommés par l'id de la conversation.

## Disclaimer
Ce projet a été réalisé précipitamment et n'est donc pas très abouti et optimisé. Il permet juste de récupérer des données.  
La fonctionnalité de téléchargement des pièces-jointes n'a pas pu être testée en intégralité.

## Installer
1. Télécharger le script
2. Modifier la ligne suivante dans le script pour qu'elle corresponde à l'URL de votre instance d'Itslearning :
```python
BASE_URL = "https://example.itslearning.com"
```
4. Exécuter cette commande :
```
pip install requests selenium chromedriver_autoinstaller
```
> Note : il faut avoir le navigateur Chrome installé au préalable
3. Exécuter le script
