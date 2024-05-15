from openai import OpenAI
client = OpenAI()
import json
import re
import random
from openai import OpenAI

from unidecode import unidecode
import string

from fuzzywuzzy import fuzz

def is_substring_similar(substring, target_string):
    """
    Vérifie si une sous-chaîne est similaire à une chaîne cible.
    """
    max_sim=0
    for i in range(len(target_string) - len(substring) + 1):
        sub_target = target_string[i:i + len(substring)]
        max_sim =  max(max_sim,fuzz.ratio(substring, sub_target))
    return max_sim

def compare_struct_names(n1,n2):
    return max(is_substring_similar(n1,n2),is_substring_similar(n2,n1))

def printjs(s):
 print(json.dumps(s, indent=4,   ensure_ascii=False))

def nettoyer_chaine(chaine):
    print('clean',chaine)
    if chaine==None:
        return ''
    chaine = unidecode(chaine).lower()#accents et capitales
    chaine = re.sub(r'\([^)]*\)', '', chaine)#retirer parentheses
    chaine = re.sub(r'[\/\\].*', '', chaine)#enlever apres slashs
    chaine = re.sub(r'[%s]' % re.escape(string.punctuation), '', chaine)#retirer ponctuation
    # Supprimer le contenu entre parenthèses et les parenthèses elles-mêmes, ou ce qu'il y a après un slash
    #chaine = re.sub(r'\([^)]*\)|/.*', '', chaine)

    #chaine=''.join(e for e in chaine if e.isalnum() or e.isspace())
    chaine=chaine.strip()#enlever espace au debut et a la fin d'une chaine
    print(chaine)

    return chaine

def comparer_chaines(chaine1, chaine2):#comparer des noms de structures
    print('compare',chaine1, chaine2)
    chaine1_nettoyee = nettoyer_chaine(chaine1)
    chaine2_nettoyee = nettoyer_chaine(chaine2)

    return (chaine1_nettoyee in chaine2_nettoyee) or (chaine2_nettoyee in chaine1_nettoyee)

def clean(k):#enlever caracteres dans mauvais json retourné par chatgpt
    print('clean',k,'+++')
    x= (k.replace('"','').replace('\n','').replace('{','').replace('}','').replace(':','').strip())
    try:
        x=int(x)
    except:
        x=x
    return x

def split_dot(chaine):#split basé sur caracteres :;,{}
    return re.split(r'[:,;{}]', chaine)


def random_elements(input_list, n):
    # Return a new list containing n randomly selected elements from the input list
    return random.sample(input_list, min(n, len(input_list)))

to_grade=[]

def parse_json_str(resp,compare):
    #global unknown_names
    global to_grade
    resp=re.sub(r'\n+', '\n', resp)
    skipped=0
    result_dict={}
    counter=0
    for s in resp.split('''}'''):#parse gpt result
        print(repr(s),'**')
        if len(clean(s).replace('.',''))<10:
            print('skip short')
            continue
        try:
            nom=clean(s.split('{')[-2])
        except:
            continue
        print('nom',nom)
        if len(nom)<2:
            print(nom)
            print('no name')
        if compare:
            found=False
            best_match=''
            max_sofar=0
            for orig_nom in to_grade:
                sim_score=compare_struct_names(nettoyer_chaine(orig_nom),nettoyer_chaine(nom))
                print('#######',nom,'***',orig_nom,'***',sim_score)
                if sim_score>max_sofar:
                    max_sofar=sim_score
                    best_match=orig_nom
            if max_sofar>80:
                print(nom,best_match,max_sofar)
                if max_sofar<90:
                    input('ok?')
                nom=best_match
            else:
                input('no match')
                continue
            # if not found:
            #     print(repr(nom))
            #     print('suspected',to_grade[counter])
            #     x=input('valider?y/n:')
            #     if x=='y':
            #         found=True
            #         nom=to_grade[counter]
            #     else:
            #         unknown_names+=[nom]
        try:
            lines=s.split('{')[-1].lstrip('\n').split('\n')
            print('lines',lines)
            explic=clean(lines[0].replace('explication','').replace('explanation',''))
            try:
                #score=clean(split_dot(lines[1])[1].replace('.','').replace('"','').replace("'",""))
                score = re.search(r'\b\d+\b', lines[1]).group()
                print('score',score)
                score=int(score)
                confiance=re.search(r'\b\d+\b',lines[2]).group()#[1].replace('.','').replace('"','').replace("'",""))
                print('confiance',confiance)
                confiance=int(confiance)
            except:
                print('skip grade pb***')
                skipped+=1
                continue
        except:
            print('skip parse pb***')
            skipped+=1
            continue
        parse_s={nom:{"score":score,"explication":explic,'confiance':confiance}}
        result_dict.update(parse_s)
        print('result so far',result_dict)
        print('***',parse_s,'***')
        counter+=1
    print('skipped',skipped)
    return result_dict

