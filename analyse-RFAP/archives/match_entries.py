import subprocess
import json
import requests
import time
import re
from unidecode import unidecode

def printjs(s):
    print(json.dumps(s, indent=4, sort_keys=True, ensure_ascii=False))

import string
from fuzzywuzzy import fuzz
import Levenshtein

def save_data(s,filename):
    print('saving...do not break')
    with open(filename+".json", "w+") as jsonFile:
            json.dump(s, jsonFile, indent = 4, separators = (',', ':'))#, sort_keys=True)
            jsonFile.truncate()
            print('data saved')

 
#load class_gpt
with open('openAI/class-gpt.json') as f:
    class_gpt=json.load(f)
#load other_names
with open('other_names.json') as f:
    other_names=json.load(f)
#load suppl_info
with open('firms_suppl_info.json') as f:
    suppl_info=json.load(f)
#create to_grade
to_grade={}
 


# suppl_info={}
# for key in firms_suppl_info:
#     print(key)
#     k=key.split('-SIREN')[0].split('-RNA')[0].split('-HATVP')[0]
#     suppl_info[k]=firms_suppl_info[key]
# for key in firms_suppl_info['matched']:
#     print(key)
#     k=key.split('-SIREN')[0].split('-RNA')[0].split('-HATVP')[0]
#     try:
#         suppl_info[k].update(firms_suppl_info['matched'][key])
#         print('updated')
#     except KeyError:
#         suppl_info[k]=firms_suppl_info['matched'][key]

# for key in firms_suppl_info['unknowns']:
#     print(key)
#     k=key.split('-SIREN')[0].split('-RNA')[0].split('-HATVP')[0]
#     try:
#         suppl_info[k].update(firms_suppl_info['unknowns'][key])
#         print('updated')
#     except KeyError:
#         suppl_info[k]=firms_suppl_info['unknowns'][key]


# save_data(suppl_info,"firms_suppl_info")
# exit()
#for key in class_gpt:
#    print(key)
#    info=insee_search(key)
#    il ne faudrait garder que tres peu de champs
#    possible_names=...
#    to_grade[key].update( all info with all names)
#   
#on récupère une liste de to_grade avec le max d'infos
#grace a 'collect to grade', on identifie des champs qui mettent dans le privé direct (il vaut mieux identifier les autres champs pour aller plus vite)

# donc maintenant on donne a manger a chatgpt et on espère avoir des meilleures notes, et une note de confiance



# def is_substring_similar(substring, target_string):
#  """
#  Vérifie si une sous-chaîne est similaire à une chaîne cible.
#  """
#  max_sim=0
#  for i in range(len(target_string) - len(substring) + 1):
#      sub_target = target_string[i:i + len(substring)]
#      max_sim =  max(max_sim,fuzz.ratio(substring, sub_target))
#  return max_sim

# def compare_struct_names(n1,n2):
#     return max(is_substring_similar(n1,n2),is_substring_similar(n2,n1))
# Opening JSON file
#f = open('agora_repertoire_opendata.json')


# with open('agora_repertoire_opendata-matched.json', 'r') as file:
#     data_matched = json.load(file)



def filter_dict(input_dict, fields):
    result = {}
    for field in fields:
        if isinstance(field, dict):
            for key, subfields in field.items():
                if key in input_dict:
                    if isinstance(input_dict[key], list):
                        result[key] = [filter_dict(item, subfields) for item in input_dict[key]]
                    elif isinstance(input_dict[key], dict):
                        result[key] = filter_dict(input_dict[key], subfields)
                else:
                    result[key] = None
        elif field in input_dict:
            result[field] = input_dict[field]
    return {k: v for k, v in result.items() if v is not None}

