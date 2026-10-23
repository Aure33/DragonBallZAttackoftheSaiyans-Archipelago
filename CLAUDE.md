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
- **Phase 0 — Installation : terminée (2026-10-23).** Phase suivante : 1 — Recherche du contenu (à lancer avec l'accord de l'utilisateur). Tableau des phases : cahier des charges, §9.
- Vérifié : dépôt GitHub privé, sources d'Archipelago 0.6.8 + venv dans WSL, lien symbolique du world vu par le chargeur, seed générée, `test/general` qui passe (376 tests) ; Archipelago Windows en 0.6.8 ; ROM DBZ lancée dans BizHawk ; client BizHawk connecté au script Lua (« No handler was found » : normal sans world).
- Disponible : état de sauvegarde BizHawk en début de partie (`BizHawk…\NDS\State\Dragon Ball Z Attack of the Saiyans.MelonDS.QuickSave1.State`).
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

# Tests limités à notre world (à vérifier en phase 3, quand le world existera)
AP_TEST_WORLDS=dbz_aots .venv/bin/python -m pytest -q -n auto

# Construire le .apworld (sortie : build/apworlds/dbz_aots.apworld), puis le copier côté Windows
.venv/bin/python Launcher.py "Build APWorlds" -- "Dragon Ball Z: Attack of the Saiyans"
cp build/apworlds/dbz_aots.apworld /mnt/c/ProgramData/Archipelago/custom_worlds/
```

## Conventions
- **Pas d'invention** : aucune adresse, aucun nom d'objet/zone/quête, aucune API sans source. Sinon on le dit et on propose comment vérifier.
- Sources : chaque donnée de jeu dans [research/game_data.md](research/game_data.md), chaque adresse dans [research/ram_map.md](research/ram_map.md), avec la façon dont elle a été trouvée.
- Langues : code, noms d'objets/lieux et docs du world en **anglais** ; recherche, journal, ce fichier en **français**. Chaque donnée de jeu a un nom FR (écran) et EN (guides).
- World : `worlds/dbz_aots/`, nom du jeu `Dragon Ball Z: Attack of the Saiyans`. Imports internes relatifs (`from .items import …`), imports d'Archipelago absolus (`from worlds.AutoWorld import World`).
- Python typé, style Archipelago (`docs/style.md` du clone). Toutes les adresses mémoire dans `ram.py`, commentées.
- Vérifier l'API dans le clone 0.6.8, pas de mémoire.
- Git : petits commits clairs. **Jamais** de ROM, sauvegarde, état de sauvegarde ou extrait de la ROM dans le dépôt (voir `.gitignore`).
- Projets tiers sans licence (randomizer, traductions) : lire pour apprendre, ne pas copier de code, revérifier les données.
- À chaque fin de phase : mettre à jour ce fichier, `ram_map.md`, `game_data.md`, `decisions.md`.

## Agents et skills
Créés au moment où leur phase arrive (cahier des charges §11) :
- Phases 1–2 : agents `game-data-researcher`, `ram-researcher` ; skill `ram-diff`.
- Phase 3+ : `apworld-dev`, `client-dev`, `logic-reviewer`, `tester` ; skills `add-location`, `add-item`, `build-and-test`, `playtest-checklist`.
