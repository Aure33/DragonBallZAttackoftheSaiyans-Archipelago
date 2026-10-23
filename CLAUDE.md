# DBZ: Attack of the Saiyans → Archipelago

## But
Ajouter *Dragon Ball Z: Attack of the Saiyans* (Nintendo DS, 2009) à Archipelago, avec le client BizHawk générique.
Usage personnel d'abord (dépôt privé), mais code propre pour une publication possible.
Cahier des charges complet : [Prompt_archipelago_dbz.md](Prompt_archipelago_dbz.md). Décisions : [research/decisions.md](research/decisions.md).

## Utilisateur
- Développeur Python à l'aise (Git, tests, CI) ; **débutant** sur Archipelago, la rétro-ingénierie, la mémoire DS, le Lua.
- Explications **courtes et simples, en français**. Un mot technique est défini en une phrase la première fois.
- Joue au jeu **en français** (ROM EU). Il l'a déjà fini une fois.
- Les étapes sont découpées selon un **résultat testable**, jamais selon une durée.
- Quand il doit faire quelque chose (jouer, état de sauvegarde, lire une valeur) : instructions numérotées, puis on attend son retour.

## État actuel
- **Phase 7 — Tests : terminée (2026-10-24).** `tools/mass_seeds.py` (D39) : 1000 seeds variées sur 1000 réussies (1 à 3 joueurs DBZ aux options au hasard + APQuest/ChecksFinder). Prochaine : phase 8 (partie avec les amis), sur feu vert de l'utilisateur.
- **Phase 6 — Extension : terminée (2026-10-24).** Tableau des phases : cahier des charges, §9.
  - Étape 1 faite : world 0.3.0 = 200 coffres de toute l'histoire (194 + 6 en option `east_city_ruins`), logique par chapitre (Masque à gaz, Ki-Blast Fruit ×2), objectif = drapeau 1050 (après le dernier Vegeta). 32 tests du world, 40 seeds générées sans échec. Décisions D28–D33.
  - Étape 2 faite : world 0.4.0 = 224 lieux par défaut (195 coffres + 14 objets à examiner + 15 fins de chapitre), 230 avec l'option. 34 tests du world, 40 seeds sans échec. Décisions D34–D35, constats C21–C24.
  - Données : `research/chests.md` et `worlds/dbz_aots/location_data.py` sont **générés** (`extract_chests.py` puis `build_world_data.py`) ; ne pas les modifier à la main.
  - Étape 3 faite : zones manquables exclues de la progression (D36), groupes de lieux (D37). 96 tests, 60 seeds sans échec.
  - Étape 4 faite : option `experience_multiplier` (1–10, D38), validée en jeu (exp. et PA triplés, montées de niveau faites par le jeu). World 0.5.0, 103 tests.
  - À faire (demande de l'utilisateur, 2026-10-24) : enrichir les options du YAML : quoi mélanger (coffres, objets cachés, fins de chapitre…), condition de victoire, DeathLink, etc. Le modèle YAML est généré par Archipelago à partir de `options.py`.
  - Reste : 23 lieux mis de côté à vérifier, dons à plusieurs drapeaux (carottes, captures…), DeathLink ?, voir le drapeau 1050 en jeu.
- **Phase 5 — Test réel : terminée (2026-10-23).** Seed DBZ + APQuest (2e joueur simulé par `/send_location` du serveur), jouée par Claude via la télécommande : checks, objets envoyés et reçus, objectif, `collect`, aucun doublon (`research/decisions.md`, C14).
- **Phase 4 — Client minimal : terminée (2026-10-23).**
  - `client.py` : coffres → checks, retrait de l'objet d'origine, objets reçus hors combat, compteur dans la sauvegarde, objectif (arrivée en Ville est). 22 tests du world. Essai réel réussi (`research/decisions.md`, C11). World 0.2.0 installé côté Windows.
- **Phase 3 — World minimal : terminée (2026-10-23).**
  - `worlds/dbz_aots` : Île d'entraînement, 8 coffres, objectif « Defeat Jackie Chun », 15 tests qui passent ; `.apworld` construit et testé (seed à 3 joueurs avec ChecksFinder et APQuest).
  - Discord vérifié : personne ne travaille sur ce jeu.
- **Phase 2 — Carte mémoire : terminée (2026-10-23).**
  - `ram_map.md` : en-tête ROM, inventaire, zénis, drapeaux (dont les 8 coffres de l'île), code de carte, combat, emplacement provisoire du compteur.
- **Phase 1 — Recherche du contenu : terminée (2026-10-23).**
  - `game_data.md` : 40 zones, ~240 objets par zone (guide DSR), 42 boss, noms FR tirés de la ROM ; prologue vérifié en jeu (✅).
  - `rom_names.md` : noms officiels EN/US/FR extraits de la ROM (objets, capsules, objets clés, techniques, lieux, personnages).
- **Phase 0 — Installation : terminée (2026-10-23).**
- Vérifié : dépôt GitHub privé, sources d'Archipelago 0.6.8 + venv dans WSL, lien symbolique du world vu par le chargeur, seed générée, `test/general` qui passe (376 tests) ; Archipelago Windows en 0.6.8 ; ROM DBZ lancée dans BizHawk ; client BizHawk connecté au script Lua (« No handler was found » : normal sans world).
- États de sauvegarde BizHawk (`BizHawk-2.11.1-win-x64\NDS\State\Dragon Ball Z Attack of the Saiyans.MelonDS.QuickSave<N>.State`, `Shift+F<N>` = sauver, `F<N>` = charger) :
  - 1 : Kame House, début de partie (réenregistré le 2026-10-23 à 19h41) ;
  - 2 : juste avant d'entrer dans l'Île d'entraînement ;
  - 3 : **manquant** (devait être devant le 1er coffre) → à refaire au début de la phase 2 depuis l'état 2 ;
  - 4 : après Jackie Choun, prologue terminé, sauvegarde en jeu faite (copie de secours dans `dbz_research\backup\`) ;
  - 7, 8, 9 : réservés à Claude (télécommande) ; 5, 6 : photos manuelles.
  - ⚠️ Charger un état remet aussi la sauvegarde en jeu de ce moment-là : fermer la ROM peut écraser `SaveRAM` avec une version plus ancienne. Copie de la sauvegarde d'après prologue dans `dbz_research\backup\`.
  - Sauvegarde en jeu : `NDS\SaveRAM\Dragon Ball Z Attack of the Saiyans.SaveRAM` (8 Ko).
- **Rappel avant la phase 3** : vérifier sur le Discord Archipelago que personne ne travaille déjà sur ce jeu.

## Environnement
| Élément | Emplacement / version |
|---|---|
| Ce dépôt | `~/Coding/ArchipelagoRom/DragonBallZAttackoftheSaiyans-Archipelago` (WSL2 Ubuntu 24.04) |
| Sources Archipelago | `~/Coding/ArchipelagoRom/Archipelago` (tag `0.6.8`, venv `.venv`, Python 3.12.3) |
| Lien du world | `Archipelago/worlds/dbz_aots` → `ce dépôt/worlds/dbz_aots` (masqué via `.git/info/exclude` du clone) |
| Archipelago Windows | `C:\ProgramData\Archipelago` (= `/mnt/c/ProgramData/Archipelago`), apworlds dans `custom_worlds\` |
| BizHawk | 2.11.1, `C:\Users\Aurelien\Desktop\archipelago\BizHawk-2.11.1-win-x64\EmuHawk.exe`, cœur melonDS |
| ROM | EU `BRPP` rév. 0, `C:\Users\Aurelien\Desktop\Jeu\SAve jeu\Rom DS\Dragon Ball Z Attack of the Saiyans.nds` — **jamais dans Git** |

BizHawk et son script Lua tournent sous **Windows**. Le script n'écoute que sur `localhost` côté Windows, donc le client BizHawk tourne aussi sous Windows (Archipelago installé), avec le `.apworld` copié dans `custom_worlds`. Code, tests et génération : dans WSL.

## Commandes utiles
Depuis `~/Coding/ArchipelagoRom/Archipelago` :
```bash
# Générer une seed (YAMLs dans un dossier)
.venv/bin/python Generate.py --player_files_path <dossier_yaml> --outputpath <dossier_sortie>

# Tests généraux d'Archipelago
.venv/bin/python -m pytest test/general -q -n auto

# Tests limités à notre world (+ tests génériques appliqués au world) — voir le skill build-and-test
AP_TEST_WORLDS=dbz_aots .venv/bin/python -m pytest -q -n auto -p no:cacheprovider

# Recherche : extraire les noms officiels (EN/US/FR) de la ROM -> research/rom_names.md
# (depuis ce dépôt ; environnement research/.venv avec ndspy)
research/.venv/bin/python research/scripts/extract_rom_names.py "/mnt/c/Users/Aurelien/Desktop/Jeu/SAve jeu/Rom DS/Dragon Ball Z Attack of the Saiyans.nds"

# Coffres et drapeaux d'histoire depuis la ROM -> research/chests.md + worlds/dbz_aots/chest_data.py
(cd research/scripts && ../.venv/bin/python extract_chests.py "<ROM>" > /dev/null && ../.venv/bin/python extract_story_flags.py "<ROM>")
python3 research/scripts/build_world_data.py

# Télécommande BizHawk (remote.lua doit tourner dans la console Lua de BizHawk)
python3 research/scripts/remote.py "shot ecran" "read 0CC398 8"   # capture -> dbz_research/remote/ecran.png

# Construire le .apworld (build/apworlds/dbz_aots.apworld) ; --deploy le copie aussi côté Windows
<ce dépôt>/tools/build_apworld.sh --deploy
```

## Essai du client en conditions réelles
Prérequis : BizHawk ouvert avec la ROM, `remote.lua` **et** `connector_bizhawk_generic.lua` chargés dans la console Lua,
**aucun autre BizHawk Client ouvert** (le script de connexion n'accepte qu'un client).
```bash
tools/build_apworld.sh --deploy                     # world à jour côté Windows
# générer une seed (skill build-and-test), puis, chacun en arrière-plan :
tools/live_test.sh server <dossier>/AP_xxx.archipelago
tools/live_test.sh client
tools/live_test.sh to-client "Aure"                 # nom du joueur, quand le client le demande
tools/live_test.sh to-server "/send Aure Gas Mask"  # faire recevoir un objet
tools/live_test.sh to-server "/send_location Ami Top Middle Chest"  # simuler l'autre joueur qui ouvre un coffre
tools/live_test.sh logs
python3 research/scripts/remote.py "read 0CC398 2"  # vérifier la mémoire
```
À la fin : arrêter client et serveur, puis **recharger l'état du joueur** (ex. état 4) pour effacer les objets de test.

## Conventions
- **Pas d'invention** : aucune adresse, aucun nom d'objet/zone/quête, aucune API sans source. Sinon on le dit et on propose comment vérifier.
- Noms officiels du jeu (EN EU / US / FR) : [research/rom_names.md](research/rom_names.md), extraits de la ROM. Les noms du world = colonne EN (EU).
- Sources : chaque donnée de jeu dans [research/game_data.md](research/game_data.md), chaque adresse dans [research/ram_map.md](research/ram_map.md), avec la façon dont elle a été trouvée.
- Langues : code, noms d'objets/lieux et docs du world en **anglais** ; recherche, journal, ce fichier en **français**. Chaque donnée de jeu a un nom FR (écran) et EN (guides).
- World : `worlds/dbz_aots/`, nom du jeu `Dragon Ball Z - Attack of the Saiyans` (tiret, pas de « : »). ID objet = 1000 × (catégorie + 1) + numéro interne ; ID coffre = 100000 + drapeau. Imports internes relatifs (`from .items import …`), imports d'Archipelago absolus (`from worlds.AutoWorld import World`).
- Python typé, style Archipelago (`docs/style.md` du clone). Toutes les adresses mémoire dans `ram.py`, commentées.
- Vérifier l'API dans le clone 0.6.8, pas de mémoire.
- Git : petits commits clairs. **Jamais** de ROM, sauvegarde, état de sauvegarde ou extrait de la ROM dans le dépôt (voir `.gitignore`).
- Projets tiers sans licence (randomizer, traductions) : lire pour apprendre, ne pas copier de code, revérifier les données.
- À chaque fin de phase : mettre à jour ce fichier, `ram_map.md`, `game_data.md`, `decisions.md`.

## Agents et skills
Créés au moment où leur phase arrive (cahier des charges §11), dans `.claude/agents/` et `.claude/skills/` :
- Recherche : agents `game-data-researcher`, `ram-researcher` ; skill `ram-diff`.
- World : agents `apworld-dev`, `logic-reviewer`, `tester` ; skills `build-and-test`, `add-location`, `add-item`.
- Client : agent `client-dev`.
- À venir : skill `playtest-checklist` (phase 8).
