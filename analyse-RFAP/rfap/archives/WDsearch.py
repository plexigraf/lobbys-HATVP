import requests

def search_wikidata(query):
    endpoint_url = "https://www.wikidata.org/w/api.php"

    params = {
        'action': 'wbsearchentities',
        'format': 'json',
        'language': 'fr',
        'search': query,
    }

    response = requests.get(endpoint_url, params=params)
    data = response.json()

    if 'search' in data and data['search']:
        # Retourne le résultat le mieux noté
        best_result = data['search'][0]
        return best_result
    else:
        return None

# Exemple d'utilisation
entities_to_search = ["CERCLE D'ETUDE REALITES ECOLOGIQUES ET MIX ENERGETIQUE", 'U2P LOIRE ATLANTIQUE', 'U2P VENDEE', 'GPT INDUSTRIEL FRANCAIS APPAREIL MENAGER', 'SEMAE', 'ANICURA FRANCE SAS', 'RASSEMBLEMENT DES OPTICIENS DE FRANCE', 'AFL - GROUPE AFL - AFL-SOCIÉTÉ TERRITORIALE', 'CREDIT AGRICOLE CORPORATE AND INVESTMENT BANK', 'CONSEIL NATIONAL ORDRE DES SAGES FEMMES']

for entity in entities_to_search:
    result = search_wikidata(entity)
    if result:
        print(f"Entité: {entity}\nMeilleur résultat Wikidata: {result['label']} ({result['id']})\n")
    else:
        print(f"Aucun résultat trouvé pour l'entité: {entity}\n")
