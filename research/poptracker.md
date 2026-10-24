# Pack PopTracker (bloc 5)

PopTracker est un programme qui affiche les lieux d'une partie, avec ceux déjà fouillés et ceux atteignables. Il peut
se connecter au serveur Archipelago pour se mettre à jour tout seul (« autotracking »).

## Format d'un pack (doc officielle : `doc/PACKS.md` et `doc/AUTOTRACKING.md` du dépôt black-sliver/PopTracker)
- `manifest.json` : nom, `game_name`, `package_uid`, `package_version`, variantes avec le drapeau `ap`.
- `items/*.json` : objets suivis (`toggle`, `consumable` avec `max_quantity` et `initial_quantity`…), chacun avec un
  `code`.
- `maps/*.json` : images de carte. `locations/*.json` : lieux posés sur une carte (`map_locations`), avec des
  `sections`, des `access_rules` (« a,b » = a ET b ; deux entrées = OU ; `code:2` = au moins 2) et des
  `visibility_rules` (même syntaxe : le lieu est caché si aucune n'est vraie).
- `layouts/*.json` : disposition (`tracker_default`, `tracker_broadcast`, conteneurs `dock`, `tabbed`, `map`).
- `scripts/init.lua` charge le tout. Autotracking : objet global `Archipelago` avec `AddClearHandler(nom, f(slot_data))`,
  `AddItemHandler(nom, f(index, item_id, item_name, player))`, `AddLocationHandler(nom, f(location_id, name))`.
- Schémas JSON officiels livrés avec PopTracker (`poptracker/schema/packs`, version stricte dans `strict/`).
- Raccourcis (README de PopTracker) : F5 recharger, Ctrl+F5 recharger depuis le disque, F11 cacher les lieux faits.

## Pack actuel (2026-10-24) : vraies cartes du jeu
Construit en deux temps, pour que les images du jeu ne soient **jamais** dans le dépôt :
1. `research/.venv/bin/python research/scripts/extract_tracker_assets.py "<ROM>"` → `build/tracker_assets/` :
   l'image de chaque écran qui contient un lieu (116 écrans) et `positions.json` (drapeau → écran, x, y).
2. `~/Coding/ArchipelagoRom/Archipelago/.venv/bin/python tools/build_poptracker.py [--deploy]` → le pack, généré
   depuis le world (lieux, ID, règles) : `build/poptracker/dbz_aots/` (+ `.zip`).

Contenu :
- un onglet par zone (35), rangés par partie de l'histoire (« Prologue - Ch. 4 », « Ch. 5 - 8 »…) ; dans chaque
  onglet, tous les écrans de la zone avec leur nom, et un point par coffre / objet à examiner, à sa place exacte ;
- un onglet « Story » : fins de chapitre et scènes qui donnent un objet clé ;
- en haut : Masque à gaz, Ki-Blast Fruit (×3), Clé du champ de neige, Sous-marin, Truc de Bubbles ;
- `slot_data` (`hidden_items`, `chapter_checks`, `key_items`, `east_city_ruins`, `goal_chapter`) cache ce que la
  partie ne mélange pas ; `key_items` coupé = les trois objets clés comptent comme acquis (l'histoire les donne).

Décodage des cartes (decisions.md C53) : fichiers `fld/map/<zone>/<carte>.map`, en-tête « dMAP » (largeur et
hauteur en carreaux de 8 px), palette 256 couleurs, image 8 bits compressée (fonction ARM `0x0200A6C0`, réécrite dans
`research/scripts/fieldmap.py`). Les coordonnées des scripts (`CreateBox`, `Point`, `Line`) sont des pixels de
cette image. Écran `skr06` : pas de fichier de carte, une case grise le remplace. Carte du monde : `worldmap.map` se
décode aussi, mais la position des zones dessus n'a pas été trouvée (pas d'onglet « monde » pour l'instant).

Vérifié :
- les 5 fichiers JSON passent les schémas **stricts** de PopTracker ;
- PopTracker 0.35.4 charge le pack (variante « Maps ») ; les points tombent sur les coffres (Tour du Muscle) ;
- suivi automatique : connexion à un serveur de test (`localhost:38281`, joueur `Aure`) ; objets reçus allumés
  (compteur du Ki-Blast Fruit), lieu coché passé en gris, lieux du ch. 15 cachés avec `goal_chapter: 12`.

## Ce qui reste
1. Onglet « monde » (carte du monde décodée) : trouver ou relever en jeu la position de chaque zone.
2. Vraies icônes d'objets (dossier `menu/icon` de la ROM, format à décoder).
3. Distribution aux amis : chacun peut générer le pack avec sa ROM (Python + ndspy + Pillow), ou recevoir le pack
   en privé ; ne pas publier les images du jeu.