#def parse_json_str(resp):
    result_dict={}

    for s in resp.split('''}'''):#parse gpt result
        print(s,'**')
        if len(clean(s).replace('.',''))<10:
            print('skip short')
            continue
        mots = ["explication", "score", "confiance"]
        index = 0
        for mot in mots:
            index = s.find(mot, index)
            if index == -1:
                print(s)
                input('skip?')
                continue
            index += len(mot)
        nom=clean(s.split('explication')[0])
        rest=s.split('explication')[1]
        #print('rest',rest)
        confiance=int(clean(rest.split('confiance')[1].replace(',','')))
        rest2=rest.split('confiance')[0]
        score=int(clean(rest2.split('score')[1].replace(',','')))
        explic=clean(rest2.split('score')[0])
        result_dict.update({nom:{"score":score,"explication":explic,'confiance':confiance}})
    return result_dict


    # print('parse',s,'***')
    # key=clean(s.split("{")[0].replace(':',''))
    # dict_str=s.split("{")[1].replace('}','')
    # #il faut distinguer les virgules entre dicts des virgules du texte
    # splitted = dict_str.split(',')#re.split(r'[:,]', dict_str)
    # value=''
    # new_dict={}
    # keys=set()
    # first=True
    # for w in splitted:
    #     if ":" in w:
    #         if not first:
    #             print(key_e)
    #             new_dict[key_e]=clean(value)
    #         else:
    #             first=False
    #         key_e=clean(w.split(':')[0])
    #         keys.add(key_e)
    #         value=w.split(':')[1]
    #     else:
    #         value+=w
    # new_dict[key_e]=clean(value)
    # if keys!={"confiance","score","explication"}:
    #     print(s,keys)
    #     input('error keys')
    # return {key:new_dict}

with open('missing-missing.json','r') as f:
    missing_missing=json.load(f)



