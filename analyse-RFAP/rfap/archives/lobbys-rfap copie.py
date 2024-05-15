

correct_outliers=False#remplacer les valeurs aberrantes
out_str=str(correct_outliers)
if correct_outliers:#pour corriger les budgets des assos de lobbying
    agressive="agressive"
    deform="ln"# #fonction de déformation du budget pour détecter les outliers, possibilités: "id"; "ln", "sqrt", ...
    out_str+='-'+agressive+'-'+deform
sample="all" #n premieres entrees uniquement (pour dev), ou "all"
sampleStr="-sample"+str(sample) if sample else ""
uniform_ress_actions=True#toutes les actions ont les memes ressources

if uniform_ress_actions:
    uniform_weight=True#not really used
    str_wgt_actions="unif-"
else:
    uniform_weight=False#chaque action a la même ressource au sein d'un exercice
    str_wgt_actions="formula-" if uniform_weight else "by-ex-"
cost_lobbyist=1#30000
sansAgri=''#'sansAgri'
years=['']#[2021,2022]#exercices se terminant une année donnée

file_suffix='-out='+out_str+'-acts='+str(str_wgt_actions)+'-lobbyist='+str(cost_lobbyist)+'-'+sampleStr+'-'+sansAgri+str(years)




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

## TODO:
#priorité:
# récolter notes gpt dans boucle sur tiers. Ou pas, on se sert de la boucle pour tester si les différents nom de la firme sont dans results_gpt
# classer par catégorie et évaluer changement
# refaire une évaluation gpt et tester changement
# tester en mettant objet social etc...?



transf = math.log if correct_outliers and deform=="ln" else lambda x:x
transfinv= math.exp if correct_outliers and deform=="ln" else lambda x:x


verbosis=True

def printjs(s):
    if verbosis:
        print(json.dumps(s, indent=4, sort_keys=False, ensure_ascii=False))


def gini_coefficient(data):
    # Convert data to numpy array
    data = np.array(data)

    # Sort the data
    sorted_data = np.sort(data)

    # Calculate cumulative area under the Lorenz curve
    cumulative_areas = np.cumsum(sorted_data) / np.sum(sorted_data)

    # Calculate Gini coefficient
    gini_coeff = 1 - 2 * np.trapz(cumulative_areas) / len(data)

    return gini_coeff


today = str(date.today())
print( today)

#save=False

#now: check that all nodes and tiers from "lobbys" are in "to_grade" or "results-gpt"

with open('openAI/results-gpt.json', 'r') as fich:#contains grades of associations
    results_gpt = json.load(fich)
with open('openAI/class-gpt.json', 'r') as fich:#contains grades of associations
    class_gpt = json.load(fich)
#with open('openAI/to-grade.json') as f:#elements fichier lobbys.json matched
#    to_grade = json.load(f)
with open('agora_repertoire_opendata.json') as f:#répertoire HATVP
    data = json.load(f)['publications']

if sample!="all":
    data=data[0:sample]
# Iterating through the json
# list



#First, iterate over the firms of data


firmes={}#contiendra les poids des actions et les ressources des firmes par exercice, et qqs autres infos
actions={}
tiers={}#récolte les actions commanditées et la note de chaque mandant
triplets_ressources=[]#récole les ressources de chaque firme pour détercter outliers
doublons_gpt={}#quand on récolte les tiers, au passage on récole les notes, et ceux qui ont deux notes - devrait être fait dans la boucle sur tiers