def merge_dicts(dict1, dict2):
    """
    Recursively merge two dictionaries with fields and subfields.
    """
    merged_dict = dict1.copy()

    for key, value in dict2.items():
        if key in merged_dict and isinstance(merged_dict[key], dict) and isinstance(value, dict):
            # If both values are dictionaries, merge them recursively
            merged_dict[key] = merge_dicts(merged_dict[key], value)
        else:
            # Otherwise, simply update the value
            merged_dict[key] = value
#
    return merged_dict

def nettoyer_chaine(chaine):
    #print('clean',chaine)
    if chaine==None:
        return ''
    chaine = unidecode(chaine).lower()#accents et capitales
    chaine = re.sub(r'\([^)]*\)', '', chaine)#retirer parentheses
    chaine=re.sub(r'\'.*?\'', '', chaine)#retirer apres slash
    chaine = re.sub(r'[%s]' % re.escape(string.punctuation), '', chaine)#retirer ponctuation
    # Supprimer le contenu entre parenthèses et les parenthèses elles-mêmes, ou ce qu'il y a après un slash
    #chaine = re.sub(r'\([^)]*\)|/.*', '', chaine)

    #chaine=''.join(e for e in chaine if e.isalnum() or e.isspace())
    chaine=chaine.strip()#enlever espace au debut et a la fin d'une chaine

    return chaine

def comparer_chaines(chaine1, chaine2):
    chaine1_nettoyee = nettoyer_chaine(chaine1)
    chaine2_nettoyee = nettoyer_chaine(chaine2)

    return chaine1_nettoyee == chaine2_nettoyee

entreprise_fields = [
    "activite_principale",
    {"complements":["est_association","identifiant_association"]},
    "categorie_entreprise",
    "finances",
    "nom_complet",
     "nom_raison_sociale",
      "section_activite_principale",
      "siren",
      "tranche_effectif_salarie",
      {"siege":["libelle_pays_etranger"]},
    {"matching_etablissements": ["activite_principale","nom_commercial","siret"]},
    {'dirigeants':['denomination','siren']}]

asso_fields=[{"activites":["nom",
            "lib_tranche_effectif",
            "lib_activite_principale",
            "lib_famille1",
            "lib_famille2",
            "lib_famille3",
            "lib_objet_social1",
            "lib_objet_social2",
            "lib_objet_social3",
            "lib_theme1",
            "lib_theme2",
            "lib_theme3",
            "objet",
            "appartenance_ess"]},
            {"identite":["nom_sirene","id_rna",
                        "id_siren",
                        "impots_commerciaux",
                        "lib_forme_juridique",
                        "util_publique","eligibilite_cec"]},
            {"reseau_affiliation":["nom","numero"]}
            ]
# if initialise_file:
#         with open("agora_repertoire_opendata-matched.json", "w+") as jsonFile:
#             jsonFile.truncate()
#             print('effacé')
# else:
#     with open("agora_repertoire_opendata-matched.json", "r") as jsonFile:
#         lines = jsonFile.readlines()
#         print(lines)
#         derniere_position = jsonFile.tell()
#         print('derniere position:',derniere_position)
#         input('ok?')

