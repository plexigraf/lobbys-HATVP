import json

def printjs(s):
 print(json.dumps(s, indent=4,   ensure_ascii=False))

# #open opendata_matched, opendata, missing_matched, unknown_matched,all_matched
# with open('openAI/all-matched.json','r') as f:
#     matched=json.load(f)['matched']
# with open('openAI/unknowns-matched.json','r') as f:
#     matched.update(json.load(f)['matched'])
# with open('missing_matched.json','r') as f:
#     matched.update(json.load(f)['matched'])
# with open('agora_repertoire_opendata-matched.json','r') as f:
#     matched.update(json.load(f)['matched'])
# with open('opendata-matched.json','r') as f:
#     matched.update(json.load(f))


# with open('firms_suppl_info.json','w') as f:
#     json.dump(matched, f, indent = 4, separators = (',', ':'))#, sort_keys=True)



with open('nafs.json','r') as f:
    nafs_raw=json.load(f)

nafs={}
for code in nafs_raw:
    nafs[code['id']]=code['label']



class UniqueList(list):
    def add(self, item):
        if len(self) < 3 and item not in self:
            self.append(item)


# with open('agora_repertoire_opendata.json','r') as f:
#     opendata=json.load(f)['publications']

#on fait deux listes avec tous les matched
#une liste d'asso avec objets qui peuvent être tout

# with open('openAI/assos_to_grade.json','r') as f:
#     assos_to_grade=json.load(f)
# with open('openAI/firms_to_grade.json','r') as f:
#     firms_to_grade=json.load(f)


with open('firms_suppl_info.json','r') as f:
    matched=json.load(f)
#une liste de pure entreprises, qui pourront que être syndicat ou entreprise à la fin

# c=0
# d=0
# for key in matched['matched']:
#     if key in matched:
#         printjs(matched[key])
#         printjs(matched['matched'][key])
#         d+=1
#         matched[key].update(matched['matched'][key])
#     else:
#         c+=1
#         matched[key]=matched['matched'][key]
# input(c)
# input(d)
# del matched['matched']
# del matched['unknowns']
# with open('firms_suppl_info.json','w') as f:
#     json.dump(matched, f, indent = 4, separators = (',', ':'))#, sort_keys=True)

# exit()


activ_princ_s={}
obj_soc_s={}
fam_s={}
form_jur_s={}
act_code_s={}
counter=0

primary_fields=set()

info_found=set()
for key  in matched:
    for k in matched[key]:
        primary_fields.add(k)
    orga=matched[key]
    counter=counter+1
    print(key)
    act=""
    key=key.split('-HATVP')[0].split('-SIREN')[0].split('-RNA')[0]
    #print(counter,'/',len(matched))
    #print('***',orga)
    info={}
    asso=False
    try:
        info['objet']=orga['activites']['objet']
        asso=True
    except KeyError:
        try:
            if orga['activites']['lib_activite_principale'] != 'Autres organisations fonctionnant par adhésion volontaire':
                info_found.add(key)
                act=orga['activites']['lib_activite_principale']
                info['secteur']=act
                if act in activ_princ_s:
                    activ_princ_s[act]+=[key]
                else:
                    activ_princ_s[act]=[key]
        except KeyError:
            pass

    try:
        soc=orga['activites']['lib_objet_social1']
        info['objet social']=soc
        asso=True
        if soc in obj_soc_s:
            obj_soc_s[soc]+=[key]
        else:
            obj_soc_s[soc]=[key]
    except  KeyError:
        pass


    try:
        fam=orga['activites']['lib_famille1']
        info['famille']=fam
        asso=True
        if fam in fam_s:
            fam_s[fam]+=[key]
        else:
            fam_s[fam]=[key]
    except  KeyError:
        pass

    try:
        code=orga['activite_principale']
        info['code activite principale']=code
        lab=nafs[code]
        if lab=='Autres organisations fonctionnant par adhésion volontaire':
            print(nafs['kllkkkljkjllk'])#to exit the try
        if 'activite' in info:
            if info['secteur']!=lab:
                info['autre activité']=lab
        else:
            info['secteur']=lab
        if lab in act_code_s:
            act_code_s[lab]+=[key]
        else:
            act_code_s[lab]=[key]
    except KeyError:
        pass


    try:
        jur=orga['identite']['lib_forme_juridique']
        if  jur != "Association déclarée" and act!="Activités des organisations patronales et consulaires":
            if jur in form_jur_s:
                form_jur_s[jur]+=[key]
            else:
                form_jur_s[jur]=[key]
            info['forme juridique']=jur
            info_found.add(key)
        else:
            asso=True
    except KeyError:
        pass


    if 'activites' in orga and 'id_rna' in orga['activites']:
        asso=True

    print(info)
    # if asso:
    #     if key in assos_to_grade:
    #         assos_to_grade[key].update(info)
    #     else:
    #         assos_to_grade[key]=info
    #     print('asso')
    # else:
    #     if key in firms_to_grade:
    #         firms_to_grade[key].update(info)
    #     else:
    #         firms_to_grade[key]=info

