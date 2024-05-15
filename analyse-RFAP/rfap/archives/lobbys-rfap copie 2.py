import json
from datetime import date
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
#ressources=[]#montants et nombreSalaries pour calculer corrélation
#ressources_num=[]
triplets_ressources=[]
missing=set()
#avail_ress={}
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

        if 'activites' in ex:
            if len(ex['activites'])<int(ex['nombreActivite']):
                print(len(ex['activites']),ex['nombreActivite'])
                print('manque activité(s)')
            for act in ex['activites']:
                dict=act['publicationCourante']
                #if 'domainesIntervention' in act:
                #print(dict['domainesIntervention'])
                #print('domaines: '+str(dict['domainesIntervention'])+" ***")
                action=fusionner_dictionnaires(dict['actionsRepresentationInteret'])
                poids_action=5#1+len(action['tiers'])+len(action['actionsMenees'])+len(action['decisionsConcernees'])+len(action['reponsablesPublics'])
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

        #####pour corrections outliers:
        # if periode not in avail_ress:
        #     avail_ress[periode]={'salaries':{},"dépenses":{},'total':1}
        # else:
        #     avail_ress[periode]['total']+=1

        #détern montant et nbsalariés
        if 'montantDepense' in ex:
            print(ex['montantDepense'],ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =',''))
            montant=int(ex['montantDepense'].split('<')[-1].replace('euros','').replace('> =','').replace(' ',''))
        else:
            montant='NA'
        if 'nombreSalaries' in ex and int(ex['nombreSalaries'])>0 and int(ex['nombreSalaries'])<42:
            salaries=int(ex['nombreSalaries'])
        else:
            salaries='NA'

        #
        if not 'activites' in ex or len(ex['activites'])==0:
            if montant!='NA' or int(ex['nombreActivite'])>0:# or x['noActivite']=='true'):#on comptabilise une action
                actions['action inconnue']={periode:{nom:{'XXXX':{'tiers':nom,'poids_abs':5}}}}
                poids_activites_exercice=5
            else:
                continue
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
        try:
            triplets_ressources+=[((math.log(int(montant))),int(salaries),int(poids_activites_exercice))]
            triplet=True
        except:
            print('données manquantes')
        firmes[nom][periode]={'montant':montant,'nbSalaries':salaries,'poids_exercice':poids_activites_exercice,'triplet':True,'outliers':{}}


######correc outliers des ressources par exercice

#Basée sur les 10 ppv
#on prend le log du budget
#ensuite on renormalise les triplets de données
#pour chaque triplet avec 3 valeurs numérique (NAs=0), on regarde le zscore  par rapport aux 10 points qui sont des ppv par rapport aux 2 autres coordonnées
#on le fait pour budget et nbSalaries, pas pour poids_exercice, car on considère que c'est plus difficile de se tromper dans la saisie pour ças
#de plus, si une firme se trompe "de la même manière" pour ses poids_exercice, ce n'est pas grave vu qu'on renormalise
#Si le zscore est plus grand (ou plus petit) que le seuil indiqué, on classifie comme outlier, et on stocke dans firmes[firme][période]{zscore,recommanded}
#les seuils ont été choisis de manière empirique
#on pourra tester sans et avec correction

# Calcul de la moyenne pour chaque coordonnée
moyennes = np.mean(triplets_ressources, axis=0)

# Calcul de l'écart type pour chaque coordonnée
ecart_types = np.std(triplets_ressources, axis=0)

triplets_ressources=(triplets_ressources-moyennes)/ecart_types

#paires de coordonnées où i est exclu
triplets_coords={i: [  [t[j] for j in [0,1,2] if j!= i] for t in triplets_ressources  ]     for i in [0,1,2]}

knn_model=[0,1,2]
for i in [0,1,2]:
    knn_model[i]=NearestNeighbors(n_neighbors=11, algorithm='auto')
    knn_model[i].fit(triplets_coords[i])

outliers=[[],[]]
seuil=[[4.5,-3],[3.8,-1.4]]

def kNN(t,i):#renvoie mean et std de la i-eme valeur des 10 triplets dont les couples de coord j≠i sont les 10 ppv de [t[j],j≠i] parmi triplets_coords[i]
    couple_cible=np.array([ t[j] for j in [0,1,2] if j!= i ]).reshape(1, -1)
    print('cible',couple_cible)
    res, indices = knn_model[i].kneighbors(couple_cible)
    print(indices,res,triplets_ressources[indices])
    for j,val in enumerate(indices[0]):
        print('j',j,val,triplets_ressources[j],t)
        print(np.allclose(triplets_ressources[val],t,atol=.001))
    print([j for j, val in enumerate(indices[0]) if np.allclose(triplets_ressources[val],t,atol=.001)])
    index_excl=next((j for j, val in enumerate(indices[0]) if np.allclose(triplets_ressources[val],t,atol=.001)),None)
    print(index_excl)
    ppv = [triplets_ressources[j][i] for j in indices[0] if j!= index_excl]
    print('ppv',ppv)


for f in firmes:
    for p in [p for p in firmes[f] if p.startswith('20')]:
        print(f,p)
        ress=firmes[f][p]
        t=[ress['montant'],ress['nbSalaries'],ress['poids_exercice']]
        print(t)
        if t[0]!='NA':
            t[0]=(math.log(t[0]))
        nas = t.count("NA")
        print('nas',nas)
        if nas==0:
            print(t)
            t=(t-moyennes)/ecart_types
            x=t[0]*ecart_types[0]+moyennes[0]
            #indice_t = next((index for index, triplet in enumerate(triplets_ressources) if np.allclose(triplet, t,atol=.001)), None)

            print(t)#,triplets_ressources[indice_t])
            #détecter et remplacer
            for i in [0,1]:
                print('i',i)
                real_value=t[i]
                print('real',real_value)
                couple_cible=np.array([ t[j] for j in [0,1,2] if j!= i ]).reshape(1, -1)
                print('cible',couple_cible)
                _, indices = knn_model[i].kneighbors(couple_cible)
                print(indices)
                index_excl=next((j for j, val in enumerate(indices[0]) if np.allclose(triplets_ressources[j],t,atol=.001)),None)
                print(index_excl)
                ppv = [triplets_ressources[j][i] for j in indices[0] if j!= index_excl]
                print('ppv',ppv)
                kNN(t,i)
                m=np.mean(ppv)
                s=max(np.std(ppv),.5)
                #m,s=kNN(triplet=t,indice=i)
                print(np.round(m,2))
                zscore_ = ((real_value-m)/s)
                print(np.round(zscore_,2))
                if (zscore_)>seuil[i][0] or zscore_<seuil[i][1]:
                    m_back=ecart_types[i]*m+moyennes[i]
                    t_back_i=ecart_types[i]*t[i]+moyennes[i]
                    if i==0:
                        m_back=math.exp(m_back)
                        t_back_i=math.exp(t_back_i)
                    outliers[i]+=[{"firme":f,'periode':p,'orig triplet':ress,'zscore':np.round(zscore_,2),'recommanded':round(m_back,2),'check':round(t_back_i,2)}]
                    firmes[f][p]['outliers'][i]={'zscore':np.round(zscore_,2),'recommanded':round(m_back,2)}
                    printjs(firmes[f][p])

        if nas==1:
            continue
            for i in [0,1,2]:
                if t[i]=='NA':
                    replacement,std=kNN(t,i)
            #idem, prioriser poids puis montant
        if nas==2:
            pass
            #erreur si pas poids, sinon inférer à partir de poids

printjs(outliers[0])
input(len(outliers[0]))

printjs(outliers[1])
input(len(outliers[1]))

for i in [0,1]:
    print('sorted **',i)
    outliers[i] = sorted(outliers[i], key=lambda x: x['zscore'])
    printjs(outliers[i])
    input('?'+str(i))


# def sq_norm(a):
#     return a[0]*a[0]+a[1]*a[1]+a[2]*a[2]
#
# mean_ress=np.mean(triplets_ressources,axis=0)
# std_ress=np.std(triplets_ressources,axis=0)
# print(std_ress)
# input(mean_ress)
#
# for t in triplets_ressources:
#     print(t)
#     zscore=(t-mean_ress)/std_ress
#     print(zscore)
#     if sq_norm(zscore)>5:
#         print(t,sq_norm(zscore))
#         input(zscore)
# #
# # Calcul des z-scores pour chaque coordonnée
# z_scores = zscore(triplets_ressources, axis=0)
#
#
# # Détection des indices des outliers
# outlier_indices = np.abs(z_scores) > 3  # Seuil fixé à 3 fois l'écart type
#
# input(outlier_indices[0:100])
#
# # Traitement des outliers en remplaçant les valeurs aberrantes par une moyenne sur les deux autres coordonnées
# for i, outlier_index in enumerate(outlier_indices):
#     print(i,triplets_ressources[i],outlier_index)
#     for j, is_outlier in enumerate(outlier_index):
#         print(j,'outlier',is_outlier)
#         if is_outlier:
#             valid_values = triplets_ressources[i][np.logical_not(outlier_index)]
#             input(valid_values)
#             triplets[i][j] = np.mean(valid_values)
#
# # Détection des indices des outliers
# outlier_indices = np.abs(z_scores) > 3  # Vous pouvez ajuster ce seuil selon vos besoins
#
#
# printjs(triplets_ressources[outlier_indices[0:20]])
# input('?')
#
#
# # Traitement des outliers en remplaçant les valeurs aberrantes par la moyenne des deux autres coordonnées
# for i, outlier_index in enumerate(outlier_indices):
#     for j, is_outlier in enumerate(outlier_index):
#         if is_outlier:
#             valid_values = triplets[i][np.logical_not(outlier_index)]
#             triplets[i][j] = np.mean(valid_values)
#
# print("Triplets après correction des outliers :\n", triplets)

#########STATS RESSOURCES

def imput_valeur(nombre, dictionnaire,window=3):#retourne les valeurs moyennes des n clés les plus proches (n=window)
    print('imput valeur',nombre)
    #printjs(dictionnaire)
    # Calculer les écarts absolus entre la clé donnée et les clés du dictionnaire
    ecarts_absolus = {abs(float(cle) - nombre): cle for cle in dictionnaire.keys()}

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

def carre(x):
    return x*x
# def detect_outlier(nombre,valeur,dictionnaire):
#     ecarts_absolus = {abs(float(cle) - nombre): cle for cle in dictionnaire.keys()}
#     cles_proches = [ecarts_absolus[ecart] for ecart in sorted(ecarts_absolus.keys())[:10]]
#
#     valeurs = []
#     for cle in cles_proches:
#         valeurs.extend(map(int, dictionnaire[cle]))
#
#
#
# print(avail_ress.keys())
# #bilan ressources
valeurs_montants = [x[0] for x in triplets_ressources]
valeurs_salaries = [x[1] for x in triplets_ressources]

# print('*** montants_act - salaries_act')
# printjs(montants_act)
# printjs(salaries_act)

#calcul des moyennes et moyennes conditionnelles
def moyenne(liste):
    return sum(liste)/len(liste)
#
# montant_moyen=moyenne(valeurs_montants)
# salaries_moyen=moyenne(valeurs_salaries)
#
# print("montant moyeb",montant_moyen)
# print('salaries_moyen',salaries_moyen)
# print('ratio',montant_moyen/salaries_moyen)

montant_moyen_s={}
salaries_moyen_s={}
for m in valeurs_montants:
    if m not in salaries_moyen_s:
        salaries_moyen_s[int(m)]=[ress[1] for ress in triplets_ressources if ress[0]==m]
for s in valeurs_salaries:
    if s not in montant_moyen_s:
        montant_moyen_s[int(s)]=[ress[0] for ress in triplets_ressources if ress[1]==s]

# json.dumps(montant_moyen_s, indent=4, sort_keys=True, ensure_ascii=False)
# json.dumps(salaries_moyen_s, indent=4, sort_keys=True, ensure_ascii=False)


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
# correlation = np.corrcoef(valeurs_montants, valeurs_salaries)
#
# # Tracé du nuage de points
# # plt.scatter(premieres_valeurs, deuxiemes_valeurs, color='blue', alpha=0.5)
# # plt.title('Nuage de points')
# # plt.xlabel('Premières valeurs')
# # plt.ylabel('Deuxièmes valeurs')
# # plt.grid(True)
# #plt.show()
# print('correlation',correlation)#=.29743457

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
