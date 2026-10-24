# Projet : Dragon Ball Z: Attack of the Saiyans (Nintendo DS) pour Archipelago

Tu vas m'aider sur un projet complet, de A à Z. Lis tout ce document avant de faire quoi que ce soit. **Ne code rien avant que j'aie répondu aux questions de la section 10.**

---

## 1. Qui je suis

- Développeur, Mastère 2 Développement Web. À l'aise en **Python**, Git, tests automatisés (Robot Framework, Selenium), CI.
- **Débutant** sur : Archipelago, la rétro-ingénierie de jeux, la mémoire d'un jeu DS, le Lua.
- Je veux des explications **courtes et simples**, sans jargon inutile. Quand un mot technique est nécessaire, explique-le en une phrase la première fois.
- Je veux comprendre ce que tu fais, pas juste recevoir du code.

## 2. But du projet

Ajouter **Dragon Ball Z: Attack of the Saiyans** (DS, 2009, Monolith Soft / Namco Bandai, RPG au tour par tour) à **Archipelago**, le randomizer multi-jeux.

Concrètement : je joue à ce jeu sur émulateur pendant que mes amis jouent à d'autres jeux. Les objets de nos jeux sont mélangés entre nous. Quand j'ouvre un coffre, je peux envoyer un objet à un ami. Quand un ami trouve un de mes objets, je le reçois dans mon jeu.

- **Usage personnel** au départ (dépôt GitHub privé). Une publication pourra venir plus tard, donc on code proprement dès le début.
- Le projet doit rester **jouable par étapes** : une première version minimale qui marche, puis on enrichit.

## 3. Rappel : comment fonctionne Archipelago

