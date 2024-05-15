#from openai import OpenAI

import json
import re
def printjs(s):
 print(json.dumps(s, indent=4,   ensure_ascii=False))




import random
from openai import OpenAI
#terminal:OPENAI_API_KEY="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"
from unidecode import unidecode
import string

from fuzzywuzzy import fuzz
from fuzzywuzzy import process

def recherche_similaire(chaine, liste):
    return process.extractOne(chaine, liste)

def best_nom(firme):
    if 'nomUsage' in firme:
        return firme['nomUsage']
    else:
        return firme['denomination']

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


def nettoyer_chaine(chaine):
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
    global to_grade_now
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
            for orig_nom in to_grade_now:
                sim_score=compare_struct_names(nettoyer_chaine(orig_nom),nettoyer_chaine(nom))
                if sim_score>max_sofar:
                    max_sofar=sim_score
                    best_match=orig_nom
            if max_sofar>80:
                print(nom,best_match,max_sofar)
                # if max_sofar<90:
                #     input('ok?')
                nom=best_match
            else:
                #if 'carrosserie perez' not in nettoyer_chaine(nom) and 'courtier huile' not in nettoyer_chaine(nom): #ghost results
                print('no match',nom)
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

#
# but: faire passer de to_grade a


with open('to-grade.json','r') as f:#elements fichier lobbys.json matched
# search in lobbys file
    to_grade = json.load(f)
print('to grade '+str(len(to_grade)))

with open('results-gpt.json', 'r') as fichier:#maj progressivement, resultats gpt
    results_gpt = json.load(fichier)

