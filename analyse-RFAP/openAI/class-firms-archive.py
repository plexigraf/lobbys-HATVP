#from openai import OpenAI

import json
import re
import time
def printjs(s):
 print(json.dumps(s, indent=4,   ensure_ascii=False))
import random
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
    substring=str(substring)
    target_string=str(target_string)
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
    return chaine

def simplifier(chaine):
    if chaine==None:
        return ''
    chaine = unidecode(chaine).lower()#accents et capitales
    chaine = re.sub(r'\([^)]*\)', '', chaine)#retirer parentheses
    chaine = re.sub(r'[\/\\].*', '', chaine)#enlever apres slashs
    chaine = re.sub(r'[%s]' % re.escape(string.punctuation), '', chaine)#retirer ponctuation
    # Supprimer le contenu entre parenthèses et les parenthèses elles-mêmes, ou ce qu'il y a après un slash
    #chaine = re.sub(r'\([^)]*\)|/.*', '', chaine)

    #chaine=''.join(e for e in chaine if e.isalnum() or e.isspace())
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

def find_best_match(liste,infos_dict,verb=False):#find best match between 1 list and the keys of a dict (containing infos)
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
                best_match['ressemblance avec ']=k
            if best_score>90:
                break
    return {'best_score':best_score,'best_match':best_match}


with open('openAI/class-gpt.json','r') as f:
    class_gpt_keys=list(json.load(f).keys())


with open('openAI/class-gpt_2.json', 'r') as fichier:#maj progressivement, resultats gpt
    class_gpt_2 = json.load(fichier)

with open('firms_suppl_info.json','r') as f:
    to_grade=json.load(f)
for k in class_gpt_keys:
    if k not in to_grade:
        to_grade[k]={}

class UniqueList(list):
    def add(self, item):
        if item not in self:
            self.append(item)


with open('other_names.json','r') as f:
    other_names=json.load(f)


with open('nafs.json','r') as f:
    nafs_raw=json.load(f)

nafs={}
for code in nafs_raw:
    nafs[code['id']]=code['label']


#seules formes juridiques n'amenant pas classif "privé":
not_private_forme_jur=['NA',"Association de droit local (Bas-Rhin, Haut-Rhin et Moselle)","Fondation","Autre société civile","SA d'économie mixte à conseil d'administration","Syndicat de salariés","Association d'avocats à responsabilité professionnelle individuelle","Syndicat mixte fermé","Association déclarée","Autre organisme professionnel"]

#formes juridiques amenant classif "public"
public_forme_jur=["Association déclarée, reconnue d'utilité publique","Établissement public national à caractère industriel ou commercial non doté d'un comptable public","Établissement public national à caractère industriel ou commercial doté d'un comptable public","Association déclarée d'insertion par l'économique","SA nationale à conseil d'administration","Association syndicale libre","Région","Autre établissement public national administratif à compétence territoriale limitée","Communauté d'agglomération","Métropole","Établissement public local à caractère industriel ou commercial"]


public_obj_soc=[
    "aide à  l'emploi, développement local, solidarité économique",
    "accompagnement, aide aux malades",
    "promotion de l'art et des artistes",
    "défense de droits fondamentaux, activités civiques",
    "associations caritatives intervenant au plan international",
    "associations caritatives, humanitaires, aide au développement",
    "associations d'étudiants, d'élèves",
    "mouvements de consommateurs",
    "action sensibilisatrion environnement  , développement durable",
    "accueil et protection de la petite enfance",
    "défense des droits des personnes homosexuelles",
    "mouvements écologiques",
    "associations caritatives à  buts multiples",
    "secours en nature, distribution de nourriture et de vêtements",
    "protection des animaux",
    "usagers de services publics",
    "amicale de personnes originaires d'une même région",
    "protection de sites naturels",
    "mouvements  éducatifs de jeunesse et d'éducation populaire",
    "associations de personnes malades, ou anciens malades",
    "prévention et lutte contre l'alcoolisme,, le tabac,  la toxico",
    "associations familiales, services sociaux pour les  familles",
    "groupements d'entraide et de solidarité",
    "activités citoyennes européennes",
    "aide à  l'insertion des jeunes",
    "défense des libertés publiques et des droits de l'Homme",
    "entraide et solidarité des personnes homosexuelles",
    "comités de défense du patrimoine",
    "préservation de la faune sauvage",
    "aide aux accidentés du travail",
    "entraide et solidarité des personnes en situation de handicap",
    "préservation du patrimoine",
    "aide sociale aux personnes en situation de handicap",
    "foyers socio-éducatifs",
    "défense des droits des enfants",
    "aide aux victimes de maladies professionnelles",
    "défense des droits  des victimes",
    "amicale de personnes originaires d'un même pays (hors défense",
    "aide aux personnes en danger, solitude, désespoir, soutien psy",
    "défense des droits des personnes étrangères ou immigrées",
    "secours financiers et autres services aux personnes en difficult",
    "associations philanthropiques",
    "associations féminines pour l'entraide et la solidarité",
    "amicales, personnel d'établissements scolaires ou universitaire",
    "maisons de jeunes, foyers, clubs de jeunes",
    "aide aux réfugiés et aux immigrés (hors droits fondamentaux)",
    "défense des droits des personnes en situation de handicap",
    "groupements de chômeurs, aide aux chômeurs",
    "lutte contre les discriminations",
    "aide et conseils aux familles",
    "loisirs pour personnes en situation de handicap",
    "sécurité routière",
    "défense des droits des personnes rapatriées",
    "défense de la paix",
    "aide à  domicile",
    "services médicaux d'urgence",
    "aide au logement",
    ]
