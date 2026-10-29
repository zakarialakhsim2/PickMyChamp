# PickMyChamp — audit produit et feuille de route

**Date :** 29 octobre 2026
**Périmètre :** code Python, CLI, application web, API Flask/Vercel, sources de
données, tests, documentation et captures des deux pages partagées.
**Important :** les notes et scores ci-dessous sont une analyse qualitative du
dépôt, pas des métriques d’usage. Aucun analytics de production n’est présent.
Les captures de navigateur reflètent une session déjà ouverte ; elles ne
remplacent pas un test visuel reproductible sur plusieurs appareils.

## 1. Résumé exécutif

PickMyChamp est aujourd’hui un **assistant de draft expérimental** avec une
bonne discipline de transparence : il sépare les statistiques de matchup, les
guides artisanaux et les signaux de composition d’équipe, et évite de présenter
une heuristique comme une prédiction certaine. Son playbook de draft est le
meilleur point de différenciation potentiel.

Ce n’est pas encore une plateforme de coaching complète : il y a deux écrans,
aucun compte utilisateur, aucune base de données, aucune historique web, peu de
guides vérifiés et aucune boucle de rétention ou de croissance mesurée. Le
profil web stocke des préférences que les recommandations web n’utilisent pas.
L’application dépend de pages et de services tiers sans SLA.

**Décision produit recommandée :** devenir un **laboratoire de draft
explicable et partageable**, pas une copie d’overlay généraliste. Renforcer
d’abord la confiance dans les données, le playbook et les boucles de partage.
Construire des fonctions IA post-partie ou hors-partie et non des conseils qui
pilotent une décision en cours de jeu. Le compagnon d’objets hors ligne déjà en
cours n’a pas de benchmark de qualité et ne doit pas être présenté comme un
coach fonctionnel.

| Axe qualitatif | État observé | Conséquence |
|---|---|---|
| Utilité immédiate | Bonne promesse, un contre et un playbook | Expliquer la couverture et guider vers la prochaine action |
| Différenciation | Potentiel dans le raisonnement d’équipe | Le compteur seul est déjà une commodité |
| Confiance | Sources explicites, mais couverture étroite | Ajouter âge, patch, rang, échantillon et limites partout |
| Rétention | Aucune boucle de retour intégrée | Introduire historique local, progrès post-partie et saisons saines |
| Croissance | Pas de partage ni d’invitation avant cette tranche | Livrer des drafts partageables, puis une preview publique |
| Préparation IA | Modèles de données exploratoires, données synthétiques | Pas de scoring IA crédible ni de coach en temps réel aujourd’hui |
| Exploitation | Deux serveurs et caches mémoire locaux | Standardiser la couche API et mesurer latence/erreurs |

## 2. État de l’application et audit détaillé

### Points forts

- Modules séparés pour API Riot, matchmaking, recommandations, guides,
  playbook, assets et interface : les domaines sont testables sans framework
  lourd.
- **46 tests automatisés réussis avant cette livraison**. Les tests couvrent
  les fonctions métier, certains contrats API, des erreurs de données et les
  assets.
- Le code signale les limites : échantillon personnel, rang/patch, source,
  rôle adverse différent et guides non disponibles.
- La logique ne fabrique pas un taux de victoire de matchup à partir des
  seules statistiques personnelles.
- Les données du profil web restent dans `localStorage`; la clé Riot n’est pas
  placée dans le JavaScript.
- Le parseur de Data Dragon et le classement d’objets existants ont des types,
  validations et fixtures. Le travail de classement d’objets reste
  expérimental, déterministe et non connecté à la partie.
- Le picker de champions est filtrable et utilisable au clavier ; plusieurs
  états de chargement, erreur, source et absence d’image sont prévus.
- Le site a des règles responsive et une prise en compte de `prefers-reduced-motion`.

### Faiblesses fonctionnelles et lacunes UX

1. **Promesse plus large que la couverture.** Le guide détaillé de matchup
   couvre Vayne ADC seulement. Les autres résultats reposent sur le tableau de
   matchup ; les runes, le build et le plan de lane sont souvent absents ou
   renvoyés vers un guide externe.