to_grade=['SOGERES', 'MARCK & BALSAN', 'KORPORATE', 'FEDER INDUS CINEMA AUDIOVISUEL MULTIMEDI', 'VERISURE', 'FED NAT SOCIETES ANONYMES FONDATION HLM', 'TOTALENERGIES MARKETING SERVICES', 'KLASMANN-DEILMANN FRANCE', 'ASSOCIATION DES CONSEILS EN INNOVATION', 'ASSOCIATION FRANCAISE DES MARCHES FINANCIERS AMAFI', 'LYSIOS', 'FNSICAE', 'UFL', 'MUTUALITE FRANCAISE ILE DE FRANCE', 'GSOTF', 'SARP INDUSTRIES', 'ECF', 'AFL-ST', 'CREDIT AGRICOLE ASSURANCES', 'FNPHP', 'TOTALENERGIES ELECTRICITE ET GAZ FRANCE', 'NOKIA France', 'UNION REGIONALE MUT FRANCAISE LIMOUSIN', 'FNTR PROVENCE ALPES', 'UNION REGIONALE MUTUALITE FRANCAISE HAUT DE FRANCE NORD PAS DE CALAIS PICARDIE', 'WO2 HOLDING', 'MUTUALITE FRANCAISE PROVENCE ALPES COTE D AZUR', 'FONCIERE DE TRANSFORMATION IMMOBILIERE', 'FEDER REG BAT PROVE ALPES COTE D AZUR', 'KAUFMAN & BROAD SA', 'GROUPE SOUFFLET', 'ATOS', 'FEDERATION FRANCAISE DU BATIMENT DU CANTAL', 'FEDERATION DU BTP DU FINISTERE - 29', 'PLUXEE FRANCE', 'NOVAXIA INVESTISSEMENT', 'CERCLE VULNÉRABILITÉS ET SOCIÉTÉ', 'LE TRAIN', 'FEDERATION FRANCAISE DU BATIMENT DES PAYS DE LA LOIRE', 'CISCO SYSTEMS FRANCE', 'OTRE OCCITANIE', 'CMI PUBLISHING', 'RÉSEAU DES DIRIGEANTS FINANCIERS (DFCG)', 'USIPA', 'FÉDÉRATION EDT BRETAGNE', 'RHODIA OPERATIONS', 'SYND TRANSPORTEURS ROUTIERS', 'FEDER BATIMENT TRAVAUX PUB LOT & GARONNE', 'Naval Energies', 'BACK MARKET', 'FNTV CENTRE', 'JEUNESSE TV', 'UICB', 'VERMILION ENERGIES NOUVELLES', 'Fnas', 'ATARAXIE SOLUTIONS', 'XIAOMI TECHNOLOGY FRANCE', 'INSTITUT MERIEUX', 'GREENLOBBY - GL', 'WPD ONSHORE FRANCE', 'KEVIN SPEED', 'G-AGENCE', 'SMACL ASSURANCES', 'IPTA', 'UNION DE LA PRESSE EN REGIONS', "ASSO FEDER BATIMENT ET DES TP DE L'AUDE", 'STORENGY SAS', 'NATIXIS', 'FRANCE DATACENTER', "ASFA ASSOCIATION PROFESSIONNELLE DES SOCIETES FRANCAISES CONCESSIONNAIRES OU EXPLOITANTES D'AUTOROUTES OU D'OUVRAGES ROUTIERS", 'FED DEPT DU BATIMENT TRAVAUX PUBLICS', 'DAVID RAUSCENT', 'CHAMBRE SYNDICALE DE LA LEVURE FRANCAISE', 'PAPREC GROUP', 'OTRE BRETAGNE', 'MEDEF PF', 'SELL', 'UNIS', 'SHOPIFY COMMERCE FRANCE', 'FVD', 'CLEVER CLOUD', 'ESTERIFRANCE', 'SYNDICAT NATIONAL FAB HUILE', 'ACCOR', 'AXA FRANCE IARD', 'SP2C', "UNICINE L'UNION DES CINEMAS", 'FRANCE TELEVISIONS', 'SNROC', 'H2X ECOSYSTEMS', 'GILLES SAVARY CONSULTANTS', 'MONEL', 'SEANCE PUBLIQUE', 'BOULIN FRANCK RICHARD HENRI', "FEDERATION NATIONALE DE L'AVIATION ET DE SES METIERS", 'ALAN', 'FEDE BATIMENT ET TRAVAUX PUBLICS HAUT RHIN', 'ST', 'LNA SANTE', 'MUTUALITE FRANCAISE NORMANDIE', 'SHLMR', 'FED DEP BATIMENT TRAVAUX PUBLICS ARDENNE', 'ILIAD', 'TWITTER FRANCE SAS', 'CONFED SYND MEDICAUX FRANCAIS', "CONSEIL REGIONAL DE L'ORDRE DES ARCHITECTES DE NORMANDIE", 'FED BATIMENT TRAVAUX PUBLICS INDRE', 'ECOLOGIE LOGISTIQUE', 'AKUO ENERGY SAS', 'FEDER REGIONALE DES T P BRETAG', 'LABORATOIRE FRANCAIS DU FRACTIONNEMENT ET DES BIOTECHNOLOGIES', 'FEDERATION BATIMENT TP ILLE ET VILAINE', 'SNJV', 'TEREOS PARTICIPATIONS', 'FEDERATION BTP VOSGES', 'CLARIANE FRANCE', 'ENTREPRISES FLUVIALES DE FRANCE', 'CAP', 'FNEC', "CONSEIL NATIONAL DE L'ORDRE DES CHIRURGIENS DENTISTES", 'SIFPAF', 'FEDERAT NATIONALE ARTISANAT AUTOMOBILE', 'MEDICOM', 'FEFIS', 'INSTITUTIONS ET STRATEGIES', 'FEDERATION FRANCAISE DU BATIMENT HAUTE-VIENNE', 'ABB FRANCE', 'EQIOM', 'SNC ALTAREA MANAGEMENT', 'INTERPROFESSION VOLAILLE DE CHAIR', 'GTP 31', 'FFB 14', 'EFFY', 'SFIL', 'UCFF', 'FEDERATION NATIONALE PRODUCTEURS FRUITS', 'DOMPLUS GROUPE', 'AROMATES', 'BIM UK', 'SETO', 'FEDERATION DU BTP DU TERRITOIRE DE BELFORT', 'CCIC', 'FEDERATION B T P SARTHE', 'HAVAS PARIS', 'M2I LIFE SCIENCES', 'ERICSSON FRANCE', 'VERBA ET RES', 'PIETRA CONSULTING', 'STR@T-ALGO CONSEIL', 'OGMIOS CONSULTING', 'AGENCE KOMUN', 'EXPEDIA GROUP', 'FEDERATION DU NEGOCE AGRICOLE', 'CAPITAL ENERGY', 'RES', 'FEDALIM', 'SIEMENS GAMESA RENEWABLE ENERGY S.A.S.', 'SERVIER MONDE', 'FEDER BATIMENT TRAVAUX PUBLIC DE MOSELLE', 'EVOLIS-SYMOP', 'ZIMMER BIOMET FRANCE', 'PAYPAL EUROPE ET CIE SCA', 'LME', 'RATP SOLUTIONS VILLE', 'CONFÉRENCE DES BÂTONNIERS', 'FÉDÉRATION DES FABRICANTS DE CIGARES', 'SIEMENS MOBILITY SAS', 'EURONEXT PARIS SA', 'MUTUALITE FRANCAISE BRETAGNE', 'ATR', 'ENOTIKO', 'UBISOFT', 'FRANCE AGRIVOLTAISME', 'CFSI', 'CONFEDERATION GENERALE PME', 'U2P NORMANDIE', 'CPME RHONE ', 'BELLET OLIVIER', 'PERLUCERE', 'CABINET PISTRE', 'PROFEDIM', 'SYND FEDERATION  FRANCAISE DU BATIMENT GRAND PARIS', 'EDENRED', 'ASSOCIATION INTERPROFESSIONNELLE DE LA BANANE', 'ALLIANCE DU COMMERCE', 'MUTUALITE FRANCAISE AUVERGNE RHONE ALPES', 'BONNEAU OLIVIER PHILIPPE MICHEL', 'UNION FRANCAISE INDUSTRIES CARTONS PAPIERS ET CELLULOSES', 'GROUPEMENT NATIONAL CHAINES HOTELIERES', 'UNION PATRON PROTHESE DENTAIRE', 'FFB DORDOGNE', 'ALTA CONSEILS', 'CPME AUVERGNE RHONE ALPES', 'FNTV BFC', 'MORE IMPACT', 'RENAULT TRUCKS', 'MBDA FRANCE', 'FEDERATION DU BATIMENT & DES TP DE VAUCL', 'FFB44', 'STRYKER FRANCE', 'BLUESTORAGE', 'CREDIT AGRICOLE CORPORATE AND INVESTMENT BANK', 'VOLVO COMPACT EQUIPMENT SA', 'U2P NOUVELLE-AQUITAINE', 'EUROAPI FRANCE', 'CIE IBM FRANCE', 'FEDER NATIONAL INDUST LAITIERE', 'JJSBF - KENVUE FRANCE', 'FEDERATION DEP ENTREP. ARTISANS DU BAT', 'UNION DE LA PUBLICITE EXTERIEURE', 'CHIMIREC DEVELOPPEMENT', 'MILENCE FRANCE SAS', 'TOTALENERGIES RAFFINAGE FRANCE', 'BLUEFLOAT ENERGY HOLDINGS FRANCE SAS', 'COVIVIO DEVELOPPEMENT', 'COMITE INTERPROF VIN APPELLATION ORIGINE', 'GEMME', 'CONSTELLIUM SE', 'ACIM', 'ARESIA', 'ERG FRANCE', 'P&B PARTNERS CONSEIL', 'FEDERATION DEP B.T.P. CORSE DU SUD', 'COMPLIANCE - ETHIQUE - CONFORMITE DES AFFAIRES IMMOBILIERES', 'FFVA', 'FTOM', 'DENTONS GLOBAL ADVISORS FRANCE SAS', 'ACIFTE', 'VANTIVA', 'Association des organismes HLM Auvergne-Rhône-Alpes - AURA HLM', 'FEDERATION DES ENTREPRISES DE PORTAGE SALARIAL', 'ADN TOURISME', 'OTRE GIRONDE', 'TOTALENERGIES PETROCHEMICALS FRANCE', 'ECOMAISON', 'ELENGY', 'FED BTP 53', 'FPMM', 'OTRE PACA', 'SOFRADIR', 'REFORM PARIS', 'CARMILA', 'GARRD', 'UNION MUT FRANCAISE PAYS DE LA LOIRE', 'AXA', 'GE FRANCE', 'BOUYGUES', 'MUTUALITÉ FRANÇAISE NOUVELLE-AQUITAINE', 'ARKEMA FRANCE', 'INTRUM CORPORATE', 'FFB 17', 'UNION INDUSTRIES ENTR EAU ENVIRONNEMENT', 'CROAPL', 'PRIMUM NON NOCERE', 'NW ENERGY', 'SICPA FRANCE', 'FEDERAT NAT COOPERAT CONSOMM', 'ASSOCIATION DES PRODUCTEURS INDEPENDANTS', 'FEDERATION BATIMENT TRAVAUX PUBLICS ISER', 'UNIBAIL MANAGEMENT', 'U2P DES HAUTS DE FRANCE', "FEDERATION FRANCAISE DES METIERS DE L'INCENDIE", 'CONFEDERATION DES PETITES ET MOYENNES ENTREPRISES', 'FLIXBUS FRANCE SARL', 'CONVICTIO LEGAL', 'FEDERATION DE LA MODE CIRCULAIRE', 'UNELEG', 'HYVIA', 'OTRE DES PAYS DE L ADOUR', 'HOMEAWAY FRANCE', 'UPF', 'FFB CHER', 'LES ENTREPRISES DU VOYAGE', 'DROPBOX FRANCE', 'MAIAGE', 'FFPO', 'LAFARGE FRANCE', 'AGDATAHUB', 'USH OCCITANIE M&P', 'FEDERATION FRANCAISE DU BATIMENT LANDES', 'OTRE AUVERGNE RHONE ALPES', 'FEDERATION BANCAIRE FRANCAISE', 'FFB BRETAGNE', 'YOPLAIT FRANCE', 'ROCHE DIAGNOSTICS FRANCE', 'FDJ', 'FILIANCE', 'EKWATEUR', 'GTB', 'DB CARGO FRANCE - DBCFR SAS', 'FNTR ALPES MARITIMES', "FEDERATION NATIONALE DES SYNDICATS D'EXPLOITANTS AGRICOLES 76", 'GE RENEWABLE MANAGEMENT', 'AXA FRANCE VIE', 'CLARIANE', 'GNI', 'UAF', 'FRANCE MEDIAS MONDE', 'FEDERATION FRANCAIS BATIMENT EURE & LOIR', 'SOLIFAP', 'SOCIETE GENERALE', 'FED FRANCAISE DU PRET A PORTER FEMININ', 'FEDERATION BAT TRAVAUX PUBLICS DES P.A.', 'MCPHY ENERGY', 'AFNOR CERTIFICATION', 'CORTEVA AGRISCIENCE', 'Fédération du bâtiment et des travaux publics de la meuse', 'FFB 37', 'LIGHTHOUSE EUROPE', 'CONSEIL REGIONAL DE L ORDRE DES ARCHITECTES DES HAUTS DE FRANCE', 'ALLIANCE DES MINERAIS MINERAUX ET METAUX - A3M', 'FEDERATION BATIMENT TRAVAUX PUBLICS PDD', 'SEQENS', 'MUTUALITE FRANCAISE BOURGOGNE FRANCHE COMTE', 'EGF BTP', 'REV Mobilities', 'SCALEWAY', 'TOTALENERGIES RAFFINAGE CHIMIE', 'GHN', 'DOCAPOSTE', 'CNAOC', 'ORANO SA', 'CONSEIL REG ORDRE ARCHITECTES DU CENTRE', 'CSD', 'SOMFY ACTIVITES SA', 'FEDERA REG TRAVAU PUBLIC REG CHAMP ARDEN', 'Syndicat des radios indépendantes', 'APECESU', 'XXII', 'FEDERATION DES INDUSTRIES NAUTIQUES', 'SYNDICAT TRANSPORTS ROUTIERS DU TARN', 'PARROT', 'ELIANCE', 'SUPERMARCHES MATCH', 'NATIXIS INVESTMENT MANAGERS', 'SODERN', 'ECOMINERO', 'FEDERATION FRANCAISE DU BATIMENT CENTRE-VAL DE LOIRE', 'RAMSAY GENERALE DE SANTE', 'SODEXO SANTE MEDICO SOCIAL', 'SALTO', 'EURO2C', 'BINANCE FRANCE SAS', 'FEDERATION BTP DE LA LOIRE', 'CONSEIL NATIONAL DE L ORDRE DES PHARMACIENS', "CONSEIL RÉGIONAL DE L'ORDRE DES ARCHITECTES D'ÎLE-DE-FRANCE", "LES COOP'HLM", 'BTP 77', 'GCK', 'TOTALENERGIES MARKETING FRANCE', 'FEDER PATRONALE BAT ET TP EURE', 'KRONENBOURG SAS', 'FNC HN', "EVOLIS ORGANISATION PROFESSIONNELLE DE BIENS D'EQUIPEMENT", 'GROUPE LACTALIS', 'FI GROUP', 'FEDERATION FR DU BAT DE MAINE ET LOIRE', 'SAS TRADITAB', 'FEDER DEPART SYNDIC EXPLOI AGRIC HERAULT', 'BAILLET DULIEU ASSOCIES', 'ASS  FENACEREM', 'IPSEN', 'FEDERATION MORB DU BATIMENT ET DES T.P.', 'GROUPE CANAL+ SA', 'DOREMI', 'HELLIO SOLUTIONS', 'SULO FRANCE', 'FEDERATION BATIMENT TRAVAUX PUBLICS DROME ARDECHE', 'Fédération Française des Télécoms', 'STELLANTIS', 'FEDERATION FRANÇAISE DES PROFESSIONNELS DE LA BLOCKCHAIN (FFPB)', 'OTRE CENTRE VAL DE LOIRE', 'UDTR 12', 'EUROTRADIA INTERNATIONAL', 'FORWARD GLOBAL', 'FÉDÉRATION DES ENTREPRISES DE PROPRETÉ D’HYGIÈNE ET SERVICES ASSOCIÉ', 'ORTHONGEL', 'FBTP DOUBS', "TECH'IN FRANCE", 'FIPEC', 'FEDERATION FRANCAISE BATIMENT AUVERGNE RHONE ALPES', 'FFB OCCITANIE', 'BPCE', 'TOMRA COLLECTION FRANCE', 'TLF OVERSEAS', 'UNION DES ENTREPRISES DE PROXIMITE DES HAUTES-ALPES', 'FFB67', "AGÉA - FÉDÉRATION NATIONALE DES SYNDICATS D'AGENTS GÉNÉRAUX D'ASSURANCE", "ENR'CERT", 'LIVI', 'UNION DES ENTREPRISES DE PROXIMITE DE BOURGOGNE FRANCHE-COMTE (U2P BOURGOGNE FRANCHE-COMTE)', 'CPME ISERE', 'OTRE ILE DE FRANCE', 'BEL', 'CONFED COMMERC DETAIL FRANCE', 'AEGIDE', 'GRANDVISION FRANCE', 'FED FRANC COOPER FRUIT LEGUME HORTICOLE', 'SISLEY', 'SYNDICAT FRANCAIS DES SIROPS', 'FDMC', 'UNAM', 'ALLIANCE PLASTURGIE ET COMPOSITES DU FUTUR PLASTALLIANCE', 'STORENGY FRANCE', 'SYNDICAT NATIONAL DES SCENES PUBLIQUES', 'FFB 86', 'REMADEGROUP', 'FEDERATION FRANCAISE DE LA CHAUSSURE', 'FFB BTP71', 'FNCUMA', 'NILE', 'FEDERATION DES PARTICULIERS EMPLOYEURS DE FRANCE', 'FEDERATION BTP 13', 'OTRE POITOU CHARENTES', 'UNION REG MUTUALITE FRANCAISE DE CORSE', 'U2P06', 'QONTO', 'ANTHENOR PUBLIC AFFAIRS', 'AORIF', 'FEDERATION DU BATIMENT ET DES TRAVAUX PUBLICS DE LA SOMME', 'KNAUF INDUSTRIES', 'Marquat GBM', 'FEDERATION DU BATIMENT ET DES TRAVAUX PUBLICS DU VAR', 'UNION INDUSTRIES TEXTILES', 'ARTHESIAS CONSEIL', 'NEWS REPUBLIC', 'STR 47', 'F.F.A.F.', 'PERIFEM', 'UNION NATIONALE DES ECONOMISTES DE LA CONSTRUCTION', 'FEDER DEPAR BATIM TRAVA PUBLI HTE-LOIRE', 'FIGEC', 'BOEHRINGER INGELHEIM ANIMAL HEALTH FRANCE', 'CGPME DE HAUTE SAVOIE', 'GENERAL MILLS FRANCE', 'GNTC', 'SCAM', 'OTRE DORDOGNE LIMOUSIN', 'MATERA', 'GIFEN', 'NPA CONSEIL', 'SYNDICAT DES ENTREPRISES DE SURETE AERIENNE ET AEROPORTUAIRE', 'FRANCE CHIMIE ILE DE FRANCE', 'CONFED NAT MUTUALITE COOP ET CREDIT AGRI', 'ENALIA', 'UNION DES MAISONS DE CHAMPAGNE', 'URGO GROUP', 'BAYWA R.E. FRANCE', "COMPAGNIE EUROPEENNE D'INTELLIGENCE STRATEGIQUE (CEIS)", 'CREDIT AGRICOLE SA', 'ENI GAS & POWER FRANCE', 'UNAFOS', 'ALPIQ ENERGIE FRANCE SAS', 'CATENAE', 'BUREAU INTERPROFESSIONNEL VINS DU CENTRE', 'FFB 21', 'AFCOME', 'ASSOCIATION REGIONALE HLM DE BOURGOGNE', 'FEDERATION NATIONALE TRANSPORT VOYAGEURS', 'MCI FRANCE', 'EP FRANCE', 'FEDERATION DEPART DU BTP DES AM', 'NEXTROAD', 'FESAC', 'IQVIA OPERATIONS FRANCE SAS', 'CSDEM', 'BETCLIC', 'COVEA', 'UNION FRANCAIS INDUSTRIE HABILLEMENT', 'SVM CONSULT', 'SOROA', 'BUREAU VERITAS SERVICES FRANCE', 'CPME AISNE', 'NEWCLEO', 'INTEL CORPORATION SAS', 'FEDERATION DES BATIMENTS ET DES TP DE LA MANCHE', 'TOO GOOD TO GO', 'CNATP', 'GTFI', 'COMITE DE LIAISON CENTRES DE GESTION', 'CNP ASSURANCES', 'FEDERATION FRANCAISE DU BATIMENT ROUEN METROPOLE ET TERRITOIRES', 'ANM CONSEILS SAS', 'FEDERAT DEP BAT TRAVAUX PUBLICS L AUBE', 'SODEXO SPORTS ET LOISIRS', 'SYND TRANSP ROUTIERS LOIRE', 'FEDERATION FRANCAISE DE LA CORDONNERIE MULTISERVICE', 'FEDERATION DEPARTEM BATIMENT T.P. ORNE', 'FFB DU GARD', 'AMYNOS', 'MACOPHARMA', 'ALLIAGES ET TERRITOIRES', 'FEDERAT BATIM TRAVAUX PUBLIC REGION HAVR', 'CGAD', 'FEDER BATIMENT REGION BOURGOGN', 'CONFEDERATION NATIONALE DE LA MOBILITE', 'AMARENCO', 'FRANSYLVA', 'ASS NATIONAL MEUNERI FRANCAISE', 'CERTIVEA', 'UNION TERRITORIALE DES PETITES ET MOYENNES ENTREPRISES DE LA GUYANE', 'RIVIERE VIANNEY LIONEL LOUIS', 'CGR', 'MERCIALYS', 'FED DEP DU BATIMENT ET DES T P DU GERS', 'UNION REGIONALE MUTUALITE FRANCAISE GRAND EST', 'AMUNDI ASSET MANAGEMENT', 'HEINEKEN FRANCE', 'HEIDELBERGCEMENT FRANCE S.A.S', 'THALES ALENIA SPACE FRANCE', 'GROUPEMENT NAT CARROSSIERS REPARATEURS', 'MUTUALITE FRANCAISE DE GUADELOUPE', 'U2P GRAND EST', 'ARIANEGROUP HOLDING', 'MIROVA', 'MEL SDC', 'SNELAC', 'UIMM 35-56', 'SUEZ', 'BEDARD AVOCAT', 'FBTP22', 'RIVINGTON', 'ENERCOOP', 'ALDES AERAULIQUE', 'FEDERATION DES ENTREPRISES DE LA SECURITE FIDUCIAIRE( FEDESFI)', 'FEDERATION BATIM TRAVA PUBLIC D SEVRES', 'ADOBE']