prive_obj_soc=["organisation de professions (hors caractère syndical)","radios privées",
    "groupement d\\'employeurs",
    "chasse",
    "chambres de commerce, chambres économiques",
    "professionnels de l'information  et de communication",
    "gestion financière, gestion immobilière",
    "élevage canin, clubs de chiens de défense",
    "Golf",
    "actionnaires, épargnants",
    "conduite d'activités économiques",
    "représentation, promotion et défense d'intérêts économiques",
    "représentation d'intérêts économiques sectoriels",
    "groupement d'achats, groupement d'entreprises",
    "groupements professionnels",
    "unions patronales",
    "professionnels de l\\'information  et de communication",
    "artisans commerçants",
    "association à  but commercial, développement économique"]

public_fam=[
    'associations caritatives, humanitaires, aide au développement, développement du bénévolat',
    "interventions sociales",
    "aide à l'emploi, développement local, promotion de solidarités économiques, vie locale",
    "défense de droits fondamentaux, activités civiques",
    "associations caritatives, humanitaires, aide au développement, développement du bénévolat",
    "préservation du patrimoine",
    "action socio-culturelle",
    "activités religieuses, spirituelles ou philosophiques"]

prive_fam=[
    "représentation, promotion et défense d'intérêts économiques",
    "conduite d'activités économiques",
    "Tourisme"]

