import json
from datetime import date
import sys
import collections
import os
import shutil
import re
import unicodedata
import numpy as np

import matplotlib.pyplot as plt
#prgm utilisé pour article RFAP
#voir fichier lobbys-pxg.py pour traiter les données pour la visualisation pxg,
#ou pour faire des recherches insee


sample="all" #n premieres entrees uniquement (pour dev), ou "all"
sampleStr="-sample"+str(sample) if sample else ""


verbosis=True



def printjs(s):
    if verbosis:
        print(json.dumps(s, indent=4, sort_keys=False, ensure_ascii=False))


def fusionner_dictionnaires(liste_de_dicts):
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



today = str(date.today())
print( today)

#save=False


#now: check that all nodes and tiers from "lobbys" are in "to_grade" or "results-gpt"

with open('openAI/results-gpt.json', 'r') as fich:#already graded
    results_gpt = json.load(fich)
with open('openAI/to-grade.json') as f:#elements fichier lobbys.json matched
    to_grade = json.load(f)
with open('agora_repertoire_opendata.json') as f:#elements fichier lobbys.json matched
    data = json.load(f)['publications']




if sample!="all":
    data=data[0:sample]
# Iterating through the json
# list


def best_nom(firme):
    try:
        return firme['nomUsageHatvp']
    except KeyError:
        try:
            return firme['nomUsage']
        except KeyError:
            return firme['denomination']


firmes={}
actions={}
tiers={}
ressources=[]#montants et nombreSalaries pour calculer corrélation
ressources_num=[]
missing=set()
avail_ress={}
montants_act={}#montants pour poids activité donnée
salaries_act={}#salaries ...
counter=0