liste_firmes_to_grade=[
"Association",
"Syndicat",
"Chambre consulaire",
"Organisation syndicale et professionnelle",
"Autres organisations",
"Société civile (autre que cabinet d’avocats)",
"Fondation",
"Autre organisation",
"Etablissement public exerçant une activité industrielle et commerciale",
"Groupe de réflexion (think tank)",
"Établissement public exerçant une activité industrielle et commerciale",
"Organisme de recherche ou de réflexion",
"Autres organisations non gouvernementales",
"Coopérative agricole"
]
# for key in lobbys:
#     firme=lobbys[key]
#     parent=firme['parentId']
#     print(key,parent)
#     print(parent)
#     if parent in liste_firmes_to_grade:
#         print('parent ok')
#         if key not in results_gpt:
#             to_grade[key]={'categorie':parent,'ident':lobbys[key]['options']['identifiant']['value']}
#             if key in missing_matched['matched']:
#                 to_grade[key].update(missing_matched['matched'][key])
#                 printjs(to_grade[key])
#                 print('missing matched')
#             elif key in opendata_matched['unknowns']:
#                 to_grade[key].update(opendata_matched['unknowns'][key])
#                 printjs(to_grade[key])
#                 print('opendate matched')
#             elif key in opendata_matched['matched']:
#                 print(opendata_matched['matched'][key])
#                 to_grade[key].update(opendata_matched['matched'][key])
#                 printjs(to_grade[key])
#                 input('opendate matched. what to include?')
#             elif key in missing_matched['unknowns']:
#                 print(missing_matched['unknowns'][key].keys())
#                 to_grade[key]={}
#                 print('missing unknown. nothing to include?')