prive_act=[
    "Réassurance",
    "Autres intermédiations monétaires",    "Télécommunications filaires",
    "Réparation de machines et équipements mécaniques",
    "Transformation du thé et du café",
    "Supermarchés",
    "Réparation d'ouvrages en métaux",
    "Transports aériens de passagers",    "Recherche-développement en biotechnologie",
    "Travaux d'installation d'équipements thermiques et de climatisation",    "Réparation d'équipements électriques",
    "Portails Internet",
    "Installation de machines et équipements mécaniques",
    "Extraction de pétrole brut",
    "Autres activités des médecins spécialistes",
    "Vente à distance sur catalogue spécialisé",
    "Activités comptables",
    "Construction de réseaux électriques et de télécommunications",    "Activités de centres d'appels",
    "Extraction d'autres minerais de métaux non ferreux",    "Activités de pré-presse",
    "Activités des voyagistes",
    "Régie publicitaire de médias",
    "Entreposage et stockage non frigorifique",
    "Centrales d'achat alimentaires",
    "Raffinage du pétrole",
    "Autres activités auxiliaires de services financiers, hors assurance et caisses de retraite, n.c.a.",    "Hébergement touristique et autre hébergement de courte durée",
    "Promotion immobilière de logements",
    "Autre distribution de crédit",
    "Sciage et rabotage du bois, hors imprégnation",
    "Sidérurgie",
    "Distribution de films cinématographiques",
    "Construction de véhicules automobiles",
    "Culture de céréales (à l'exception du riz), de légumineuses et de graines oléagineuses",    "Restauration traditionnelle",
    "Hypermarchés",
    "Fonds de placement et entités financières similaires",
    "Location et location-bail d'articles de loisirs et de sport",
    "Centrales d'achat non alimentaires",
    "Transformation et conservation de la viande de boucherie",
    "Métallurgie de l'aluminium",
    "Activités des centres de culture physique",
    "Télécommunications sans fil",
    "Activités des agents et courtiers d'assurances",
    "Restauration collective sous contrat",    "Location de longue durée de voitures et de véhicules automobiles légers",    "Activités des agences de recouvrement de factures et des sociétés d'information financière sur la clientèle",    "Services auxiliaires des transports aériens",    "Élevage d'autres animaux",
    "Édition de logiciels système et de réseau",    "Étirage à froid de barres",
    "Location et location-bail d'autres machines, équipements et biens matériels n.c.a.",
    "Location de terrains et d'autres biens immobiliers",
    "Location de courte durée de voitures et de véhicules automobiles légers",    "Activités des parcs d'attractions et parcs à thèmes",
    "Construction de locomotives et d'autre matériel ferroviaire roulant",    "Forge, estampage, matriçage ; métallurgie des poudres",
    "Services administratifs combinés de bureau",
"Activités des agences de publicité",    "Industrie des eaux de table",
    "Location et location-bail de machines de bureau et de matériel informatique",    "Construction de véhicules militaires de combat",
    "Construction aéronautique et spatiale",    "Autres services de restauration n.c.a.",
    "Travaux d'installation électrique dans tous locaux",    "Gestion d'installations informatiques",    "Transformation et conservation de fruits",
    "Études de marché et sondages",
    "Enseignement de la conduite",
    "Installation d'équipements électriques, de matériels électroniques et optiques ou d'autres matériels",    "Assurance vie",
    "Vente à distance sur catalogue général",
    "Supports juridiques de gestion de patrimoine immobilier",
    "Grands magasins",
    "Entretien et réparation d'autres véhicules automobiles","Autres activités de soutien aux entreprises n.c.a.","Gestion de fonds","Activités des sociétés holding","Activités de sécurité privée","Administration d'immeubles et autres biens immobiliers","Administration d'immeubles et autres biens immobiliers","Agences immobilières","Entretien et réparation de véhicules automobiles légers",'Conseil en relations publiques et communication','Activités des sièges sociaux','Conseil pour les affaires et autres conseils de gestion',"Conseil pour les affaires et autres conseils de gestion","Édition de revues et périodiques",
    "Edition de logiciels applicatifs",
    "Gestion de salles de spectacles",
    "Transports de voyageurs par taxis",
    "Activités des marchands de biens immobiliers",
    "Installation de structures métalliques, chaudronnées et de tuyauterie",
    "Tierce maintenance de systèmes et d’applications informatiques",
    "Location-bail de propriété intellectuelle et de produits similaires, à l'exception des œuvres soumises à copyright",
    "Nettoyage courant des bâtiments",
    "Édition de jeux électroniques",
    "Activités liées aux systèmes de sécurité",
    "Photocopie, préparation de documents et autres activités spécialisées de soutien de bureau",
    "Activités des agences de voyage",
    "Autres activités des services financiers, hors assurance et caisses de retraite, n.c.a.",
    "Construction de maisons individuelles",
    "Métallurgie des autres métaux non ferreux",
    "Activités des agences de placement de main-d'œuvre",
    "Promotion immobilière de bureaux",
    "Coiffure",
    "Préparation de jus de fruits et légumes",
    "Transports fluviaux de fret",
    "Découpage, emboutissage",
    "Construction d'ouvrages maritimes et fluviaux",
    "Entreposage et stockage frigorifique",
    "Charcuterie",
    "Mécanique industrielle",
    "Transports fluviaux de passagers",
    "Activités des agences de travail temporaire",
    "Supports juridiques de gestion de patrimoine mobilier",
    "Débits de boissons",
    "Activité des économistes de la construction",
    "Courtage de valeurs mobilières et de marchandises",
    "Élevage d'autres bovins et de buffles",
    "Construction de bateaux de plaisance",
    "Edition de logiciels outils de développement et de langages",
    "Réparation d'ordinateurs et d'équipements périphériques",
    "Travaux d'étanchéification",
    "Hôtels et hébergement similaire",
    "Activités de conditionnement",
    "Travaux d'installation d'eau et de gaz en tous locaux",
    "Travaux de menuiserie métallique et serrurerie",
    "Promotion immobilière d'autres bâtiments",
    "Traitement et revêtement des métaux",
    "Autre transformation et conservation de légumes",
    "Travaux de maçonnerie générale et gros œuvre de bâtiment",
    "Forages et sondages",
    "Travaux de revêtement des sols et des murs",
    "Restauration de type rapide",
    "Manutention portuaire",
    "Vente à domicile",
    "Transformation et conservation de pommes de terre",
    "Transformation et conservation de poisson, de crustacés et de mollusques",
    "Autres activités de nettoyage des bâtiments et nettoyage industriel",
    "Edition et distribution vidéo",
    "Décolletage",
    "Autre imprimerie (labeur)",
    "Travaux de démolition",
    "Réparation de produits électroniques grand public",
    "Location et location-bail d'autres biens personnels et domestiques",
    "Services des traiteurs",
    "Travaux de couverture par éléments",
    "Travaux de plâtrerie",
    "Construction de voies ferrées de surface et souterraines",
    "Réparation de matériels électroniques et optiques",
    "Projection de films cinématographiques",
    "Agencement de lieux de vente",
    "Pêche en mer",
    "Pâtisserie",
    "Vinification",
    "Taille, façonnage et finissage de pierres",
    "Services d'aménagement paysager",
    "Exploitation de gravières et sablières, extraction d’argiles et de kaolin",
    "Travaux de charpente",
    "Blanchisserie-teinturerie de détail",
    "Activités de soutien aux autres industries extractives",
    "Supérettes",
    "Métallurgie du cuivre",
    "Location et location-bail de machines et équipements pour la construction",
    "Autres activités de nettoyage n.c.a.",
    "Activités spécialisées de design",
    "Réparation d'équipements de communication",
    "Conception d'ensemble et assemblage sur site industriel d'équipements de contrôle des processus industriels",
    "Métallurgie du plomb, du zinc ou de l'étain",
    "Services funéraires",
    "Extraction des minéraux chimiques et d'engrais minéraux",
    "Culture de légumes, de melons, de racines et de tubercules",
    "Fonderie d'acier",
    "Travaux de terrassement courants et travaux préparatoires",
    "Fonderie de fonte",
    "Façonnage et transformation du verre plat",
    "Blanchisserie-teinturerie de gros",
    "Contrôle technique automobile",
    "Travaux de menuiserie bois et PVC",
    "Location et location-bail de matériels de transport aérien",
    "Travaux de montage de structures métalliques",
    "Édition de répertoires et de fichiers d'adresses",
    "Ambulances",
    "Aquaculture en mer",
    "Travaux de peinture et vitrerie",
    "Terrains de camping et parcs pour caravanes ou véhicules de loisirs",
    "Boulangerie et boulangerie-pâtisserie",
    "Centrales d'achat de carburant",
    "Location de vidéocassettes et disques vidéo",
    "Désinfection, désinsectisation, dératisation",
    "Cuisson de produits de boulangerie",
    "Soins de beauté",
    "Activités de soutien à l'extraction d'hydrocarbures",
    "Travaux d'isolation",
    "Activités de radiodiagnostic et de radiothérapie",
    "Autres travaux de finition"]
public_act=[ "Hébergement social pour enfants en difficultés",
    "Accueil de jeunes enfants",
    "Hébergement social pour personnes âgées",'Action sociale sans hébergement n.c.a.',
    "Distribution sociale de revenus",
    "Hébergement médicalisé pour enfants handicapés",
    "Hébergement social pour adultes et familles en difficultés et autre hébergement social",
    "Autre accueil ou accompagnement sans hébergement d’enfants et d’adolescents",
    "Accueil ou accompagnement sans hébergement d’enfants handicapés",
    "Administration publique (tutelle) de la santé, de la formation, de la culture et des services sociaux, autre que sécurité sociale",
    "Accueil ou accompagnement sans hébergement d’adultes handicapés ou de  personnes âgées",
    "Hébergement social pour handicapés mentaux et malades mentaux",
    "Hébergement social pour toxicomanes"]



