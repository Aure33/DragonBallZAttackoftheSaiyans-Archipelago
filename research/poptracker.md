# Pack PopTracker : étude et prototype (bloc 5)

PopTracker est un programme qui affiche les lieux d'une partie, avec ceux déjà fouillés et ceux atteignables. Il peut
se connecter au serveur Archipelago pour se mettre à jour tout seul (« autotracking »).

## Format d'un pack (doc officielle : `doc/PACKS.md` et `doc/AUTOTRACKING.md` du dépôt black-sliver/PopTracker)
- `manifest.json` : nom, `game_name`, `package_uid`, `package_version`, variantes avec le drapeau `ap`.
- `items/*.json` : objets suivis (`toggle`, `consumable` avec `max_quantity`, `progressive`…), chacun avec un `code`.
- `maps/*.json` : images de carte. `locations/*.json` : zones posées sur une carte (`map_locations`), avec des
  `sections` (un lieu chacune) et des `access_rules` (« a,b » = a ET b ; deux entrées = OU ; `code:2` = au moins 2).
- `layouts/*.json` : disposition (`tracker_default`, `tracker_broadcast`).
- `scripts/init.lua` charge le tout. Autotracking : objet global `Archipelago` avec `AddClearHandler(nom, f(slot_data))`,
  `AddItemHandler(nom, f(index, item_id, item_name, player))`, `AddLocationHandler(nom, f(location_id, name))`.
- Schémas JSON officiels livrés avec PopTracker (`poptracker/schema/packs`, version stricte dans `strict/`).

## Prototype (2026-10-24)
`tools/build_poptracker.py` **génère** le pack depuis le world (lieux, ID, règles), dans `build/poptracker/dbz_aots`
(+ `.zip`) ; `--deploy` le copie dans les packs de PopTracker. Rien n'est tiré de la ROM : la « carte » est un tableau
dessiné par le script (une case par chapitre, un point par zone du chapitre) et les icônes sont des pastilles.

Vérifié :
- les 5 fichiers JSON passent les schémas **stricts** de PopTracker ;
- PopTracker 0.35.3 charge le pack (`--load-pack ap_dbz_aots`) : 62 zones, 230 lieux ; prologue à ch. 5 en vert,
  ch. 6 et suivants en rouge sans Masque à gaz (même logique que `rules.py`).

Pas encore vérifié :
- le suivi automatique par Archipelago (le bouton « AP » demande un clic dans la fenêtre ; les options en ligne de
  commande `--ap-host`/`--ap-slot` n'existent pas dans la 0.35.3 installée, le programme quitte avec le code 1).

## Ce qu'il reste pour un bon pack
1. Essai du suivi automatique (clic sur « AP », hôte `localhost:38281`, joueur `Aure`) avec une partie de test.
2. Lire `slot_data` dans `onClear` : cacher les chapitres après `goal_chapter`, les objets cachés et les fins de
   chapitre quand leurs options sont coupées (`visibility_rules` ou codes d'options).
3. Objets clés suivis quand le bloc 2 en aura mélangé (Clé du champ de neige…).
4. Vraies cartes de zones : demande des captures d'écran et la position de chaque coffre (`CreateBox(x, y)` dans
   les scripts). **Question de droits** : ne pas publier d'images du jeu sans y réfléchir ; le tableau dessiné suffit
   pour jouer.
5. Publication : dépôt GitHub du pack + `versions_url` pour les mises à jour automatiques.
