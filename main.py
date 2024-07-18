import argparse
import csv
import requests
import os
import time
from dotenv import load_dotenv
import statistics
from urllib.parse import urlencode
from bs4 import BeautifulSoup
import pandas as pd
import re

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
API_KEY = os.getenv('YTG_API')

# Définir les constantes pour les URLs de l'API
URL_GUIDE = 'https://yourtext.guru/api/guide/'
URL_CHECK_TEMPLATE = 'https://yourtext.guru/api/check/{}'
URL_SERP_TEMPLATE = 'https://yourtext.guru/api/serp/{}'

def check_keyword(kw):
    """Cette fonction vérifie que la requête écrite est compatible
    avec YTG.
    Arguments:
    kw:(string): La requête à vérifier
    """
    # On regarde si la requête est trop longue
    if len(kw) > 150:
        print(f"Keyword '{kw}' is too long ({len(kw)} characters).")
        return False
    # On vérifie que la requête ne contient pas de caractères interdits
    match = re.fullmatch(r'[\w \/"!\'\+\?\.\-:]+', kw)
    if match is None:
        print(f"Keyword '{kw}' contains invalid characters.")
    return match is not None

def get_url_content(url):
    """
    Récupère le contenu textuel d'une URL donnée.
    """
    print(f"Processing {url}")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
            print("Content successfully retrieved.")
            return content
        else:
            print(f"Error fetching content for {url}: {response.status_code}")
            return "Content not available"
    except Exception as e:
        print(f"Error fetching content for {url}: {e}")
        return "Content not available"

def process_csv_and_add_content(nom_fichier_csv):
    """
    Traite un fichier CSV en ajoutant le contenu des URLs.
    """
    colonnes_necessaires = ['KEYWORD', 'URL']

    print("Lecture du fichier CSV...")
    try:
        df = pd.read_csv(nom_fichier_csv, usecols=colonnes_necessaires)
        print("Fichier CSV chargé avec succès.")
    except FileNotFoundError:
        print(f"Le fichier {nom_fichier_csv} n'existe pas")
        exit(1)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier CSV : {e}")
        exit(1)

    print("Traitement des URLs et sauvegarde ligne par ligne...")
    df['CONTENT'] = df['URL'].apply(get_url_content)

    # Utiliser le chemin absolu pour le fichier d'entrée
    nom_fichier_csv = os.path.abspath(nom_fichier_csv)
    
    # S'assurer que nous avons un répertoire valide pour le fichier de sortie
    output_dir = os.path.dirname(nom_fichier_csv)
    if not output_dir:
        output_dir = os.getcwd()  # Utiliser le répertoire de travail actuel si aucun répertoire n'est spécifié
    
    output_file = os.path.join(output_dir, "processed_" + os.path.basename(nom_fichier_csv))
    
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)

    df.to_csv(output_file, index=False)
    print(f"Toutes les données ont été traitées et sauvegardées dans {output_file}")
    return output_file

def fetch_guide_id(keyword, lang='fr_fr'):
    """
    Récupère l'ID du guide pour un mot-clé donné.
    """
    print(f"Début de la récupération de l'ID de guide pour le mot-clé: '{keyword}'")
    
    if not check_keyword(keyword):
        print(f"Keyword '{keyword}' is not valid.")
        return None

    headers = {'KEY': API_KEY, 'accept': 'application/json'}
    data = {'query': keyword, 'lang': lang, 'type': 'premium'}

    for attempt in range(1, 4):
        response = requests.post(URL_GUIDE, headers=headers, data=data)
        if response.status_code == 200:
            guide_id = response.json().get('guide_id')
            print(f"ID de guide récupéré pour '{keyword}': {guide_id}")
            return guide_id
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 35))
            print(f"Tentative {attempt} pour '{keyword}': Trop de tentatives. Réessai dans {retry_after} secondes...")
            time.sleep(retry_after)
        else:
            print(f"Erreur pour '{keyword}': {response.text}")
            return None
    print(f"Échec de la récupération de l'ID de guide après plusieurs tentatives pour '{keyword}'")
    return None