#en dernier lieu, on classe comme privé ceux dont l'activite n'est pas dans:
not_private_activities=[
    'NA',"Activités des organisations patronales et consulaires","Autres assurances","Autres activités liées au sport","Édition et diffusion de programmes radio","Activités de soutien au spectacle vivant","Location de logements","Édition de chaînes généralistes","Transport ferroviaire interurbain de voyageurs","Enseignement secondaire technique ou professionnel", "Activités de poste dans le cadre d'une obligation de service universel", "Services auxiliaires des transports aériens","Activités générales de sécurité sociale","Action sociale sans hébergement n.c.a.","Administration d'immeubles et autres biens immobiliers","Administration d'immeubles et autres biens immobiliers","Construction d'autres ouvrages de génie civil n.c.a.","Transports routiers réguliers de voyageurs","Autre création artistique","Autres activités informatiques","Enseignement supérieur","Gestion des jardins botaniques et zoologiques et des réserves naturelles","Gestion des sites et monuments historiques et des attractions touristiques similaires","Aide par le travail","Activités de santé humaine non classées ailleurs","Arts du spectacle vivant","Activités des organisations politiques","Fabrication d'autres équipements de transport n.c.a.","Hébergement social pour enfants en difficultés"]


def contient_simpl(chaine, liste_de_chaines):
    #true si un élément de liste_de_chaines est dans chaine (apres simplification)
    for chaine_de_liste in liste_de_chaines:
        if simplifier(chaine_de_liste).lower() in simplifier(chaine).lower():
            return True
    return False


def contient(chaine, liste_de_chaines):
    #true si un élément de liste_de_chaines est dans chaine (apres simplification)
    for chaine_de_liste in liste_de_chaines:
        if (chaine_de_liste).lower() in (chaine).lower():
            return True
    return False


def begin_with(chaine, liste_de_chaines):
    for chaine_de_liste in liste_de_chaines:
        if simplifier(chaine).lower().startswith(simplifier(chaine_de_liste).lower()):
            return True
    return False

matches=set()

