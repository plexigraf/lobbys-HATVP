
#PARAMETRES (en majuscule)
CORRECT_OUTLIERS=False#remplacer les valeurs aberrantes
FOURCHETTE='average' #'low', 'average' ou 'high', pour choisir dans la fourchette du budget pour chaque firme
out_str=str(CORRECT_OUTLIERS)
if CORRECT_OUTLIERS:#pour corriger les budgets aberrants des assos de lobbying
    AGRESSIVE="agressive" #détermination des seuils déclarant une valeur comme problématique
    DEFORM="sqrt"# #fonction de déformation du budget pour détecter les outliers, possibilités: "id"; "ln", "sqrt", ...
    out_str+='-'+AGRESSIVE+'-'+DEFORM
SAMPLE="all" #n premieres entrees uniquement (pour dev), ou "all"
sampleStr="-sample"+str(SAMPLE) if SAMPLE else ""
UNIFORM_RESS_ACTIONS=True#toutes les actions ont les memes ressources
if UNIFORM_RESS_ACTIONS:
    UNIFORM_WEIGHT=True#not used
    COST_LOBBYIST=0
    str_wgt_actions="unif-"
else:
    UNIFORM_WEIGHT=False#chaque action a la même ressource au sein d'un exercice
    COST_LOBBYIST=30000#cout annuel estimé d'un lobbyiste
    str_wgt_actions="by-ex-" if UNIFORM_WEIGHT else "formula-"
strLobbyist='' if UNIFORM_RESS_ACTIONS else '-lobbyist='+str(COST_LOBBYIST)
YEARS=[]# include 2017? 2023? - exercices se terminant une année donnée (2016 ou plus)
yrs_str='' if len(YEARS)==0 else str(YEARS[0]) if len(YEARS)==1 else str(YEARS[0])+'-'+str(YEARS[-1])
IMPUTER_DOMAINE=True#quand pas de domaine renseigné sur une action, on prend les secteurs de la firme (s'il y en a...)
domaineStr='' if IMPUTER_DOMAINE else '-pas_imputer_domaine'

FILE_SUFFIX=FOURCHETTE+'-out='+out_str+'-acts='+str(str_wgt_actions)+strLobbyist+'-'+sampleStr+'-'+yrs_str+domaineStr

verbose="synthese"#"debug"

def print_debug(*args):
    if verbose=="debug":
        print(*args)

import json
import textwrap
from datetime import date
import random
import sys
import collections
import os
import shutil
import re
import unicodedata
from sklearn.neighbors import NearestNeighbors
import numpy as np
import math
import matplotlib.pyplot as plt
#prgm utilisé pour article RFAP
#voir fichier lobbys-pxg.py pour traiter les données pour la visualisation pxg,
#ou pour faire des recherches insee
from scipy.stats.mstats import zscore
from collections import Counter




transf = math.log if CORRECT_OUTLIERS and DEFORM=="ln" else lambda x:x
transfinv= math.exp if CORRECT_OUTLIERS and DEFORM=="ln" else lambda x:x



def printjs(s):
    print(json.dumps(s, indent=4, sort_keys=False, ensure_ascii=False))
def printjs_debug(s):
    if verbose=="debug":
        print(json.dumps(s, indent=4, sort_keys=False, ensure_ascii=False))


# def gini_coefficient(data):
#     # Convert data to numpy array
#     data = np.array(data)

#     # Sort the data
#     sorted_data = np.sort(data)

#     # Calculate cumulative area under the Lorenz curve
#     cumulative_areas = np.cumsum(sorted_data) / np.sum(sorted_data)

#     # Calculate Gini coefficient
#     gini_coeff = 1 - 2 * np.trapz(cumulative_areas) / len(data)

#     return gini_coeff


today = str(date.today())
print( today)

#save=False

#now: check that all nodes and tiers from "lobbys" are in "to_grade" or "results-gpt"

# with open('openAI/results-gpt.json', 'r') as fich:#contains grades
#     RESULTS_GPT = json.load(fich)
with open('classif_clients.json', 'r') as fich:#contains grades
    CLASSIF = json.load(fich)
#with open('openAI/to-grade.json') as f:#elements fichier lobbys.json matched
#    to_grade = json.load(f)
with open('agora_repertoire_opendata.json') as f:#répertoire HATVP
    DATA = json.load(f)['publications']

if SAMPLE!="all":
    DATA=DATA[0:SAMPLE]
# Iterating through the json
# list


results={'params':FILE_SUFFIX}
#First, iterate over the firms of data


firmes={}#contiendra les poids des actions et les ressources des firmes par exercice, et qqs autres infos
actions={}
tiers={}#récolte les actions commanditées et la note de chaque mandant
triplets_ressources=[]#récole les ressources de chaque firme pour détercter outliers
doublons_gpt={}#quand on récolte les tiers, au passage on récole les notes, et ceux qui ont deux notes - devrait être fait dans la boucle sur tiers

other_names={}


####### secteurs par firmes
DOMAINE={
    'Construction, logement, aménagement du territoire':['Occupation des sols','Patrimoine', 'Développement des territoires', 'Bâtiments et travaux publics','Construction, logement, aménagement du territoire','Logement','Construction'],
    "Aide et protection sociale":[ 'Assurance chômage',  'Handicap','Droit du travail','Dialogue social','Famille','Emploi, solidarité'],
    "Enseignement et recherche": [ 'Recherche et innovation','Education','Education, enseignement, formation',
        "Enseignement supérieur, recherche, innovation",
        "Éducation, enseignement, formation",
        "Enseignement supérieur",
        "Formation professionnelle",
        "Statistiques"
    ],
    "Droits de l'homme et libertés": [  'Aide au développement','Humanitaire','Principe de précaution','Egalité femmes/hommes','Bien-être animal','Egalité des chances', 'Asile', 'Immigration','Discriminations','Questions migratoires','Société',
        "Droits et libertés fondamentales",
        "Liberté d’expression et d’information",
        "Droits des victimes",
        "Laïcité"
    ],
    "Industries de télécommunications et du numérique": [
        "Accès à l’Internet",
        "Accès aux moyens de télécommunications", 'Marché du numérique', 'Protection des données', 'E-commerce',
        "Numérique",
        "Télécommunications",
        "Infrastructures de télécommunications",
        "Marché du numérique",
        "E-commerce"
    ],
    "Santé et pharmaceutique": [ 'Médicaments', 'Remboursements', 'Soins et maladies', 'Système de santé et médico-social','Prévention',
        "Santé",
        "Système de santé et médico-social",
        "Soins et maladies"
    ],
    "Banques, assurances, finance":[ 'Banques, assurances, secteur financier', 'Protection des marques','Assurances', 'Finances', 'Banques','Banques, assurances, secteur financier et extra financier',
        "Finances",
        "Banques",
        "Assurances",
    ],
    "Gouvernance et institutions publiques": [
    "Outre-mer",
    "Français de l’étranger",'Collectivités territoriales',
        "Pouvoirs publics et institutions",
        "Institutions européennes",
        "Institutions des outre-mer",
        "Ordre administratif",
        "Moralisation/Transparence",
        "Coopération internationale",
        "Accords internationaux",
        "Economie des outre-mer",
        "Développement économique des outre-mer"
    ],
    "Concurrence et régulation":['Secret des affaires / Secret professionnel',
        "Aides aux entreprises",'Brevet',  'Droit de la concurrence','Marchés réglementés','PME/TPE', 'Normes de production',
        "Professions réglementées",'Entreprises et professions libérales','Concurrence, consommation','Gouvernance d’entreprise','Commerce extérieur'],
    "Economie et finances publiques": [  'Taxes',  'Politique industrielle', 'Fonction publique','Retraites',
        "Partenariats public/privé",
        "Finances publiques",
        "Economie",
        "Budget",
        "Taxation",
        "Impôts"
    ],
    "Energies non-renouvelables":['Energie nucléaire','Energie','Ressources naturelles',
        "Ressources minières",
        "Energies fossiles",],
    "Environnement et développement durable": ['Chasse', 'Eaux',  'Produits chimiques', 'Accidents et catastrophes naturelles',
        "Impact des transports individuels",
        "Impact des transports marchands et collectifs",
        "Qualité de l'eau",
        "Environnement",
        "Déchets",
        "Energies renouvelables",
        "Impact de l'activité industrielle",
        "Dépollution",
        "Forêt"
    ],
    "Justice et sécurité": [ 'Institutions judiciaires', 'Défense', 'Institutions pénitentiaires',
        "Justice",
        "Institutions judiciaires",
        "Justice civile",
        "Justice pénale",
        "Défense, sécurité",
        "Sécurité nationale",
        "Sécurité routière",
        "Espionnage et surveillance"
    ],
    "Culture, loisirs, tourisme, Médias": ["Médias",'Tourisme/hôtellerie',  "Droit d'auteur",  'Publicité',  'Sports','Propriété intellectuelle','Sports, loisirs, tourisme',
        "Accès à la culture",
        "Arts, culture",
        "Musique",
        "Spectacle vivant",
        "Cinéma",
        "Presse écrite",
        "Audiovisuel",
        "Jeux d'argent",
        "Jeux-vidéo",
        "Livre"
    ],
    "Transport et logistique": [
    "Industrie aérospatiale", 'Services postaux', 'Infrastructures','Industrie aéronautique','Aéronautique, aérospatiale',
        "Transports, logistique",
        "Transport de voyageurs",
        "Transport de fret",
        "Transports alternatifs",
        "Services postaux"
    ],
    "Agriculture et alimentation": [ 'Sécurité et normes alimentaires', 
        'Appellations',"Agriculture, agroalimentaire",
        "Agriculture",
        "Industrie agroalimentaire",
        "Pêche"
    ],
    'NA':['NA']
}

