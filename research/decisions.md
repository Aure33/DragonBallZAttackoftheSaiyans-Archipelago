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
