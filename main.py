import argparse
import csv
import requests
import trafilatura
import os
import time
from dotenv import load_dotenv
import statistics

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Récupérer la clé API depuis les variables d'environnement
API_KEY = os.getenv('YTG_API')

def get_url_content(url):
    print(f"Début de l'extraction du contenu pour: {url}")
    res = trafilatura.fetch_url(url)
    content = trafilatura.extract(res) if res else "Échec de la récupération"
    print(f"Fin de l'extraction pour: {url}. Succès: {'oui' if content else 'non'}.")
    return content

def fetch_guide_id(keyword, lang='fr_fr'):
    print(f"Début de la récupération de l'ID de guide pour le mot-clé: '{keyword}'")
    URL_GUIDE = 'https://yourtext.guru/api/guide/'
    headers = {'KEY': API_KEY, 'accept': 'application/json'}
    data = {'query': keyword, 'lang': lang, 'type': 'premium'}

    for attempt in range(1, 4):
        response = requests.post(URL_GUIDE, headers=headers, data=data)
        if response.status_code == 200:
            guide_id = response.json().get('guide_id')
            print(f"ID de guide récupéré pour '{keyword}': {guide_id}")
            return guide_id
        elif response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 30))
            print(f"Tentative {attempt} pour '{keyword}': Trop de tentatives. Réessai dans {retry_after} secondes...")
            time.sleep(retry_after)
        else:
            print(f"Erreur pour '{keyword}': {response.text}")
            return None
    print(f"Échec de la récupération de l'ID de guide après plusieurs tentatives pour '{keyword}'")
    return None

def fetch_scores(guide_id, content, keyword):
    print(f"Récupération des scores pour le guide ID: {guide_id} et le mot-clé: {keyword}")
    URL_CHECK = f'https://yourtext.guru/api/check/{guide_id}'

    headers = {'KEY': API_KEY, 'accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'}
    data = f'content={content}'

    attempt = 1
    while attempt <= 3:
        response = requests.post(URL_CHECK, headers=headers, data=data)
        if response.status_code == 200:
            data = response.json()
            if 'errors' in data and 'No Corresponding Guide' in data['errors']:
                print(f"Erreur 'No Corresponding Guide', réessai dans 20 secondes...")
                time.sleep(20)
            else:
                score_seo = data.get('score', 0)
                danger = data.get('danger', 0)
                print(f"Scores récupérés pour '{keyword}': SEO={score_seo}, Danger={danger}")
                return {"data": data, "score_seo": score_seo, "danger": danger}
        elif response.status_code == 429:
            print(f"Tentative {attempt} pour '{keyword}': Trop de tentatives. Réessai dans 20 secondes...")
            time.sleep(20)
        else:
            print(f"Erreur lors de la récupération des scores pour le guide ID '{guide_id}' et le mot-clé '{keyword}': {response.text}")
            return None
        attempt += 1
    print(f"Échec de la récupération des scores après plusieurs tentatives pour le guide ID '{guide_id}' et le mot-clé '{keyword}'")
    return None

def fetch_serp_and_calculate_averages(guide_id, keyword):
    print(f"Récupération des données SERP pour le guide ID: {guide_id} et le mot-clé: '{keyword}'...")
    attempt = 1
    while attempt <= 3:
        response = requests.get(f"https://yourtext.guru/api/serp/{guide_id}", headers={'KEY': API_KEY})
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
    print(f"Début du traitement du fichier: {input_file}")
    output_filename = os.path.splitext(input_file)[0] + '_final_scores.csv'
    guides_info = []

    with open(input_file, mode='r', encoding='utf-8') as csv_input:
        reader = csv.DictReader(csv_input)
        for row in reader:
            url, keyword = row['URL'], row['KEYWORD']
            content = get_url_content(url)
            guide_id = fetch_guide_id(keyword, lang)
            if guide_id:
                guides_info.append({'keyword': keyword, 'url': url, 'content': content, 'guide_id': guide_id})

    print("Attente pour la disponibilité des guides...")
    time.sleep(60)  # Ajustez ce délai selon les besoins

    with open(output_filename, mode='w', newline='', encoding='utf-8') as csv_output:
        writer = csv.writer(csv_output)
        headers = ['KEYWORD', 'URL', 'CONTENT', 'GUIDE_ID', 'SEO_SCORE', 'DANGER', 'SOSEO_AVG_3', 'SOSEO_AVG_5', 'DSEO_AVG_3', 'DSEO_AVG_5']
        writer.writerow(headers)

        for guide_info in guides_info:
            scores = fetch_scores(guide_info['guide_id'], guide_info['content'], guide_info['keyword'])
            if scores:
                # Appel à fetch_serp_and_calculate_averages pour chaque guide
                soseo_avg_3, soseo_avg_5, dseo_avg_3, dseo_avg_5 = fetch_serp_and_calculate_averages(guide_info['guide_id'], guide_info['keyword'])
                writer.writerow([
                    guide_info['keyword'], 
                    guide_info['url'], 
                    guide_info['content'], 
                    guide_info['guide_id'], 
                    scores['score_seo'], 
                    scores['danger'],
                    soseo_avg_3,  # Ajout de la moyenne SOSEO pour les 3 premiers
                    soseo_avg_5,  # Ajout de la moyenne SOSEO pour les 5 premiers
                    dseo_avg_3,  # Ajout de la moyenne DSEO pour les 3 premiers
                    dseo_avg_5   # Ajout de la moyenne DSEO pour les 5 premiers
                ])

    print(f"Les données ont été enregistrées dans {output_filename}.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script pour récupérer le contenu des URLs, récupérer les IDs de guides et les scores associés.")
    parser.add_argument('-f', '--file', required=True, help="Fichier CSV contenant les URLs et mots-clés.")
    parser.add_argument('-l', '--lang', default='en', help="Langue pour la demande de guide.")
    args = parser.parse_args()

    process_file(args.file, args.lang)

