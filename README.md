# lobbys-HATVP
Analyse statistique du registre des lobbys de la HATVP.
Script utilisé pour l'analyse du répertoire des lobbyistes de la HATVP. Voir l'article correspondant.

Dans le dossier résultats: résultats numériques et visualisations d'analyse, sous différents jeux de paramètres

## Installation
 - Installez Python3
 - Téléchargez le script lobbys-rfap.py
 - Téléchargez le répertoire agora_repertoire_opendata.json sur le site de la HATVP
 - Téléchargez les classifications classif_clients.json
 - Exécutez le script

## Paramètres
Divers paramètres sont ajustables dans le préambule du script:
 - CORRECT_OUTLIERS (True or False): Effectuer une correction statistique des outliers
 - FOURCHETTE ('low', 'average' ou 'high'): Quelle budget choisir pour une firme qui déclare dans une fourchette low-high
 - SAMPLE ('all' ou nombre): nombre de firmes à analyser
 - YEARS (liste vide ou contenant des années, ex: [2018,2019]): sélectionner les exercices se terminant une année donnée

### Evaluer le poids financier d'une action
 - UNIFORM_RESS_ACTIONS (True or False): Toutes les actions ont le même poids
 - COST_LOBBYIST (valeur numérique): Affecter un coût supplémentaire aux lobbyistes
 - UNIFORM_WEIGHT (True or False): Les actions ont le même poids au sein d'un exercice

### Paramètres spécifiques de détection des outliers:
 - STRICT ('strict' ou ''): Seuils plus ou moins bas de détection d'outliers
 - DEFORM ('ln', 'sqrt' ou 'id'): Transformation à appliquer au budget avant de tester si outlier 