def fetch_scores(guide_id, content, keyword):
    """
    Récupère les scores SEO pour un contenu donné et un guide spécifique.
    """
    print(f"Récupération des scores pour le guide ID: {guide_id} et le mot-clé: {keyword}")
    URL_CHECK = URL_CHECK_TEMPLATE.format(guide_id)

    headers = {'KEY': API_KEY, 'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'content': content}
    
    print("Contenu envoyé à l'API :")
    print(data)

    attempt = 1
    while attempt <= 3:
        response = requests.post(URL_CHECK, headers=headers, data=urlencode(data).encode('utf-8'))
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data and 'No Corresponding Guide' in data['errors']:
                print(f"Erreur 'No Corresponding Guide', réessai dans 20 secondes...")
                time.sleep(35)
            else:
                score_seo = data.get('score', 0)
                danger = data.get('danger', 0)
                print(f"Scores récupérés pour '{keyword}': SEO={score_seo}, Danger={danger}")
                return {"data": data, "score_seo": score_seo, "danger": danger}
        elif response.status_code == 429:
            print(f"Tentative {attempt} pour '{keyword}': Trop de tentatives. Réessai dans 35 secondes...")
            time.sleep(20)
        else:
            print(f"Erreur lors de la récupération des scores pour le guide ID '{guide_id}' et le mot-clé '{keyword}': {response.text}")
            return None
        attempt += 1
    print(f"Échec de la récupération des scores après plusieurs tentatives pour le guide ID '{guide_id}' et le mot-clé '{keyword}'")
    return None

def fetch_serp_and_calculate_averages(guide_id, keyword):
    """
    Récupère les données SERP et calcule les moyennes des scores SOSEO et DSEO.
    """
    print(f"Récupération des données SERP pour le guide ID: {guide_id} et le mot-clé: '{keyword}'...")
    attempt = 1
    while attempt <= 3:
        response = requests.get(URL_SERP_TEMPLATE.format(guide_id), headers={'KEY': API_KEY})
        if response.status_code == 200:
            serp_data = response.json().get('serps', [])
            if serp_data:
                serp_scores_soseo_main = [int(item['scores']['soseo_main_content']) for item in serp_data[:5]]
                serp_scores_dseo_main = [int(item['scores']['dseo_main_content']) for item in serp_data[:5]]

                soseo_avg_3 = statistics.mean(serp_scores_soseo_main[:3]) if len(serp_scores_soseo_main) >= 3 else 0
                soseo_avg_5 = statistics.mean(serp_scores_soseo_main) if serp_scores_soseo_main else 0
                dseo_avg_3 = statistics.mean(serp_scores_dseo_main[:3]) if len(serp_scores_dseo_main) >= 3 else 0
                dseo_avg_5 = statistics.mean(serp_scores_dseo_main) if serp_scores_dseo_main else 0

                print(f"Résultats des moyennes pour '{keyword}': SOSEO_AVG_3={soseo_avg_3}, SOSEO_AVG_5={soseo_avg_5}, DSEO_AVG_3={dseo_avg_3}, DSEO_AVG_5={dseo_avg_5}")
                return soseo_avg_3, soseo_avg_5, dseo_avg_3, dseo_avg_5
            else:
                print("Aucune donnée SERP disponible pour le calcul des moyennes.")
                return None, None, None, None
        elif response.status_code == 429:
            print(f"Tentative {attempt} échouée avec réponse 429 (Trop de requêtes). Réessai dans 20 secondes...")
            time.sleep(20)
        else:
            print(f"Erreur lors de la récupération des données SERP pour le guide ID '{guide_id}' et le mot-clé '{keyword}': Statut HTTP: {response.status_code}")
            return None, None, None, None
        attempt += 1
    print(f"Échec de la récupération des données SERP après {attempt-1} tentatives pour le guide ID '{guide_id}' et le mot-clé '{keyword}'")
    return None, None, None, None

def process_file(input_file, lang='en'):
    """
    Traite le fichier CSV d'entrée et ajoute les informations de contenu.
    """
    print("Lecture du fichier CSV d'entrée...")
    df = pd.read_csv(input_file)
    output_filename = os.path.join(os.path.dirname(input_file), "processed_with_scores_" + os.path.basename(input_file))

    output_dir = os.path.dirname(output_filename)
    os.makedirs(output_dir, exist_ok=True)

    guides_info = []
    for index, row in df.iterrows():
        keyword = row['KEYWORD']
        content = row['CONTENT']
        guide_id = fetch_guide_id(keyword, lang)
        guides_info.append({'keyword': keyword, 'url': row['URL'], 'content': content, 'guide_id': guide_id})

    if guides_info:
        with open(output_filename, 'w', newline='') as output_file:
            fieldnames = ['keyword', 'url', 'guide_id', 'soseo_avg_3', 'soseo_avg_5', 'dseo_avg_3', 'dseo_avg_5', 'score_seo', 'danger']
            writer = csv.DictWriter(output_file, fieldnames=fieldnames)
            writer.writeheader()

            for guide in guides_info:
                if guide['guide_id']:
                    scores = fetch_scores(guide['guide_id'], guide['content'], guide['keyword'])
                    if scores:
                        soseo_avg_3, soseo_avg_5, dseo_avg_3, dseo_avg_5 = fetch_serp_and_calculate_averages(guide['guide_id'], guide['keyword'])
                        writer.writerow({
                            'keyword': guide['keyword'],
                            'url': guide['url'],
                            'guide_id': guide['guide_id'],
                            'soseo_avg_3': soseo_avg_3,
                            'soseo_avg_5': soseo_avg_5,
                            'dseo_avg_3': dseo_avg_3,
                            'dseo_avg_5': dseo_avg_5,
                            'score_seo': scores['score_seo'],
                            'danger': scores['danger']
                        })
                    else:
                        writer.writerow({'keyword': guide['keyword'], 'url': guide['url'], 'guide_id': guide['guide_id']})
                else:
                    writer.writerow({'keyword': guide['keyword'], 'url': guide['url'], 'guide_id': None})

    print(f"Traitement terminé. Résultats enregistrés dans: {output_filename}")
    return output_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process SEO scores for given CSV file")
    parser.add_argument("csv_file", help="Path to the input CSV file")
    parser.add_argument("-l", "--lang", default="en", help="Language for the guide (default: en)")

    args = parser.parse_args()

    processed_csv = process_csv_and_add_content(args.csv_file)
    process_file(processed_csv, args.lang)