def force_classify(to_grade):
    unfounds={}
    global class_gpt_2
    forced={'synd agro':UniqueList(),'privé':UniqueList(),'syndicat':UniqueList(),'public':UniqueList(),'collectivite':UniqueList(),'mutuelle':UniqueList()}
    counter=0
    unmapped_act=set()
    only_entre=set()
    for k in to_grade:
        counter+=1
        print(k)
        dict_k=to_grade[k]
        #on va chercher des infos dans les données pour forcer la classification, on retire les infos "indirectes"
        # try:
        #     del dict_k['activites']['objet']
        # except:
        #     pass
        # try:
        #     del dict_k['firme']['affiliations']
        # except:
        #     pass
        try:
            dict_k['categorie']=dict_k['firme']['categorie']['label']
        except KeyError:
            dict_k['categorie']='NA'
        try:
            code=dict_k['activite_principale']
            lab=nafs[code]
            dict_k['activite_principale']=lab
        except KeyError:
            try:
                dict_k['activite_principale']=dict_k['identite']['lib_activite_principale']
            except KeyError:     
                try:
                    dict_k['activite_principale']=nafs[dict_k['matching_etablissement'][0]['activite_principale']]
                except KeyError:
                    dict_k['activite_principale']='NA'
        try:
            dict_k['lib_forme_juridique']=dict_k['identite']['lib_forme_juridique']
        except KeyError:
            dict_k['lib_forme_juridique']='NA'
        try:
            dict_k['famille']=dict_k['activites']['lib_famille1']
        except KeyError:
            dict_k['famille']='NA'
    
        try:
            dict_k['obj_soc']=dict_k['activites']['lib_objet_social1']
        except KeyError:
            dict_k['obj_soc']='NA'
        try:
            dict_k['est_association']=dict_k['complements']['est_association']
        except KeyError:
            dict_k['est_association']='NA'
        

        if contient_simpl(k+' '+str(dict_k),['SYNDICATS EXPLOITANT AGRI','FRSEA','FNSEA','FDSEA','chambre d agric','chambre agric',"chambre d'agric",'jeunes agr',"Fédération Nationale des Syndicats d'Exploitants Agricoles","Fédération Départementale des Syndicats d'Exploitants Agricoles","Fed nat synd expl","fed dep synd expl",'DEP SYND EXPLOITANT AGRI',"FEDE NAT SYNDIC EXPL AGRICOLE",'syndicat agricole','syndicat des agriculteurs','syndicat agricole','syndicat des exploitants agricoles','syndicat des eleveurs',"CHAMBRE DEP D'AGRI","CHAMBRE DEP D AGRI","CHAMBRE DEPartementale D'AGRIC","CHAMBRE DEPartementale D AGRICULTURE","SYNDIC EXPLOIT AGRI"]):
            print('synd agro',k)
            forced['synd agro'].add(k)
            class_gpt_2[k]={'classes':{"syndicat":50,'privé':50},'explication':'syndicat agricole','manuel':True}
        elif contient_simpl(k+' '+str(dict_k),['mutuelle','mutualiste','mutualité']) or ' mut ' in k.lower() or k.lower().startswith('mut') or k.lower().endswith(' mut') or dict_k['lib_forme_juridique'] in ['Mutuelle','Société d assurance à forme mutuelle']:
            print('mutuelle',k)
            forced['mutuelle'].add(k)
            class_gpt_2[k]={'classes':{"prive":50,"public":50},'explication':'mutuelle','manuel':True}
        elif contient_simpl(k+' '+str(dict_k),['Syndicat mix','synd mix','association syndicale','union syndicale','union de syndicats']):
            print('synd',k)
            forced['syndicat'].add(k)
            class_gpt_2[k]={'classes':{"syndicat":100} ,'manuel':True }
        elif contient_simpl(k,['Syndicat','synd ','syndical']):
            print('synd',k)
            forced['syndicat'].add(k)
            class_gpt_2[k]={'classes':{"syndicat":50,'prive':50} ,'manuel':True }

        elif dict_k['lib_forme_juridique'] in public_forme_jur or dict_k['activite_principale'] in public_act or dict_k['famille'] in public_fam or dict_k['obj_soc'] in public_obj_soc and not 'chasseur' in k.lower():
            print('public',k)
            forced['public'].add(k)
            class_gpt_2[k]={'classes':{"public":100},'manuel':True}
        #ne pas modifier l'ordre des elif
        elif begin_with(k,['Chambre ','SA ','SAS ','CCI']) or contient_simpl(k,['chasseur','ENTREP','holding','gmbh','limited','Societe anonyme','SARL ','Societe a responsabilite limitee',' SAS ','Societe par actions simplifiee','Societe civile','Societe en nom collectif','Societe en commandite','Societe en participation','soc expl',"societe d'exploit",'centrale d achats',"centrale d'achats","edition de revues"]) or contient(k,["S.A.",'S.A.R.L.','S.A.S.','S.A.S.U.','S.C.','S.E.L.A.R.L',' inc.']) or k.endswith(' SA')  or k.endswith(' inc')  or dict_k['categorie'] in ['Société commerciale',
                                                                'Société civile (autre que cabinet d’avocats)',
                                                                'Cabinets d’avocats',
                                                                'Cabinet d’avocats',
                                                                'Avocat indépendant',
                                                                'Cabinet de conseil',
                                                                'Cabinet de conseils',
                                                                'Consultant indépendant',#"Organisation professionnelle",
                                                                "Fédération professionnelle",
                                                                "Travailleur indépendant",
                                                                "Société commerciale et civile (autre que cabinet d’avocats et société de conseil)"] or contient_simpl(dict_k['activite_principale'],['Fabrication','ommerce','roduction']) or dict_k['activite_principale'] not in not_private_activities or dict_k['lib_forme_juridique'] not in not_private_forme_jur or dict_k['famille'] in prive_fam or dict_k['obj_soc'] in prive_obj_soc or dict_k['activite_principale'] in prive_act or dict_k['est_association']=='false':
            
            print('privé',k)
            forced['privé'].add(k)
            class_gpt_2[k]={'classes':{"prive":100},'manuel':True,'explication':'nom ou infos dans fichier auxiliaire'}
        
        else:
            other_names=[dict_k['nom_complet'],dict_k['nom_raison_sociale']] if 'nom_raison_sociale' in dict_k else []
            print('unfound')
            unmapped_act.add(dict_k['activite_principale'])
            unfounds[k]=dict_k
            best_match=find_best_match([k]+other_names,class_gpt_2)
            if best_match['best_score']>85:
                #print('best match',best_match)
                if best_match['best_score']<90:
                #input('ok?')
                    matches.add(str([k]+other_names)+'***'+best_match['best_match']['ressemblance avec ']+' *** '+str(best_match['best_score']))
                class_gpt_2[k]={'classes':class_gpt_2[best_match['best_match']['ressemblance avec ']]['classes'],'explication':'ressemblance avec '+best_match['best_match']['ressemblance avec '],'manuel':True}

    printjs(list(matches))
    input('matches')

    printjs(list(unmapped_act))
    input('?')

    printjs(forced)
    print('forced',sum(len(forced[k]) for k in forced) )
    input('?')
    
    printjs(unfounds)
    print(len(unfounds))
    input('unfounds')

    input('save forced class?')

    with open('openAI/class-gpt_2.json', 'w') as fichier:
        json.dump(class_gpt_2, fichier, indent=4)
        print('data saved')
    return to_grade


to_grade=force_classify(to_grade)

printjs([k for k in class_gpt_2 if 'public' in class_gpt_2[k]['classes'] and class_gpt_2[k]['classes']['public']==100])
input('public100')
printjs([k for k in class_gpt_2 if 'public' in class_gpt_2[k]['classes'] and class_gpt_2[k]['classes']['public']==75])
input('public75')
printjs([k for k in class_gpt_2 if 'public' in class_gpt_2[k]['classes'] and class_gpt_2[k]['classes']['public']==50])
input('public50')

 





def trouver_nombres(donnee):
    # Utilisation d'une expression régulière pour trouver tous les entiers et les floats dans la chaîne
    nombres = re.findall(r'[-+]?\d*\.\d+|\d+', donnee)
    # Convertir les nombres trouvés en entiers ou en floats selon le cas
    nombres = [int(n) if '.' not in n else float(n) for n in nombres]
    return nombres

def random_elements(input_list, n):
    # Return a new list containing n randomly selected elements from the input list
    return random.sample(input_list, min(n, len(input_list)))