2. **Le profil n’agit pas sur les résultats web.** Riot ID, rôle secondaire,
   maîtrise et style sont demandés puis enregistrés localement, mais ne
   personnalisent ni le contre ni le playbook. Le champ Riot ID est
   particulièrement coûteux en confiance si sa finalité n’est pas démontrée.
3. **La draft est principalement manuelle.** Jusqu’à dix sélecteurs de
   champions sont proposés sans import de composition, sauvegarde, reprise,
   historique de variantes ou comparaison avant/après.
4. **Peu d’explication du choix.** Le playbook donne des rôles et des signaux,
   mais la taxonomie artisanale n’inclut qu’une partie des champions. Le
   résultat peut honnêtement dire « pas de pattern clair », ce qui est
   préférable à une invention mais peut frustrer sans prochaine action.
5. **Onboarding absent.** La première arrivée montre la draft et le profil,
   mais ne distingue pas « saisir un contre », « construire une équipe » et
   « préparer une partie ». Vayne est une valeur de démonstration/initiale,
   pas un vrai choix utilisateur.
6. **Langue incohérente.** Le document de présentation et plusieurs réponses
   serveur sont en français, tandis que l’application visible est
   essentiellement en anglais et indique `lang="en"`. Les noms Data Dragon
   sont aussi chargés en anglais.
7. **Statut ambigu.** Le badge « LIVE DATA » laisse entendre un flux temps réel ;
   la page charge un patch et des pages de stats à la demande. Ce n’est pas
   une session live.
8. **Confiance et résultat peu persistants.** Recharger la page perd les
   sélections et l’analyse ; il n’y a ni sauvegarde, ni historique, ni
   export, ni comparaison de deux drafts.
9. **La publicité n’est pas une stratégie produit.** Un emplacement est
   présent, mais la page ne montre pas de politique/consentement ni de
   contrôle de fréquence. La monétisation doit attendre les prérequis Riot et
   de confidentialité.
10. **Pas de promesse virale actuelle.** Aucun partage de draft, carte image,
    défi, invitation, saison ou intégration Discord n’existait avant cette
    tranche.

### Performance, fiabilité et architecture

- [`web/styles.css`](../web/styles.css) pèse environ **52 KB** et contient plusieurs générations
  empilées de thèmes, tokens, règles responsive et composants dupliqués. Il
  est difficile de savoir quelle règle fait foi et les changements visuels
  risquent des régressions.
- [`web/app.js`](../web/app.js) pèse environ **25 KB** pour deux écrans. La page charge des
  polices tierces et plusieurs images de Data Dragon ; les images de champions
  passent par le serveur applicatif.
- Une requête de matchup peut enchaîner un fetch U.GG (timeout 15 s), un
  fallback OP.GG (initialisation 15 s puis appel 20 s), puis les appels
  Data Dragon (jusqu’à trois requêtes séquentielles, timeout 10 s chacun).
  Sans cache chaud, le chemin dégradé peut bloquer longtemps. L’interface
  affiche un chargement, mais aucune échéance globale ou réponse stale
  explicite.
- `lru_cache` évite des répétitions dans un processus mais n’a ni TTL ni
  partage entre fonctions Vercel ; un redémarrage perd le cache et une donnée
  peut rester périmée dans un processus chaud.
- Le serveur HTTP local et `api/index.py` implémentent des surfaces proches
  séparément. Les contrats et les erreurs peuvent dériver.
- Les scrapers/parseurs U.GG et OP.GG dépendent de formats non contractuels.
  La limite de réponse est utile, mais il manque un pipeline versionné,
  monitoré et un repli explicite avec date/fiabilité.
- Il n’y a pas de mesure de latence, taux d’erreur amont, cache hit, abandon
  de formulaire, activation ou partage ; il est impossible de confirmer les
  problèmes de performance à l’échelle réelle.
- Le dépôt contient aussi un prototype Python historique dans
  [`python/`](../python), mentionné comme retiré dans le
  [README](../README.md). Il utilise d’anciens scrapers et des dépendances non
  déclarées dans [`requirements.txt`](../requirements.txt); il faut clairement
  l’archiver ou le retirer du parcours d’installation.

### Accessibilité et présentation