def browse_agora(data):

    global class_gpt
    global results_gpt
    global firmes
    global actions
    global tiers
    global doublons_gpt
    global triplets_ressources
    global years

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
        global uniform_weight
        return 5 if uniform_weight else 5+len(action['tiers'])+len(action['actionsMenees'])+len(action['decisionsConcernees'])+len(action['reponsablesPublics'])

    def extract_classif(names_gpt_class):
        global class_gpt
        all_classifs=[]
        for n in names_gpt_class:
            proba=class_gpt[n]['classes']
            if 'manuel' in proba and proba['manuel']:
                return proba
            else:
                for cl in ['prive','syndicat','public','collectivite']:
                    if cl not in proba:
                        proba[cl]=0
                if sum(proba.values())!=100:
                    printjs(class_gpt[n])
                    print(sum(proba.values()))
                    input('erreur total')
                all_classifs+=[proba]
        return {cl:np.mean([proba[cl] for proba in all_classifs]) for cl in ['prive','syndicat','public','collectivite']}

    missing={}
    tiers_pas_clients={}
    clients_firme={}
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

        firmes[nom]={'identifiant':ident,
                        'categorie':firme['categorieOrganisation']['label'],
                        'affiliations':firme['affiliations'],
                        'Nom complet':firme['denomination'],
                        'Secteurs':[item['label'] for item in firme['activites']['listSecteursActivites']]}
        #il faudrait faire afficher les options par plexigraf

        clients_firme[nom]={cl['denomination']:{'found':False} for cl in firme['clients']}
        #{client1:{'found':False},client2:...}

        print('******exercices')
        possible_names=[firme[key] for key in ['denomination','nomUsage','nomUsageHatvp','sigleHatvp'] if key in firme]
        for ex in firme['exercices']:
            ex=ex['publicationCourante']
            filter_year=(len(years)==0)
            # for y in years:
            #     if y in ex['dateFin']:
            #         filter_year=True
            # if not filter_year:
            #     continue

            #on  détermine s'il y a une activité, et si oui on calcule le poids de l'exercice
            
            #d'abord on détermine les ressources et on enregistre dans triplets_ressources pour les correct_outliers
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
            try:
                #for outliers and filling NAs
                triplets_ressources+=[((transf(int(montant))),int(salaries),int(poids_activites_exercice))]
                triplet=True
            except:
                print('données manquantes')


            if not 'activites' in ex or len(ex['activites'])==0:
                if (montant!='NA' and int(montant)!=10000) or int(ex['nombreActivite'])>0:#pas d'action enregistrée mais on comptabilise une activité en raison des ressources. On met comme tiers tous les clients de la firme
                    printjs(ex)
                    ghost=True
                    print('ghost exercice')#on créée une activité fictive
                    dict={ "identifiantFiche" : "XXXXX", "objet" : "en propre non renseigné", "domainesIntervention" : [0],
                                                    "actionsRepresentationInteret" : [
                                                    {"reponsablesPublics" : [0],
                                                        "decisionsConcernees" : [0],
                                                        "actionsMenees" : [0],
                                                        "tiers" : [k for k in clients_firme]
                                                        }]}

                    ex['activites']=[{'publicationCourante':dict}]

                    if nom in tiers:
                        tiers[nom]['actions']+=[ 'en propre non renseigné']
                    else:
                        tiers[nom]={'actions':['en propre non renseigné']}
                    poids_activites_exercice=5
                else:
                    print('pas d activité')
                    continue
            #s'il y a activité, on détermine le poids total:
            if 'activites' in ex:#on va compter les poids et enregistrer les tiers et les actions
                poids_activites_exercice=0
                periode=ex['dateDebut']+'-'+ex['dateFin']
                if len(ex['activites'])<int(ex['nombreActivite']):
                    print(len(ex['activites']),ex['nombreActivite'])
                    print('manque activité(s)')
                for act in ex['activites']:
                    dict=act['publicationCourante']
                    action=merge_actions(dict['actionsRepresentationInteret'])
                    poids_action=poids_formula(action)
                    poids_activites_exercice+=poids_action
                    objet=dict['objet']
                    if objet not in actions:
                        actions[objet]={}
                    if periode not in actions[objet]:
                        actions[objet][periode]={}
                    if nom not in actions[objet][periode]:
                        actions[objet][periode][nom]={}
                    actions[objet][periode][nom][dict['identifiantFiche']]={'tiers':action['tiers'],'poids_abs':poids_action}

                    action_tiers_modif=[]
                    if len(action['tiers'])==0:#par défaut, on met la firme en propre
                        action['tiers']=[nom]
                    for t in action['tiers']:#on récolte les tiers et leur notes gpt, mais ça serait plus logique de mettre les notes dans la boucle sur tiers. On utilise ici le fait d'avoir les possibles names pour les actions 'en propre'
                        if 'en propre' in t or t in possible_names:
                            t=nom#il faut mettre le nom de cette firme pour bien capter les ressources de l'action du bon endroit
                            #t=best_nom(firme)
                            print('en propre')
                            names_gpt_results=[name for name in possible_names if name in results_gpt]
                            names_gpt_class=[name for name in possible_names if name in class_gpt]
                        else:# pas en propre
                            if t not in clients_firme[nom]:
                                if nom in tiers_pas_clients:
                                    tiers_pas_clients[nom].add(t)
                                else:
                                    tiers_pas_clients[nom]=set(t)
                            else:
                                clients_firme[nom][t]['found']=True
                            # if t in results_gpt:
                            #     names_gpt_results=[t]
                            # else:
                                # names_gpt_results=[]
                            if t in class_gpt:
                                names_gpt_class=[t]
                            else:
                                names_gpt_class=[]
                        if t not in tiers:
                            tiers[t]={'actions':[objet]}
                        else:
                            tiers[t]['actions']+=[objet]

                        action_tiers_modif+=[t]

                        #à déplacer
                        if len(names_gpt_class)==0:
                            print(t,'**',nom)
                            input('erreur de nom')
                            missing[t]={}
                            continue
                        elif len(names_gpt_class)>1:
                            if not t in doublons_gpt:
                                doublons_gpt[t]=[class_gpt[n] for n in names_gpt_class]
                                
                            #tiers[t]['classe']={'score':max([d['score'] for d in doublons_gpt[t]]),'confiance':min([d['confiance'] for d in #doublons_gpt[t]]),'explication':'doublon','doublon':doublons_gpt[t]}
                        classif=extract_classif(names_gpt_class)
                        tiers[t]['classes']=classif

                    actions[objet][periode][nom][dict['identifiantFiche']]={'tiers':action_tiers_modif,'poids_abs':poids_action}
                if poids_activites_exercice>10000:
                    print('gros ex')

            if periode in firmes[nom]:#2 périodes pleines déclarées?
                printjs(firmes[nom][periode])
                printjs(ex)
                print('double période - très rare, uniquement FEDERATION NAL METIERS STATIONNEMENT, il faudrait les fusionner mais tant pis. a minima il faudrait garder celui qui a les activités et on lui imputera les ressources')
            firmes[nom][periode]={'montant':montant,'nbSalaries':salaries,'poids_exercice':poids_activites_exercice,'triplet':True,'outliers':{}}
        clients_firme[nom]=[cl  for cl in clients_firme[nom] if not clients_firme[nom][cl]['found']]
    print(missing)
    print('missing')

    printjs(tiers_pas_clients)
    print('tiers pas clients')
    input('?')

    printjs(clients_firme)
    input('clients pas trouvés')


