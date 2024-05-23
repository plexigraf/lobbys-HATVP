# Résultats

Chaque dossier contient les résultats avec un certain type de paramètres, indiqués en suffixe du nom de dossier / fichier. 
 - "out=True" signifie que les valeurs aberrantes ont été corrigés, "out=False" signifie qu'elles ne l'ont pas été.
 - "agressive" signifie que des seuils plus restrictifs ont été appliqués pour détecter les valeurs aberrantes, et que donc plus de valeurs ont été corrigées.
 - "sqrt" ou "ln", transformation corrective du budget d'un exercice avant de tester si outlier
 - lobbyist=0 est le coût annuel d'un lobbyiste pris en compte pour estimer les ressources dépensées.
 - "acts=formula" signifie que la formule a été prise en compte pour le calcul des ressources d'une action, "acts=uni" signifie que toutes les actions ont la même ressource, "acts=by-ex" signifie que chaque action a le même poids au sein d'un exercice.
 -  "2017-2022" période prise en compte

Voir le préambule du script 'lobbys-rfap.py' pour plus de descriptions des différents paramètres.

Le fichier RESULTS_[suffix]contient les résultats numériques, sous forme d'un fichier JSON. Les autres fichiers sont des graphiques pour visualiser certains résultats. 