def parse_json_str(resp,compare,input_list={}):
    #global unknown_names
    resp=re.sub(r'\n+', '\n', resp)
    result_dict={}
    for s in resp.split('''}'''):#parse gpt result
        print(repr(s),'**')
        if len(clean(s).replace('.',''))<10:
            print('skip short')
            continue
        try:
            nom=str(clean(s.split('{')[-2]))
        except:
            continue
        print('nom',nom)
        if len(nom)<2:
            print(nom)
            print('no name')
        info_match={}
        if compare:
            found=False
            best_match=''
            max_sofar=0
            for orig in input_list:
                orig_nom=orig['name']
                sim_score=compare_struct_names(nettoyer_chaine(orig_nom),nettoyer_chaine(nom))
                if sim_score>max_sofar:
                    max_sofar=sim_score
                    best_match=orig_nom
                    #info_match=orig['firm']
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
        #try:
        lines=s.split('{')[-1].lstrip('\n').split('\n')
        explic=""
        explic_max_score=0
        prive_max_score=0
        prive=0
        syndicat_max_score=0
        syndicat=0
        collectivite_max_score=0
        collectivite=0
        public_max_score=0
        public=0
        for line in lines:
            line=clean(nettoyer_chaine(line))
            print('line**',line)
            explic_score= is_substring_similar('explication',line)
            prive_score= is_substring_similar('prive',line)
            syndicat_score= is_substring_similar('syndicat',line)
            collectivite_score= is_substring_similar('collectivite',line)
            public_score= is_substring_similar('public',line)
            if explic_score>explic_max_score:
                explic=line.replace('explication','').replace('explanation','')
                explic_max_score=explic_score
            if prive_score>prive_max_score:
                nombres=trouver_nombres(line)
                if len(nombres)>1:
                    print(line,'nombres',nombres)
                    nombres=[nombres[0]]
                    continue
                if len(nombres)==1:
                    prive=nombres[0]
                    prive_max_score=prive_score
            if syndicat_score>syndicat_max_score:
                nombres=trouver_nombres(line)
                if len(nombres)>1:
                    print(line,'nombres',nombres)
                    nombres=[nombres[0]]
                    continue
                if len(nombres)==1:
                    syndicat=nombres[0]
                    syndicat_max_score=syndicat_score
            if collectivite_score>collectivite_max_score:
                nombres=trouver_nombres(line)
                if len(nombres)>1:
                    print(line,'nombres',nombres)
                    nombres=[nombres[0]]
                    continue
                if len(nombres)==1:
                    collectivite=nombres[0]
                    collectivite_max_score=collectivite_score
            if public_score>public_max_score:
                nombres=trouver_nombres(line)
                if len(nombres)>1:
                    print(line,'nombres',nombres)
                    nombres=[nombres[0]]
                    continue
                if len(nombres)==1:
                    public=nombres[0]
                    public_max_score=public_score
        seuil=80
        if prive_max_score<seuil:
            prive=0
        if syndicat_max_score<seuil:
            syndicat=0
        if collectivite_max_score<seuil:
            collectivite=0
        if public_max_score<seuil:
            public=0
        print(prive,syndicat,collectivite,public)
        total=prive+syndicat+collectivite+public
        if total==100:
            classes={"prive":prive,"syndicat":syndicat,"collectivite":collectivite,"public":public}  
        else:
            continue       


        #     print(classe_line,'*-*')
        #     #score=clean(split_dot(lines[1])[1].replace('.','').replace('"','').replace("'",""))
        #     classes=[]
        #     for x in ["prive","syndicat","inconnu","collectivite","public"]:
        #         res=is_substring_similar(x,classe_line)
        #         print(res)
        #         classes+=[x] if res>70 else []
        #     if len(classes)==0 or len(classes)>2:
        #         print(classes)
        #         print('skip pb parse classes')
        #         continue
        # except:
        #     print('skip parse pb***')
        #     continue
        parse_s={nom:{"explication":explic,'classes':classes,'info':info_match}}
        result_dict.update(parse_s)
        #print('result so far',result_dict)
        printjs(parse_s)
        print('parsed')
    return result_dict

#def parse_json_str(resp):
    # result_dict={}

    # for s in resp.split('''}'''):#parse gpt result
    #     print(s,'**')
    #     if len(clean(s).replace('.',''))<10:
    #         print('skip short')
    #         continue
    #     mots = ["explication", "score", "confiance"]
    #     index = 0
    #     for mot in mots:
    #         index = s.find(mot, index)
    #         if index == -1:
    #             print(s)
    #             input('skip?')
    #             continue
    #         index += len(mot)
    #     nom=clean(s.split('explication')[0])
    #     rest=s.split('explication')[1]
    #     #print('rest',rest)
    #     confiance=int(clean(rest.split('confiance')[1].replace(',','')))
    #     rest2=rest.split('confiance')[0]
    #     score=int(clean(rest2.split('score')[1].replace(',','')))
    #     explic=clean(rest2.split('score')[0])
    #     result_dict.update({nom:{"score":score,"explication":explic,'confiance':confiance}})
    # return result_dict







printjs(to_grade)
print('to grade',len(to_grade))


# def numerize(classes):
#     if isinstance(classes, dict):
#         return classes
#     new_classes={'collectivite':0,'public':0,'prive':0,'syndicat':0}
#     for k in [n for n in ['collectivite','public','prive','syndicat'] if n in classes]:
#         try:
#             x=int(classes[k])
#         except:#si pas de valeur
#             new_classes[k]=int(100/len(classes))
#         if len(classes)==3 and sum(new_classes.values())==99:
#             new_classes[k]=34
#     if sum(new_classes.values())!=100:
#         print(classes)
#         print('pb',new_classes)
#         input('?')
#     return new_classes



from openai import OpenAI
# #pour récup de l'info:
# with open('firms_to_grade.json','r') as f:
#     firms_to_grade=json.load(f)


# unknown_class={}
# for k in class_gpt:
#     if 'inconnu' in class_gpt[k]['classes'] or len(class_gpt[k]['classes'])==0:
#         info={}
#         try:
#             info.update(assos_to_grade[k])
#         except:
#             pass
#         try:
#             info.update(firms_to_grade[k])
#         except:
#             pass
#         unknown_class.update({k:class_gpt[k],'info':info})

# printjs(unknown_class)




# to_grade=unknown_class

def get_random_entries(my_dict, num_entries):
    keys = list(my_dict.keys())
    random_entries = random.sample(keys, min(num_entries, len(keys)))
    return {key: my_dict[key] for key in random_entries}