print(primary_fields)
print('primary fields')

printjs(activ_princ_s)
print(len(activ_princ_s))
input('***activties')

printjs(obj_soc_s)
print(len(obj_soc_s))
printjs(list(obj_soc_s.keys()))
input('***objet social')

printjs(fam_s)
print(len(fam_s))
printjs(list(fam_s.keys()))
input('***famille')

printjs(form_jur_s)
print(len(form_jur_s))
input('***forme jur')

act_code_s={k:v for k,v in act_code_s.items() if k not in activ_princ_s}
printjs(act_code_s)
print(len(act_code_s))

printjs([a for a in list(act_code_s.keys()) if 'Fabrication' not in a and 'ommerce' not in a and 'roduction' not in a])
input('***act code')

exit()

#on fait aussi une liste de tous ceux qui restent avec open_data
tiers_to_grade={}


def best_nom(firme):
    try:
        return firme['nomUsageHatvp']
    except KeyError:
        try:
            return firme['nomUsage']
        except KeyError:
            return firme['denomination']

liste_firmes_to_grade=[
"Association",
"Syndicat",
"Chambre consulaire",
"Organisation syndicale et professionnelle",
"Autres organisations",
"Fondation",
"Autre organisation",
"Etablissement public exerçant une activité industrielle et commerciale",
"Groupe de réflexion (think tank)",
"Établissement public exerçant une activité industrielle et commerciale",
"Organisme de recherche ou de réflexion",
"Autres organisations non gouvernementales",
"Coopérative agricole"
]



for firme in opendata:
    nom=best_nom(firme)
    print(nom,'***')
    #if nom not in assos_to_grade and nom not in firms_to_grade:
    lab=firme['categorieOrganisation']['label']
    if lab in liste_firmes_to_grade:
        print(lab)
        temp_firme={'categorie':lab}
        affils=[f['denomination'] for f in firme['affiliations']]
        if len(affils)>0:
            temp_firme['affiliations']=affils
    else:
        try:
            del assos_to_grade[nom]
        except KeyError:
            try:
                del firms_to_grade[nom]
            except KeyError:
                pass
        continue
    try:
        assos_to_grade[nom].update(temp_firme)
        print('asso')
    except KeyError:
        try:
            print('firm')
            firms_to_grade[nom].update(temp_firme)
        except KeyError:
            print('tiers')
            tiers_to_grade[nom]=temp_firme
    for ex in firme['exercices']:
        ex=ex['publicationCourante']
        possible_names=[firme[key] for key in ['denomination','nomUsage','nomUsageHatvp','sigleHatvp'] if key in firme]

        if 'activites' in ex:
            for act in ex['activites']:
                objet=act['publicationCourante']['objet']
                for a in act['publicationCourante']["actionsRepresentationInteret"]:
                    for t in a['tiers']:
                        if t=='UNION NAT CENTRES COMMUNAUX ACTION SOCIA':
                            input('here')
                        print('tiers',t)
                        if 'en propre' in t or t in possible_names:
                            t=nom

                            found=False
                            for n in possible_names:
                                if n  in firms_to_grade or n in assos_to_grade:
                                    print('found')
                                    found=True
                            if not found:
                                input('?')
                            
                        # try:
                        #     assos_to_grade[t]['intéressé par'].add(objet)
                        # except KeyError:
                        #     try:
                        #         assos_to_grade[t]['intéressé par']=UniqueList([objet])
                        #     except KeyError:
                        #         try:
                        #             firms_to_grade[t]['intéressé par'].add(objet)
                        #         except KeyError:
                        #             try:
                        #                 firms_to_grade[t]['intéressé par']=UniqueList([objet])
                        #             except KeyError:
                        #                 try:
                        #                     tiers_to_grade[t]["intéressé par"].add(objet)
                        #                 except KeyError:
                        #                     tiers_to_grade[t]={"intéressé par":UniqueList([objet])}

printjs(assos_to_grade)

exit()

with open('assos_to_grade.json','w') as f:
    json.dump(assos_to_grade, f, indent = 4, separators = (',', ':'))#, sort_keys=True)
    f.truncate()

firms_to_grade={**firms_to_grade,**tiers_to_grade}

input(len(firms_to_grade))

printjs(firms_to_grade)
with open('firms_to_grade.json','w') as f:
    json.dump(firms_to_grade, f, indent = 4, separators = (',', ':'))#, sort_keys=True)
    f.truncate()




#ouvrir classif_gpt.json
