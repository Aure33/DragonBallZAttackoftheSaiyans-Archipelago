# Journal des décisions

Format : date — décision — raison. Les décisions les plus récentes en bas.

## 2026-10-23 — Phase 0

| # | Décision | Raison |
|---|---|---|
| D1 | ROM cible : **EU `BRPP` rév. 0** (MD5 `45ba1dcb…6f73`), copie de la cartouche du joueur | C'est la cartouche qu'on possède. Les adresses mémoire changent d'une version à l'autre, donc une seule version au début |
| D2 | Archipelago **0.6.8** (sources dans WSL et installation Windows à la même version) | Dernière version stable. Un `.apworld` construit avec une version doit tourner sur la même |
| D3 | **Dépôt séparé** (world + recherche), privé sur GitHub. Sources d'Archipelago clonées à côté (`~/Coding/ArchipelagoRom/Archipelago`), reliées par un lien symbolique `worlds/dbz_aots` | Dépôt léger, forme habituelle des apworlds communautaires. Un fork ne sert que pour entrer dans le dépôt officiel |
| D4 | Nom du world : `dbz_aots` ; nom du jeu : `Dragon Ball Z: Attack of the Saiyans` | « AotS » est l'abréviation déjà utilisée par la communauté |
| D5 | Environnement **WSL + Windows** : code, tests et génération dans WSL ; BizHawk et le client BizHawk tournent sous Windows, avec le `.apworld` copié dans `C:\ProgramData\Archipelago\custom_worlds` | Le script Lua de BizHawk n'écoute que sur `localhost` côté Windows (`server:bind("localhost", port)` dans `connector_bizhawk_generic.lua`), que WSL ne voit pas par défaut. Plan B si les essais du client deviennent pénibles : réseau « miroir » de WSL |
| D6 | Approche **A** d'abord (pas de patch de ROM) | Beaucoup plus simple. Le patch (approche B) sera évalué une fois que tout marche |
| D7 | Victoire = battre le **dernier boss de l'histoire** ; quêtes annexes et contenu bonus = **options** | Choix du joueur |
| D8 | Code, noms d'objets/lieux et docs du world en **anglais** ; recherche, journal et `CLAUDE.md` en **français** | Convention Archipelago (le site n'affiche que l'anglais) ; le joueur travaille en français |
| D9 | Chaque donnée du jeu porte un nom FR (écran) **et** un nom EN (guides) | Le joueur joue en français, les guides sont en anglais |
| D10 | Les étapes sont découpées selon un **résultat testable**, jamais selon une durée | Demande du joueur |
| D11 | Projets tiers sans licence (randomizer, traductions) : on lit pour apprendre, **on ne copie pas de code**, et toute donnée est revérifiée sur notre ROM | Sans licence = tous droits réservés |
| D12 | Partenaire de test (phase 5) : un jeu déjà joué sur ce PC (Pokémon Émeraude de préférence) ou un 2e joueur fictif | Les amis jouent à d'autres jeux |