results['sous-secteurs']=DOMAINE

SECTEUR={}

CIBLES=["Titulaire d'un emploi à la décision du Gouvernement",'Premier ministre',
        "Collaborateur du Président de la République",
        "Député, sénateur, collaborateur, agents des services des assemblées",
        "NA",
        "Membre du Gouvernement ou membre de cabinet ministériel",
        'Premier ministre',
        "Agent de l’État, d’un centre hospitalier, ou d’une collectivité territoriale"
        ,"Direction autorité administrative ou publique indépendante",
        "Élu ou membre de cabinet d'une collectivité territoriale"
    ]





for s in DOMAINE:
    for d in DOMAINE[s]:
        if d!="nombre":
            if d in SECTEUR and s!= SECTEUR[d]:
                print(s,d)
                print('doublon')
            else:
                SECTEUR[d]=s
print('domaines')
printjs(DOMAINE)
missing_secteurs=set()

def browse_agora(data):
    print('browse agora file...')
    global other_names
    global CIBLES
    global CLASSIF
    global RESULTS_GPT
    global firmes
    global actions
    global tiers
    global doublons_gpt
    global triplets_ressources
    global YEARS

    def reduce_cible(cible):#simplifier?
        cibles=[]
        if cible=="Membre du Gouvernement ou membre de cabinet ministériel - Premier ministre":
            cibles=['Premier ministre']
        elif cible.startswith("Membre du Gouvernement ou membre de cabinet ministériel"):
            cibles=["Membre du Gouvernement ou membre de cabinet ministériel"]
            if "Premier ministre" in cible:
                cibles+=['Premier ministre']
        elif cible.startswith("Député, sénateur, collaborateur"):
            cibles=[ "Député, sénateur, collaborateur, agents des services des assemblées"]
        elif cible.startswith("Agent d"):
            cibles=["Agent de l’État, d’un centre hospitalier, ou d’une collectivité territoriale"]
        elif cible.startswith("Directeur ou secrétaire général, ou leur adjoint, ou membre du collège ou d'une commission des sanctions d'une autorité administrative ou publique indépendante"):
            cibles=["Direction autorité administrative ou publique indépendante"]
        elif cible.startswith("Élu ou membre de cabinet d'une collectivité territoriale -"):
            cibles=["Élu ou membre de cabinet d'une collectivité territoriale"]
        elif cible in CIBLES:
            cibles=[cible]
        else:
            print('pb cible inconnue')
            input(cible)
        return cibles
    
    def merge_actions(liste_de_dicts):#utilisé pour fusionner des actions d'une activité
        # Initialiser le dictionnaire résultant
        resultat = {}

        # Parcourir chaque dictionnaire dans la liste
        for dictionnaire in liste_de_dicts:
            # Parcourir chaque clé-valeur dans le dictionnaire
            for cle, valeur in dictionnaire.items():
                # Mettre à jour le dictionnaire résultant
                if cle in resultat:
                    resultat[cle]+=valeur  # Concaténer les listes si la clé existe déjà
                else:
                    resultat[cle] = valeur  # Sinon, ajouter la clé-valeur au dictionnaire résultant

        return resultat
    def best_nom(firme):
        try:
            return firme['nomUsageHatvp']
        except KeyError:
            try:
                return firme['nomUsage']
            except KeyError:
                return firme['denomination']
    def poids_formula(action):
        global UNIFORM_WEIGHT
        return 5 if UNIFORM_WEIGHT else 5+len(action['tiers'])+len(action['actionsMenees'])+len(action['decisionsConcernees'])+len(action['reponsablesPublics'])
    def extract_budget(s):
        high=int(ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =','').replace(' ',''))
        l=s.split('=')
        low=int(l[1].split('euros')[0].replace(' ','')) if len(l)>1 else 0
        return 0.5*(high+low) if FOURCHETTE=='average' else high if FOURCHETTE=='high' else low

    missing={}
    tiers_pas_clients={}
    clients_firme={}
    montant_ttl_declares=0
    salaries_ttl_declares=0
    counter=0
    nb_actions=0
    for firme in data:
        #allKeys |= set(firme.keys())
        counter=counter+1
        #printjs(firme)
        print_debug(counter,'/',len(data))
        print_debug('********')
        nom=best_nom(firme)
        other_names[nom]=[firme[key] for key in ['denomination','nomUsage','nomUsageHatvp','sigleHatvp'] if key in firme and firme[key]!=nom]
        print_debug(nom+":"+str(other_names[nom]))
        possible_names=other_names[nom]+[nom]

        lab=firme['categorieOrganisation']['label']
        print_debug('label: '+lab)
        ident=firme['typeIdentifiantNational']+str(firme['identifiantNational'])
        if nom in firmes:
            nom=nom+' * '+firme['denomination']
            if nom in firmes:
                nom=nom+' * '+ident
                if nom in firmes:
                    input('really?')
            #print('nom doublon',nom)
            #input('?')
        other_names[nom]=possible_names
        secteurs_firme=[item['label'] for item in firme['activites']['listSecteursActivites']]
        for s in secteurs_firme:
            if s not in SECTEUR:
                missing_secteurs.add(s)
        firmes[nom]={'identifiant':ident,
                        'categorie':firme['categorieOrganisation']['label'],
                        'affiliations':firme['affiliations'],
                        'Nom complet':firme['denomination'],
                        'Secteurs':secteurs_firme}
        #il faudrait faire afficher les options par plexigraf

        clients_firme[nom]={cl['denomination']:{'found':False} for cl in firme['clients']}
        #{client1:{'found':False},client2:...}

        print_debug('******exercices')
        for ex in firme['exercices']:
            ex=ex['publicationCourante']
            filter_year=(len(YEARS)==0)#True by default
            for y in YEARS:
                if str(y) in ex['dateFin']:
                    filter_year=True
            if not filter_year:
                continue

            #on  détermine s'il y a une activité, et si oui on calcule le poids de l'exercice
            
            #d'abord on détermine les ressources et on enregistre dans triplets_ressources pour les CORRECT_OUTLIERS
            #détern montant et nbsalariés
            if 'montantDepense' in ex:
                print_debug(ex['montantDepense'],ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =',''))
                montant=extract_budget(ex['montantDepense'])
                montant_ttl_declares+=montant
            else:
                montant='NA'
            if 'nombreSalaries' in ex and int(ex['nombreSalaries'])>0 and int(ex['nombreSalaries'])<42:
                salaries=int(ex['nombreSalaries'])
                salaries_ttl_declares+=salaries
            else:
                salaries='NA'
            try:
                #for outliers and filling NAs
                triplets_ressources+=[((transf(int(montant))),int(salaries),int(poids_activites_exercice))]
                triplet=True
            except:
                print_debug('données manquantes')


            if not 'activites' in ex or len(ex['activites'])==0:
                if (montant!='NA' and int(montant)!=10000) or int(ex['nombreActivite'])>0:#pas d'action enregistrée mais on comptabilise une activité en raison des ressources. On met comme tiers tous les clients de la firme
                    printjs_debug(ex)
                    print_debug('ghost exercice')#on créée une activité fictive
                    ex['activites']=[{'publicationCourante':{ "identifiantFiche" : "XXXXX", "objet" : "en propre non renseigné",
                                                                "domainesIntervention":secteurs_firme if IMPUTER_DOMAINE else ['NA'] ,
                                                                "actionsRepresentationInteret" : [
                                                                    {"reponsablesPublics" : ['NA'],
                                                                        "decisionsConcernees" : [0],
                                                                        "actionsMenees" : [0],
                                                                        "tiers" :  []#remplacé automatiquement après par les clients de la firme
                                                        }           ]}
                                     }]

                    if nom in tiers:
                        tiers[nom]['actions']+=[ 'en propre non renseigné']
                    else:
                        tiers[nom]={'actions':['en propre non renseigné']}
                    poids_activites_exercice=5
                else:
                    print_debug('pas d activité comptabilisée')
                    continue
            #s'il y a activité, on détermine le poids total:
            if 'activites' in ex:#on va compter les poids et enregistrer les tiers et les actions
                poids_activites_exercice=0
                periode=ex['dateDebut']+'-'+ex['dateFin']
                if len(ex['activites'])<int(ex['nombreActivite']):
                    print_debug(len(ex['activites']),ex['nombreActivite'])
                    print_debug('manque activité(s)')
                for act in ex['activites']:
                    nb_actions+=1
                    act=act['publicationCourante']
                    action=merge_actions(act['actionsRepresentationInteret'])
                    poids_action=poids_formula(action)
                    poids_activites_exercice+=poids_action
                    objet=act['objet']
                    if objet not in actions:
                        actions[objet]={}
                    if periode not in actions[objet]:
                        actions[objet][periode]={}
                    if nom not in actions[objet][periode]:
                        actions[objet][periode][nom]={}

                    action_tiers_modif=[]
                    if len(action['tiers'])==0:#par défaut, on met tous les clients. 
                        action['tiers']=[k for k in clients_firme[nom]]
                        if len(clients_firme[nom])==0:
                            print_debug('pas de clients et pas de tiers sur cette action - en propre par défaut')
                            action['tiers']=['en propre']
                    #on va enregistrer ces tiers dans le dict "tiers" avec tiers[t]={actions:[objet1,objet2...]}. On va ensuite enregistrer ces tiers dans le dict "actions" avec actions[objet][periode][nom][code]={tiers:[t1,t2...],poids_abs:5}
                    for t in action['tiers']:#on récolte les tiers et leur notes gpt, mais ça serait plus logique de mettre les notes dans la boucle sur tiers. On utilise ici le fait d'avoir les possibles names pour les actions 'en propre'
                        if 'en propre' in t or t in possible_names:
                            t=nom#il faut mettre le nom de cette firme pour bien capter les ressources de l'action du bon endroit
                            #t=best_nom(firme)
                            print_debug('en propre')
                            #names_gpt_results=[name for name in possible_names if name in RESULTS_GPT]
                            #names_gpt_class=[name for name in possible_names if name in CLASSIF]
                        else:
                            if t not in clients_firme[nom]:
                                if nom in tiers_pas_clients and t not in tiers_pas_clients[nom]:
                                    tiers_pas_clients[nom]+=[t]
                                else:
                                    tiers_pas_clients[nom]=[t]
                            else:
                                clients_firme[nom][t]['found']=True
                            # if t in RESULTS_GPT:
                            #     names_gpt_results=[t]
                            # else:
                                # names_gpt_results=[]
                            # if t in CLASSIF:
                            #     names_gpt_class=[t]
                            # else:
                            #     names_gpt_class=[]
                        if t not in tiers:
                            tiers[t]={'actions':[objet]}
                        else:
                            tiers[t]['actions']+=[objet]

                        action_tiers_modif+=[t]
                    cibles_action=[]
                    for c in action['reponsablesPublics']:
                        cibles_action+=reduce_cible(c)

                    actions[objet][periode][nom][act['identifiantFiche']]={'tiers':action_tiers_modif,'poids_abs':poids_action,'domaines':act['domainesIntervention'],'cibles':cibles_action} #on enregistre les tiers et le poids de l'action et les cibles 
                    for d in act['domainesIntervention']:
                        if d not in SECTEUR:
                            missing_secteurs.add(d)
                if poids_activites_exercice>10000:
                    print_debug('gros ex')

            if periode in firmes[nom]:#2 périodes pleines déclarées?
                printjs_debug(firmes[nom][periode])
                printjs_debug(ex)
                print_debug('double période - très rare, uniquement FEDERATION NAL METIERS STATIONNEMENT, il faudrait les fusionner mais tant pis. a minima il faudrait garder celui qui a les activités et on lui imputera les ressources')
            firmes[nom][periode]={'montant':montant,'nbSalaries':salaries,'poids_exercice':poids_activites_exercice,'triplet':True,'outliers':{}}
        clients_firme[nom]=[cl  for cl in clients_firme[nom] if not clients_firme[nom][cl]['found']]
        if len(clients_firme[nom])==0:
            del clients_firme[nom]
    
    counts = Counter(CIBLES).most_common()
    printjs_debug(counts)


    results.update({"nombre de firmes":counter,
                    'nombre d actions':nb_actions,
                    'montant ttl declaré':montant_ttl_declares,
                    'salariés ttl declarés':salaries_ttl_declares,
                    'ressources déclarées estimées':montant_ttl_declares+salaries_ttl_declares*COST_LOBBYIST,
                    'nb tiers':len(tiers)})
    printjs(results)


    results['Cibles']=counts
    results['tiers']=len(tiers)
    
    print_debug(missing)
    print_debug('missing')

    printjs_debug(tiers_pas_clients)
    ttl=sum([len(tiers_pas_clients[t]) for t in tiers_pas_clients])
    print('tiers pas clients, par nom de cabinet de lobbying - a confronter avec other_names',ttl)

    printjs_debug(clients_firme)
    ttl=sum([len(clients_firme[f]) for f in clients_firme])
    print('clients pas trouvés',ttl)


    unique_clients=set()
    for f in clients_firme:
        unique_clients.update(clients_firme[f])



    unique_clients_wo_class=set()
    for u in unique_clients:
        if not u in CLASSIF and u in other_names:
            possible_names=other_names[u]
            found=False
            for n in possible_names:
                if n in CLASSIF:
                    found=True
            if not found:
                unique_clients_wo_class.add(u)
    # with open('data-clients_wo_class.json','w') as file:
    #     json.dump(list(unique_clients_wo_class), file, indent = 4, separators = (',', ':'))


    results['incoherences clients/tiers']={'tiers pas clients':{'nombre':ttl,'par firme':tiers_pas_clients},
                                           'clients pas trouvés':{'nombre':ttl,'par firme':clients_firme},
                                           'unique clients pas trouvés':len(unique_clients)
                                           }

    print('unique clients sans classe qqs le nom',len(unique_clients_wo_class))
    # if len(unique_clients_wo_class)==0:
    #     input('?')

#save other names

browse_agora(DATA)
with open('other_names.json','w') as file:
    json.dump(other_names, file, indent = 4, separators = (',', ':'))

print('missing secteurs',missing_secteurs)
if missing_secteurs != set(''):
    input('missing sthg')
####doublons gpt

#On analyse les firmes notées 2 fois par erreur, ça permet d'estimer la consistance de la procédure
# print("*****doublons gpt")
# printjs_debug(doublons_gpt)
# print('doublons gpt')


# ecarts_scores=[]
# confiances=[]

# def explore_doublons():
#     global doublons_gpt
#     for f in doublons_gpt:
#         db=doublons_gpt[f]
#         #print(f)
#         #printjs_debug(db)
#         scores=[r['class'] for r in db]
#         if len(db)>2:
            # input('more than 2')
        #ecarts_scores+=[max(scores)-min(scores)]
        #confiances+=[max([r['confiance'] for r in db])]
    
    #print('erreur moyenne doublons',np.mean(ecarts_scores))
    #print('correl confiance',np.corrcoef(ecarts_scores,confiances))
    #input("*****doublons gpt")


#explore_doublons()


######classes tiers et doublons notes

print('classification tiers')

def add_values(dict1,dict2):#to add class dict numeric values
    for k in [k for k in dict1 if k not in dict2]:
        dict2[k]=0
    for k in [k for k in dict2 if k not in dict1]:
        dict1[k]=0
    return {k:dict1[k]+dict2[k] for k in dict1}    

#ces firmes auront la catégorie "privé" par défaut:
PRIVATE_LABELS=['Société commerciale',
'Société civile (autre que cabinet d’avocats)',
'Cabinets d’avocats',
'Cabinet d’avocats',
'Avocat indépendant',
'Cabinet de conseil',
'Cabinet de conseils',
'Consultant indépendant',#"Organisation professionnelle",
"Fédération professionnelle",
"Travailleur indépendant",
"Société commerciale et civile (autre que cabinet d’avocats et société de conseil)"]
POSSIBLE_LABELS=['prive','syndicat','public','collectivite']

#create-dir
directory='results/'+FILE_SUFFIX
if os.path.exists(directory):
    # If it exists, append a suffix until a non-existing directory name is found
    i = 1
    while True:
        directory = f"{directory}_{i}"
        print(directory)
        if not os.path.exists(directory):
            break
        i += 1

RESULTS_DIR=directory

# Create the directory
os.makedirs(RESULTS_DIR)
print("Directory", directory, "created successfully")

def get_classes_tiers():
    classes_manuelles=0
     #affecte la valeur "privé" aux catégories corresp, sinon va chercher dans CLASSIF, et fait un histogramme de tous les tiers
    
    classes_hist={cl:0 for cl in POSSIBLE_LABELS}#donnera l'histogramme
    missing=set()#entités sans note - devrait être vide
    #double_notation=[]#firmes qui ont reçu une note gpt par erreur, permet d'évaluer gpt
    synd_agro=0
    for t in tiers:
        print_debug(t)
        possible_names=[t]
        if t in other_names:
            possible_names+=other_names[t]
        classifs_of_t=[CLASSIF[n] for n in possible_names if n in CLASSIF]
        

        if t in firmes and firmes[t]['categorie'] in PRIVATE_LABELS:#on met 100 pour les privés
            classifs_of_t+=[{'classes':{'prive':100,'collectivite':0,'public':0,'syndicat':0},'explication':firmes[t]['categorie'],'manuel':True}]
        
        if len(classifs_of_t)==0:
            print_debug(t)
            print_debug('pas de note')
            missing.add(t)
            classifs_of_t=[{'classes':{'prive':25,'collectivite':25,'public':25,'syndicat':25},'explication':'client non tiers, pas répertorié, note arbitraire (mais négligeable, 144 en tout - a noter dans l idéal)'}]

        #confronter notes
        # d' abord tester s'il y a deux manual differents
        manual_found=False
        corr_classifs=[]
        for classif in classifs_of_t:
            printjs_debug(classif)
            for cl in ['prive','syndicat','public','collectivite']:#compléter par 0 les classes NA
                if cl not in classif['classes']:
                    classif['classes'][cl]=0
                classif['classes'][cl]=int(classif['classes'][cl])
            if 'manuel' in classif and classif['manuel']:
                if manual_found:
                    if 'explication' in classif and classif['explication']=="syndicat agricole":
                        synd_agro+=100
                    if classif['classes'] != manual_class['classes']:
                        printjs_debug(classif)
                        printjs_debug(manual_class)
                        print_debug(t)
                        print_debug('bizarre - double note manuelle')
                manual_found=True
                manual_class=classif

            if sum(classif['classes'].values())!=100:
                printjs_debug(classif)
                print_debug(sum(classif.values()))
                input('erreur total')
            corr_classifs+=[classif]
        if manual_found:
            classes_manuelles+=1
            tiers[t].update(manual_class)
        else:
            tiers[t].update({'manuel':False,'classes': {cl:np.mean([proba['classes'][cl] for proba in corr_classifs]) for cl in ['prive','syndicat','public','collectivite']}})

        
        
        classes_hist=add_values(classes_hist,tiers[t]['classes'])

    def random_elements(input_list, n):
        # Return a new list containing n randomly selected elements from the input list
        return random.sample(input_list, min(n, len(input_list)))
    

    public100={t for t in tiers if tiers[t]['classes']['public']==100}
    print(random_elements(public100,20))
    print('public100 sample')

    public75={t for t in tiers if tiers[t]['classes']['public']<100 and tiers[t]['classes']['public']>50}
    print(random_elements(public75,20))
    print('public75 sample')


    public50={t for t in tiers if tiers[t]['classes']['public']==50}
    print(random_elements(public50,20))
    print('public50 sample')


    prive100={t for t in tiers if tiers[t]['classes']['prive']==100}
    print(random_elements(prive100,20))
    print('prive100 sample')


    print_debug(missing)
    print('missing - note arbitraire, a noter dans l ideal',len(missing))


    print('classes')
    total=sum([classes_hist[cl] for cl in classes_hist])
    print({k:classes_hist[k]/total for k in classes_hist})
    plt.bar(POSSIBLE_LABELS,[classes_hist[cl] for cl in POSSIBLE_LABELS])
    plt.xlabel("Classes")
    plt.ylabel("Nombre de mandants")
    # print(double_notation)
    # print(np.mean(double_notation))
    # print(np.mean(confiances))

    # hist,_ = np.histogram(notes, bins=POSSIBLE_LABELS)

    # #xvals=[str(x) for x in bins[0:-1]]
    # # Créer un histogramme
    # plt.bar(bins[0:-1], hist)

    plt.title('Distribution interêt public/privé')# - Gini:'+str(gini))
    results['classes manuelles']=classes_manuelles
    results['classifs_tiers']=classes_hist
    s=sum([v for (k,v) in classes_hist.items()])
    results['classif_tiers_%']={k:100*v/s for (k,v) in classes_hist.items()}
    results['syndicats agricole']=synd_agro
    results['syndicats agricole_%']=synd_agro*100/s
    if SAMPLE=="all":
        print('save histogram')

        plt.savefig(RESULTS_DIR+'/classes-clients-'+FILE_SUFFIX+'.jpg', format='jpg')
    # Afficher l'histogramme
    #plt.show()
    plt.clf()

get_classes_tiers()

######correc outliers et calcule ressources par exercice

def treat_data_pb():
    global firmes
    global triplets_ressources
    global CORRECT_OUTLIERS
    global AGRESSIVE
    global seuils
    global transf
    print('treat data pb and compute ressources ******')

    #Basée sur les 10 ppv
    #on transform le budget éventuellement avec la fonction transf
    #ensuite on renormalise les triplets de données (dépenses, nbSalaries, poids_exercice)
    #pour chaque triplet avec 3 valeurs numérique (NAs=0), on regarde le zscore  par rapport aux 10 points qui sont des ppv par rapport aux 2 autres coordonnées
    #on le fait pour budget et nbSalaries, pas pour poids_exercice, car on considère que c'est plus difficile de se tromper dans la saisie
    #de plus, si une firme se trompe "de la même manière" pour ses poids_exercice, ce n'est pas grave vu qu'on renormalise
    #Si le zscore est plus grand (ou plus petit) que le seuil indiqué, on classifie comme outlier, et on stocke dans firmes[firme][période]{zscore,recommanded}
    #les seuils ont été choisis de manière empirique
    if CORRECT_OUTLIERS:
        if AGRESSIVE!="agressive":
            seuils=[[4.5,-3],[3.8,-1.4]]#conservateur
        else:
            seuils=[[3.5,-2],[3.5,-1.5]]#agressif

    #on pourra tester sans et avec correction

    #pour les NAs budget et nbSalaries, on les remplace par la moyenne des 10 ppv pour les 2 autres coord (ou juste le poids)


    # Calcul de la moyenne pour chaque coordonnée
    moyennes = np.mean(triplets_ressources, axis=0)
    # Calcul de l'écart type pour chaque coordonnée
    ecart_types = np.std(triplets_ressources, axis=0)
    #garder triplets originaux pour suivi
    triplets_renorm=(triplets_ressources-moyennes)/ecart_types
    #nuage de tous les poids
    poids_s=[t[2] for t in triplets_ressources]
    #paires de coordonnées renorm où i est exclu pour trouver les ppv
    triplets_coords={i: [  [t[j] for j in [0,1,2] if j!= i] for t in triplets_renorm  ]     for i in [0,1,2]}
    #on fit les ppv pour detect outliers depenses et nbSalaries
    montant_ttl_calcule=0
    salaries_ttl_calcule=0
    knn_model=[0,0,0]
    for i in [0,1]:
        knn_model[i]=NearestNeighbors(n_neighbors=11, algorithm='auto')
        knn_model[i].fit(triplets_coords[i])


    glob_corrected=[]
    glob_imputed=[]
    def ressource_formula(exercice):
        return float(exercice['montant'])+float(exercice['nbSalaries'])*COST_LOBBYIST
    def kNN(t,i,excl_index=True):#renvoie mean et std de la i-eme coord des 10 triplets dont les couples de coord j≠i sont les 10 ppv de [t[j],j≠i] parmi triplets_coords[i]
        couple_cible=np.array([ t[j] for j in [0,1,2] if j!= i ]).reshape(1, -1)
        #print('cible',couple_cible)
        dist, indices = knn_model[i].kneighbors(couple_cible)
        #print([triplets_renorm[j] for j in indices[0]])
        ppv = [round(triplets_renorm[j][i],3) for j in indices[0]]
        if excl_index:
            #print('before',ppv,dist)
            if sum(sum(dist))>0:
                try:
                    ppv.remove(round(t[i],3))
                except ValueError:
                    pass
        #print('ppv',ppv)
        return np.mean(ppv),max(np.std(ppv),.5)
    def closest_indices(target, values, n=10):#Trouve les indices des n valeurs les plus proches d'une valeur cible dans une liste de valeurs.
        """

        Args:
            target: La valeur cible.
            values: Une liste de valeurs.
            n (optionnel): Nombre de valeurs les plus proches à trouver. Par défaut, 10.

        Returns:
            Une liste des indices des n valeurs les plus proches de la cible.
        """
        # Création d'une liste d'indices associés aux valeurs
        indexed_values = list(enumerate(values))
        # Tri de la liste selon la distance à la cible
        indexed_values.sort(key=lambda x: abs(x[1] - target))
        # Sélection des n premiers indices
        closest_indices = [index for index, _ in indexed_values[:n]]
        return closest_indices

    #on va remplacer/corriger les ressources pour les firmes, et calculer le score ressource
    for f in firmes:
        firmes[f]['total ressources']=0
        for p in [p for p in firmes[f] if '20' in p]:#on détecte une période
            print_debug(f,p)
            ress=firmes[f][p].copy()
            t=[ress['montant'],ress['nbSalaries'],ress['poids_exercice']]
            print_debug(t)
            if t[2]==0:
                continue
            if t[0]!='NA':
                t[0]=(transf(t[0]))
            #print(t)
            nas = t.count("NA")
            print_debug('nas',nas)
            if nas==0:
                if not CORRECT_OUTLIERS:
                    firmes[f][p]['ressources']=1 if UNIFORM_RESS_ACTIONS else ressource_formula(firmes[f][p])
                    continue
                #print(t)
                t=(t-moyennes)/ecart_types
                #x=t[0]*ecart_types[0]+moyennes[0]
                #indice_t = next((index for index, triplet in enumerate(triplets_renorm) if np.allclose(triplet, t,atol=.001)), None)

                #print(t)#,triplets_renorm[indice_t])
                #détecter et remplacer
                nb_out=0
                outliers=[{'exceed':0},{'exceed':0}]
                for i in [0,1]:
                    print_debug('i',i)
                    real_value=t[i]
                    #print_debug('real',real_value)
                    m,s=kNN(t,i)
                    #print_debug(np.round(m,2))
                    zscore_ = ((real_value-m)/s)
                    #print_debug(np.round(zscore_,2))
                    if (zscore_)>seuils[i][0] or zscore_<seuils[i][1]:
                        nb_out+=1
                        m_back=ecart_types[i]*m+moyennes[i]
                        t_back_i=ecart_types[i]*t[i]+moyennes[i]
                        exceed=max( zscore_/seuils[i][0] , zscore_/ seuils[i][1])
                        #firmes[f][p]['outliers'][i]={'zscore_':np.round(zscore_,2),'exceed':np.round(exceed,2),'recommanded':round(m_back,2)}
                        if i==0:
                            m_back=transfinv(m_back)
                            t_back_i=transfinv(t_back_i)
                        print_debug(m_back)
                        outliers[i]={'exceed':exceed,"firme":f,'periode':p,'orig triplet':ress,'zscore':np.round(zscore_,2),'recommanded':round(m_back,2),'check':round(t_back_i,2)}
                    if nb_out>0 and i==1:
                        i_replace=0 if outliers[0]['exceed']>outliers[1]['exceed'] else 1#lequel on remplace?
                        key_replace = 'montant' if i_replace==0 else 'nbSalaries'
                        print_debug(i_replace,key_replace)
                        firmes[f][p][key_replace]=outliers[i_replace]['recommanded']
                        glob_corrected+=outliers

            elif nas==1:#necessarily nb salaries
                t[1]=0#pour éviter erreur type ligne suivante
                t=(t-moyennes)/ecart_types
                m,std=kNN(t,i=1,excl_index=False)
                replacement=round(m*ecart_types[1]+moyennes[1],2)
                print_debug('replacement',replacement)
                firmes[f][p]['nbSalaries']=replacement
                firmes[f][p]['imput value']=['nbSalaries; std='+str(np.round(std,2))]
                glob_imputed+=[{'firme':f,'periode':p,'orig_triplet':ress,'nb salariés imputé':replacement}]
                #idem, prioriser poids puis montant
            elif nas==2:#budget et nbsalaries
                #print_debug('poids',t[2])
                indexes=closest_indices(t[2], poids_s, n=10)
                #print_debug(indexes)
                similar_couples=[triplets_ressources[j][0:2] for j in indexes]
                #print_debug('couples',similar_couples)
                m=np.mean(similar_couples,axis=0)
                firmes[f][p]['montant']=transfinv(m[0])
                firmes[f][p]['nbSalaries']=m[1]
                firmes[f][p]['imput value']=['montant','nbSalaries']
                glob_imputed+=[{'firme':f,'periode':p,'orig_triplet':ress,'nb salariés imputé':firmes[f][p]['nbSalaries']},
                               {'firme':f,'periode':p,'orig_triplet':ress,'budget imputé':firmes[f][p]['montant']}]
            firmes[f][p]['ressources']=1 if UNIFORM_RESS_ACTIONS else ressource_formula(firmes[f][p])#formule ressources
            firmes[f]['total ressources']+=firmes[f][p]['ressources']
            montant_ttl_calcule+=firmes[f][p]['montant']
            salaries_ttl_calcule+=firmes[f][p]['nbSalaries']
        
    printjs_debug(glob_corrected)
    print('outliers corrected',len(glob_corrected))


    res_data_pb={'valeurs imputées':len(glob_imputed),'montant total calculé':montant_ttl_calcule,'salariés total calculé':salaries_ttl_calcule}
    printjs(res_data_pb)
    results['outliers et données manquantes']=res_data_pb

    
#     print_debug('outliers dépenses')
#     input(len(outliers[0]))
#
#     printjs_debug(outliers[1])
#     print('outliers nbSalariés')
#     input(len(outliers[1]))
#
#     for i in [0,1]:
#         print('sorted ** coord',i)
#         outliers[i] = sorted(outliers[i], key=lambda x: x['zscore'])
#         printjs_debug(outliers[i])
#         input('sorted coord'+str(i))


treat_data_pb()


printjs_debug(firmes)
print_debug('firmes',len(firmes))



def stats_secteurs():#basé sur secteurs des firmes, et non pas secteurs des actions. On pourrait comparer
    secteurs={}

    for firme in firmes:
        f=firmes[firme]
        t_ress=f['total ressources']
        secteurs_firme=[SECTEUR[s] for s in f['Secteurs']]
        nb_sec=len(secteurs_firme)

        if nb_sec==0:
            input('0 sec')
        ress_sec_f=t_ress/nb_sec
        for s in secteurs_firme:
            if s in secteurs:
                secteurs[s]+=ress_sec_f
            else:
                secteurs[s]=ress_sec_f

    print('secteurs')
    printjs(secteurs)

    results['secteurs']=secteurs
    sect_short=[]

    secteurs=dict(sorted(secteurs.items()))
    for s in secteurs:
        l=s.split(' ')
        sec=' '.join(l[0:3])
        if len(l)>3:
            sec+='...'
        sect_short+=[sec]
    # Emballer les labels pour les légendes longues
    def wrap_labels(labels, width):
        return ['\n'.join(textwrap.wrap(label, width)) for label in labels]
    bar_width = 0.5
    sect_short = wrap_labels(list(secteurs.keys()), 40)  # Ajustez le nombre 20 pour la largeur souhaitée
    resources = list(secteurs.values())

    # Créer une figure et un axe
    fig, ax = plt.subplots()

    # Créer les barres horizontales
    bars = ax.barh(range(len(secteurs)), resources, bar_width, color='skyblue')

    # Ajouter des étiquettes et un titre
    ax.set_ylabel('Secteurs')
    ax.set_xlabel('Ressources')
    ax.set_title('Secteurs: FILE_SUFFIX')
    ax.set_yticks(range(len(secteurs)))
    ax.set_yticklabels(sect_short, fontsize='small')

    # Ajuster les marges pour que les légendes soient entièrement visibles
    plt.subplots_adjust(left=0.4, top=0.9)

    #plt.title('Répartition des ressources des actions par influence')
    if SAMPLE=="all":
        plt.savefig(RESULTS_DIR+'/secteurs_by_firme_'+FILE_SUFFIX+'.jpg', format='jpg')
    # Afficher l'histogramme
    #plt.show()
    plt.clf()

stats_secteurs()

########ACTIONS

def ress_actions():

    print('browse actions...')
    ressources_actions=[]#pour faire un histogramme

    #on va calculer les ressources de chaque action, obtenu comme les ressources allouées par la firme à l'exercice contenant l'action, au prorata du poids de cette action
    #une action peut être effectuée sur plusieurs périodes et par plusieurs firmes, on calcule les ressources pour chaque occurence
    for act in actions:
        action=actions[act]
        print_debug(act,'*** ressources action')
        #printjs(action)
        for p in action:
            for f in action[p]:
                for code in action[p][f]:
                    #ressources
                    poids_ex=firmes[f][p]['poids_exercice']
                    ress_ex=firmes[f][p]['ressources']
                    ress_act=1 if UNIFORM_RESS_ACTIONS else ress_ex* action[p][f][code]['poids_abs']/poids_ex#in main loop, by exercise of formula
                    ressources_actions+=[ress_act]
                    if ress_act>1000000:

                        print(act)
                        print('big ressource, means the outliers work was not done properly :)')
                    actions[act][p][f][code]['ressources']=ress_act

                    

    results['intitulés actions']=len(actions)
    print('actions intitulés',len(actions))
    printjs_debug(actions)



    

    #def hist_values(valeurs,bins,xlab="Entrées",ylab="Valeurs",title='Histogramme des données'):
    if not UNIFORM_RESS_ACTIONS:
        # Calcul de l'histogramme

        ressources_actions=sorted(ressources_actions,reverse=True)
        bins=[4000*x for x in range(0,40)]+[1000000]+[10000000]
        hist,_ = np.histogram(ressources_actions, bins=bins)



        xvals=[str(x) for x in bins[0:-1]]
        # Créer un histogramme
        plt.bar(xvals, hist)

        # Ajouter des étiquettes et un titre
        plt.xlabel('Influence')
        plt.ylabel("Nombre d'actions")
        plt.title('Répartition des ressources des actions par influence')
        if SAMPLE=="all":
            plt.savefig(RESULTS_DIR+'/ressources_actions_'+FILE_SUFFIX+'.jpg', format='jpg')
        # Afficher l'histogramme
        #plt.show()
        plt.clf()




ress_actions()



def classif_actions_by_mean():#chaque action a comme classif la moyenne des classifs de ses tiers, on ajoute toutes les classifs d'actions pour avoir l'histogramme final, on fait aussi l'histogramme par secteur
    croise_secteur_classif={k:{c:0 for c in POSSIBLE_LABELS} for k in DOMAINE}
    croise_cibles_classif={c:{cl:0 for cl in POSSIBLE_LABELS} for c in CIBLES}
    actions_by_secteur={k:0 for k in DOMAINE}
    actions_by_classe={k:0 for k in POSSIBLE_LABELS}
    actions_by_cible={k:0 for k in CIBLES}
    ttl_ress_so_far=0
    print('classify actions by mean')
    for objet in actions:
        print_debug(objet[0:100]+'...')
        printjs_debug(actions[objet])
        for p in actions[objet]:
            for f in actions[objet][p]:
                for code in actions[objet][p][f]:
                    print_debug('new')
                    action=actions[objet][p][f][code]

                    ress_act=action['ressources']
                    ttl_ress_so_far+=ress_act
                    tiers_action_classifs=[tiers[t]['classes'] for t in action['tiers']]#toutes les classifs des tiers de cette action 
                    mean_classif_wgt={cl:ress_act*np.mean([classif[cl] for classif in tiers_action_classifs])/100 for cl in POSSIBLE_LABELS}#classif moyenne,multipliée par ressources de l'action, sums to ress_act
                    #'mettre au prorata s'il y a plusieurs domaines d'un meme secteur
                    secteurs_action={d:0 for d in DOMAINE}
                    for d in action['domaines']:
                        secteurs_action[SECTEUR[d]]+=ress_act/len(action['domaines'])#sums to ress_act
                    cibles_action={c:ress_act/len(action['cibles']) for c in action['cibles']}


                    actions_by_classe=add_values(actions_by_classe,mean_classif_wgt)
                    actions_by_secteur=add_values(actions_by_secteur,secteurs_action)
                    actions_by_cible=add_values(actions_by_cible,cibles_action)

                    for d in action['domaines']:
                        for cl in POSSIBLE_LABELS:
                            croise_secteur_classif[SECTEUR[d]][cl]+=mean_classif_wgt[cl]/len(action['domaines'])#sums to ress_act

                    for c in action['cibles']:
                        for cl in POSSIBLE_LABELS:
                            croise_cibles_classif[c][cl]+=mean_classif_wgt[cl]/len(action['cibles'])#sums to ress_act

                    printjs_debug(tiers_action_classifs)
                    print_debug(action['domaines'])
        ttl_ress_classes=sum([actions_by_classe[cl] for cl in POSSIBLE_LABELS])
        ttl_ress_sect=sum([actions_by_secteur[s] for s in DOMAINE])
        ttl_ress_cibles=sum([actions_by_cible[c] for c in CIBLES])
        ttl_ress_croise_secteurs= sum([sum([croise_secteur_classif[s][cl] for cl in POSSIBLE_LABELS]) for s in DOMAINE ])
        ttl_ress_croise_cibles= sum([sum([croise_cibles_classif[c][cl] for cl in POSSIBLE_LABELS]) for c in CIBLES ])
        print_debug(ttl_ress_classes,ttl_ress_sect ,ttl_ress_cibles,ttl_ress_croise_secteurs,ttl_ress_croise_cibles ,ttl_ress_so_far)
        # if round(ttl_ress_classes)!=round(ttl_ress_sect) or round(ttl_ress_sect)!=round(ttl_ress_croise) or round(ttl_ress_croise)!=round(ttl_ress_so_far):#check
        #     input('?')

              

    
    print('###')
    results.update({'actions_par_classe':actions_by_classe,'actions_par_secteur':actions_by_secteur,'croisement secteur/classif':croise_secteur_classif,'croisement cibles classif':croise_cibles_classif})
    print('check total',ttl_ress_so_far)


    with open(RESULTS_DIR+'/RESULTS-'+FILE_SUFFIX+'.json','w') as file:
        json.dump(results, file, indent = 4, separators = (',', ':'))#, sort_keys=True)
        file.truncate()



    if True:#SAMPLE=="all":

        #plot hist classif
        print('hist actions')
        plt.bar(POSSIBLE_LABELS,[actions_by_classe[cl] for cl in POSSIBLE_LABELS])
        plt.xlabel("Classes")
        plt.ylabel("Poids actions")
        plt.title('Distribution interêt public/privé')# - Gini:'+str(gini))
        plt.savefig(RESULTS_DIR+'/classifs_actions_'+FILE_SUFFIX+'.jpg', format='jpg')
        #plt.show()
        plt.clf()

        #plot hist secteur
        actions_by_secteur=dict(sorted(actions_by_secteur.items()))

        print('secteurs actions')
        printjs(actions_by_secteur)
        plt.bar(list(actions_by_secteur.keys()),[actions_by_secteur[d] for d in actions_by_secteur])
        plt.xlabel('Secteurs (actions)')
        plt.ylabel("Ressources")
        plt.title('Secteurs:'+FILE_SUFFIX)
        plt.xticks(rotation=90)
        plt.subplots_adjust(wspace=0.8)
        plt.subplots_adjust(bottom=.6) 

        plt.savefig(RESULTS_DIR+'/secteurs_actions_'+FILE_SUFFIX+'.jpg', format='jpg')
        #plt.show()
        plt.clf()

        #plot hist croisé secteurs

        # Extraire les noms des secteurs industriels et les données de financement
        secteurs = list(croise_secteur_classif.keys())
        financements_publics = [croise_secteur_classif[secteur]['public'] for secteur in secteurs]
        financements_prives = [croise_secteur_classif[secteur]['prive'] for secteur in secteurs]
        financements_syndicats = [croise_secteur_classif[secteur]['syndicat'] for secteur in secteurs]

        # Emballer les labels pour les légendes longues
        def wrap_labels(labels, width):
            return ['\n'.join(textwrap.wrap(label, width)) for label in labels]

        wrapped_labels = wrap_labels(secteurs, 40)  # Ajustez le nombre 20 pour la largeur souhaitée

        # Création de l'histogramme
        bar_width = 0.5
        index = range(len(secteurs))

        fig, ax = plt.subplots()

        bar1 = ax.barh(index, financements_publics, bar_width, label='Public')
        bar2 = ax.barh(index, financements_prives, bar_width, label='Privé', left=financements_publics)
        bar3 = ax.barh(index, financements_syndicats, bar_width, label='Syndicats',  left=np.array(financements_publics) + np.array(financements_prives))

        #bar3 = ax.bar(index, financements_syndicats, bar_width, label='Syndicats', bottom=financements_publics)

        ax.set_ylabel('Secteurs')
        ax.set_xlabel('Classe')
        ax.set_title('Répartition des classes par secteur industriel')
        ax.set_yticks(index)
        ax.set_yticklabels(secteurs, fontsize='small')
        plt.subplots_adjust(left=0.5)
        ax.legend()

        #ax.xticks(rotation=90)
        #ax.subplots_adjust(wspace=0.8)
        #ax.subplots_adjust(bottom=.6) 

        plt.savefig(RESULTS_DIR+'/croise_secteur_classif_actions_'+FILE_SUFFIX+'.jpg', format='jpg')
        #plt.show()
        plt.clf()


        #plot hist croisé secteurs 

        # Extraire les noms des secteurs industriels et les données de financement
        cibles = list(croise_cibles_classif.keys())
        financements_publics = [croise_cibles_classif[c]['public'] for c in cibles]
        financements_prives = [croise_cibles_classif[c]['prive'] for c in cibles]
        financements_syndicats = [croise_cibles_classif[c]['syndicat'] for c in cibles]


        # Emballer les labels pour les légendes longues
        def wrap_labels(labels, width):
            return ['\n'.join(textwrap.wrap(label, width)) for label in labels]

        wrapped_labels = wrap_labels(cibles, 40)  # Ajustez le nombre pour la largeur souhaitée

        # Création de l'histogramme
        bar_width = 0.5
        index = range(len(cibles))

        fig, ax = plt.subplots()

        bar1 = ax.barh(index, financements_publics, bar_width, label='Public')
        bar2 = ax.barh(index, financements_prives, bar_width, label='Privé', left=financements_publics)
        bar3 = ax.barh(index, financements_syndicats, bar_width, label='Syndicats',  left=np.array(financements_publics) + np.array(financements_prives))

        #bar3 = ax.bar(index, financements_syndicats, bar_width, label='Syndicats', bottom=financements_publics)

        ax.set_ylabel('Cibles')
        ax.set_xlabel('Classe')
        ax.set_title('Répartition des classes par cible')
        ax.set_yticks(index)
        ax.set_yticklabels(wrapped_labels, fontsize='small')
        plt.subplots_adjust(left=0.4)
        ax.legend()

        plt.savefig(RESULTS_DIR+'/croise_cibles_classif_actions_'+FILE_SUFFIX+'.jpg', format='jpg')
        #
        #plt.show()
        plt.clf()

classif_actions_by_mean()

printjs_debug(actions)
if not UNIFORM_RESS_ACTIONS and CORRECT_OUTLIERS:
    with open('actions.json','w') as file:
        json.dump({'params':FILE_SUFFIX,'actions':actions}, file, indent = 4, separators = (',', ':'))
        
exit()


########TIERS NOTATION
#la liste des tiers a été construite dans la boucle principale
#on va maintenant affecter une note à chaque tiers, soit en fonction de sa catégorie, soit fournie par chatGPT






def notes_tiers():
    #refaire avec la fonction hist_values
    notes=[]
    examples={i:[] for i in range(0,11)}
    missing=set()#entités sans note - devrait être vide
    double_notation=[]#firmes qui ont reçu une note gpt par erreur, permet d'évaluer gpt
    confiances=[]
    for t in tiers:
        print(t)
        if t in firmes and firmes[t]['categorie'] in PRIVATE_LABELS:#on met 10
            print(firmes[t])
            if 'note' in tiers[t]:#on confronte avec la note gpt pour voir
                print('déjà une note')
                printjs(tiers[t]['note'])
                double_notation+=[tiers[t]['note']['score']]
                confiances+=[tiers[t]['note']['confiance']]
            tiers[t]['note']={'score':10,'confiance':10,'explication':firmes[t]['categorie']}
        elif not 'note' in tiers[t]:#note manquante- ne devrait pas arriver
            if t in firmes:
                print(firmes[t]['categorie'],firmes[t]['categorie'] in PRIVATE_LABELS)
            print('grade missing')
            missing.add(t)
        score=tiers[t]['note']['score']
        notes+=[score]
        if len(examples[score])<20:
            examples[score]+=[t]

    print(double_notation)
    print(np.mean(double_notation))
    print(np.mean(confiances))


    printjs(examples)
    print('notes')

    bins=[x for x in range(0,11)]
    hist,_ = np.histogram(notes, bins=bins)


    gini=int(100*gini_coefficient(hist))
    print('Gini',gini)


    print(bins)
    print(hist)
    #xvals=[str(x) for x in bins[0:-1]]
    # Créer un histogramme
    plt.bar(bins[0:-1], hist)

    # Ajouter des étiquettes et un titre
    plt.xlabel('Interêt privé')
    plt.ylabel("Nombre de mandants")
    plt.title('Distribution interêt public/privé - Gini:'+str(gini))

    if SAMPLE=="all":
        plt.savefig(RESULTS_DIR+'/notes-clients-'+FILE_SUFFIX+'-gini-'+str(gini)+'.jpg', format='jpg')
    # Afficher l'histogramme
    #plt.show()
    plt.clf()




######calcul notes actions

counter=0
influences=[0]*11#va récolter la somme des influences des actions ayant une note donnée
#on pourra rafiner
for act in actions:
    counter=counter+1
    print(counter,'/',len(actions.keys()))
    action=actions[act]
    print(act,'*** note')

    for p in action:
        for f in action[p]:
            for code in action[p][f]:#on calcule la note de l'action
                ttl=0
                nb_tiers=len(action[p][f][code]['tiers'])
                print(nb_tiers,'tiers mandant')
                for t in action[p][f][code]['tiers']:
                    ttl+=tiers[t]['note']['score']
                score_action=round(ttl/nb_tiers,2)
                actions[act][p][f][code]['note']=score_action
                print(score_action)
                ress_act=1 if UNIFORM_RESS_ACTIONS else action[p][f][code]['ressources']
                influences[int(score_action)]+=ress_act
                #if len(notes_action)>1:
                #    actions[act]['std']=round(np.std(notes_action),2)

printjs(actions)
print('actions')



gini=str(int(100*gini_coefficient(influences)))

#notes_actions=[actions[act]['note'] for act in actions]
#plt.hist(notes_actions, bins=10, edgecolor='black')  # bins peut être ajusté selon vos besoins

bins=[x for x in range(0,11)]
plt.bar(bins,influences)

plt.xlabel("Interêt privé")
plt.ylabel("Influence")
plt.title("Actions par notes pondérées par l'influence - Gini:"+gini)

# Sauvegarder le plot en format JPG
if SAMPLE=="all":
    plt.savefig(RESULTS_DIR+'/influence-interet-'+FILE_SUFFIX+'-gini-'+gini+'.jpg', format='jpg')

# Afficher l'histogramme
#plt.show()
plt.clf()