for firme in data:
    #allKeys |= set(firme.keys())
    counter=counter+1
    #printjs(firme)
    print(counter,'/',len(data))
    print('********')
    nom=best_nom(firme)



    print(nom)

    lab=firme['categorieOrganisation']['label']

    print('label: '+lab)

    ident=firme['typeIdentifiantNational']+str(firme['identifiantNational'])
    if nom in firmes:
        nom=nom+' * '+firme['denomination']
        if nom in firmes:
            nom=nom+' * '+ident
            if nom in firmes:
                input('really?')
        #print('nom doublon',nom)
        #input('?')
    print(nom)
    url='https://www.hatvp.fr/fiche-organisation/?organisation='
    if ident.startswith('SIREN'):
        url+=ident.replace('SIREN','')
    elif ident.startswith('HATVPH'):
        url+=ident.replace('HATVPH','H')
    elif ident.startswith('RNAW'):
        url+=ident.replace('RNAW','W')
    else:
        print(ident)
        input('?')
    firmes[nom]={'identifiant':ident,
                    'categorie':firme['categorieOrganisation']['label'],
                    'affiliations':firme['affiliations'],
                    'Nom complet':firme['denomination'],
                    'url':url}
    #il faudrait faire afficher les options par plexigraf

    print('******exercices')

    for ex in firme['exercices']:
        ex=ex['publicationCourante']

        poids_activites_exercice=0

        periode=ex['dateDebut'][6:]+'-'+ex['dateFin'][6:]
        if periode not in avail_ress:
            avail_ress[periode]={'salaries':{},"dépenses":{},'total':1}
        else:
            avail_ress[periode]['total']+=1
        if 'montantDepense' in ex:
            print(ex['montantDepense'],ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =',''))
            montant=int(ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =','').replace(' ',''))
        else:
            montant='NA'
        if 'nombreSalaries' in ex and int(ex['nombreSalaries'])>0 and int(ex['nombreSalaries'])<42:
            salaries=int(ex['nombreSalaries'])
        else:
            salaries='NA'
        print(montant,salaries)
        try:
            ressources_num+=[(int(montant),int(salaries))]
        except:
            print('données manquantes')
        ressources+=[(montant,salaries)]

        if montant in avail_ress[periode]['dépenses']:
            avail_ress[periode]['dépenses'][montant]+=1
        else:
            avail_ress[periode]['dépenses'][montant]=1
        if salaries in avail_ress[periode]['salaries']:
            avail_ress[periode]['salaries'][salaries]+=1
        else:
            avail_ress[periode]['salaries'][salaries]=1

        firmes[nom][periode]={'montant':montant,'nbSalaries':salaries}
        if not 'activites' in ex or len(ex['activites'])==0:
            if montant=='NA' and int(ex['nombreActivite'])==0:# or x['noActivite']=='true'):
                continue
            else:
                actions['action inconnue']={periode:{nom:{'XXXX':{'tiers':nom,'poids_abs':5}}}}
                poids_activites_exercice=5
        else:
            if len(ex['activites'])<int(ex['nombreActivite']):
                print(len(ex['activites']),ex['nombreActivite'])
                print('manque activité(s)')
            for act in ex['activites']:
                dict=act['publicationCourante']
                #if 'domainesIntervention' in act:
                #print(dict['domainesIntervention'])
                #print('domaines: '+str(dict['domainesIntervention'])+" ***")
                action=fusionner_dictionnaires(dict['actionsRepresentationInteret'])
                poids_action=1+len(action['tiers'])+len(action['actionsMenees'])+len(action['decisionsConcernees'])+len(action['reponsablesPublics'])
                poids_activites_exercice+=poids_action
                #score_action=len(action['actionsMenees'])#a completer: reponsablesPublics, decisionsConcernees
                objet=dict['objet']
                if objet not in actions:
                    actions[objet]={}
                if periode not in actions[objet]:
                    actions[objet][periode]={}
                if nom not in actions[objet][periode]:
                    actions[objet][periode][nom]={}
                actions[objet][periode][nom][dict['identifiantFiche']]={'tiers':action['tiers'],'poids_abs':poids_action}

                action_tiers_modif=[]
                for t in action['tiers']:
                    print(t)
                    if 'en propre' in t or t == firme['denomination'] or t==nom:
                        t=best_nom(firme)
                    if t not in tiers:
                        tiers[t]={'actions':[objet]}
                    else:
                        tiers[t]['actions']+=[objet]
                    if t not in results_gpt and firme['denomination'] not in results_gpt and firme['nomUsage'] not in results_gpt and firme['nomUsageHatvp'] not in results_gpt and t not in missing:
                        print(t,'en propre' in t)
                        input('missing')
                        missing.add(t)
                    action_tiers_modif+=[t]

                actions[objet][periode][nom][dict['identifiantFiche']]={'tiers':action_tiers_modif,'poids_abs':poids_action}
        if poids_activites_exercice>10000:
            print('gros ex')
        try:
            try:
                montants_act[poids_activites_exercice]+=[int(montant)]
            except:
                montants_act[poids_activites_exercice]=[int(montant)]
        except ValueError:
            pass
        try:
            try:
                salaries_act[poids_activites_exercice]+=[int(salaries)]
            except:
                salaries_act[poids_activites_exercice]=[int(salaries)]
        except ValueError:
            pass
        firmes[nom][periode]['poids_exercice']=poids_activites_exercice



#########STATS RESSOURCES

def imput_valeur(nombre, dictionnaire,window=3):#retourne les valeurs moyennes des n clés les plus proches (n=window)
    print('imput valeur',nombre)
    #printjs(dictionnaire)
    # Calculer les écarts absolus entre la clé donnée et les clés du dictionnaire
    ecarts_absolus = {abs(int(cle) - nombre): cle for cle in dictionnaire.keys()}

    # Trier les clés selon les écarts absolus et sélectionner les 5 plus proches
    cles_proches = [ecarts_absolus[ecart] for ecart in sorted(ecarts_absolus.keys())[:window]]
    #print('cles proches',cles_proches)
    # Extraire les valeurs associées aux clés sélectionnées et calculer leur moyenne
    valeurs = []
    for cle in cles_proches:
        valeurs.extend(map(int, dictionnaire[cle]))

    #print('valeurs',valeurs)
    # Calculer la moyenne des valeurs
    moyenne = sum(valeurs) / len(valeurs) if valeurs else None
    print(moyenne)
    return moyenne


printjs(avail_ress)

print(avail_ress.keys())
#bilan ressources
valeurs_montants = [x[0] for x in ressources_num]
valeurs_salaries = [x[1] for x in ressources_num]

print('*** montants_act - salaries_act')
printjs(montants_act)
printjs(salaries_act)

#calcul des moyennes et moyennes conditionnelles
def moyenne(liste):
    return sum(liste)/len(liste)

montant_moyen=moyenne(valeurs_montants)
salaries_moyen=moyenne(valeurs_salaries)

print("montant moyeb",montant_moyen)
print('salaries_moyen',salaries_moyen)
print('ratio',montant_moyen/salaries_moyen)

montant_moyen_s={}
salaries_moyen_s={}
for m in valeurs_montants:
    if m not in salaries_moyen_s:
        salaries_moyen_s[int(m)]=[ress[1] for ress in ressources_num if ress[0]==m]
for s in valeurs_salaries:
    if s not in montant_moyen_s:
        montant_moyen_s[int(s)]=[ress[0] for ress in ressources_num if ress[1]==s]

json.dumps(montant_moyen_s, indent=4, sort_keys=True, ensure_ascii=False)
json.dumps(salaries_moyen_s, indent=4, sort_keys=True, ensure_ascii=False)


def afficher_histogramme(data):
    # Trier les données par clé
    data_trie = sorted(data.items())

    # Extraire les clés et les valeurs
    cles = [k for k, v in data_trie]
    valeurs = [v for k, v in data_trie]

    # Créer un histogramme
    plt.bar(cles, valeurs)

    # Ajouter des étiquettes et un titre
    plt.xlabel('Entrées')
    plt.ylabel('Valeurs')
    plt.title('Histogramme des données')

    # Afficher l'histogramme
    plt.show()

#afficher_histogramme(salaries_moyen_s)
#afficher_histogramme(montant_moyen_s)

# Calcul de la corrélation entre les deux séries de valeurs
correlation = np.corrcoef(valeurs_montants, valeurs_salaries)

# Tracé du nuage de points
# plt.scatter(premieres_valeurs, deuxiemes_valeurs, color='blue', alpha=0.5)
# plt.title('Nuage de points')
# plt.xlabel('Premières valeurs')
# plt.ylabel('Deuxièmes valeurs')
# plt.grid(True)
#plt.show()
print('correlation',correlation)#=.29743457

########FIRMES

#imputer valeurs manquantes en cherchant valeurs propres montant/salaries, ou nb activites si pas dispo
for f in firmes:
    print(firmes[f])
    for p in [p for p in firmes[f] if p.startswith('20')]:#test si key est péruiode
        if 'poids_exercice' in firmes[f][p]:
            montant=firmes[f][p]['montant']
            salaries=firmes[f][p]['nbSalaries']
            poids_act=firmes[f][p]['poids_exercice']
            impute='aucun'
            if montant=='NA' and salaries=='NA':
                montant=imput_valeur(poids_act,montants_act)
                salaries=imput_valeur(poids_act,salaries_act)
                impute='both'
            elif montant=='NA':
                montant=imput_valeur(salaries,montant_moyen_s,5)
                impute='montant'
            elif salaries=='NA':
                salaries=imput_valeur(montant,salaries_moyen_s,5)
                impute='salaries'
            firmes[f][p]['montant']=float(montant)
            firmes[f][p]['nbSalaries']=float(salaries)
            firmes[f][p]['ressources']=montant+salaries*30000#formule ressources
            firmes[f][p]['imputé']=impute

printjs(firmes)


########ACTIONS

influences=[]

for act in actions:
    action=actions[act]
    print(act,'*** influence')
    for p in action:
        for f in action[p]:
            for code in action[p][f]:
                printjs(action[p][f])
                printjs(firmes[f][p])
                poids_ex=firmes[f][p]['poids_exercice']
                ress=firmes[f][p]['ressources']
                inf=ress* action[p][f][code]['poids_abs']/poids_ex
                influences+=[inf]
                if inf>1000000:
                    input('big inf')
                actions[act][p][f][code]['influence']=inf


printjs(actions)
print('actions',len(actions))


influences=sorted(influences,reverse=True)
input(influences[0:10])

print(influences)
#influences=[13333.333333333334, 8333.333333333334, 8333.333333333334, 25714.285714285714, 14285.714285714286]
plt.hist(influences, bins=150, color='blue', edgecolor='black')

# Ajout de titres et étiquettes
plt.title('Histogramme des influences')
plt.xlabel('Valeurs')
plt.ylabel('Fréquence')

# Affichage de l'histogramme
plt.show()


########TIERS NOTATION

printjs(tiers)

notes_labels=['Société commerciale',
'Société civile (autre que cabinet d’avocats)',
'Cabinets d’avocats',
'Avocat indépendant',
'Cabinet de conseil',
'Consultant indépendant',
'Cabinet de conseil',
"Organisation professionnelle",
"Fédération professionnelle",
"Travailleur indépendant",
"Société commerciale et civile (autre que cabinet d’avocats et société de conseil)"]


notes={}
for i in range(0,11):
    notes[i]={'nb':0,'exemples':[]}

for t in tiers:
    if t in firmes and firmes[t]['categorie'] in notes_labels:
        print(firmes[t])
        note={'score':10,'confiance':10,'explication':firmes[t]['categorie']}
    elif t in results_gpt:
        note=results_gpt[t]
    tiers[t]['note']=note
    notes[note['score']]['nb']+=1
    if notes[note['score']]['nb']<10:
        notes[note['score']]['exemples']+=[t]

printjs(notes)
print('notes')

    #x=raw_input('press any key')

print('found '+str(found))
print('missing',len(sorted(missing)))
print('results gpt',results_gpt_count)
print('to grade',to_grade_count)
print('to grade new',len(missing))
input('???')
input('CAP BOURBON' in to_grade)
with open('openAI/to-grade.json','w') as fichier:
        json.dump(to_grade, fichier, indent=4)
exit()

# Closing file
print("###############activites non publiees",unpublished)

print("###############appartenance non declaree",pasAppart)
print('###############labs')
printjs(collections.Counter(labs))
printjs(collections.Counter(lib_objet_social1s))
print('***objets')
printjs(pas_dobjet)
input('pas d objet',len(pas_dobjet))

printjs(collections.Counter(lib_activite_principales))
input('***activite principale')


printjs(collections.Counter(lib_theme1s))
input('***theme')

print("###############pas d'affil",collections.Counter(pasdaffil))
print('###############pas de secteur',nosecteur)
print('############ occurences')
printjs(occurs)



lookForAffilsSector=False
if lookForAffilsSector:
    valid_sect={}
    counter=0
    total=0
    plusQue3=0
    for o in occurs:
        total+=1
        keep=False
        groupe=occurs[o]
        sect=groupe['secteurs']
        if len(sect)==1:#il est valide s'il n'a qu'un secteur
            main_sect=sect.keys()[0]
            keep=True
        elif groupe['total']>2:#cette affil apparait 3 fois ou plus
            plusQue3+=1
            values = sorted(sect.values(),reverse=True)
            if values[0]>values[1]+1 or values[0]==groupe['total']:
                keep=True
                main_sect=[k for k,v in sect.items() if v==values[0]][0]
            print(o)
            printjs(groupe)
        if keep:
            counter+=1
            valid_sect[o]=main_sect

    printjs(valid_sect)
    print(counter,'sur',total,plusQue3)

print(identifiants_firmes)
print(identifiants_affiliations)

print("intersection affil",identifiants_firmes.intersection(identifiants_affiliations))
print("difference affils",identifiants_affiliations.difference(identifiants_firmes))
print('intersection clients',identifiants_firmes.intersection(identifiants_clients))
print('diff clients',identifiants_clients.difference(identifiants_firmes))
#print('all keys',allKeys)

# Get the first 1000 keys
print(list(nodes.keys())[:1000])


with open("lobbys"+version+".json", "w+") as jsonFile:
        jsonFile.seek(0)
        result={"nodes":nodes,"links":links,"params":{
  "description" : "Ceci est une visualisation des registre des représentants d'interêt publiés sur le site de la HATVP",
  "displayFiliation" : False,
  "hierarchyInfo" : False,
  "inheritPicFromChild" : False,
  "oldNodesNumber" : 3,
  "defaultInfoWidth": 500,
  "cutStringLength": 40,
  "dispLinksWithWithoutType": False
}
}
        json.dump(result, jsonFile, indent = 4, separators = (',', ':'))#, sort_keys=True)
        jsonFile.truncate()
