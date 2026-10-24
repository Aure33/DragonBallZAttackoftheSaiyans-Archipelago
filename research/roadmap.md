# Plan : de « ça marche » à un très bon Archipelago DBZ AotS

## Contexte
Phases 0 à 7 faites. Le world 0.6.0 compte 224 lieux et une logique par chapitre (Masque à gaz, 2 Ki-Blast Fruits). DeathLink marche avec l'équipe Krillin, Tien et Yamcha. 1000 seeds sur 1000 réussissent.

L'utilisateur veut un world propre, utilisable par le plus grand nombre :
- tester DeathLink à fond, y compris les combats où un seul personnage se bat (Krillin seul au ch. 1, Goku seul au ch. 5) ;
- des options de `.yaml` : condition de victoire, ce qu'on mélange ;
- les **objets clés de l'histoire** dans le mélange, sans jamais pouvoir être bloqué ;
- étudier un pack **PopTracker**.

Ce plan donne l'ordre, la méthode et le critère de fin de chaque bloc. Il s'appuie sur ce qui existe déjà :
- la télécommande (`research/scripts/remote.py` et `remote.lua`) ;
- `tools/live_test.sh` et `tools/mass_seeds.py` ;
- le faux joueur DeathLink (`friend.py`, à ranger dans `tools/`) ;
- l'analyse des scripts `.sb` (`research/scripts/extract_chests.py` : `parse_script`, natives `4a n`).

Règles qui ne changent pas :
- jouer seulement sur mes états 7, 8 et 9, et réserver `write` à ces états ;
- recharger l'état 4 du joueur à la fin de chaque essai ;
- ne rien mettre du jeu dans Git ;
- un commit par résultat testable.

---

## Bloc 0 : outils et états de sauvegarde (base de tout le reste)
1. Ranger dans `tools/` les outils de test, qui se perdent dans le scratchpad :
   - `friend.py` : faux joueur DeathLink, modes `listen` et `kill` ;
   - `go.sh` : ordres à la télécommande, puis capture d'écran ;
   - `fight.py` : combat automatique ;
   - `walk_to_battle.py` : marcher jusqu'à un combat aléatoire.
2. **Avancer dans l'histoire** avec la télécommande, depuis l'état 4 (début du ch. 1), et poser des états de sauvegarde aux moments clés. Mes trois emplacements (7, 8, 9) ne suffisent pas. Je copie donc chaque fichier d'état, après coup, dans `dbz_research\states\` (hors Git) sous un nom parlant, par exemple `ch01_krillin_seul.State`. Je recopie l'un d'eux dans l'emplacement 9 quand j'en ai besoin.
   - Points d'arrêt prévus : ch. 1 (Krillin seul), ch. 2 et 3 (chacun son personnage), ch. 5 (Goku seul, Mt. Five Element), ch. 6 (combat scripté contre Raditz), ch. 8 (rochers de niveau 2), ch. 13, ch. 15 (avant Vegeta).
   - C'est le plus long à faire, mais ça sert à tous les blocs suivants : DeathLink, objets clés, drapeau 1050, lieux mis de côté.

**Critère de fin** : un état par point d'arrêt, chacun noté dans `CLAUDE.md` avec son chapitre et sa zone.

## Bloc 1 : DeathLink testé à fond
Tester chaque cas avec le serveur, le client et le faux joueur :

| Cas | Ce qu'on vérifie |
|---|---|
| Krillin seul (ch. 1) | Le repère `0C` n'est que sur Krillin. Sa mort envoie une mort ; une mort reçue le fait tomber |
| Équipe de 3, un seul K.O. | Aucune mort envoyée |
| Personnage qui rejoint ou quitte l'équipe | Le repère suit le changement |
| **Combat scripté qu'on doit perdre** (Raditz au ch. 6, autres boss scénarisés) | L'histoire continue-t-elle avec tout le monde à 0 PV ? Si oui, il ne faut **pas** envoyer de mort |
| Mort reçue pendant un boss ou un combat scripté | Pas de blocage de l'histoire |
| Mort reçue hors combat, puis rechargement d'un état ou fermeture du client | La mort en attente ne se déclenche pas deux fois |

Correction prévue si une fausse mort apparaît : ne compter une défaite que si elle **finit à l'écran titre**. Il faudrait alors trouver une valeur « retour au titre », en comparant la mémoire d'un combat scripté et d'une vraie défaite. Les photos `p9`, `b9` et `t9` existent déjà.

**Critère de fin** : tous les cas du tableau sont notés dans `decisions.md`. 0 fausse mort. Les tests unitaires couvrent chaque cas trouvé.

## Bloc 2 : objets clés de l'histoire dans le mélange (le cœur d'un bon world)
Objets concernés (`game_data.md`) : Éventail magique (Bansho Fan), Coquille d'œuf, Miel (ch. 5), Clé du champ de neige (ch. 8), Cristal d'Esprit (ch. 13), Eau de l'ermite, Bracelet du Diable, Passe pour la Ville est.

1. **Recherche dans les scripts `.sb`** : pour chaque objet clé, trouver où il est donné (`GetItem` ou une native proche) et où il est vérifié. Je chercherai des natives du type `CheckItem` ou `GetItemNum` (noms à confirmer dans la table des natives), ou bien un test de drapeau.
2. Classer chaque objet clé :
   - **Vérifié par l'inventaire** : on peut le mélanger. Le client retire l'objet donné par la scène, comme pour les coffres. Le lieu « reçu de X » devient un check, et l'objet entre dans le pool en progression, avec une règle sur le chapitre qui le demande.
   - **Vérifié par un drapeau d'histoire** : on ne peut pas le mélanger sans patch de la ROM. Il reste un simple check, et on le note pour la phase 9.