#unknown_names=[]
def grade(limit):
    global to_grade
    total_ratio=0
    for iter_number in range(1,limit):

        with open('results-gpt.json', 'r') as fichier:
            prev_res = json.load(fichier)


        json_data =['''"THIVILLIER OLIVER YVETTE": {
 "explication": "Il s'agit probablement du nom d'une personne privée, sans but commercial évident.",
 "score": 1,
 "confiance": 7
 }

"THOM EUROPE": {
 "explication":"Cette entité semble avoir une orientation commerciale claire, en particulier avec le terme 'Europe'.",
 "score": 9,
 "confiance": 8
 }

"TOUTES A L ECOLE":{
 "explication":"L'objectif principal de cette entité semble être d'aider à l'éducation et aux causes sociales, plutôt que des intérêts commerciaux.",
 "score":2,
 "confiance": 9
 }

"TOUZET DOMINIQUE":{
 "explication":"Il est probable que cette entité soit liée à une personne privée, sans but commercial évident.",
 "score":1,
 "confiance":6
 }

"TPG CAPITAL":{
 "explication":"Cette entité est clairement axée sur des intérêts commerciaux et financiers.",
 "score":10,
 "confiance":9
 }

"TRAITEMENT INDUSTRIEL RESIDUS URBAINS":{
 "explication":"L'activité principale de cette entité semble être industrielle et environnementale, plutôt qu'à but commercial direct.",
 "score":3,
 "confiance":7
 }

"TRAME":{
 	"explication":"Pas assez d'informations pour déterminer un objectif commercial clair.",
	"score":4,
	"confiance":5
}

"TRANS URBAIN SOCIETE DES TRANSPORTS DE L'AGGLOMERATION D'EVREUX":{
	"explication":"Cette entreprise de transport a un objectif principal de fournir des services à ses clients, indiquant un but commercial évident.",
	"score":10,
	"confiance":9
}

"TRANSACTION GESTION CONSEIL IMMOBILIER":{
	"explication":"Le nom suggère une activité immobilière orientée vers des transactions commerciales.",
	"score":8,
	"confiance:8"
}

"TRANSGENE SA":{
	"explication":"Cette entreprise biotechnologique a un objectif commercial évident dans le domaine de la recherche et du développement.",
	"socre:10",
    confidence:9"
}

Les autres entrées sont en attente.''']

        # parsed=parse_json_str(json_data[0],False)
        # print('***********')
        # print(parsed)
        # print(len(parsed),'parsed')
        # input('save?')
        #
        # prev_res.update(parsed)
        # with open('results-gpt.json', 'w') as fichier:
        #    json.dump(prev_res, fichier, indent=4)
        #
        # exit()
        # input('stop')





        f = open('all-matched.json')
        # search in lobbys file
        data = json.load(f)

        to_grade=[]
        counter=0
        max_query=20
        for key in data['unknowns']:
            if key not in prev_res:
                counter+=1
                to_grade+=[key]

        print('to grade total',len(to_grade))

        to_grade= random_elements(to_grade, max_query)

        print('to grade now',to_grade)


        system_str="Je vais te donner une liste de noms d'entités, qui peuvent être des entreprises ou des associations. \n###\nJe veux en sortie un dictionnaire parfaitement valide, avec des guillemets doubles et des virgules, comme les entrées du fichier d'exemple, avec le même nombre d'entrées que dans la liste. Il doit donner un nombre entre 1 et 10 qui estime à quel point le but poursuivi par l'entité et ses membres est  commercial, ou est l'enrichissement de ses membres, de ses clients ou de ses actionnaires. Un score de 1 signifie une action sans portée commerciale, qui vise à aider les citoyens, l'environnement, ou l'interêt public, et un score de 10 signifie uniquement les interêts d'entreprises ou de clients privés, ou l'entité a le nom d'une personne privée.  Chaque score doit être précédé d'une courte phrase d'explication et suivi d'un niveau de confiance entre 1 et 10 pour chaque réponse. Le nombre de réponses doit être égale au nombre d'entrées.\n###\nVoilà des exemples de sorties:\n \"21 CENTRALE PARTNERS\": {\n \"explication\": \"Cette entité semble principalement axée sur des intérêts commerciaux et d'enrichissement de ses membres.\",\n \"score\": 10,\n \"confiance\": 8\n }\n#\n \"2C2I GESTION\": {\n \"explication\":\"Il est probable que cette entité ait une orientation commerciale, mais il est possible qu'elle ait d'autres objectifs également.\",\n \"score\": 8,\n \"confiance\": 5\n }\n#\n \"A C E P B\":{\n \"explication\":\"Pas d'élément précis, le A dénote peut-être une association.\",\n  \"score\":4,\n\"confiance\":2\n  }   \n#\n\"A ESPACE CARROSSERIE PEREZ\":{\n\"explication\": \"Cette entreprise vise principalement à fournir des services à ses clients, ce qui indique un but commercial évident. \",\n\"score\":10,\n\"confiance\": 10,\n}\n#\n\"A VIEILLE COURTIER HUILES\":{\n\"explication\":\"Entreprise de courtage.\",\n\"score\":10,\n\"confiance\": 10\n}\n#\n\"ALLORY ANTHONY\":{\n\"explication\" :\"Il s'agit du nom d'un individu, probablement entrepreneur représentant ses interêts.\",\n\"score\" :10 ,\n\"confiance\" :7\n}"
        msgs_gpt=[{
         "role": "system",
         "content": system_str
        }]




        for name in to_grade:
            msgs_gpt+=[{
             "role": "user",
             "content": name
            }]

        exampl={
         "21 CENTRALE PARTNERS": {
         "explication": "Cette entité semble principalement axée sur des intérêts commerciaux et d'enrichissement de ses membres.",
         "score": 10,
         "confiance": 8
         },
         "2C2I GESTION": {
         "explication":"Il est probable que cette entité ait une orientation commerciale, mais il est possible qu'elle ait d'autres objectifs également.",
         "score": 8,
         "confiance": 5
         },
         "A C E P B":{
         "explication":"Pas d'élément précis, le A dénote peut-être une association.",
          "score":4,
        "confiance":2
          }   ,
        "A ESPACE CARROSSERIE PEREZ":{
        "explication": "Cette entreprise vise principalement à fournir des services à ses clients, ce qui indique un but commercial évident. ",
        "score":10,
        "confiance": 10,
        },
        "A VIEILLE COURTIER HUILES":{
        "explication":"Entreprise de courtage.",
        "score":10,
        "confiance": 10
        },
        "ALLORY ANTHONY":{
        "explication" :"Il s'agit du nom d'un individu, probablement entrepreneur représentant ses interêts.",
        "score" :10 ,
        "confiance" :7
        }
        }
        #liste=["AMICALE ETUDIANTS PHARMACIE DE TOULOUSE","ANIVIN DE FRANCE","AQUA TEMPS-TRAITEMENT EAUX MIDI PYRENEES SERVICE","ARSENAL-CDM","ASS COORDINA TECHN INDUSTRIE AGRO ALIMEN","ALLIANCE CARTON NATURE"]

        printjs(msgs_gpt)
        print('*** msg gpt')
        #input('go gpt?')



        client = OpenAI()

        response = client.chat.completions.create(
          model="gpt-3.5-turbo",
          messages=msgs_gpt,
          temperature=0,
          max_tokens=4096,
          top_p=1,
          frequency_penalty=0.58,
          presence_penalty=0.45
        )

        resp=response.choices[0].message.content

        with open("backup-raw-gpt-res.txt", "w+") as file:
            file.write(str(resp))#backup reponse

        print(resp)
        parsed_res=parse_json_str(resp,True)
        printjs(parsed_res)
        prev_res.update(parsed_res)

        lpars=len(parsed_res)
        lgrad=len(to_grade)
        ratio=len(parsed_res)/len(to_grade)
        total_ratio+=ratio
        avg=total_ratio/iter_number

        print('parsed',lpars,'to grade',lgrad,'ratio',ratio,'avg ratio',str(avg))


        with open('results-gpt.json', 'w') as fichier:
            json.dump(prev_res, fichier, indent=4)
            print('data saved')


        if lpars<10 or ratio<.5 or avg<.65:
            input('warning, continue?')

        #print('unknown *******'+str(unknown_names))