browse_agora(data)


####doublons gpt

#On analyse les firmes notées 2 fois par erreur, ça permet d'estimer la consistance de la procédure
print("*****doublons gpt")
printjs(doublons_gpt)
print('doublons gpt')


ecarts_scores=[]
confiances=[]

def explore_doublons():
    global doublons_gpt
    for f in doublons_gpt:
        db=doublons_gpt[f]
        #print(f)
        #printjs(db)
        scores=[r['class'] for r in db]
        if len(db)>2:
            input('more than 2')
        #ecarts_scores+=[max(scores)-min(scores)]
        #confiances+=[max([r['confiance'] for r in db])]
    
    #print('erreur moyenne doublons',np.mean(ecarts_scores))
    #print('correl confiance',np.corrcoef(ecarts_scores,confiances))
    #input("*****doublons gpt")


#explore_doublons()


######classes tiers



def add_values(dict1,dict2):
    return {k:dict1[k]+dict2[k] for k in dict1}    

#ces firmes auront la catégorie "privé" par défaut:
private_labels=['Société commerciale',
'Société civile (autre que cabinet d’avocats)',
'Cabinets d’avocats',
'Cabinet d’avocats',
'Avocat indépendant',
'Cabinet de conseil',
'Cabinet de conseils',
'Consultant indépendant',
"Organisation professionnelle",
"Fédération professionnelle",
"Travailleur indépendant",
"Société commerciale et civile (autre que cabinet d’avocats et société de conseil)"]
possible_labels=['prive','syndicat','public','collectivite']
def get_classes_tiers():
     #affecte la valeur "privé" aux catégories corresp et fait un histogramme de tous les tiers
    
    classes={cl:0 for cl in possible_labels}
    examples={i:[] for i in possible_labels}
    missing=set()#entités sans note - devrait être vide
    #double_notation=[]#firmes qui ont reçu une note gpt par erreur, permet d'évaluer gpt
    for t in tiers:
        print(t)
        if t in firmes and firmes[t]['categorie'] in private_labels:#on met 10
            print(firmes[t])
            if 'classes' in tiers[t]:#on confronte avec la note gpt pour voir
                print('déjà une note')
                printjs(tiers[t]['classes'])
                print('do something else')
            tiers[t]['classes']={'prive':100,'collectivite':0,'public':0,'syndicat':0,'explication':firmes[t]['categorie'],'manuel':True}
        elif not 'classes' in tiers[t]:#note manquante- ne devrait pas arriver
            if t in firmes:
                print(firmes[t]['categorie'],firmes[t]['categorie'] in private_labels)
            input('grade missing')
            missing.add(t)
        classes=add_values(classes,tiers[t]['classes'])

    print('classes')
    input(classes)
    plt.bar(possible_labels,[classes[cl] for cl in possible_labels])
    plt.xlabel("Classes")
    plt.ylabel("Nombre de mandants")
    # print(double_notation)
    # print(np.mean(double_notation))
    # print(np.mean(confiances))

    # hist,_ = np.histogram(notes, bins=possible_labels)

    # #xvals=[str(x) for x in bins[0:-1]]
    # # Créer un histogramme
    # plt.bar(bins[0:-1], hist)

    plt.title('Distribution interêt public/privé')# - Gini:'+str(gini))

    if sample=="all":
        plt.savefig('rfap/figs/classes-clients-'+file_suffix+'.jpg', format='jpg')
    # Afficher l'histogramme
    #plt.show()