- Les champs de formulaire ont majoritairement des labels et les erreurs
  utilisent des régions d’alerte. Le picker expose plusieurs attributs ARIA
  et un parcours clavier.
- Les tailles de labels, métadonnées et textes d’aide descendent souvent à
  **8–10 px**. Cela nuit à la lecture, surtout sur mobile et en zoom.
- Le menu de navigation est composé de boutons visuellement sélectionnés,
  mais n’expose pas clairement l’état courant aux technologies d’assistance.
  Il manque un lien d’évitement vers le contenu principal.
- Les mises à jour de résultats ne sont pas toutes annoncées comme
  événements live ; la structure de focus après erreur ou chargement doit être
  testée avec clavier et lecteur d’écran.
- `prefers-reduced-motion` existe, bon point. Les contrastes des textes
  secondaires, focus et badges restent à mesurer avec un outil WCAG sur les
  deux thèmes/états.
- Le thème est dense et très typographique ; la hiérarchie visuelle du contre,
  des limites de données et du prochain geste peut être clarifiée.
- Les captures partagées montrent une interface desktop cohérente, mais
  l’illustration principale peut tomber en fallback et la page déployée
  partagée n’a pas affiché un état complet pendant l’inspection. Ce constat
  n’est pas reproductible et doit être retesté dans une session propre.

### Rétention et croissance

- Aucun mécanisme ne relie « draft analysée » à « résultat après la partie ».
- Aucun objectif de progression, défi ou collection n’existe. Il faut viser
  une progression volontaire et saine, pas des streaks punitifs ou des
  notifications manipulatrices.
- Aucune sauvegarde de draft, comparaison, partage, attribution de parrainage
  ou intégration communautaire n’existait dans le code.
- Pas de compte ni de backend de profil : l’utilisateur change de navigateur
  ou d’appareil et perd son profil.
- Pas de recherche utilisateur, événements analytiques ou cohortes D1/D7.
  Éviter de conclure que l’app est « addictive » ou retenante avant d’avoir
  mesuré rétention, valeur et consentement.

### Risque API et données personnelles à traiter avant croissance

- Le navigateur utilise le stockage local pour le profil, mais une API
  `/api/profile` séparée peut aussi lire/écrire un fichier unique sous le
  répertoire personnel du processus. Cette route n’est pas utilisée par le
  formulaire web actuel. Si elle est déployée telle quelle, elle n’est ni
  authentifiée ni isolée par utilisateur ; il faut la supprimer du déploiement
  ou la rendre stateless/isolée avant d’y envoyer de vrais profils.
- Le Riot ID et les préférences sont des données de compte identifiantes.
  Aucune politique de confidentialité, durée de conservation, suppression
  serveur ou procédure de consentement n’est documentée pour une future
  collecte centralisée.
- L’API Riot officielle exige la protection de la clé côté serveur et des
  limites de débit. Le code CLI respecte le principe de variable
  d’environnement, mais l’interface web ne consomme pas ces données.