3. Vérifier en jeu (états du bloc 0) qu'un objet retiré bloque bien, puis qu'une fois rendu par le client, l'histoire repart.
4. Revoir la logique des Ki-Blast Fruits (C22) : le niveau du tir de Ki vient de l'histoire. Si un essai aux rochers du ch. 8 montre que les fruits ne servent pas, simplifier la règle.

**Critère de fin** : chaque objet clé est marqué « mélangé » ou « laissé en place, avec la raison ». Les seeds réussissent toujours (`mass_seeds.py`, 1000 sur 1000). Un essai réel montre un objet clé reçu d'un autre joueur qui débloque la suite.

## Bloc 3 : options du `.yaml`
À ajouter dans `options.py`, à passer par `fill_slot_data` quand le client en a besoin, et à documenter dans la doc anglaise du world :

| Option | Valeurs | Remarque |
|---|---|---|
| `goal` | `vegeta` (par défaut), `chapter` | Avec `goal_chapter` (1–15), la victoire tombe à la fin du chapitre choisi (drapeau de début du chapitre suivant). Ça raccourcit une partie pour les amis |
| `hidden_items` | oui/non | Les 14 objets à examiner |
| `story_checks` | oui/non | Les 15 fins de chapitre |
| `key_items` | oui/non | Résultat du bloc 2 |
| `east_city_ruins` | existe déjà | |
| `experience_multiplier` | existe déjà | |
| `death_link` | fait | |
| `start_with_gas_mask` | oui/non | Confort, moins de blocage |

Les lieux devenus optionnels passent par `included_locations()` dans `locations.py`. La règle de victoire reste dans `rules.py`. Il faut un test du world par option, et `mass_seeds.py` doit tirer chaque option au hasard.

**Critère de fin** : le modèle de `.yaml` généré par Archipelago montre toutes les options. Chaque combinaison donne des seeds finissables. Un essai réel avec `goal: chapter` = 1 envoie la victoire à la fin du ch. 1.

## Bloc 4 : plus de lieux (contenu)
Par ordre de rapport intérêt / risque :
1. Les **23 lieux mis de côté** (`research/chests.md`) : vérifier l'accès en jeu avec les états du bloc 0, puis les ajouter en relançant les générateurs, jamais à la main.
2. **Boss vaincus** comme lieux : un drapeau d'histoire par boss, extrait des scripts comme pour les chapitres.
3. **Dons à plusieurs drapeaux** (carottes, captures, Bubbles : C24) : seulement si on trouve un drapeau sûr pour chaque don.
4. **Boules de cristal** : à étudier en option avec les Ruines de la Ville est.

**Critère de fin** : chaque lieu ajouté a sa source (script ou essai en jeu) et passe les 1000 seeds.

## Bloc 5 : étude du pack PopTracker
1. Lire la doc PopTracker (format des packs : `manifest.json`, `items/*.json`, `locations/*.json`, `layouts/*.json`, `scripts/*.lua`) et 2 packs Archipelago existants (format et suivi automatique par `slot_data` et ID).
2. Prototype **sans carte** : une grille d'objets (progression, objets clés) et une liste de lieux par zone et par chapitre. Le tout est **généré** depuis `location_data.py`, `items.py` et `rules.py` par un script `tools/build_poptracker.py`, pour ne jamais diverger du world. Suivi automatique branché sur l'ID du serveur.
3. Plus tard, les **cartes** : captures d'écran des zones, avec un point par coffre. Les positions viennent de `CreateBox(x, y)` dans les scripts. Attention : ne pas publier d'images extraites de la ROM sans y réfléchir (question de droits).

**Critère de fin de l'étude** : une note dans `decisions.md` sur la faisabilité et le coût. Le prototype sans carte se charge dans PopTracker et coche les lieux pendant une partie de test.

## Bloc 6 : finitions pour le grand public
- Guide d'installation (`setup_en.md`) testé de bout en bout sur un PC neuf : version d'Archipelago, BizHawk 2.11, ROM EU vérifiée par son empreinte.
- Vérifier la ROM dans le client (déjà fait par l'en-tête), avec un message clair si la version ne va pas.
- Messages en jeu (`display_message`) pour les objets reçus et les morts DeathLink.
- Skill `playtest-checklist` (phase 8) : une liste de vérifications pour une partie avec les amis.
- Relecture du world par l'agent `logic-reviewer` et `/code-review`.
- Phase 8 : vraie partie avec les amis. Phase 9 : patch de la ROM si un objet clé l'exige, puis publication (`.apworld`, doc, Discord Archipelago).

---

## Ordre proposé
Bloc 0, puis le bloc 1 (en même temps que le bloc 0 : chaque état posé sert tout de suite aux tests DeathLink), le bloc 2, le bloc 3, le bloc 5 (étude), le bloc 4, le bloc 6 et enfin la phase 8.

Chaque bloc se termine par : les tests du world, `mass_seeds.py`, le déploiement côté Windows, la mise à jour de `CLAUDE.md`, `decisions.md` et `ram_map.md`, puis un commit et un push.

## Vérification
- Tests : `AP_TEST_WORLDS=dbz_aots .venv/bin/python -m pytest -q -n auto -p no:cacheprovider` (depuis le clone d'Archipelago).
- Seeds : `python3 tools/mass_seeds.py --count 1000`.
- Essais réels : `tools/live_test.sh server|client` et `tools/friend.py listen|kill`, avec la télécommande pour jouer.
- Fin de chaque essai : arrêter le serveur, le client et le faux joueur, puis recharger l'état 4.
