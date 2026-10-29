---
title: PickMyChamp
emoji: 🎮
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
---

# PickMyChamp

Do you ever dodge queue or pick Vayne mid because because you don't know who else to play? PickMyChamp is a solution to all your problems: a utility to generate the best choice of champion in a game of League of Legends (LoL).

## Assistant CLI (new)

The original scraper and script remain in `python/` for reference. The new
`main.py` CLI uses Riot's official API for account lookup, recent match history,
and champion mastery. It does not depend on OP.GG or LoLCounter.

Requirements: Python 3.10+ and a Riot API key for personal account statistics. Create a key at
[developer.riotgames.com](https://developer.riotgames.com/) and set it in the
`RIOT_API_KEY` environment variable; do not put the key in source code or commit
it. For example, in PowerShell:

```powershell
$env:RIOT_API_KEY = "your-key"
python main.py
```

This opens the local visual interface in your browser. The app binds only to
`127.0.0.1`; keep its terminal open while using it and press Ctrl+C to stop.
The enemy champion is selected from a dropdown populated with the current
English champion names from Riot Data Dragon; changing the selection refreshes
the result. Matchup picks, win rates, and sample sizes are read from U.GG's
public counter page for that champion. Rune, item, and summoner-spell names
use English. The app/profile works without a Riot API key; the key is only
needed for personal Riot match-history features in the CLI.

The web draft assistant also includes a Draft-to-Playbook beta. Enter revealed
champions by role for both teams to get a cautious, rules-based team briefing.
Its curated strategy profiles are limited, so the briefing shows its evidence
and coverage and may report that no reliable pattern is available. It is not a
win-rate prediction or a substitute for matchup statistics.
Generated drafts can be shared as links. The link encodes only the selected
champions, player role, and patch in the URL fragment; it does not save a draft
on the server or include the local profile or Riot ID.

The original commands remain available, for example
`python main.py history --count 50` or `python main.py counter --enemy Vayne
--role adc`. `python main.py demo` shows synthetic examples that are not real
player or matchup data.

`setup` stores the Riot ID, region, roles, mastered champions, and play-style
preferences in `~/.pickmychamp/config.json`. Riot ID is entered interactively
and is not embedded in the program; the initial region prompt defaults to
`euw`. Draft/history need an API key and network access. The API key is not
stored in the profile.

`history` and `draft` accept `--count` from 1 to 100 (20 by default). Draft can
filter matches with `--queue ranked`, `--queue flex`, or `--queue normal`;
without it, all returned queues are combined. If `--role` is omitted, the
configured primary role is used.
Role-specific personal records are shown alongside each suggestion. The
profile score is a heuristic combining a smoothed personal win rate (65%),
KDA (15%), Riot mastery or a declared mastery preference (10%), and recent
role-specific experience (10%). The displayed confidence index is also a
heuristic based on sample size, not a probability.
The opponent argument is context only: Riot's official API does not provide
current-patch lane matchup win rates, team-synergy rankings, recommended runes,
skill orders, or optimal builds. Those claims are therefore not fabricated;
recommendations may be fewer than three if the player has insufficient
role-specific data and has not configured enough mastered champions. Match
statistics are not filtered to the current patch. Even with `--count 100`,
this is still a recent-history sample, not the player's lifetime record.

`counter` and the visual draft view both query U.GG's public champion counter
pages. The app requests the selected lane, uses the page's default World
Emerald+ view, win-rate sample, and patch, and caches recently viewed
champion/lane combinations in memory. Changing either the enemy champion or
the role refreshes the recommendations. The source HTML is bounded to 500 KB
per request. U.GG pages can change, so failed parsing/network access produces
an explicit error. The stats describe the source's population, not your
personal performance; if U.GG returns a different lane than requested, the
app warns that the picks may not fit your lane.

Rune, spell, skill-order, and item build recommendations are not available
from the matchup counter table for most champions. The app links to each
recommended champion's English U.GG build page instead of inventing those
details. The existing hand-authored detailed matchup guide supplements the
small set of recommendations covered by the local guide; other champions use
the linked English build page and clearly report the missing details.

`build` requires the League client to be open and a live match to be running.
It reads the authenticated local League Client API and Live Client Data
interface on loopback. `LEAGUE_CLIENT_LOCKFILE` can point to the client's
`lockfile` if it is installed outside the standard Windows paths. Client data
is a snapshot and can be unavailable during loading or outside a match. The
command reports only facts exposed by the client; it currently does not make
future item recommendations because the official APIs do not provide
item-performance evidence for the current matchup.

Riot API access is rate-limited and may not expose all historical data. Recent
match statistics are not lifetime/global statistics. OP.GG is not scraped, and
public profile availability is not assumed.

Run the local tests with:

```powershell
python -m unittest discover -s tests
```

### Public deployment 100% gratuit avec Hugging Face Spaces

Le projet est prêt pour un **Docker Space** Hugging Face. Le plan gratuit
convient à une démo publique et ne nécessite ni carte bancaire ni serveur
payant. Le Space peut s'endormir après une période d'inactivité : le premier
chargement suivant peut donc être plus lent.

1. Crée un dépôt GitHub vide nommé `PickMyChamp` dans le compte
   `zakarialakhsim2`, puis pousse le projet.
2. Sur [Hugging Face](https://huggingface.co/), crée un Space public avec
   `SDK: Docker`.
3. Dans **Files**, importe le contenu du dépôt, ou connecte le dépôt GitHub
   via l'intégration disponible dans ton compte.
4. Le `Dockerfile` expose le port `7860`; le Space démarre automatiquement
   `python main.py app`.
5. Attends la construction de l'image puis ouvre l'URL publique du Space.

Cette version publique utilise les données de champions Data Dragon et les
pages publiques U.GG. Les fonctions personnelles Riot (`setup`, `history` et
`draft`) nécessitent une clé `RIOT_API_KEY`; ne l'ajoute jamais au dépôt.
Pour une clé dans un Space, utilise un **Secret** Hugging Face plutôt qu'une
variable publique. La persistance du profil local n'est pas garantie sur le
stockage éphémère gratuit.

#### Limites et coûts

- Hugging Face Spaces gratuit : ressources partagées et mise en veille
  possible; ce n'est pas un SLA de production.
- Le plan reste à 0 € tant que tu n'ajoutes pas de matériel ou de service
  payant.
- Riot API et U.GG peuvent appliquer leurs propres limites et modifier leurs
  pages; l'application affiche explicitement les erreurs réseau.

### Déploiement dynamique gratuit avec Vercel

Le dépôt contient `api/index.py` et `vercel.json` pour Vercel Hobby. Dans
Vercel, importe le dépôt GitHub `zakarialakhsim2/PickMyChamp`, garde la branche
`master`, puis lance le déploiement sans ajouter de carte. Vercel exécute les
routes Python comme des fonctions serverless et sert l'interface web depuis
`web/`. Sur le déploiement web, le profil est conservé dans le stockage local du
navigateur, car le système de fichiers des fonctions serverless n'est pas
persistent. En local, `python main.py setup` continue d'utiliser
`~/.pickmychamp/config.json`. Les données U.GG et Data Dragon restent
récupérées à la demande.

### Publicité

L'interface contient un emplacement AdSense discret au-dessus du pied de page.
L'identifiant éditeur AdSense est configuré dans `web/index.html` avec
`ca-pub-6962406875891285`. La diffusion effective reste soumise à
l'approbation du site par Google. Ajouter une politique de confidentialité et
le consentement cookies requis avant la diffusion d'annonces personnalisées.
Vérifier également les conditions commerciales de l'hébergeur avant d'activer
la monétisation.
La liste des alternatives envisagées est conservée dans
[`docs/advertising-options.md`](docs/advertising-options.md).

### Future in-game AI companion

La vision d'une interface compagnon en jeu, avec recommandations de build
contextuelles et LLM optionnel, est documentée dans
[`docs/in-game-ai-companion.md`](docs/in-game-ai-companion.md). Cette
fonctionnalité n'est pas implémentée actuellement ; les règles Riot, la
confidentialité et les limites contre l'automatisation devront être vérifiées
avant tout développement.

![Project Sample](images/SampleOutput.png)

## Legacy prototype

The original single-script prototype is still in `python/`, but its scraping
sources and page assumptions may no longer work. Use the `main.py` assistant
above for current development.

## How does it work?

The following describes the retired scraper prototype in `python/`, not the
current `main.py` assistant. Its OP.GG/LoLCounter scraping and regression model
are kept for historical reference only.

This project can be broken down into 3 components:
   1. Collecting and manipulating user input
      - To keep things simple, I only ask for a summoner username and opponent the user is facing, in order to develop a profile of the user and their possible picks for the game.
      - Although we request information from the user at various points, we have to actually interpret it to come to a conclusion. I have basic information about the user, but **how do I actually _transcribe_ it?**
      	- Throughout the whole runtime of the application, I only webscrape two distinct sources:
       	    1. LoL database for user statistics: [op.gg](http://na.op.gg)
	        2. Portal of good/bad picks for any and every champion that exists in LoL: [lolcounter](https://www.lolcounter.com)
	  
       ```python 
       def get_true_url(text_to_add, url_to_add, symbol):
	        final_url = url_to_add
	        if len(text_to_add.split()) == 1:
		          final_url = url_to_add + text_to_add
	        else:
		          words = text_to_add.split()
		          i = 0
		          for word in words:
			          if i < len(words) - 1:
				          final_url = final_url + (word + symbol)
			          else:
				          final_url = final_url + word
			        i = i + 1
	        return final_url
       ```
       To create a final URL to parse and webscrape from, I had to generate it from the user input. Let's examine the makeup of URLs for both sources using the sample output above, as well as for another set of inputs.
       
       | Username URL     | Champion URL |
       | ------------- | ------------- |
       | http://na.op.gg/summoner/userName=Imaqtpie | https://www.lolcounter.com/champions/akali/weak or https://www.lolcounter.com/champions/akali/strong      |
       | http://na.op.gg/summoner/userName=Hide+on+Bush | https://www.lolcounter.com/champions/twistedfate/weak or https://www.lolcounter.com/champions/twistedfate/strong      |
       
       The input username (Imaqtpie) and the input enemy champion (Akali) are simply appended to a generic url displaying data and statistics. In the case that either inputs exceed one word, a symbol such as *'+'* is concatenated between each additional word. This is all accomplished through the ```get_true_url()``` function.
   2. Gathering and organizing user-specific data
   
      After opening the connection to our sources and using [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/) to parse the HTML to an applicable format for operating upon, I had to scrape the HTML for the variables to use in my calculations.      
      
      ![Data Sample](images/DataSample.png)
      
      When deciding a player's rating on a champion in comparison to the rest of their champion pool, I had to take a few factors into consideration: **Kill/Death/Assist Ratio, Games Played, Win Ratio.** Once this data was identified, I had to _search for and extract it_ within the HTML. Here is a portion of an [HTML sample](SampleChampAttributes.html) for a champion I worked with:
     
		     
		     <td class="RatioGraph Cell" data-value="65.957446808511">
		       <div class="WinRatioGraph">
			 <div class="Graph">
			    <div class="Fill Left" style="width: 65%"></div>
			    <div class="Text Left">62W</div>
			    <div class="Fill Right"></div>
			    <div class="Text Right">32L</div>
			    <div class="Bar" style="left: 65%;"></div>
			 </div>
			 <span class="WinRatio red">66%</span>
		       </div>
		      </td>
		      
	      
         To scrape the static winrate from the HTML, I had to search for ```<td>``` tags, going **layer by layer** until I got to the magic number I was looking for. Repeating this step for KDA ratio and Games played, the simplest way to work with this data was with ```Champion()``` objects in an array storing a user's champion pool. I had to repeat this process to generate the opponent counter list array as well.
   
   3. Coming to a conclusion of champions

      - In order to generate a list of top champions for the user to play, I needed some sort of relation between *games played, KDA and win rate*. 
      ```python 
       X = frame[['Games','KDA']] 
       Y = frame['Win Rate']

       regr = linear_model.LinearRegression()
       regr.fit(X, Y)
       ```
        - Using [pandas](https://pandas.pydata.org) and [sklearn](https://scikit-learn.org/stable/), I implemented a multiple linear regression with a data frame, utilizing games played, KDA and win rate. In other words, I was testing the effects that the number games played and the KDA ratio had on a champion's win rate.
![Graph](images/KDAVsWR.png)
        - When I had generated a prediction of weights for each champion using user-specific stats, I also had to take counter picks into account. If the opponent was strong against a champion in the user's pool, that champion's corresponding weight was multipled by ```0.75```. As you can guess, If the opponent was weak against a champion, the weight was multiplied by ```1.25```. 
        - Sorting the array of weights in descending order, the *champions with the top three highest weights* were returned and printed!
## Historical FAQ (original prototype)

- **Can I choose a lane?**
    - The original prototype did not support lanes. The current CLI supports
      `--role top`, `jungle`, `mid`, `adc`, or `support`.
- **How can I support PickMyChamp?**
    - Spreading the word or generating test cases is more than enough! I'm always looking for feedback, so please reach out to me with advice or ideas for future capabilities.

## License

[![License](http://img.shields.io/:license-mit-blue.svg?style=flat-square)](http://badges.mit-license.org)

- **[MIT license](http://opensource.org/licenses/mit-license.php)**
- Copyright 2022 © <a href="http://vijaybaliga.com" target="_blank">Vijay Baliga</a>.