- La documentation Riot indique l’obligation d’enregistrer un produit qui
  sert des joueurs ; la monétisation exige un statut approprié, un accès
  gratuit et un contenu transformateur. Voir
  [Riot Developer API Policy](https://developer.riotgames.com/docs/lol).
- Le dépôt documente une question de conformité sur le LCU et le coaching
  live. Ne pas étendre le `build` local ou connecter l’IA à des décisions
  pendant une partie avant validation de Riot ; voir
  [`in-game-ai-companion.md`](./in-game-ai-companion.md).

## 3. Analyse concurrentielle

Recherche effectuée le 29 octobre 2026. La page officielle de Mobalytics et la
politique Riot étaient accessibles. L’accès web de l’environnement bloque
plusieurs sites de jeux ; les fonctionnalités et prix exacts d’OP.GG, U.GG,
Blitz et Porofessor n’ont donc pas été vérifiés à partir de leurs pages
officielles dans cette passe. **Aucun prix ou paywall non vérifié n’est
présenté comme un fait.**

| Concurrent / catégorie | Écart visible avec PickMyChamp | Premium/IA vérifié | Avantage concurrentiel |
|---|---|---|---|
| **Mobalytics** — direct, assistant + stats | Catalogue, builds, runes, guides, filtres, client desktop, pré-match et post-match | Sa page officielle présente l’app comme gratuite, les imports de build en un clic et une feuille pré-match. Smart Highlights utilise l’IA pour sélectionner les moments ; 1 clip gratuit, les 5 clips sont réservés aux membres Plus. | Surface produit plus large, coaching sur toute la boucle de jeu, partage de highlights. Sources : [app LoL](https://mobalytics.gg/lol/glp/download-welcome?isElectron=true), [Smart Highlights](https://mobalytics.gg/lol/glp/smart-highlights-1), [champions](https://mobalytics.gg/lol/champions). |
| **U.GG** — direct, stats/draft | Le code actuel dépend de son tableau de contres ; l’app ne possède pas son propre dataset versionné | Les fonctionnalités/prix actuels n’ont pas pu être vérifiés ; le projet y récupère patch, lane, win rate et sample size. | Source directement intégrée et connue des joueurs ; l’app peut se concentrer sur l’explication de composition et la personnalisation. |
| **OP.GG** — direct, stats/profils | Le projet n’en utilise qu’un fallback MCP de matchup quand U.GG répond 403 | Prix/fonctions commerciales non vérifiés dans cette passe. Le fallback actuel ne garantit pas une version de patch explicite. | Présence historique forte pour les profils et statistiques ; données larges plutôt qu’un seul playbook. |
| **Blitz** — direct, compagnon desktop | PickMyChamp est une web app/CLI ; pas d’import automatique ou de companion complet | Page officielle inaccessible dans l’environnement ; paywall et IA non vérifiés. | Catégorie desktop et guidance au moment de la partie. Examiner les contraintes Riot avant d’imiter cette intégration. |
| **Porofessor / LeagueOfGraphs** — direct/adjacent, analyse | Pas de profil public riche, historique visuel ou outils communautaires | Détails/prix non vérifiés dans cette passe. | Découverte, statistiques, profils et communauté établis. |
| **LoLalytics et autres sites de données** — indirect | Les tableaux PickMyChamp reposent sur une source externe au lieu de normaliser plusieurs sources | Pas de revendication sur un paywall sans vérification. | Profondeur des filtres et granularité des statistiques. |
| **Client League of Legends / communautés Discord, Reddit, YouTube** — indirect | Pas de templates d’équipe, échanges, votes ou contenus créateurs | Généralement modèle plateforme/contenu ; pas une comparaison paywall fiable ici. | Distribution, confiance sociale et discussions déjà intégrées aux habitudes des joueurs. |

### Conséquence stratégique

Ne pas gagner sur la largeur des statistiques ou l’overlay : les acteurs
établis ont déjà davantage de données, de builds et de surfaces. Chercher une
différenciation mesurable sur :

1. **Draft 5v5 compréhensible** : signaux, couverture, risques, compromis, et
   raisons sourcées.
2. **Confort du joueur + composition** : montrer plusieurs options et leurs
   raisons, sans déclarer un vainqueur garanti.
3. **Partage du raisonnement** : lien de draft et carte lisible pour groupe,
   streamer ou Discord.
4. **Apprentissage hors-partie** : retour post-match explicable et plans
   d’entraînement fondés sur des données consenties.
5. **Confiance** : fraîcheur, population, sample size, données manquantes et
   limites visibles.

## 4. Portefeuille priorisé — 50 propositions

Estimations en **jours-personne d’ingénierie** pour une personne expérimentée,
tests inclus, hors validation Riot, acquisition de données, contenus éditoriaux,
design externe et revue légale. Difficulté 1 = petite modification, 10 =
infrastructure/algorithme complexe. Les impacts sont des hypothèses à valider,
pas des résultats attendus.

### 10 innovations distinctives

| Nom | Description | Valeur utilisateur | Tech | Business | Engagement | Temps | Priorité |
|---|---|---:|---:|---:|---:|---:|---|
| Draft Evidence Ledger | Afficher pour chaque signal la source, le patch, l’échantillon, la couverture et ce qui manque. | Décision auditable plutôt qu’un score opaque. | 3 | 8 | 6 | 3–4 j | MVP |
| Draft Counterfactual Lab | Comparer 2–3 picks/ban hypothétiques et montrer comment ils modifient les signaux, sans prédire un taux de victoire. | Comprendre le compromis et apprendre à drafter. | 7 | 9 | 8 | 10–15 j | V1 |
| Pick à trois axes | Séparer confort personnel, matchup documenté et utilité de composition ; ne pas fusionner en score trompeur. | Choisir selon sa vraie priorité. | 5 | 8 | 7 | 6–9 j | V1 |
| Role-flex risk map | Signaler les champions flexibles et les rôles encore ambigus dans une draft, avec niveau de preuve. | Anticiper l’incertitude de lane. | 6 | 7 | 7 | 7–10 j | V2 |
| Draft coverage radar | Visualiser engage, peel, portée, dégâts et contrôle uniquement si les tags ont une source vérifiable. | Voir les besoins non couverts de l’équipe. | 5 | 8 | 7 | 6–8 j | V1 |
| Draft replay / variante | Sauvegarder localement plusieurs étapes et comparer le plan avant/après un pick. | Rejouer une discussion d’équipe. | 4 | 7 | 7 | 4–6 j | V1 |
| Patch confidence delta | Comparer les recommandations entre patchs et réduire la confiance quand un changement affecte le champion/objet. | Éviter de réutiliser aveuglément un ancien guide. | 8 | 8 | 6 | 12–20 j | V2 |
| Blind draft trainer | Exercice hors-partie avec révélations progressives et feedback sourcé après chaque choix. | S’entraîner sans pression de partie. | 5 | 6 | 8 | 7–12 j | V2 |
| Champ de bataille des plans | Montrer plusieurs win conditions concurrentes, leurs prérequis et leurs contre-mesures au lieu d’en imposer une. | Nuance et diversité de décisions. | 7 | 8 | 8 | 10–15 j | V1 |
| Draft Accessibility Mode | Vue simplifiée, gros texte, clavier, lecteur d’écran, daltonisme et export imprimable. | Utilisable sous contrainte de temps ou d’accessibilité. | 4 | 5 | 5 | 5–8 j | V1 |

### 10 fonctionnalités « premium » à rendre gratuites

Ces fonctions sont des opportunités de valeur fréquemment associées aux
produits d’analyse avancés. Sauf indication Mobalytics ci-dessus, leur
tarification concurrente n’a pas été vérifiée. Elles doivent rester gratuites
ou financées par une monétisation transparente, sans avantage compétitif
payant.

| Nom | Description | Valeur utilisateur | Tech | Business | Engagement | Temps | Priorité |
|---|---|---:|---:|---:|---:|---:|---|
| Filtres de données complets | Filtres patch, file, région, rang et intervalle, seulement lorsque la source expose ces dimensions. | Comparer des situations équivalentes. | 7 | 8 | 6 | 10–15 j | V1 |
| Builds situationnels | Plusieurs chemins d’objets/runes avec motif, patch et disponibilité vérifiés. | Préparer sans ouvrir plusieurs sites. | 6 | 8 | 7 | 8–12 j | V1 |
| Historique de drafts | Enregistrer, nommer, dupliquer, supprimer et retrouver des drafts localement. | Réutiliser les compositions d’équipe. | 3 | 6 | 7 | 4–6 j | MVP |
| Pool de champions personnel | Gérer mains/comfort picks et comparer explicitement données personnelles et tendances globales. | Réponses adaptées au joueur, pas au seul méta. | 6 | 8 | 8 | 10–15 j | V1 |
| Comparateur 5v5 | Comparer deux compositions sur leurs besoins/tags et leur couverture, sans score de victoire non validé. | Résoudre un débat de draft. | 6 | 9 | 8 | 8–12 j | V1 |
| Export de briefing | PDF/PNG accessible avec picks, sources, version et limites. | Emporter ou partager l’analyse. | 4 | 7 | 7 | 4–7 j | V1 |
| Suivi personnel post-match | Tendances par rôle/champion à partir de Riot Match-V5 avec consentement. | Mesurer son propre apprentissage. | 7 | 8 | 8 | 12–20 j | V2 |
| Alertes de patch configurables | Résumé des changements qui touchent les champions sauvegardés ; opt-in et fréquence contrôlée. | Rester à jour sans surveiller plusieurs sites. | 6 | 7 | 6 | 8–12 j | V2 |
| Profils de stratégie | Sauvegarder des priorités (engage, scaling, confort, etc.) sans présumer du résultat. | Réduire la répétition de réglages. | 3 | 6 | 6 | 3–5 j | MVP |
| API d’export personnel | Export JSON/CSV des données personnelles et drafts enregistrées. | Portabilité et contrôle des données. | 5 | 5 | 4 | 5–8 j | V2 |

### 10 fonctionnalités IA

Les assistants proposés doivent citer leurs sources, distinguer donnée et
inférence, offrir plusieurs choix, signaler l’incertitude, être désactivables
et ne jamais inventer une donnée. Le coaching en direct/overlay n’est pas
retenu sans validation Riot et contrôle conformité.

| Nom | Description | Valeur utilisateur | Tech | Business | Engagement | Temps | Priorité |
|---|---|---:|---:|---:|---:|---:|---|
| Explication sourcée des contres | Générer une explication à partir de statistiques/version et guides validés, avec citations de données. | Comprendre pourquoi une suggestion apparaît. | 6 | 9 | 7 | 10–15 j | V1 |
| Coach post-partie | Résumer une partie Riot Match-V5 consentie, avec contexte limité aux champs disponibles. | Transformer les statistiques en apprentissage. | 8 | 9 | 9 | 18–30 j | V2 |
| Plan d’entraînement personnel | Proposer trois exercices hors-partie à partir de tendances répétées et non d’un match isolé. | Prochaine étape concrète. | 7 | 8 | 9 | 15–25 j | V2 |
| Assistant de draft hors-partie | Questions en langage naturel sur une composition sauvegardée ; réponse fondée sur le ledger. | Explorer rapidement des scénarios. | 7 | 8 | 8 | 12–20 j | V1 |
| Résumé de patch vérifiable | Synthétiser les notes officielles et relier chaque affirmation à un changement précis. | Réduire la lecture et repérer les impacts. | 5 | 7 | 6 | 6–10 j | V1 |
| Détection de habitudes | Détecter un motif robuste (champions/rôles/échantillons) ; ne pas diagnostiquer tilt ou santé mentale. | Voir un comportement récurrent avec prudence. | 8 | 7 | 8 | 15–25 j | V2 |
| Q/R sur le playbook | Assistant conversationnel borné au contenu du draft et aux sources autorisées. | Clarifier les termes et rôles. | 6 | 7 | 7 | 8–14 j | V1 |
| Compte rendu de replay opt-in | Aider à annoter un fichier fourni par l’utilisateur après la partie, sans collecte cachée. | Retrouver les moments à revoir. | 9 | 7 | 8 | 20–35 j | Futur |
| Recommandation de pratique champion | Comparer le pool du joueur et des objectifs d’apprentissage, sans « pick gagnant » garanti. | Choisir un champion à travailler. | 6 | 7 | 8 | 8–14 j | V2 |
| Highlights IA | Détecter des séquences marquantes dans une source vidéo autorisée et préparer un export partageable. | Moment utile et viral après la partie. | 10 | 8 | 10 | 30–60 j | Futur |

### 10 fonctionnalités communautaires

| Nom | Description | Valeur utilisateur | Tech | Business | Engagement | Temps | Priorité |
|---|---|---:|---:|---:|---:|---:|---|
| Salles d’équipe | Inviter un groupe, partager une draft et commenter une variante. | Décider ensemble sans captures dispersées. | 8 | 9 | 9 | 20–30 j | V2 |
| Classement hebdomadaire | Tableau opt-in par défi/catégorie, pas un MMR parallèle. | Motivation et découverte sociale. | 8 | 8 | 9 | 15–25 j | V2 |
| Défis de composition | Défi asynchrone avec contraintes et solution expliquée. | Apprendre avec une tâche courte. | 5 | 7 | 9 | 8–14 j | V1 |
| Saisons communautaires | Thème, défis et objectifs cosmétiques périodiques, sans pénalité de streak. | Motif de retour sain. | 8 | 8 | 9 | 20–30 j | V2 |
| Badges de contribution | Récompenser guides relus, signalements et explications utiles. | Reconnaissance de la qualité. | 5 | 6 | 8 | 8–12 j | V2 |
| Playbooks créateurs | Publier des compositions et explications modérées avec source/patch. | Accéder à des stratégies variées. | 8 | 9 | 9 | 20–35 j | V2 |
| Vote de variantes | Les membres choisissent une variante et voient le raisonnement majoritaire. | Discussion sans imposer une réponse. | 5 | 7 | 8 | 8–12 j | V1 |
| Débrief de groupe | Discussion post-partie à partir d’une draft sauvegardée et de notes volontaires. | Apprendre sans profiler des joueurs cachés. | 7 | 7 | 8 | 15–25 j | V2 |
| Bot Discord de draft | Requête de composition, lien partageable et carte de résultat dans un serveur. | Utilité là où les équipes discutent déjà. | 7 | 9 | 9 | 12–20 j | V2 |
| Modération et confiance | Signalement, versionnage, attribution et retrait rapide des contenus faux/abusifs. | Maintenir une communauté fiable. | 8 | 6 | 7 | 15–25 j | V2 |

### 10 fonctionnalités virales

| Nom | Description | Valeur utilisateur | Tech | Business | Engagement | Temps | Priorité |
|---|---|---:|---:|---:|---:|---:|---|
| Lien de draft portable | Encoder les choix et le rôle dans le fragment URL ; pas de compte ni de stockage serveur. | Envoyer une draft en un geste. | 3 | 8 | 8 | 2–3 j | MVP — livré |
| Carte de draft partageable | Générer PNG/visuel lisible avec sources, patch et URL/QR. | Partager hors application. | 5 | 8 | 8 | 5–8 j | V1 |
| Aperçu Discord/Open Graph | URL publique courte et aperçu serveur avec image/description. | Rendre le lien visible dans les conversations. | 8 | 9 | 9 | 12–20 j | V2 |
| Défi « choisis ton plan » | Partager deux variantes et demander au groupe de voter. | Susciter réponse et retours. | 6 | 8 | 9 | 8–12 j | V1 |
| Comparaison entre amis | Comparer les drafts, préférences ou réponses sans exposer de Riot ID. | Conversation et compétition légère. | 7 | 8 | 9 | 12–18 j | V2 |
| Récapitulatif hebdomadaire | Image opt-in de progrès et d’analyses, partageable sans statistiques sensibles par défaut. | Partager un progrès authentique. | 6 | 7 | 8 | 8–12 j | V2 |
| Badge de contribution partageable | Carte de badge basée sur contribution vérifiée, pas sur puissance ou rareté manipulatrice. | Reconnaissance transportable. | 4 | 6 | 7 | 5–8 j | V2 |
| QR pour salle d’équipe | Rejoindre une draft commune via QR à durée limitée. | Réduire la friction en vocal/LAN. | 6 | 8 | 8 | 8–12 j | V2 |
| Défi communautaire à lien unique | Un lien ouvre un challenge court, son résultat et une option de partage. | Distribution organique par tâche. | 5 | 8 | 9 | 6–10 j | V1 |
| Invitation sans récompense manipulatrice | Lien d’invitation mesurable, sans récompenses payantes ni incitation au spam. | Croître par recommandation honnête. | 6 | 8 | 7 | 8–12 j | V2 |

### Ordre d’exécution recommandé

1. **Avant croissance :** décider du sort de l’API profil serveur, ajouter les
   mentions/préavis requis, politique de confidentialité et consentement pub,
   vérifier l’enregistrement Riot et arrêter les claims « live » trompeurs.
2. **MVP :** ledger de données, historique local simple, profils de stratégie
   et liens de draft. Le lien est implémenté dans cette livraison.
3. **V1 :** améliorer couverture et qualité du playbook ; filtres de source,
   comparaison de variantes, carte exportable et assistant IA hors-partie
   strictement sourcé.
4. **V2 :** comptes et partage serveur seulement si la demande est démontrée,
   puis salle d’équipe/Discord, statistiques post-match et progression.
5. **Futur :** replay/highlights IA et tout coaching en partie après preuve de
   qualité, de coût et de conformité.

## 5. Exécution de la fonctionnalité retenue : lien de draft (MVP)

### Expérience et comportement

- Après génération du playbook, le bouton **Share this draft** utilise le
  partage natif du navigateur ou copie un lien.
- Le lien embarque une petite charge versionnée (`version`, patch, rôle,
  picks alliés/adverses et adversaire ciblé) encodée en Base64 URL-safe dans
  le **fragment** (`#draft=...`). Le fragment n’est pas envoyé au serveur dans
  la requête HTTP ordinaire.
- À l’ouverture, le client vérifie la version, les rôles, la taille et la
  présence de chaque champion dans le catalogue Data Dragon. Il remplit les
  sélecteurs et recalcule le playbook. Un patch différent est signalé.
- Le Riot ID, les préférences, l’historique Riot et toute donnée de compte ne
  sont pas inclus. Aucun identifiant persistant n’est créé.
- Les fragments sont adaptés à un MVP court ; pas de carte Discord avec image
  ni d’aperçu Open Graph. Ces fonctions exigent une route publique et un
  stockage serveur à concevoir séparément.

### Modifications de code livrées

| Surface | Changement |
|---|---|
| [`web/index.html`](../web/index.html) | Ajout du bouton de partage et d’une région de statut accessible ; statut de la scène ennemi adapté à l’absence de pick. |
| [`web/app.js`](../web/app.js) | Encodeur/décodeur versionné, validation stricte, import des drafts à l’ouverture, recalcul du playbook, partage natif/clipboard et feedback d’erreur. |
| [`web/styles.css`](../web/styles.css) | Présentation du bouton et du feedback avec adaptation au thème existant. |
| [`README.md`](../README.md) | Documentation du fonctionnement, des données incluses et de l’absence de stockage serveur. |

### API, données et migrations

- **API nouvelle :** aucune.
- **API existante réutilisée :** `POST /api/playbook`, qui recalcule à partir des
  picks importés.
- **Schéma de stockage :** aucun ; la charge est encodée dans le lien.
- **Migration de base de données :** aucune ; le projet ne possède actuellement
  pas de base de données.
- **Sécurité/limites :** la charge n’est jamais considérée comme fiable ; elle
  est bornée à 2 048 caractères, limitée aux rôles supportés et aux noms de
  champions du catalogue. Ce lien n’est pas un mécanisme d’autorisation.

### Vérification

- Tests Python existants : **46/46 réussis avant et après les changements**.
- `node --check web/app.js` réussit. Un test Node isolé exécute les fonctions
  réelles du module et valide le round-trip du token, l’import du fragment,
  l’encodage URL-safe et le rejet d’un token malformé/trop long ou d’un
  champion inconnu.
- L’exécution Playwright automatique n’était pas disponible dans cet
  environnement faute de binaire Chromium ; le fonctionnement du partage natif,
  clipboard, clavier et viewport mobile doit aussi être vérifié sur un
  navigateur réel avant déploiement.

## 6. Sources de l’audit

- Sources du dépôt : [`README.md`](../README.md), [`main.py`](../main.py),
  [`api/index.py`](../api/index.py),
  [`pickmychamp/webapp.py`](../pickmychamp/webapp.py),
  [`pickmychamp/counter_source.py`](../pickmychamp/counter_source.py),
  [`pickmychamp/counter_guides.py`](../pickmychamp/counter_guides.py),
  [`pickmychamp/draft_playbook.py`](../pickmychamp/draft_playbook.py),
  [`pickmychamp/item_companion.py`](../pickmychamp/item_companion.py),
  [`pickmychamp/lcu.py`](../pickmychamp/lcu.py),
  [`web/app.js`](../web/app.js), [`web/index.html`](../web/index.html),
  [`web/styles.css`](../web/styles.css), tests et documents existants.
- [Mobalytics — application desktop LoL](https://mobalytics.gg/lol/glp/download-welcome?isElectron=true)
- [Mobalytics — Smart Highlights](https://mobalytics.gg/lol/glp/smart-highlights-1)
- [Mobalytics — catalogue champions](https://mobalytics.gg/lol/champions)
- [Riot — League of Legends Developer API Policy](https://developer.riotgames.com/docs/lol)
- [Riot — General Developer Policies](https://developer.riotgames.com/policies/general)