get_classes_tiers()

######correc outliers et calcule ressources par exercice

def treat_data_pb():
    global firmes
    global triplets_ressources
    global correct_outliers
    global agressive
    global seuils
    global transf
    print('data pb******')

    #Basée sur les 10 ppv
    #on transform le budget éventuellement avec la fonction transf
    #ensuite on renormalise les triplets de données (dépenses, nbSalaries, poids_exercice)
    #pour chaque triplet avec 3 valeurs numérique (NAs=0), on regarde le zscore  par rapport aux 10 points qui sont des ppv par rapport aux 2 autres coordonnées
    #on le fait pour budget et nbSalaries, pas pour poids_exercice, car on considère que c'est plus difficile de se tromper dans la saisie
    #de plus, si une firme se trompe "de la même manière" pour ses poids_exercice, ce n'est pas grave vu qu'on renormalise
    #Si le zscore est plus grand (ou plus petit) que le seuil indiqué, on classifie comme outlier, et on stocke dans firmes[firme][période]{zscore,recommanded}
    #les seuils ont été choisis de manière empirique
    if correct_outliers:
        if agressive!="agressive":
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
    knn_model=[0,0,0]
    for i in [0,1]:
        knn_model[i]=NearestNeighbors(n_neighbors=11, algorithm='auto')
        knn_model[i].fit(triplets_coords[i])

    def ressource_formula(exercice):
        return float(exercice['montant'])+float(exercice['nbSalaries'])*cost_lobbyist
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

    glob_outliers=[]
    #on va remplacer/corriger les ressources pour les firmes, et calculer le score ressource
    for f in firmes:
        firmes[f]['total ressources']=0
        for p in [p for p in firmes[f] if '20' in p]:#on détecte une période
            print(f,p)
            ress=firmes[f][p].copy()
            t=[ress['montant'],ress['nbSalaries'],ress['poids_exercice']]
            print(t)
            if t[2]==0:
                continue
            if t[0]!='NA':
                t[0]=(transf(t[0]))
            #print(t)
            nas = t.count("NA")
            print('nas',nas)
            if nas==0:
                if not correct_outliers:
                    firmes[f][p]['ressources']=ressource_formula(firmes[f][p])
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
                    print('i',i)
                    real_value=t[i]
                    #print('real',real_value)
                    m,s=kNN(t,i)
                    #print(np.round(m,2))
                    zscore_ = ((real_value-m)/s)
                    #print(np.round(zscore_,2))
                    if (zscore_)>seuils[i][0] or zscore_<seuils[i][1]:
                        nb_out+=1
                        m_back=ecart_types[i]*m+moyennes[i]
                        t_back_i=ecart_types[i]*t[i]+moyennes[i]
                        exceed=max( zscore_/seuils[i][0] , zscore_/ seuils[i][1])
                        #firmes[f][p]['outliers'][i]={'zscore_':np.round(zscore_,2),'exceed':np.round(exceed,2),'recommanded':round(m_back,2)}
                        if i==0:
                            m_back=transfinv(m_back)
                            t_back_i=transfinv(t_back_i)
                        print(m_back)
                        outliers[i]={'exceed':exceed,"firme":f,'periode':p,'orig triplet':ress,'zscore':np.round(zscore_,2),'recommanded':round(m_back,2),'check':round(t_back_i,2)}
                    if nb_out>0 and i==1:
                        i_replace=0 if outliers[0]['exceed']>outliers[1]['exceed'] else 1#lequel on remplace?
                        key_replace = 'montant' if i_replace==0 else 'nbSalaries'
                        print(i_replace,key_replace)
                        firmes[f][p][key_replace]=outliers[i_replace]['recommanded']
                        glob_outliers+=[outliers]

            elif nas==1:#necessarily nb salaries
                t[1]=0#pour éviter erreur type ligne suivante
                t=(t-moyennes)/ecart_types
                m,std=kNN(t,i=1,excl_index=False)
                replacement=round(m*ecart_types[1]+moyennes[1],2)
                print('replacement',replacement)
                firmes[f][p]['nbSalaries']=replacement
                firmes[f][p]['imput value']=['nbSalaries; std='+str(np.round(std,2))]
                #idem, prioriser poids puis montant
            elif nas==2:#budget et nbsalaries
                #print('poids',t[2])
                indexes=closest_indices(t[2], poids_s, n=10)
                #print(indexes)
                similar_couples=[triplets_ressources[j][0:2] for j in indexes]
                #print('couples',similar_couples)
                m=np.mean(similar_couples,axis=0)
                firmes[f][p]['montant']=transfinv(m[0])
                firmes[f][p]['nbSalaries']=m[1]
                firmes[f][p]['imput value']=['montant','nbSalaries']
            firmes[f][p]['ressources']=ressource_formula(firmes[f][p])#formule ressources
            firmes[f]['total ressources']+=firmes[f][p]['ressources']
    