#
# to_grade_info={}
# to_grade_cat={}
# to_grade_naked={}
#
# input(len(results_gpt))
#
# counter=0
# for key  in to_grade:
#     counter=counter+1
#     #print(counter,'/',len(to_grade))
#     #print('***',to_grade[key])
#     if 'activites' in to_grade[key]:
#         to_grade_info[key]={}
#         if 'objet' in to_grade[key]['activites']:
#             to_grade_info[key]['objet']=to_grade[key]['activites']['objet']
#
#         if 'lib_activite_principale' in to_grade[key]['activites'] and to_grade[key]['activites']['lib_activite_principale'] != 'Autres organisations fonctionnant par adhésion volontaire':
#             to_grade_info[key]['activite']=to_grade[key]['activites']['lib_activite_principale']
#
#         if 'lib_objet_social1' in to_grade[key]['activites']:
#             to_grade_info[key]['objet social']=to_grade[key]['activites']['lib_objet_social1']
#
#         if 'lib_famille1' in to_grade[key]['activites']:
#             to_grade_info[key]['famille']=to_grade[key]['activites']['lib_famille1']
#
#         print('info',to_grade_info[key])
#     elif 'categorie' in to_grade[key]:
#         to_grade_cat[key]={'categorie':to_grade[key]['categorie']}
#         #print('cat')
#     else:
#         to_grade_naked[key]=to_grade[key]
#
#
#
#
# print('info',len(to_grade_info))
# print('cat',len(to_grade_cat))
# print('nak',len(to_grade_naked))
# exit()
#
# input('?')

