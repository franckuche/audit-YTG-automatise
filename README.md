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
- [Langues supportées](#langues-supportées)


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

Exemple de contenu du fichier CSV :

```python
URL,KEYWORD
http://exemple.com/page1,mot-clé 1
http://exemple.com/page2,mot-clé 2
```

## Exécution du script

Pour exécuter le script, utilisez la commande suivante dans votre terminal :

```python
python main.py -f chemin_vers_votre_fichier.csv -l code_langue
```

Les options sont :

- `-f` : le chemin vers le fichier CSV d'entrée.
- `-l` : la langue des guides (par défaut : en). Les codes de langue disponibles sont `fr_fr`, `en_us`, `es_es`, etc.

## Format de sortie

Le fichier de sortie est un CSV contenant les colonnes suivantes pour chaque ligne du fichier d'entrée : `KEYWORD`, `URL`, `CONTENT`, `GUIDE_ID`, `SEO_SCORE`, `DANGER`, `SOSEO_AVG_3`, `SOSEO_AVG_5`, `DSEO_AVG_3`, `DSEO_AVG_5`.

## Nom du fichier de sortie

Le fichier de sortie sera nommé en fonction du fichier d'entrée avec l'ajout de `_final_scores.csv` à la fin. Par exemple, si votre fichier d'entrée est `data.csv`, le fichier de sortie sera `data_final_scores.csv`.

## Langues supportées

Le script supporte les langues suivantes pour la demande de guide :

`fr_fr`, `de_at`, `pt_pt`, `en_ca`, `en_us`, `en_gb`, `es_es`, `fr_ch`, `it_it`, `de_de`, `pt_br`, `fr_be`, `fr_ca`, `fr_lu`, `fr_ma`, `de_ch`, `pl_pl`, `nl_nl`, `ro_ro`, `es_mx`, `en_au`, `es_cl`, `es_ar`, `es_co`.

Assurez-vous d'utiliser le code de langue approprié avec l'option `-l` lors de l'exécution du script.
