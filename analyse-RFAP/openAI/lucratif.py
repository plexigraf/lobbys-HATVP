from openai import OpenAI
client = OpenAI()

#voir history playground

response = client.chat.completions.create(
  model="gpt-4-turbo-preview",
  messages=[
    {
      "role": "system",
      "content": "Je vais te donner des éléments concernant des actions d'influence, ou de lobbying, menées par des firmes qui représentent les intêrets d'entreprises et d'association auprès d'hommes politiques, d'élus et de membres de  cabinet. \n\nPour chaque action, je vais te donner l'intitulé de l'action, le nom de la firme qui l'exerce, son type, et éventuellement les tiers concernés, le type de ces tiers, et éventuellement l'objet de ces tiers, sous forme de données structurées.  Si le tiers n'est pas indiqué, l'action est mené pour le compte de la firme.\n\nJe veux un fichier json qui donne pour chaque action un nombre entre 1 et 10 qui estime à quel point le but de cette action est  lucratif ou non. Un score de 1 signifie une action à but non lucratif, qui vise à aider les citoyens, l'environnement, ou l'interêt public, et un score de 10 signifie uniquement les interêts d'entreprise privées. \n\nPour cela, il faut principalement se baser sur l'intitulé de l'action et une estimation de si les tiers concernés sont des acteurs privés ou associatifs, et dans le cas d'associations si elle et ses membres poursuivent des intêret privés. Pour une association agissant pour son propre compte, il faut estimer si cette association regroupe des intêrets privés ou pas.\n\nJe ne veux pasque tu répètes l'intitulé de l'action ou le nom de la firme, juste le score pour chaque action, et une explication en une petite phrase incluse dans le json."
    },
    {
      "role": "user",
      "content": "[\n\n{\"firme\":cabinet d'avocats, \n\"nom\":\"Boury tallon et associés\",\n\"action\":\"Assurer la sauvegarde et la pérennité de l’activité économique de l’entreprise Saint-Mamet, ainsi que de la filière économique qui en dépend (coopérative, arboriculteurs, ...)\",\n\"tiers\":{ \"type\":\"entreprise\",\n\"nom\":\"Saint-Mamet\"},\n\n{\"firme\":\"association\",\n\"nom\":\"FEDERATION EUROPEENNE POUR TRANSPORT ET L ENVIRONNEMENT\",\n\"action\":  \"Contribuer aux réféxions sur les leviers de décarbonation du secteur maritime\"},\n\n{\"firme\":\"cabinet de conseil\",\n\"nom\": \"comfluence\",\n \"action\": \"Favoriser le passage d'examens de certification à distance et Développer l’accès des personnes en insertion à une formation proposée au format « téléprésentiel »\"}\n\n]\n"
    }
  ],
  temperature=0,
  max_tokens=469,
  top_p=1,
  frequency_penalty=1.65,
  presence_penalty=1.4
)
