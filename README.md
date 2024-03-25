# Guide d'utilisation du Script d'Audit Yourtext guru automatique

Ce script permet d'automatiser tout le travail de Yourtext Guru : 
1. Le scrap du contenu des URLs spécifiées dans un fichier CSV
2. Création des briefs sur Yourtext Guru
3. Récupération des ID des guides correspondants via l'API YourText.Guru,
4. Calcul des scores SEO et de la suroptimsiatio
5. Comparaison des scores vs les scores moyens de la SERP pour ces guides.

## Sommaire

- [Prérequis](#prérequis)
- [Configuration](#configuration)
- [Exécution du script](#exécution-du-script)
- [Format de sortie](#format-de-sortie)
- [Nom du fichier de sortie](#nom-du-fichier-de-sortie)

## Prérequis

- Python 3.x
- Bibliothèques Python : requests, trafilatura, statistics, et python-dotenv.
- Un fichier `.env` contenant votre clé API `YTG_API` pour YourText.Guru.
- Un fichier CSV contenant les URLs et mots-clés à analyser.

## Configuration

### Fichier .env

Créez un fichier `.env` dans le même répertoire que le script et ajoutez votre clé API de la manière suivante :

```python
YTG_API=votre_clé_api
```

### Fichier CSV d'entrée

Le script attend un fichier CSV en entrée avec les colonnes suivantes :

- 'URL': L'URL de la page à analyser.
- 'KEYWORD': Le mot-clé associé à l'URL.

```python
URL,KEYWORD
http://exemple.com/page1,mot-clé 1
http://exemple.com/page2,mot-clé 2
```

Exemple de contenu du fichier CSV :

URL,KEYWORD
http://exemple.com/page1,mot-clé 1
http://exemple.com/page2,mot-clé 2

## Exécution du script

Pour exécuter le script, utilisez la commande suivante dans votre terminal :