client = OpenAI()
def grade(limit):
    global to_grade
    global to_grade_now
    total_ratio=0
    for iter_number in range(1,limit):

        with open('results-gpt.json', 'r') as fichier:#maj progressivement, resultats gpt
            results_gpt = json.load(fichier)

        to_grade_now=[]
        for key in to_grade:
            if key not in results_gpt:

                to_grade_now+=[key]
        print('remaining',len(to_grade_now))
        max_query=20
        to_grade_now= random_elements(to_grade_now, max_query)

        print('to grade now',to_grade_now)


        system_str="Je vais te donner une liste de noms d'entités, qui peuvent être des entreprises ou des associations, avec quelques informations supplémentaires.\n ###### Je veux en sortie un dictionnaire parfaitement valide, avec des guillemets doubles et des virgules, comme les entrées du fichier d'exemple, avec le même nombre d'entrées que dans la liste. Il doit donner un nombre entre 1 et 10 qui estime à quel point le but poursuivi par l'entité et ses membres est  commercial, ou est l'interêt de ses membres, de ses clients ou de ses actionnaires. Un score de 1 signifie une action sans portée commerciale ou privée, qui vise à aider les citoyens, l'environnement, ou l'interêt public, et un score de 10 signifie uniquement les interêts d'entreprises ou de clients privés, ou l'entité a le nom d'une personne privée.  Chaque score doit être précédé d'une courte phrase d'explication et suivi d'un niveau de confiance entre 1 et 10 pour chaque réponse. Le nombre de réponses doit être égale au nombre d'entrées.\n###\nVoilà des exemples de sorties:\n \"21 CENTRALE PARTNERS\": {\n \"explication\": \"Cette entité semble principalement axée sur des intérêts commerciaux et d'enrichissement de ses membres.\",\n \"score\": 10,\n \"confiance\": 8\n }\n#FDSEA Cotes d'Armor (22)\": {\n        \"score\": 7,\n        \"explication\": \"Il s'agit d'un syndicat agricole qui vise à défendre les intérêts des exploitants agricoles.\",\n        \"confiance\": 9\n    }\n#\n \"2C2I GESTION\": {\n \"explication\":\"Il est probable que cette entité ait une orientation commerciale, mais il est possible qu'elle ait d'autres objectifs également.\",\n \"score\": 8,\n \"confiance\": 5\n }\n#\n \"A C E P B\":{\n \"explication\":\"Pas d'élément précis, le A dénote peut-être une association.\",\n  \"score\":4,\n\"confiance\":2\n  }   \n#\n\"JEUNES AGRICULTEURS DE LA VIENNE\":{\n \"explication\": \"il s agit d'une classe d'individus qui veulent améliorer leurs revenus et leurs conditions de travail\",\n \"score\": 7,\n \"confiance\":9\n}\n#\n\"ALLORY ANTHONY\":{\n\"explication\" :\"Il s'agit du nom d'un individu, probablement entrepreneur représentant ses interêts.\",\n\"score\" :10 ,\n\"confiance\" :7\n}\n"
        msgs_gpt=[{
         "role": "system",
         "content": system_str
        }]




        for name in to_grade_now:
            msgs_gpt+=[{
             "role": "user",
             "content": str(name)
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
        print('ask gpt...')
        #input('go gpt?')




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
        results_gpt.update(parsed_res)

        lpars=len(parsed_res)
        lgrad=len(to_grade_now)
        ratio=len(parsed_res)/len(to_grade_now)
        total_ratio+=ratio
        avg=total_ratio/iter_number

        print('parsed',lpars,'to grade',lgrad,'ratio',ratio,'avg ratio',str(avg))


        with open('results-gpt.json', 'w') as fichier:
            json.dump(results_gpt, fichier, indent=4)
            print('data saved')


        if  ratio<.6 or avg<.5:
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