def search_insee(type_recherche,ident,nom):#phase 1: retrieve json from insee DB#retrieves 'result' with 1 entry or dict {'erreur':'...'}, also produces "response"
    print('recherche',type_recherche,ident,nom)
    result='unknown'
    if type_recherche=="entreprise-siren":
        api_url = "https://recherche-entreprises.api.gouv.fr/search"
        response = requests.get(api_url, params= {'q':ident})
        result=response.json()['results'][0]
        # if len(results)>0:
        #     result=response.json()['results'][0]
        # else:
        #     result={'erreur':resp}
    elif type_recherche=="asso-nom":
        #not used yet
        api_url='https://www.data-asso.fr/api/associations/search?q='+nom.translate(str.maketrans('', '', string.punctuation)).replace(' ','%20')
        print(api_url)
        #on recup rna sur data asso si nom match et on cherche asso-rna
        response=requests.get(api_url)
        results = response.json()
        
        #on va tester si le nom match un résultat
        results_dict_nom={res['identite']['nom']:res for res in results if 'identite' in res and 'nom' in res['identite']}
        results_dict_sigle={res['identite']['sigle']:res for res in results if 'identite' in res and 'sigle' in res['identite']}
        print('résultats noms', results_dict_nom.keys())
        best_couple_nom=find_best_match([nom],results_dict_nom,verb=True)
        best_couple_sigle=find_best_match([nom],results_dict_sigle,verb=True)
        best_couple=best_couple_nom
        if len(nom)>5 and best_couple_sigle['best_score']>85:
            best_couple=best_couple_sigle
        elif best_couple_nom['best_score']>70:
            if best_couple_nom['best_score']<80:
                print(nom,'**',best_couple_nom['best_match']['key'],'**',best_couple_nom['best_score'])
                v=input('validate?y/n:')
                if v=='y':
                    best_couple_nom['best_score']>90
                    best_couple_nom['hand validated']=True
                    best_couple=best_couple_nom
                else:
                    print('not validate')
        print('best match',best_couple)
        if best_couple['best_score']>80:#on a trouvé un bon match, on cherche les infos aupres de l'insee avec le rna ou siren
            try:
                result=search_insee('asso-rna',best_couple['rna'],'xxx')
            except:
                try:
                    result=search_insee('asso-siren',best_couple['siren'],'xxx')
                except:
                    result=best_couple['best_match']
                    result['name match info']=best_couple['best_score']
        else:
            result={'erreur':'asso nom pas trouvée','resultats recherche data-asso':results}
        #     try:
        #         if 'nom' in res['identite'] and (comparer_chaines(res['identite']['nom'],nom) or ('sigle' in res['identite'] and res['identite']['sigle']==nom)):
        #             found=True
        #             if 'rna' in res:
        #                 result=search_insee('asso-rna',res['rna'],'xxx')
        #             elif "siren" in res:
        #                 result=search_insee('asso-siren',res['siren'],'xxx')
        #             else:
        #                 result={'erreur':'vieille asso?','results':results}
        #             break
        #     except:
        #         pass#result={'erreur':'erreur recherche asso','results':results}
        # if not found:
        #     result={'erreur':'asso nom pas trouvée','resultats recherche data-asso':results}
    elif type_recherche=="entreprise-nom":
        #not used yet
        api_url = "https://recherche-entreprises.api.gouv.fr/search"
        print(api_url,nom)
        response = requests.get(api_url, params= {'q': nom+' '})
        results=response.json()['results']
        
        #on va tester si le nom match un résultat
        results_dict_social={res['nom_raison_sociale']:res for res in results}
        results_dict_complet={res['nom_complet']:res for res in results}
        results_dict_sigle={res['sigle']:res for res in results}
        print('résultats noms', results_dict_social.keys())
        best_couple_social=find_best_match([nom],results_dict_social,verb=True)
        best_couple_complet=find_best_match([nom],results_dict_complet,verb=True)
        best_couple_sigle=find_best_match([nom],results_dict_sigle,verb=True)
        best_couple=best_couple_complet
        if len(nom)>5 and best_couple_sigle['best_score']>85:
            best_couple=best_couple_sigle
        elif best_couple_social['best_score']>70:
            if best_couple_social['best_score']<80:
                print(nom,'**',best_couple_social['best_match']['key'],'**',best_couple_social['best_score'])
                v=input('validate?y/n:')
                if v=='y':
                    best_couple_social['best_score']>90
                    best_couple_social['hand validated']=True
                    best_couple=best_couple_social
                else:
                    print('not validate')
        elif best_couple_complet['best_score']>70:
            if best_couple_complet['best_score']<80:
                print(nom,'**',best_couple_complet['best_match']['key'],'**',best_couple_complet['best_score'])
                v=input('validate?y/n:')
                if v=='y':
                    best_couple_complet['best_score']>90
                    best_couple_complet['hand validated']=True
                    best_couple=best_couple_complet
                else:
                    print('not validate')
        print('best match',best_couple)
        if best_couple['best_score']>80:
            result=best_couple['best_match']
            result['name match info']=best_couple['best_score']
        else:
            result={'erreur':'asso nom pas trouvée','resultats recherche data-asso':results}

    elif type_recherche=="asso-siren":
        #siren='784854937'
        api_url='https://siva-integ1.cegedim.cloud/apim/api-asso/api/structure/'+ident
        response = requests.get(api_url)
        print(response)
        try:
            print(response.json())
        except:
            printjs(response)
        if response.status_code=='504':
            input('504 error. Try again?')
            response = requests.get(api_url)
        result=response.json()
    elif type_recherche=="asso-rna":
        #rna='W543009672'
        api_url='https://siva-integ1.cegedim.cloud/apim/api-asso/api/rna/'+ident#.replace('RNA','')
        response = requests.get(api_url)
        result=response.json()

    #check error
    if "http_status_code" in result and result['http_status_code']== 429:
        print('429, search limit reached, wait 1min. saving...')
        temps_initial = time.time()
        save_data(suppl_info,"firms_suppl_info")
        temps_ecoule = time.time() - temps_initial
        if temps_ecoule < 61:
            temps_restant = 61 - temps_ecoule
            print(f"Saved. Attente pendant {temps_restant} secondes...")
            time.sleep(temps_restant)
        return search_insee(type_recherche,ident,nom)
    elif response.status_code != 200 or 'erreur' in result:
        print('error',response.json(),result)
        return result
    elif result=='unknown':
        return {'erreur':'pas de resultats nulle part','recherche':type_recherche+ident+nom}


    if type_recherche.startswith('asso-'):
        interesting_fields=asso_fields
    elif type_recherche.startswith('entreprise-'):
        interesting_fields=entreprise_fields

    reduced_res = filter_dict(result,interesting_fields)
    print('reduced result query')
    printjs(reduced_res)
    return reduced_res

