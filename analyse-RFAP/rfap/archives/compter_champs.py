import json

#statistiques simples sur le repertoire hatvp

def append_new(liste, element):
    """
    Ajoute un élément à une liste uniquement s'il n'est pas déjà présent.

    Arguments :
    liste : list - La liste à laquelle ajouter l'élément.
    element : any - L'élément à ajouter.

    Retourne :
    list - La liste mise à jour.
    """
    if element not in liste:
        liste.append(element)
    return liste
# Charger le fichier JSON
with open('agora_repertoire_opendata.json', 'r') as file:
    data = json.load(file)

donnees=data['publications']


# Initialiser les dictionnaires pour stocker les relations
codes_labels = {}
codes_categories = {}
labels_codes = {}
labels_categories = {}
categories_codes = {}
categories_labels = {}

# Parcourir chaque entrée dans le fichier JSON
for entree in donnees:
    categorie_org = entree['categorieOrganisation']
    code = categorie_org['code']
    label = categorie_org['label']
    categorie = categorie_org['categorie']

    # Ajouter des informations aux dictionnaires
    # Codes
    if code not in codes_labels:
        codes_labels[code] = []
    codes_labels[code].append(label)

    if code not in codes_categories:
        codes_categories[code] = []
    codes_categories[code].append(categorie)

    # Labels
    if label not in labels_codes:
        labels_codes[label] = []
    labels_codes[label].append(code)

    if label not in labels_categories:
        labels_categories[label] = []
    labels_categories[label].append(categorie)

    # Catégories
    if categorie not in categories_codes:
        categories_codes[categorie] = []
    categories_codes[categorie].append(code)

    if categorie not in categories_labels:
        categories_labels[categorie] = []
    categories_labels[categorie].append(label)

# Construire le JSON final
resultat = {
    'codes_possibles': {
        code: {
            'labels_rencontres': list(set(labels)),
            'categories_rencontrees': list(set(categories))
        } for code, (labels, categories) in zip(codes_labels.keys(), zip(codes_labels.values(), codes_categories.values()))
    },
    'labels_possibles': {
        label: {
            'codes_rencontres': list(set(codes)),
            'categories_rencontrees': list(set(categories))
        } for label, (codes, categories) in zip(labels_codes.keys(), zip(labels_codes.values(), labels_categories.values()))
    },
    'categories_possibles': {
        categorie: {
            'codes_rencontres': list(set(codes)),
            'labels_rencontres': list(set(labels))
        } for categorie, (codes, labels) in zip(categories_codes.keys(), zip(categories_codes.values(), categories_labels.values()))
    }
}

# Afficher le résultat
print(json.dumps(resultat, indent=4))