## Ce qu'on a appris de la doc officielle (0.6.8)
- **`.apworld`** = archive zip en minuscules, contenant un dossier du même nom (`dbz_aots.apworld` → `dbz_aots/__init__.py`). On le construit avec `Launcher.py "Build APWorlds" -- "<nom du jeu>"`, qui le dépose dans `build/apworlds/`. Les métadonnées vont dans `archipelago.json` (`game`, `minimum_ap_version`, `world_version`, `authors`). Les imports internes au world sont relatifs (`from .options import …`).
- **Minimum d'un world** : un `__init__.py` avec une sous-classe de `World` (nom de jeu unique, une `WebWorld`, `item_name_to_id`, `location_name_to_id`, `create_item`), une région de départ (« Menu » par défaut), autant d'objets que de lieux, une condition de victoire, une page `docs/en_<nom du jeu>.md` et un guide d'installation.
- **Tests** : dossier `test/` dans le world, avec une base qui hérite de `test.bases.WorldTestBase`. Elle lance déjà 3 tests génériques (tout est atteignable avec tous les objets, quelque chose est atteignable sans objet, le remplissage marche). Pas de `pytest.mark.parametrize` : on utilise `test.param`.
- **Client BizHawk** : une classe qui hérite de `BizHawkClient`, avec `game`, `system = "NDS"`, `validate_rom()` (reconnaître la ROM), `game_watcher()` (boucle principale), et éventuellement `set_auth()`. Pour lire et écrire : `bizhawk.read`, `bizhawk.write`, `bizhawk.guarded_write` (écrit seulement si une valeur témoin n'a pas changé, pour éviter les écritures au mauvais moment). Le connecteur Lua accepte BizHawk 2.7 et plus, et a été testé jusqu'à 2.11.
- **Le client doit** : renvoyer à la connexion les checks faits hors ligne, pouvoir donner un objet à tout moment, accepter plus d'exemplaires d'un objet que le jeu n'en prévoit, et tenir un **compteur d'objets reçus** pour ne rien redonner en double.
- **Exemples à étudier** : aucun jeu DS dans le dépôt officiel. Le world communautaire `pokemon_bw` (DS) est installé : il utilise le domaine `Main RAM` et vérifie l'en-tête de la ROM en mémoire. Côté RPG dans le dépôt officiel : `mlss` (Mario & Luigi Superstar Saga, GBA), `pokemon_emerald` (GBA), `ff1` (NES).

## 2026-10-23 — Phase 1 (recherche du contenu)

| # | Décision / constat | Raison |
|---|---|---|
| D13 | Base des futurs lieux = les ~240 objets des en-têtes « Items: » du guide DSR, plus les récompenses de boss et de quêtes | C'est la seule liste complète trouvée. Elle est à vérifier en jeu (oublis connus, dons de PNJ mélangés aux coffres) |
| D14 | Les **Dragon Balls ne seront pas des lieux** | Leur position est aléatoire dans le jeu d'origine (DSR Odds-and-Ends), donc impossible de les relier à un emplacement fixe |
| C1 | La progression suit surtout l'**histoire** (chapitres linéaires). Les objets clés repérés comme candidats à la progression : Gas Mask, Bansho Fan, Honey, Eggshell, Snowfield Key, Ki-Blast Fruit (×2, rochers devant des coffres), East City pass | À confirmer en phase 2 : le jeu vérifie-t-il l'objet dans l'inventaire ou un drapeau d'histoire ? (cahier des charges §7) |
| C2 | Le contenu bonus doit être fait **avant** le dernier combat contre Vegeta : il n'y a pas de sauvegarde après les crédits | Confirme D7 (victoire = dernier Vegeta). Les lieux bonus seront donc à option |
| C3 | Les techniques s'achètent surtout avec les AP (2 viennent de l'histoire, les S-Combos viennent d'objets « memo ») | L'option « mélanger les techniques » ne pourra porter, au début, que sur les S-Combo memos |
| C4 | Le randomizer existant (RND) ne s'occupe pas des coffres et ne donne aucun identifiant d'objet | Il ne nous aide pas pour la liste des lieux. Il pourra servir plus tard pour le format de données `bdat.bin` (patch, approche B) |

## 2026-10-23 — Phase 1 : extraction des textes de la ROM

| # | Décision / constat | Raison |
|---|---|---|
| D15 | Les noms d'objets et de lieux du world seront les noms **anglais de la ROM EU** (colonne « EN (EU) » de `rom_names.md`), pas ceux des guides | Ce sont les noms officiels de notre version. Les guides (US) ne servent plus qu'à trouver *où* sont les objets |
| D16 | Les textes de la ROM sont extraits par un script (`research/scripts/extract_rom_names.py`, environnement `research/.venv` avec `ndspy` 4.2.0). Seuls les **noms** vont dans Git ; descriptions et dialogues restent dans `research/extracted/` (ignoré) | Pas de fichier du jeu dans le dépôt. Les noms, eux, sont de toute façon nécessaires dans `items.py` |
| C5 | Le numéro de ligne d'un objet dans sa table (ex. `use_item_mes` n° 0 = Small Bean) est **probablement son identifiant interne**. À confirmer en phase 2, en lisant l'inventaire en mémoire | Ça simplifierait beaucoup le client : donner l'objet n = écrire n dans l'inventaire |
| C6 | La ROM contient bien **7** Dragon Balls (objets clés One-Star à Seven-Star Ball) | Tranche le désaccord DSR (7) / LP (6) |
| C7 | Les « S-Combo memo » des guides ne sont **pas** des objets dans les tables de la ROM. Les 20 S-Combos ont leur propre table (`cf_mes_COMBO`) | Un memo apprend sans doute le combo directement. À vérifier en jeu, car ça décide si un memo peut devenir un objet Archipelago |
| C8 | Chaque zone de la carte du monde a un **code de carte** interne (ex. `kam01_00` = Kame House, `tut01_00` = Training Island) | Piste pour la phase 2 : chercher ce code (ou son numéro) en mémoire pour savoir où se trouve le joueur |

## 2026-10-23 — Phase 2 (carte mémoire)

| # | Décision / constat | Raison |
|---|---|---|
| C9 | **Correction de C5** : le numéro interne d'un objet n'est pas toujours son numéro de texte. Il faut passer par les tables de données (`Use_Item`…), voir `ram_map.md` §2 | Le texte n° 29 n'est pas utilisé, ce qui décale tous les objets suivants. Les identifiants du world devront venir des tables de données |
| D17 | Le client détectera l'ouverture d'un coffre grâce à son **drapeau** (bloc `0x0209F7E8`, bit allumé à l'instant de l'ouverture). Pour retirer l'objet d'origine (approche A), il regardera **quel objet vient d'augmenter** dans l'inventaire | Pas besoin de connaître à l'avance le contenu de chaque coffre. Le guide sert seulement à nommer les lieux |
| D18 | La liste complète des coffres du jeu (drapeau + contenu) sera tirée des scripts de carte `TreasureSet_*` (phase 6) plutôt que d'observations en jeu | Une seule extraction au lieu de rejouer chaque zone |
| D19 | Les photos mémoire se prennent avec `dump_ram.lua`, déclenché par les états de sauvegarde (`Shift+F<n>`) | Le moins de manipulations possible pour le joueur. Les fichiers `.State` ne sont pas exploitables (le cœur n'y garde que les pages modifiées) |
| D20 | Compteur d'objets reçus : **provisoirement** dans les 4 derniers octets du bloc de drapeaux (`0x0209FB44`), qui est enregistré dans la sauvegarde | Il survit à la sauvegarde et revient à la bonne valeur si le joueur recharge une ancienne partie. À confirmer (plus grand drapeau utilisé par le jeu) avant la partie avec les amis. Plan B : fichier côté client |
| D21 | Le client n'agit que si le code de carte (`0x020D226C`) est valide, et ne donne les objets que hors combat (`0x0209B236` ≠ `FF FF`) | Évite d'écrire pendant les logos, l'écran titre ou un combat |
| D22 | Expériences en jeu menées par Claude via la télécommande BizHawk (emplacements d'états 7, 8, 9 réservés à Claude ; 1, 2, 4 au joueur) | Le joueur ne veut pas faire les manipulations lui-même |

## 2026-10-23 — Phase 3 (world minimal)

| # | Décision / constat | Raison |
|---|---|---|
| C10 | Discord Archipelago vérifié par le joueur : personne ne travaille sur ce jeu. Seul un fil d'idées de 2025 existe (unknownCleric, 17/11/2025), qui propose en vérifications les coffres, les personnages, les Dragon Balls, les captures de l'Evil Containment Wave, les échanges de carottes. Il suggère comme objectifs Vegeta ou Broly (en boostant l'XP) | Pas de doublon. Idées à garder pour la phase 6 |
| D4bis | **Nom du jeu : « Dragon Ball Z - Attack of the Saiyans »** (tiret au lieu des deux-points) | Le nom sert de nom de fichier pour la doc ; « : » est interdit sous Windows. C'est la convention de « Castlevania - Circle of the Moon » |
| D23 | ID d'objet = 1000 × (catégorie + 1) + numéro interne ; ID de coffre = 100000 + n° de drapeau | Le client passe de l'ID à l'adresse mémoire par un simple calcul (`ram.inventory_address`, `ram.flag_position`) |
| D24 | Les 8 lieux s'appellent « Training Island Chest 1 » à « 8 » (ordre des drapeaux), et le pool contient les 8 objets d'origine sans les relier à un coffre précis | Le lien drapeau ↔ coffre n'est connu que pour 2 coffres. On renommera quand les scripts `TreasureSet` seront décodés |
| D25 | Objectif du world minimal : l'événement « Defeat Jackie Chun » (fin du prologue) | Seule zone couverte. La détection par le client reste à trouver (phase 4) |

## 2026-10-23 — Phase 4 (client minimal)

| # | Décision / constat | Raison |
|---|---|---|
| C11 | Essai réel réussi (seed à 2 joueurs, serveur WSL, BizHawk Client Windows, télécommande) : coffre ouvert hors connexion envoyé à la connexion ; objet reçu ajouté ; coffre ouvert en direct → check + objet d'origine retiré ; rechargement d'un ancien état → objets manquants redonnés une seule fois ; rechargement récent → aucun doublon ; objectif envoyé en arrivant en Ville est | Résultat attendu de la phase 4 (cahier des charges §9) |
| C12 | Limites connues de la v1 : un coffre ouvert sans client connecté laisse l'objet d'origine ; le message du jeu montre l'objet d'origine ; le joueur doit taper son nom de joueur (pas de patch de ROM) ; plafond de 99 par objet (choix prudent, limite réelle du jeu inconnue) | Approche A (D6). La plupart disparaîtront avec un patch (approche B, phase 9) |
| C13 | Le script de connexion de BizHawk n'accepte **qu'un seul client** : un ancien BizHawk Client resté ouvert bloque tout (« Connection timed out ») | Piège rencontré : un client ouvert à 19 h tenait la connexion. Noté dans le guide d'installation |
| D26 | Essais réels pilotés depuis WSL avec `tools/live_test.sh` : serveur dans WSL, client Windows lancé par l'interop en mode texte (`ArchipelagoLauncherDebug.exe "BizHawk Client" -- --nogui`), nom du joueur et commandes serveur passés par des tubes nommés | Aucune manipulation du joueur, sauf charger `connector_bizhawk_generic.lua` dans BizHawk |

## 2026-10-23 — Phase 5 (partie de test)

| # | Décision / constat | Raison |
|---|---|---|
| C14 | Partie de test réussie : seed à 2 joueurs (Aure = DBZ, Ami = APQuest simulé depuis la console du serveur avec `/send_location`). Joué par Claude via la télécommande depuis l'état 2 : 5 coffres ouverts en jeu → 5 checks, dont 1 objet envoyé à Ami (Key) ; objet d'origine retiré à chaque fois ; 2 objets reçus d'Ami ajoutés en direct (Petit haricot, Masque à gaz). Fin par le chargement de l'état 4 (prologue fini) : 3 coffres restants rattrapés, objectif validé, `collect` automatique, compteur = 8 = nombre d'objets reçus | Résultat attendu de la phase 5 (cahier des charges §9) |
| C15 | Emplacement physique de 5 drapeaux de coffre (l'objet d'origine reste à confirmer par les scripts) : 1400 = écran 1, coffre au sommet de l'arche (passage derrière, après les serpents) ; 1401 = écran 1, plateforme du haut à gauche ; 1402 = écran 1, derrière le rocher lumineux (tutoriel Ki) ; 1403 = écran 1, derrière le rocher brun de l'anneau ; 1404 = écran 2, derrière le rocher brun du chemin nord | Servira à nommer les lieux (D24) |
| D27 | Le second joueur des essais est simulé par le serveur (`/send_location <joueur> <lieu>`), sans client ni jeu à lancer | Zéro manipulation pour le joueur |
| C16 | Piège : un ordre mal formé arrêtait `remote.lua` (erreur Lua). Chaque ordre est maintenant exécuté dans un `pcall` et l'erreur est écrite dans le compte rendu. Si le script s'arrête quand même, il se relance sans le joueur : `luaclick.ps1 <ligne> toggle` (dans `dbz_research\`) sélectionne la ligne du script dans la console Lua et clique « Toggle Script », puis rend la main à la fenêtre d'avant | Le joueur ne veut pas de manipulations |

## 2026-10-24 — Phase 6 (extension à tout le jeu), étape 1 : tous les coffres

| # | Décision / constat | Raison |
|---|---|---|
| C17 | Les scripts `.sb` sont lisibles : code d'une machine à pile, avec les fonctions du jeu nommées (section 4) et les fonctions du script nommées (section 3). Instructions utiles : `13`/`14`/`15`/`16`–`1f` = empiler une valeur, `4a n` = appeler la fonction du jeu n, `46 n` = appeler la fonction n du script (format détaillé dans `extract_chests.py`) | Permet d'extraire les données du jeu sans jouer |
| C18 | **219 coffres** dans la ROM, tous créés par `CreateBox(…, objet, drapeau, 7)` ; code d'objet − 1 = 128 × catégorie + numéro interne. Les 8 coffres du prologue correspondent exactement à ce qu'on a vu en jeu | Liste complète : `research/chests.md` |
| D28 | Logique : une région par chapitre, en ligne droite. Chapitre 6+ : Masque à gaz ; 8+ : 1 Ki-Blast Fruit ; 13+ : 2 Ki-Blast Fruits. Chaque coffre est placé dans le chapitre où le guide DSR l'a ouvert (« Fin de jeu » = chapitre 15) | Le chapitre du guide est une condition suffisante prouvée : l'auteur avait à ce moment-là l'histoire et le niveau de Ki Blast nécessaires. Les rochers de niveau 2 (ch. 8, East Mt. Paozu) et 3 (ch. 13, Yemma Forest) sont sur le chemin de l'histoire. Description ROM du fruit : « augmente la taille max. de la jauge de tir hors combat » |
| D29 | Objets de progression : Masque à gaz et les 2 Ki-Blast Fruits des coffres (ch. 7 et 12). Bottes froides, Fourrure argentée : utiles seulement | Les sols dangereux se traversent en perdant des PV (DSR : « soignez-vous après le champ électrique ») ; le Masque à gaz est requis par choix de confort, car le chapitre 6 traverse un long sol gazé |
| D30 | 19 coffres absents du guide sont **mis de côté** (pas de lieu Archipelago, l'objet d'origine reste) : accès et chapitre inconnus. Dont 2 autres Ki-Blast Fruits (égouts `ges01`, château de Pilaf `pir05`) et un code d'objet inconnu (`snd06`, code 330) | Ne pas risquer un objet de progression dans un coffre peut-être inaccessible. À vérifier en jeu plus tard |
| D31 | Les 6 coffres des Ruines de la Ville est = option `east_city_ruins` (désactivée par défaut) | Il faut les 7 Dragon Balls et un vœu de Shenron |
| D32 | **Objectif** : drapeau d'histoire **1050** (scène `c1505_00`, qui suit le dernier combat contre Vegeta). Remplace la détection provisoire « arrivée en Ville est » (D25) | Méthode `SetScenarioCnt` validée sur le prologue (ram_map.md §4). ❓ Reste à voir le drapeau s'allumer en fin de partie |
| D33 | Noms des lieux : « <zone> <écran> - <objet d'origine> Chest » (ex. « Training Island 1 - Phoenix Feather Chest »), générés par `research/scripts/build_world_data.py` ; le fichier `worlds/dbz_aots/chest_data.py` est généré, jamais modifié à la main | Remplace les noms numérotés de D24. Une seule source pour les données |
| C19 | Pistes écartées pour l'objectif : `0x09B8C8` (« c0001_99 ») est une chaîne fixe du programme ; `0x0D226C` est le tampon « carte à charger », pas un nom de scène d'événement ; les tables `enemy_param`/`boss_param` sont compactées (pas lues) | Pour ne pas les refaire |
| C20 | Le compteur d'objets reçus (D20, drapeaux 6880–6911) reste loin des drapeaux utilisés : scripts ≤ 3854, jeu ≤ 4335 vus | D20 renforcée (🟡) |

## 2026-10-24 — Phase 6, étape 2 : objets à examiner et étapes d'histoire

| # | Décision / constat | Raison |
|---|---|---|
| C21 | **Correction de C18** : code d'objet − 1 = position dans l'inventaire en mémoire (objets clés à +0x130, pas à 128 × 3). Le code inconnu 330 du coffre `snd06` est la **Capsule vide** (objet clé n° 25), ce que dit le guide (Desert, 7e écran) : ce coffre rejoint le world | Seule la catégorie « objets clés » était fausse |
| C22 | Le **niveau** de tir de Ki vient de l'histoire : les scènes de fin du chapitre 6 (`c0609_00`) et du chapitre 12 (`c1206_00`) appellent `SetKidanLv(2)` puis `SetKidanLv(3)`. Le Ki-Blast Fruit agrandit la jauge. On ne sait pas si les gros rochers demandent aussi la jauge agrandie | La logique D28 (fruits exigés aux ch. 8 et 13) reste **sûre** : elle demande au moins autant que nécessaire. À simplifier si un essai en jeu montre que les fruits ne servent pas pour les rochers |
| C23 | 19 **objets à examiner** (tiroirs, étals, portes…) : `GetFlag(d)` → `GetItem(objet)` → `SetFlag(d)` avec un seul drapeau (3200–3233, plus 2590). Le guide confirme les emplacements (ex. 3200 = Fruit chance du tiroir de Kame House, déjà allumé avant l'île) | Nouveaux lieux sûrs : un drapeau par objet |
| D34 | 14 objets à examiner rejoignent le world (« <zone> <écran> - Hidden <objet> »), 5 sont mis de côté (pas de ligne DSR) | Même règle que les coffres (D30) |
| D35 | **Étapes d'histoire** = lieux « Prologue Cleared », « Chapter 1 Cleared » … « Chapter 14 Cleared », détectés par le drapeau de début du chapitre suivant (55, 110 … 1025), avec du remplissage dans le pool. Le client ne retire jamais d'objet pour ces lieux | 15 checks sûrs (méthode validée sur le prologue). Une scène peut donner un objet clé au même moment : il ne faut pas le prendre pour l'objet d'origine |
| C24 | Autres sources d'objets repérées, pas encore utilisées : échange de carottes (`wst03`, drapeaux 2626–2629), captures de l'onde de confinement (`god03`, 2620–2623), Bubbles (`kos02`, 2642–2645), pièges `Trap01` (`ges02`, `sna03`), objets clés d'histoire (scènes `cf1`, sans drapeau propre : à ne pas mélanger) | Pistes pour plus tard |
| D36 | Lieux « manquables » marqués **exclus** (jamais d'objet de progression, pour aucun joueur) : Autre Monde (King Yemma's Mansion, Princess Snake's House, King Kai's Planet, Yemma Forest) et Ruines de Nemuria | L'Autre Monde n'est accessible qu'aux ch. 9 et 13 puis en fin de jeu (LP Update 48) : un Ki-Blast Fruit oublié au ch. 9 bloquerait l'entrée du ch. 13. Nemuria n'est pas sur la carte du monde et aucune source ne parle d'y revenir |
| D37 | Groupes de lieux par zone (+ « Story ») pour les indices (`location_name_groups`) | Confort pour les joueurs (« !hint Kiwi Volcano ») |

## 2026-10-24 — Phase 6, étape 4 : multiplicateur d'expérience

| # | Décision / constat | Raison |
|---|---|---|
| C25 | Quêtes : `QuestAccept(n)` = `SetFlag(n, 1, 2)`, `QuestComplete(n)` = `SetFlag(n, 20, 2)`, mais les scripts de quête (`questNNN_MM`) sont surtout des dialogues ; pas de drapeau simple « quête finie » trouvé | Piste remise à plus tard |
| C26 | Fiches des personnages trouvées (ram_map.md §2). Essai (états 8–9 de Claude) : un combat ajoute le gain à l'expérience **et** le retire du compteur « exp. pour le niveau suivant » ; le niveau monte quand ce **compteur** passe sous zéro (excédent reporté), le total d'expérience n'est pas regardé (Krillin à 472 d'exp. reste niveau 2 si le compteur reste positif) | Base du multiplicateur |
| D38 | Option `experience_multiplier` (1 à 10, 1 = désactivée) : après chaque combat, le client ajoute (multiplicateur − 1) × le gain d'expérience et de PA de chaque personnage, en baissant le compteur d'autant, **sans jamais le faire descendre sous 1** ; le surplus est gardé en réserve et ajouté après les combats suivants. Le jeu fait lui-même les montées de niveau (stats, techniques) | On n'écrit jamais un état que le jeu ne saurait pas produire. Un gain n'est compté que s'il est cohérent (exp. + = compteur −, ou niveau +1), pour ignorer les chargements d'état |
| C27 | `remote.lua` sait maintenant écrire (`write`), pour les expériences dans les emplacements 7–9 de Claude seulement. Piège : deux « Toggle Script » coup sur coup ont laissé la console Lua dans un état bizarre (contrôles à −32000). Remède : `winlayout.ps1` (réduire puis restaurer la console), puis **un seul** `luaclick.ps1 3 toggle` | Pour relancer la télécommande sans le joueur |
| C28 | Essai réel de l'option (multiplicateur 3, client connecté, état 8 de Claude) : PA triplés (+15 → +45) ; expérience ajoutée jusqu'à laisser le compteur à 1 ; au combat suivant, le jeu fait passer Krillin niv. 2 → 3 et Tien 4 → 5, avec un compteur cohérent (Tien : 494 − 116 = 378, puis 140 après l'ajout) | D38 validée en conditions réelles |

## 2026-10-24 — Phase 7 : tests automatiques

| # | Décision / constat | Raison |
|---|---|---|
| D39 | `tools/mass_seeds.py` : chaque seed (numéro = graine, donc reproductible) mélange 1 à 3 joueurs DBZ aux options tirées au hasard (`east_city_ruins`, `experience_multiplier`, `accessibility` full/minimal, `progression_balancing`) et 0 à 2 joueurs APQuest/ChecksFinder. `Generate.py` tourne **en entier** (spoiler 2), car avec `--skip_output` Archipelago ne vérifie ni que la partie est gagnable ni que tous les lieux sont accessibles. Échec = code de sortie ≠ 0 ou avertissement « Location Accessibility requirements not fulfilled » | Tester la logique dans des parties variées, pas seulement sur une graine |
| C29 | Seeds 1 à 1000 : **1000/1000 réussies** (25 min avec 8 tâches). Tests du world : 42 tests, 710 sous-tests, tous OK | Phase 7 validée |