#suppl_info_as_list=[{'info':suppl_info[key],'key':key} for key in suppl_info]
save=True
counter=0
counter_match=0

def find_best_match(liste,infos_dict,verb=False):#find best match between 2 lists
    print('find best match',liste)
    best_score=0
    best_match={}
    liste=[nettoyer_chaine(n) for n in liste]
    for k in infos_dict:
        kk=nettoyer_chaine(k)
        for n in liste:  
            score=fuzz.ratio(n,kk)
            if verb:
                print(n,kk,score)
            if score>best_score:
                best_score=score
                best_match=infos_dict[k]
                best_match['key']=k
            if best_score>90:
                break
    return {'best_score':best_score,'best_match':best_match}

for key in class_gpt:
    counter=counter+1
    if counter % 100 == 0:
        save_data(suppl_info,"firms_suppl_info")
    if key in suppl_info:
        continue
    #look for similarities in suppl_info?
    print(counter,'/',len(class_gpt))
    print(key)
    found=False
    names=[key]
    print("compare with other names")
    if key in other_names:
        names+=other_names[key]
    print("compare with other names",names)
    best_couple=find_best_match(names,suppl_info)
    print('best match',best_couple['best_score'],best_couple['best_match']['key'])
    if best_couple['best_score']>80:
        print('match')
        suppl_info[key]=best_couple['best_match']
        continue
    
    # if nom=='SAS SENSICORPS':
    #     print(nom)
    #     input('continue?')
    #     save=True
    # elif not save:
    #     continue
    match=False
    print(class_gpt[key])
    res=search_insee('asso-nom','xxx',key)
    res2=search_insee('entreprise-nom','xxx',key)
    if not 'erreur' in res:
        match=True
    if not 'erreur' in res2:
        if match:
            print('double match')
            #fusionnner
            res=merge_dicts(res,res2)
            res['asso et entreprise']='true'
        # elif res2['complements']['est_association']:
        #     match=False#si on a une asso il nous faut les donnes de l'asso
        #     res={'erreur':'pas de donnes d asso, mais donnees entreprise','entreprise':res2}
        else:
            res=res2
            match=True
    if not match:
        #il faut recuperer l'asso d'une autre maniere
        #api_url='https://www.data-asso.fr/api/associations/search?q=INITIATIVE%20MINDFULNESS%20FRANCE'#+nom.replace(' ','%20')
        #response = requests.get(api_url)
        #printjs(response.json()[0])
        print('unknown')
        #missing_matched['unknowns'][key]={'erreur':res}
    else:
        counter_match+=1
        print('match :)',key)
        printjs(res)
        #printjs({**res,**missing_lobbys[key]})
        suppl_info[key]=res