#LOOP ENDS

grade(30)


#####
# rep={ "AMICALE ETUDIANTS PHARMACIE DE TOULOUSE": { "explication": "Il est probable que cette entité ait une orientation non-commerciale, axée sur les étudiants en pharmacie et leur bien-être.",  "score": 2,  "confiance": 6 },  "ANIVIN DE FRANCE": { "explication": "Cette entité semble principalement axée sur des intérêts commerciaux liés à l\'industrie du vin en France.",  "score": 9,  "confiance": 8 },  "AQUA TEMPS-TRAITEMENT EAUX MIDI PYRENEES SERVICE": { "explication": "Il est probable que cette entité ait une orientation commerciale, en offrant des services de traitement des eaux.",  "score": 7,  "confiance": 7 },  "ARSENAL-CDM": { "explication": "Cette entité semble avoir une orientation commerciale, peut-être liée à des services ou produits spécifiques.",  "score": 8,  "confiance": 6 },  "ASS COORDINA TECHN INDUSTRIE AGRO ALIMEN": { "explication": "Il est probable que cette entité ait une orientation commerciale, en offrant des services de coordination technique dans l\'industrie agroalimentaire.",  "score": 7,  "confiance": 8 },  "ALLIANCE CARTON NATURE": { "explication": "Cette entité semble avoir une orientation commerciale, en mettant en avant des produits respectueux de l\'environnement.",  "score": 6,  "confiance": 7 }}


#
# reponsegpt35={
#  "AMICALE ETUDIANTS PHARMACIE DE TOULOUSE": {
#  "score": 1,
#  "confiance": 9,
#  "explication": "Il est probable que cette entité ait un but non commercial, axé sur l'entraide et le soutien des étudiants en pharmacie."
#  },
#  "ANIVIN DE FRANCE": {
#  "score": 5,
#  "confiance": 6,
#   explication:   :"Cette entité semble avoir à la fois des intérêts commerciaux liés au vin (ANIVIN) mais peut également être impliquée dans d'autres activités plus larges."
#   } ,
# "AQUA TEMPS-TRAITEMENT EAUX MIDI PYRENEES SERVICE":
# {
# "score" :7,
# "confiance" :8 ,
# "explication:" :"Cette entreprise fournit des services de traitement de l'eau, ce qui indique une orientation commerciale pour répondre aux besoins du marché."
# },
# "ARSENAL-CDM":
# {
#  "score":10,
#  "confiance":9,
# "explication":"Le nom suggère une entreprise ou organisation avec un objectif commercial clair. "
# },
# "ASS COORDINA TECHN INDUSTRIE AGRO ALIMEN":{
# "score":8,
# "confiance":7,
#  "explication":"L'association semble avoir des objectifs techniques dans les secteurs agroalimentaires, ce qui pourrait inclure à la fois des aspects commerciaux et non-commerciaux."
# } ,
# "ALLIANCE CARTON NATURE":{
#   "score" :6 ,
# "confiance" :4 ,
#  "expication" :"Ce nom évoque potentiellement une alliance entre différentes entreprises travaillant dans le domaine du carton respectueux de l'environnement. Il y a donc probablement un aspect commercial mais aussi environnemental."  }}