to_grade=...
input('objects')

client = OpenAI()
parsed_lengths=[]
def grade(limit):
    global class_gpt_2
    global parsed_lengths
    global to_grade
    global to_grade_now
    total_ratio=0
    for iter_number in range(1,limit):

        with open('openAI/class-gpt_2.json', 'r') as fichier:#maj progressivement, resultats gpt
            class_gpt_2 = json.load(fichier)

        to_grade_now=[]
        for key in to_grade:
            if key not in class_gpt_2:# or 'inconnu' in class_gpt[key]['classes'] or len(class_gpt[key]['classes'])==0:
            #     corrected_firm=to_grade[key]
            #     # try:
            #     #     del corrected_firm['classes']
            #     #     del corrected_firm['explication']
            #     # except KeyError:
            #     #     pass
            #     if 'objet' in corrected_firm:
            #         corrected_firm['objet']=corrected_firm['objet'][0:300]
            #     if 'categorie' in corrected_firm and corrected_firm['categorie']=='Association':
            #         del corrected_firm['categorie']
            #     try:
            #         del corrected_firm['intéressé par']
            #     except:
            #         pass
                to_grade_now+=[{'name':key}]#,'firm':corrected_firm}]

        print('remaining',len(to_grade_now))
        x=1/len(to_grade_now)
        max_query=15

        to_grade_now= random_elements(to_grade_now, max_query)

        if len(to_grade_now)==0:
            print('done')
            break


        system_str='''Je vais te donner une liste de '''+str(max_query)+''' entités, avec parfois un objet, qui peuvent être des entreprises ou des associations, que je souhaite classer parmi quatre catégories:  "privé", "syndicat", "collectivité", ou "public".
Je veux en sortie une variable json parfaitement valide, avec un champ "explication" qui justifie le choix, puis un pourcentage de confiance entre 0 et 100 d'appartenir à chaque catégorie, inutile de mettre les classes avec 0%.
#####
Il faut absolument '''+str(max_query)+''' sorties.
####
Une entité doit être classé dans "privé" si l'entité est une entreprise ou si le but poursuivi par l'entité et ses membres est commercial, ou est l'enrichissement de ses membres, de ses clients ou de ses actionnaires. Il peut s'agir d'une entreprise commerciale, d'une association ou une fédération d'entreprises, d'un cabinet d'avocats, d'architectes ou de consultants, ou d'un auto-entrepreneur.

Une entité doit être classée "syndicat" si elle représente explicitement les interêts d'une catégorie d'employés,  comme des ouvriers agricoles, des médecins, ou des travailleurs d'un secteur particulier, mais pas les patrons ou les entreprises elle-même, uniquement les employés. Mettre "privé" en cas de doute.

Une entité doit être classée "collectivité" si c'est une commune, une région, un département, une agglomération, une collectivité, ou une autre entité administrative française.

Une entité doit être classée dans "public" si elle a une action sans portée commerciale, qui vise à aider les citoyens français, l'environnement, l'interêt général ou l'interêt public.
###
Voilà des exemples de sorties.
####
    "FRANCE SUPPLY CHAIN BY ASLOG (ASSOCIATION FRANCAISE DE LA SUPPLY CHAIN)": {
        "explication": "resemble à une association d'entreprises privées",
        "classes": {
            "prive": 100
        }
    ##
     "RESEAU 3S QE": {
        "explication": "organisme de formation, généralement privé",
        "classes": {
            "prive": 80,
            "public": 20
        }
    ##
    "ASSOCIATION NAT SOCIETES PAR ACTIONS": {
        "explication": "association qui etudie et defend les interets des societes par actions",
         "privé": 100
    }
    ##
    "ASSOCIATION DES ACTIONNAIRES SALARIES ET ANCIENS SALARIES DU GROUPE SAINT-GOBAIN, CLUB DES SAINT-GOBAIN": {
        "explication": "défend l'interêt d'actionnaires particuliers",
         "privé": 100
    }
    ##
    "EUROSTAR INTERNATIONAL": {
        "explication": "entreprise privée",
          "privé": 100
    ##
    "ASSOCIATION POLE MONDIAL DE COMPETITIVITE EAU": {
        "explication": "association qui vise a renforcer le potentiel regional dans le secteur de leau avec une visee sur l'emploi, et un bénéfice pour les PME/PMI",
        "public": 70,
        "privé": 30
    }
    ##
    "ASSOCIATION DES ETUDIANTS EN PHARMACIE DE POITIERS": {
        "explication": "participer aux actions de sante publique, dans une logique de corporatisme",
        "public": 50,
        "syndicat": 50
    }
    ##
    "UNION SOCIALE POUR L'HABITAT CENTRE": {
        "explication": "organisme du secteur hlm dinteret public, union peut signifier syndicat",
        "classes": {
            "syndicat": 30,
            "public": 70
        }
    ##
    "FORMEXPERT": {
        "explication": "objetinformations sur offre formation dispositifs aides publiques, il n'est pas clair si l'organisme tire une rénumération de ses services",
        "public": 70,
        "privé": 30
    }
##
"COMMUNE DE MONTVALEZAN":
 {
  "explication" : "Commune",
    "collectivité": 100
}
##
    "CONFEDERATION DES PETITES ET MOYENNES ENTREPRISES GRAND EST": {
        "explication": "défend l'interêt d'entreprises privées",
     "privé": 100
    }
##
     "ASSOCIATION REUNIONNAISE INTERPROFESSIONNELLE DE LA PECHE ET DE L'AQUACULTURE": {
        "explication": " association interprofessionnelle",
        "classes": {
            "prive": 50,
            "syndicat": 50
        }
##
    "OFFICE PUBLIC DE L HABITAT DE ROUEN": {
        "explication": "Office public",
        "public": 100
    }
##
  "ASSOCIATION FRANCAISE POUR L'HYDROGENE ET LES PILES A COMBUSTIBLE": {
        "explication": "Semble prmouvoir le filiere industrielle des piles a combustible",
        "classes": {
            "prive": 100
        }
'''

        msgs_gpt=[{
         "role": "system",
         "content": system_str
        }]
        for item in to_grade_now:
            msgs_gpt+=[{
             "role": "user",
             "content": item['name']#+" : "+str(item['firm'])
            }]
        

        printjs(msgs_gpt)
        print('ask gpt...')
        input('go?')

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

        with open("openAI/backup-raw-gpt-res.txt", "w+") as file:
            file.write(str(resp)+'''

            #####

            initial msg:
            '''+str(to_grade_now))#backup reponse

        parsed_res=parse_json_str(resp,True,to_grade_now)
        printjs(parsed_res)

        lpars=len(parsed_res)
        lgrad=len(to_grade_now)
        ratio=len(parsed_res)/len(to_grade_now)
        total_ratio+=ratio
        avg=total_ratio/iter_number

        print('parsed',lpars,'to grade',lgrad,'ratio',ratio,'avg ratio',str(avg))
        parsed_lengths+=[lpars]
        print(parsed_lengths)
        if lpars<10:
            print('wait 5 min')
            time.sleep(10)
            print("5 minutes have passed!")
            prev_to_grade=to_grade_now
        elif  avg<.4:
            input('warning, continue?')

        class_gpt.update(parsed_res)
        with open('openAI/class-gpt.json', 'w') as fichier:
            json.dump(class_gpt, fichier, indent=4)
            print('data saved')



        #print('unknown *******'+str(unknown_names))
