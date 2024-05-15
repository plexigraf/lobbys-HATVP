import json
import re
from unidecode import unidecode
import string

with open('results-gpt.json', 'r') as fich:#already graded
    results_gpt = json.load(fich)
print(len(results_gpt))

with open('to-grade.json','r') as f:#elements fichier lobbys.json matched
# search in lobbys file
    to_grade = json.load(f)
print('to grade '+str(len(to_grade)))

for key in to_grade:
    print(key)



exit()
verbosis=True

def printjs(s):
    if verbosis:
        print(json.dumps(s, indent=4, sort_keys=True, ensure_ascii=False))


def nettoyer_chaine(chaine):
    print('clean',chaine)
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
    print(chaine)

    return chaine

def comparer_chaines(chaine1, chaine2):
    chaine1_nettoyee = nettoyer_chaine(chaine1)
    chaine2_nettoyee = nettoyer_chaine(chaine2)
    print(repr(chaine1_nettoyee),len(chaine1_nettoyee))
    print(chaine2_nettoyee,len(chaine2_nettoyee))
    print(chaine1_nettoyee == chaine2_nettoyee)
    return chaine1_netto

f= open('all-matched.json')
data_raw =json.load(f)

f_agora=open('agora_repertoire_opendata.json')
data_agora=json.load(f_agora)['publications']

motifs = ["-SIREN", "-HATVP", "-RNA"]

# Créer une expression régulière en utilisant les motifs
motif_complet = "|".join(map(re.escape, motifs))

data={'matched':{},'unknowns':{}}
for key in data_raw['matched']:
    key2=re.sub(f"({motif_complet}).*", "", key)
    data['matched'][key2]=data_raw['matched'][key]
    #del data['matched'][key]

for key in data_raw['unknowns']:
    key2=re.sub(f"({motif_complet}).*", "", key)
    data['unknowns'][key2]=data_raw['unknowns'][key]
    #del data['matched'][key]
    prototype={
  "activites" : {
    "lib_objet_social1" : "information communication",
    "objet" : "informer et sensibiliser le monde politique au sens le plus large et les représentants des pouvoirs publics à la pratique et aux bienfaits que la méditation de pleine conscience peut apporter dans la société et plus particulièrement dans les domaines du travail, de l'éducation, de la santé et de la justice, l'association étant de nature strictement laïque et indépendante de tout parti politique et de toute confession ou institution religieuse"
  },
  "identite" : {
    "id_rna" : "W751239961"
  },
  "activite_principale" : "94.99Z",
  "complements" : {
    "est_association" : "true",
    "identifiant_association" : "W751239961"
  },
  "finances" : {},
  "nom_complet" : "INITIATIVE MINDFULNESS FRANCE",
  "nom_raison_sociale" : "INITIATIVE MINDFULNESS FRANCE",
  "section_activite_principale" : "S",
  "siren" : "903987295",
  "siege" : {},
  "matching_etablissements" : [
    {
      "activite_principale" : "94.99Z",
      "siret" : "90398729500016"
    }
  ],
  "dirigeants" : [],
  "asso et entreprise" : "true"
}




def best_nom(firme):
    if 'nomUsage' in firme:
        return firme['nomUsage']
    else:
        return firme['denomination']



actions={}
for firme in data_agora[0:5]:
    nom_firme_clean=nettoyer_chaine(firme['denomination'])
    print(nom_firme_clean,'**********')
    firme_dict={'nom':best_nom(firme),'type':firme['categorieOrganisation']['label']}
    if nom_firme_clean in data['matched']:
        try:
            firme_dict['objet']=data['matched'][nom_firme_clean]['activites']['objet']
        except:
            print('pas objet')
    for ex in firme['exercices']:
        ex=ex['publicationCourante']
        if 'activites' in ex:
            for act in ex['activites']:
                act=act['publicationCourante']
                printjs(act)
                obj=act['objet']
                print(obj)
                if len(act['actionsRepresentationInteret'])>1:
                    printjs(act)
                    input('more than 1 action?')
                tiers= act['actionsRepresentationInteret'][0]['tiers']
                tiers_dicts=[]
                print('tiers***')
                printjs(tiers)
                for tier in tiers:
                    print(tier)
                    if 'en propre' in tier:#en propre
                        print('en propre')
                        continue
                    tier_dict={'nom':tier}
                    if tier in data_agora:
                        entree=data_agora[tier]
                        tier_dict={'categorie':entree['categorieOrganisation']['label'],
                                    'affiliations':entree['affiliations']}
                    clean_tier=nettoyer_chaine(tier)
                    if clean_tier in data['matched']:
                        found_entry=data['matched'][clean_tier]
                        try:
                            tier_dict['objet']=found_entry["activites"]['objet']
                        except:
                            print('pas objet')
                    else:
                        tier_dict['donnes']='non disponibles'#a retirer, pour deboggage
                    tiers_dicts+=[tier_dict]
                print('tiers dicts',tiers_dicts)
                actions[firme['denomination']+' **** '+obj]=[{'firme':firme_dict,'tiers':tiers_dicts}]

input('?')
printjs(actions)