#     print('outliers dépenses')
#     input(len(outliers[0]))
#
#     printjs(outliers[1])
#     print('outliers nbSalariés')
#     input(len(outliers[1]))
#
#     for i in [0,1]:
#         print('sorted ** coord',i)
#         outliers[i] = sorted(outliers[i], key=lambda x: x['zscore'])
#         printjs(outliers[i])
#         input('sorted coord'+str(i))


treat_data_pb()


printjs(firmes)
print('firmes')


####### secteurs


def stats_secteurs():#basé sur secteurs des firmes, et non pas secteurs des actions. On pourrait comparer
    secteurs={}



    for firme in firmes:
        f=firmes[firme]
        t_ress=f['total ressources']
        nb_sec=len(f['Secteurs'])
        if nb_sec==0:
            input('0 sec')
        ress_sec_f=t_ress/nb_sec
        for s in f['Secteurs']:
            if s in secteurs:
                secteurs[s]+=ress_sec_f
            else:
                secteurs[s]=ress_sec_f

    print('secteurs')
    printjs(secteurs)

    if sample=="all":
        with open('rfap/data-rfap/secteurs-data-'+file_suffix+'.json','w') as file:
            json.dump(secteurs, file, indent = 4, separators = (',', ':'))#, sort_keys=True)
            file.truncate()


    sect_short=[]

    if sansAgri=="sansAgri":
            del secteurs["Agriculture, agroalimentaire"]
    for s in secteurs:
        l=s.split(' ')
        sec=' '.join(l[0:3])
        if len(l)>2:
            sec+='...'
        sect_short+=[sec]
    plt.bar(sect_short,[secteurs[s] for s in secteurs])
        # Ajouter des étiquettes et un titre
    plt.xlabel('Secteurs')
    plt.ylabel("Ressources")
    plt.title('Secteurs:'+file_suffix)
    plt.xticks(rotation=90)
    plt.subplots_adjust(wspace=0.8)
    plt.subplots_adjust(bottom=.6)
    #plt.title('Répartition des ressources des actions par influence')
    if sample=="all":
        plt.savefig('rfap/figs/secteurs_'+file_suffix+'.jpg', format='jpg')
    # Afficher l'histogramme
    plt.show()

#stats_secteurs()

########ACTIONS