#LOOP ENDS

grade(100)


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



examples='''    "FRANCE SUPPLY CHAIN BY ASLOG (ASSOCIATION FRANCAISE DE LA SUPPLY CHAIN)": {
        "explication": "resemble à une association d'entreprises privées",
        "classes": {
            "prive": 100
        }
    ##
    "TRANSNUMERIC": {
        "explication": " association qui oeuvre pour linclusion numerique et sociale activite non commerciale",
        "public": 100
    }
    ##
     "RESEAU 3S QE": {
        "explication": " organisme de formation, généralement privé",
        "classes": {
            "prive": 80,
            "public": 20
        }
    ##
    "ASSOCIATION NAT SOCIETES PAR ACTIONS": {
        "explication": "association qui etudie et defend les interets des societes par actions",
         "privé": 100
    }
    ##
    "ASSOCIATION DES ACTIONNAIRES SALARIES ET ANCIENS SALARIES DU GROUPE SAINT-GOBAIN, CLUB DES SAINT-GOBAIN": {
        "explication": "défend l'interêt d'actionnaires particuliers",
         "privé": 100
    }
    ##
    "EUROSTAR INTERNATIONAL": {
        "explication": "entreprise privée",
          "privé": 100
    ##
    "ASSOCIATION POLE MONDIAL DE COMPETITIVITE EAU": {
        "explication": "association qui vise a renforcer le potentiel regional dans le secteur de leau avec une visee sur l'emploi, et un bénéfice pour les PME/PMI",
        "public": 70,
        "privé": 30
    }
    ##
    "CHAMBRE DES METIERS ET DE L'ARTISANAT DE L'AUDE": {
        "explication": "organisme consulaire representant les artisans et entreprises artisanales syndicat professionnel",
        "classes": {
            "prive": 50,
            "syndicat": 50
        }
    ##
    "ASSOCIATION DES ETUDIANTS EN PHARMACIE DE POITIERS": {
        "explication": "participer aux actions de sante publique, dans une logique de corporatisme",
        "public": 50,
        "syndicat": 50
    }
    ##
     "FNSEA 03": {
        "explication": "organisation patronale qui défend les intérêts des agriculteurs et des entreprises agricoles",
        "syndicat": 50,
        "privé": 50
    }
    ##
    "UNION SOCIALE POUR L'HABITAT CENTRE": {
        "explication": "organisme du secteur hlm dinteret public, union peut signifier syndicat",
        "classes": {
            "syndicat": 30,
            "public": 70
        }
    ##  "CAISSE MUT PREV PERS COL TER HTE SAVOIE": {
        "explication": "une mutuelle dépend l'interêt de ses membres mais sans but lucratif",
        "classes": {
            "prive": 70,
            "public":30
        }
    ##
    "FORMEXPERT": {
        "explication": "objetinformations sur offre formation dispositifs aides publiques, il n'est pas clair si l'organisme tire une rénumération de ses services",
        "public": 70,
        "privé": 30
    }
##
"COMMUNE DE MONTVALEZAN":
 {
  "explication" : "Commune",
    "collectivité": 100
}
##
    "CONFEDERATION DES PETITES ET MOYENNES ENTREPRISES GRAND EST": {
        "explication": "défend l'interêt d'entreprises privées",
     "privé": 100
    }
##
     "ASSOCIATION REUNIONNAISE INTERPROFESSIONNELLE DE LA PECHE ET DE L'AQUACULTURE": {
        "explication": " association interprofessionnelle",
        "classes": {
            "prive": 50,
            "syndicat": 50
        }
##
    "OFFICE PUBLIC DE L HABITAT DE ROUEN": {
        "explication": "Office public",
        "public": 100
    }
##
  "DA VOLTERRA": {
        "explication": "La recherche-développement est une activité industrielle à finalité privée",
         "privé": 100
    }'''