print('matched',counter_match)
save_data(suppl_info,"firms_suppl_info")


exit()

#search agora
for firme in data:#data_links
    #link=data_links[key]
    node=data_pxg[key]
    input(node)
    if node['ParentId']!='Clients':# or 'targetParentId' in link and node['targetParentId']!=?'Tiers inconnus':
        continue
    counter+=1
    print(counter,'/',len(data))
    #printjs(missing_matched)
    print('********--')
    #lab=firme['categorieOrganisation']['label']
    #print('label: '+lab)
    nom=firme['denomination']
    print(nom)

    #else:
    #    save=True
    if not save:
        continue
    ident=firme['typeIdentifiantNational']+str(firme['identifiantNational'])
    index=nom+'-'+ident
    # if index not in data_matched['matched'] and index not in data_matched['unknowns']:
    #     input('unknown')
    # else:
    #     continue

    match=False
    if firme['typeIdentifiantNational']=='RNA':
        #search asso-RNA
        res=search_insee('asso-rna',firme['identifiantNational'],'xxx')
        if not 'erreur' in res:
            match=True
    elif firme['typeIdentifiantNational']=='SIREN':
        #search asso-siren
        res=search_insee('asso-siren',firme['identifiantNational'],'xxx')
        if not 'erreur' in res:
            match=True

        res2=search_insee('entreprise-siren',firme['identifiantNational'],'xxx')
        if not 'erreur' in res2:
            if match:
                print('double match')
                #fusionnner
                res=merge_dicts(res,res2)
                res['asso et entreprise']='true'
            else:
                res=res2
            match=True
    else:#recherche par nom
        res=search_insee('asso-nom',firme['identifiantNational'],nom)
        if not 'erreur' in res:
            match=True
        res2=search_insee('entreprise-nom',firme['identifiantNational'],nom)
        if not 'erreur' in res2:
            if match:
                print('double match')
                #fusionnner
                res=merge_dicts(res,res2)
                res['asso et entreprise']='true'
            elif res2['complements']['est_association']:
                match=False#si on a une asso il nous faut les donnes de l'asso
                res={'erreur':'pas de donnes d asso, mais donnees entreprise','entreprise':res2}
            else:
                res=res2
                match=True
        #recherche entreprise

        # else:
        #     res=search_insee('entreprise-nom','xxx',nom)
        #     if res!='error':
        #         match=True
    if not match:
        print(ident)
        #il faut recuperer l'asso d'une autre maniere
        #api_url='https://www.data-asso.fr/api/associations/search?q=INITIATIVE%20MINDFULNESS%20FRANCE'#+nom.replace(' ','%20')
        #response = requests.get(api_url)
        #printjs(response.json()[0])
        missing_matched['unknowns'][nom]={'erreur':res,'firme':firme}
    else:
        printjs(res)
        missing_matched['matched'][nom+'-'+ident]=res
        print(lab+'?')

save_data(missing_matched,"agora_repertoire_opendata-matched")