def compute_ress_actions():
    ressources_actions=[]#pour faire un histogramme

    #on va calculer les ressources de chaque action, obtenu comme les ressources allouées par la firme à l'exercice contenant l'action, au prorata du poids de cette action
    #une action peut être effectuée sur plusieurs périodes et par plusieurs firmes, on calcule les ressources pour chaque occurence
    for act in actions:
        action=actions[act]
        print(act,'*** ressources action')
        #printjs(action)
        for p in action:
            for f in action[p]:
                for code in action[p][f]:
                    poids_ex=firmes[f][p]['poids_exercice']
                    ress_ex=firmes[f][p]['ressources']
                    ress_act=ress_ex* action[p][f][code]['poids_abs']/poids_ex#in main loop, by exercise of formula
                    ressources_actions+=[ress_act]
                    if ress_act>1000000:
                        print('big ressource, means the outliers work was not done properly :)')
                    actions[act][p][f][code]['ressources']=ress_act

    
    printjs(actions)

    ressources_actions=sorted(ressources_actions,reverse=True)
    #print('big actions',ressources_actions[0:200])
    print('actions intitulés',len(actions))


    #def hist_values(valeurs,bins,xlab="Entrées",ylab="Valeurs",title='Histogramme des données'):

    # Calcul de l'histogramme
    bins=[4000*x for x in range(0,40)]+[1000000]+[10000000]
    hist,_ = np.histogram(ressources_actions, bins=bins)



    xvals=[str(x) for x in bins[0:-1]]
    # Créer un histogramme
    plt.bar(xvals, hist)

    # Ajouter des étiquettes et un titre
    plt.xlabel('Influence')
    plt.ylabel("Nombre d'actions")
    plt.title('Répartition des ressources des actions par influence')
    if sample=="all":
        plt.savefig('rfap/figs/ressources_actions_'+file_suffix+'.jpg', format='jpg')
    # Afficher l'histogramme
    plt.show()



if not uniform_ress_actions:
    compute_ress_actions()

def classif_actions_by_mean():
    hist_actions={'prive':0,'syndicat':0,'public':0,'collectivite':0}
    print('classify actions by mean')
    for action in actions:
        print(action[0:30]+'...')
        tiers_action=[]
        for p in actions[action]:
            for f in actions[action][p]:
                for code in actions[action][p][f]:
                    tiers_action+=actions[action][p][f][code]['tiers']
        clasifs_tiers_action=[tiers[t]['classes'] for t in tiers_action]
        mean_classif={cl:np.mean([classif[cl] for classif in clasifs_tiers_action]) for cl in ['prive','syndicat','public','collectivite']}
        hist_actions=add_values(hist_actions,mean_classif)
        actions[action]['mean_classif']=mean_classif

    print('hist actions')
    plt.bar(possible_labels,[hist_actions[cl] for cl in possible_labels])
    plt.xlabel("Classes")
    plt.ylabel("Poids actions")
  

    plt.title('Distribution interêt public/privé')# - Gini:'+str(gini))

    if sample=="all":
        plt.savefig('rfap/figs/distrib-actions-'+file_suffix+'.jpg', format='jpg')

    plt.show()



classif_actions_by_mean()

printjs(actions)
with open('actions.json','w') as file:
    json.dump(actions, file, indent = 4, separators = (',', ':'))
    


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
        if t in firmes and firmes[t]['categorie'] in private_labels:#on met 10
            print(firmes[t])
            if 'note' in tiers[t]:#on confronte avec la note gpt pour voir
                print('déjà une note')
                printjs(tiers[t]['note'])
                double_notation+=[tiers[t]['note']['score']]
                confiances+=[tiers[t]['note']['confiance']]
            tiers[t]['note']={'score':10,'confiance':10,'explication':firmes[t]['categorie']}
        elif not 'note' in tiers[t]:#note manquante- ne devrait pas arriver
            if t in firmes:
                print(firmes[t]['categorie'],firmes[t]['categorie'] in private_labels)
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

    if sample=="all":
        plt.savefig('rfap/figs/notes-clients-'+file_suffix+'-gini-'+str(gini)+'.jpg', format='jpg')
    # Afficher l'histogramme
    plt.show()




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
                ress_act=1 if uniform_ress_actions else action[p][f][code]['ressources']
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
if sample=="all":
    plt.savefig('rfap/figs/influence-interet-'+file_suffix+'-gini-'+gini+'.jpg', format='jpg')

# Afficher l'histogramme
plt.show()