- Le **serveur Archipelago** génère une partie (« seed ») à partir des réglages de chaque joueur (fichiers YAML).
- Chaque jeu est décrit par un **« world »** en Python (dossier `worlds/<jeu>/`, livré sous forme de fichier `.apworld`). Il définit :
  - les **objets** (items) du jeu ;
  - les **lieux** (locations) où on peut trouver un objet (coffre, récompense de quête, boss…) ;
  - les **régions** (zones du jeu) et leurs liens ;
  - la **logique** (règles d'accès : « pour aller dans cette zone, il faut tel objet ») ;
  - les **options** du joueur ;
  - la **condition de victoire**.
- Un **client** fait le lien entre le jeu et le serveur : il détecte les lieux visités (« checks ») et donne au joueur les objets reçus.
- Pour les jeux sur émulateur, Archipelago fournit déjà un **client BizHawk** (`worlds/_bizhawk/`) : un script Lua tourne dans l'émulateur BizHawk et le client Python lit/écrit la mémoire du jeu à travers lui. On s'appuie dessus au lieu de tout refaire.

**Avant de coder**, lis dans le dépôt officiel (https://github.com/ArchipelagoMW/Archipelago) :
- `docs/world api.md`
- `docs/adding games.md`
- `docs/apworld specification.md`
- `docs/options api.md`
- `docs/tests.md`
- le code de `worlds/_bizhawk/` (client générique)
- 2 ou 3 worlds existants qui utilisent BizHawk comme exemples (cherche ceux qui ont un fichier `client.py` héritant de `BizHawkClient`, si possible un RPG et si possible un jeu DS).

Ne te fie pas à ta mémoire pour l'API : elle évolue. **Vérifie toujours dans la version du code que j'utilise.**

## 4. Le jeu (à confirmer, ne rien inventer)

Ce que je sais :
- RPG au tour par tour en 2D, sur DS, qui suit la saga des Saiyans (tournoi, Raditz, entraînement, Nappa/Vegeta) avec du contenu en plus.
- Il y a des zones à explorer, des coffres, des objets, des équipements, des techniques, des quêtes et des boss.

**Règle importante :** tu ne connais probablement pas ce jeu en détail. **N'invente aucun nom d'objet, de zone ou de quête.** Toutes les données du jeu doivent venir :
1. de guides fiables (GameFAQs, wikis) que tu cites ;
2. de ce que j'observe en jouant ;
3. des données extraites de la ROM ou de la mémoire.

Chaque donnée doit avoir sa source notée dans les fichiers de recherche.

## 5. Architecture visée

### 5.1 Dépôts

- **Mon fork** d'Archipelago (ou un dépôt séparé qui contient seulement le world, à décider avec moi).
- Le world dans `worlds/dbz_ats/` (nom à valider).
- **Jamais** de ROM, de sauvegarde ou de fichier du jeu dans Git. Mets en place un `.gitignore` dès le début.

### 5.2 Fichiers du world (à adapter à l'API réelle)

```
worlds/dbz_ats/
├── __init__.py        # classe World + WebWorld, création des items/régions, condition de victoire
├── items.py           # table des objets (nom, id, classification : progression / utile / remplissage / piège)
├── locations.py       # table des lieux (nom, id, région, adresse mémoire + bit qui indique « déjà pris »)
├── regions.py         # zones du jeu et liens entre elles
├── rules.py           # règles d'accès
├── options.py         # options du joueur
├── client.py          # client BizHawk (hérite de BizHawkClient)
├── ram.py             # toutes les adresses mémoire, au même endroit, commentées
├── rom.py             # (plus tard) patch de la ROM si nécessaire
├── data/              # tables brutes (JSON/CSV) issues de la recherche
├── docs/
│   ├── en_<Nom du jeu>.md   # page « comment ça marche » (format Archipelago)
│   └── setup_en.md          # guide d'installation
└── test/              # tests (framework de tests d'Archipelago)
```

### 5.3 Dossier de recherche (hors du world)

```
research/
├── ram_map.md         # carte de la mémoire : adresse, taille, sens, comment on l'a trouvée, version de ROM
├── game_data.md       # liste des zones, coffres, quêtes, boss, objets, avec sources
├── decisions.md       # journal des choix (date, choix, raison)
├── savestates/        # (ignoré par Git) états de sauvegarde de référence
└── scripts/           # scripts Lua/Python d'aide à la recherche (comparaison de mémoire, etc.)
```

### 5.4 Fichier de contexte

Crée un `CLAUDE.md` à la racine qui résume : le but, l'état actuel, la phase en cours, les conventions, les commandes utiles (lancer les tests, générer une seed, construire le `.apworld`). Mets-le à jour à chaque fin de phase.

## 6. Le cœur technique : la mémoire du jeu

C'est la partie la plus dure. Il faut trouver dans la RAM du jeu :

1. **L'identification du jeu** : vérifier qu'on a la bonne ROM (code du jeu dans l'en-tête, version, région).
2. **L'inventaire** : où sont stockés les objets et leurs quantités, l'argent (zénis), l'équipement.
3. **Les drapeaux de coffres** : quel bit passe à 1 quand un coffre est ouvert.
4. **Les drapeaux d'histoire et de quêtes** : avancement du scénario, quêtes terminées, boss vaincus.
5. **Les techniques** apprises par personnage.
6. **L'état du jeu** : en combat, en menu, sur la carte, écran titre (pour ne pas écrire n'importe quand).
7. **Un endroit qui survit à la sauvegarde** pour stocker « combien d'objets Archipelago j'ai déjà reçus ». Sinon, au rechargement, le client redonnerait tous les objets. Si aucun endroit libre n'existe dans la sauvegarde, on stocke ce compteur côté client (fichier lié à la partie), à discuter.

**Méthode** (à m'apprendre pas à pas) :
- faire un état de sauvegarde juste avant une action (ouvrir un coffre), faire l'action, refaire un état ;
- comparer la mémoire avant/après (outil RAM Search de BizHawk, ou un script) ;
- recommencer jusqu'à isoler la bonne adresse ;
- noter le résultat dans `research/ram_map.md`.

Outils possibles : RAM Search / RAM Watch / Hex Editor / console Lua de BizHawk ; DeSmuME pour comparer ; outils d'exploration de ROM DS (ndstool, Tinke) ; Ghidra avec un chargeur DS pour l'analyse avancée (seulement si nécessaire).

**Les adresses dépendent de la version de la ROM** (EU, US, JP). On cible une seule version au début.

## 7. Comment remplacer les objets du jeu

Quand j'ouvre un coffre, le jeu me donne l'objet d'origine. Il faut à la place envoyer l'objet prévu par Archipelago. Deux approches :

- **A. Sans modifier la ROM (pour commencer)** : le client voit que le coffre est ouvert, envoie le check au serveur, et retire l'objet d'origine de l'inventaire. Simple, mais visible à l'écran (« Vous obtenez X » alors que ce n'est pas le bon objet).
- **B. Avec un patch de la ROM (plus tard)** : on modifie le contenu des coffres ou le code du jeu pour qu'un coffre ne donne rien (ou un objet neutre) et affiche le bon nom. Plus propre, beaucoup plus dur sur DS (système de fichiers, overlays, compression).

On commence par **A**. On évalue **B** une fois que tout fonctionne.

Même question pour la progression : si un objet clé débloque une zone, il faut savoir si le jeu vérifie un objet dans l'inventaire ou un drapeau d'histoire. Les règles de logique en dépendent.

## 8. Conception du randomizer (à valider avec moi)

- **Lieux** : coffres, récompenses de quêtes, boss vaincus, éventuellement étapes d'histoire.
- **Objets** :
  - *progression* : objets clés qui ouvrent l'accès à des zones ou quêtes ;
  - *utiles* : équipements, techniques, objets rares ;
  - *remplissage* : soins, zénis, consommables ;
  - *pièges* (option) : à définir.
- **Condition de victoire** : battre le dernier boss de l'histoire (option : finir aussi le contenu bonus).
- **Options possibles** :
  - multiplicateur d'expérience (un RPG peut être lent dans une partie à plusieurs) ;
  - inclure ou non les quêtes annexes ;
  - mélanger ou non les techniques ;
  - DeathLink (si toute l'équipe est KO, tout le monde meurt, et inversement) ;
  - niveau de départ, zénis de départ.
- La **logique** ne doit jamais bloquer la partie : une seed générée doit toujours être finissable.

## 9. Plan par phases

Chaque phase se termine par un résultat que je peux tester. Ne passe pas à la suivante sans mon accord.

| Phase | Objectif | Résultat attendu |
|---|---|---|
| 0 | Installation | Archipelago lancé depuis les sources, BizHawk + ROM qui tourne, script Lua connecté, dépôt Git prêt |
| 1 | Recherche du contenu | `game_data.md` : liste des zones, coffres, quêtes, boss, objets, avec sources |
| 2 | Carte mémoire | `ram_map.md` : identification, inventaire, coffres d'une première zone, état du jeu |
| 3 | World minimal | `.apworld` qui génère une seed avec **une seule zone** (quelques coffres) |
| 4 | Client minimal | Ouvrir un coffre envoie le check ; recevoir un objet l'ajoute à l'inventaire ; pas de doublon au rechargement |
| 5 | Test réel | Partie de test avec un autre jeu simple (ou un 2e « joueur » fictif) |
| 6 | Extension | Toutes les zones, quêtes, boss ; logique complète ; options |
| 7 | Tests | Tests automatiques (génération de nombreuses seeds, logique toujours finissable) |
| 8 | Partie avec mes amis | Retours, corrections |
| 9 | Finitions | Patch ROM (approche B) si utile, documentation, tracker éventuel |

## 10. Questions à me poser AVANT de commencer

Pose-moi ces questions en **un seul message**, avec des choix quand c'est possible, et explique en une ligne pourquoi chacune compte. Ajoute toute autre question utile.

**Le jeu et la ROM**
1. Quelle version de la cartouche j'ai (EU, US, JP) ? Langue utilisée ?
2. Comment j'ai obtenu la ROM (copie de ma propre cartouche) ? Peux-tu me donner son empreinte (MD5/SHA-1) pour qu'on la note ? Je ne t'envoie jamais le fichier lui-même.
3. La ROM est-elle complète et non modifiée (pas de patch, pas de traduction) ?
4. Est-ce que je connais bien le jeu ? Est-ce que je l'ai déjà fini ?
5. Ai-je des sauvegardes à différents moments du jeu ? Sinon, accepter qu'on en crée au fil du projet.

**L'environnement**
6. Système d'exploitation ?
7. Émulateur : BizHawk est le choix recommandé (client Archipelago déjà prêt). Est-il installé ? Quelle version ? Vérifie avec moi que sa version est compatible avec le client BizHawk d'Archipelago et qu'il lance bien la ROM DS.
8. Version de Python installée ? Archipelago installé ? Depuis les sources ou l'installateur ?
9. Où je veux le dépôt (fork d'Archipelago ou dépôt séparé) ? Privé sur GitHub ?

**Le projet**
10. Combien de temps je peux y passer par semaine ?
11. Quels jeux mes amis utilisent (pour tester les échanges) ?
12. Condition de victoire préférée ? Quêtes annexes incluses ?
13. Est-ce que je préfère d'abord une version « moche mais jouable » (approche A) ? (recommandé : oui)

## 11. Organisation de ton travail

Si ton environnement le permet (Claude Code), mets en place :

### Agents (`.claude/agents/`)
- **ram-researcher** : m'aide à trouver des adresses mémoire. Prépare les comparaisons, interprète les résultats, met à jour `ram_map.md`. Ne devine jamais une adresse.
- **game-data-researcher** : collecte les données du jeu dans des sources fiables et remplit `game_data.md` avec les sources.
- **apworld-dev** : écrit et maintient le world Python (items, lieux, régions, règles, options) en suivant l'API réelle d'Archipelago.
- **client-dev** : écrit le client BizHawk (`client.py`) et les scripts Lua d'aide.
- **logic-reviewer** : relit la logique pour trouver les blocages possibles (objet clé placé derrière lui-même, zone inaccessible…).
- **tester** : écrit et lance les tests (génération de seeds en masse, tests unitaires), rapporte les échecs.

### Skills (`.claude/skills/`)
- **ram-diff** : procédure pas à pas pour trouver une adresse (états de sauvegarde, comparaison, validation, notation).
- **add-location** : ajouter un lieu de bout en bout (donnée de recherche → `locations.py` → région → règle → client → test).
- **add-item** : idem pour un objet.
- **build-and-test** : construire le `.apworld`, générer une seed, lancer les tests.
- **playtest-checklist** : liste de vérifications avant une partie avec mes amis.

Si ces fonctions ne sont pas disponibles, garde la même organisation sous forme de sections dans `CLAUDE.md`.

## 12. Règles de travail

- **Pas d'invention.** Si tu ne sais pas (adresse, nom d'objet, API), dis-le et propose comment le vérifier.
- **Petites étapes testables.** Après chaque changement, dis-moi comment le tester.
- **Ce que je dois faire moi-même** (jouer, faire un état de sauvegarde, lancer BizHawk, lire une valeur) : donne-moi des instructions numérotées, précises, et attends mon retour.
- **Code** : Python typé, lisible, commenté là où c'est utile. Respecte le style et les conventions d'Archipelago.
- **Tests** : chaque phase ajoute des tests. Une seed doit toujours être finissable.
- **Git** : commits petits et clairs. Jamais de fichier du jeu dans le dépôt.
- **Légal** : on travaille uniquement avec ma propre copie du jeu. Aucun fichier du jeu n'est partagé ou publié.
- **Documentation** : tiens à jour `CLAUDE.md`, `ram_map.md`, `game_data.md` et `decisions.md`.
- **Communauté** : avant la phase 3, rappelle-moi de vérifier sur le Discord Archipelago que personne ne travaille déjà sur ce jeu.

## 13. Ta première réponse

1. Résume le projet en 5 lignes pour me montrer que tu as compris.
2. Pose-moi les questions de la section 10 (et les autres utiles).
3. Propose le contenu de la phase 0, étape par étape.
4. Attends mes réponses avant de créer des fichiers.