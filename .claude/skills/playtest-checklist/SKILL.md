---
name: playtest-checklist
description: Liste de vérification d'une vraie partie Archipelago avec des amis (phase 8) pour DBZ Attack of the Saiyans : préparation, génération, hébergement, connexion, pendant la partie, après. À utiliser avant et pendant une partie multijoueur réelle.
---

# Partie avec les amis : liste de vérification

Pour chaque point : on le coche quand il est **vu**, pas supposé. Les problèmes vont dans
`research/decisions.md` (constat « C… » avec ce qui s'est passé exactement).

## 1. Avant (la veille)
- [ ] Tests du world verts et `tools/mass_seeds.py --count 1000` à 1000/1000 sur la version qu'on va jouer.
- [ ] `tools/build_apworld.sh --deploy` : le `.apworld` de cette version est dans `custom_worlds` du PC qui génère.
- [ ] Même version d'Archipelago chez tous (0.6.8 ou plus) ; ceux qui ont un jeu « non officiel » envoient leur
      `.apworld` à celui qui génère.
- [ ] Chaque joueur a rempli son `.yaml` (modèle : `examples/Dragon Ball Z - Attack of the Saiyans.yaml`, ou
      « Generate Template Options » du Launcher). Noms de joueurs **différents**, 16 caractères maximum.
- [ ] Pour DBZ : ROM EU `BRPP`, BizHawk 2.10+ cœur melonDS, une **sauvegarde neuve** (début de partie) et un état
      de sauvegarde de secours avant de commencer.
- [ ] Options à décider ensemble : `goal` (chapitre court ou Broly), `death_link` (tout le monde d'accord ?),
      `experience_multiplier` (2 ou 3 conseillé en multijoueur), `release_mode`/`collect_mode` du serveur.

## 2. Génération
- [ ] Tous les `.yaml` dans un dossier → `Generate.py` (ou « Generate » du Launcher) → `AP_xxx.zip`.
- [ ] Lire le spoiler : pas d'avertissement, objets de DBZ chez les autres et inversement.
- [ ] Hébergement : envoyer le `.zip` sur archipelago.gg (« Host Game ») **ou** `MultiServer.py` en local avec le
      port 38281 ouvert. À vérifier la première fois : archipelago.gg accepte-t-il une partie avec un world non
      officiel ? (Le serveur utilise le paquet de données embarqué ; à confirmer en vrai.)

## 3. Connexion (chaque joueur DBZ)
- [ ] BizHawk ouvert, ROM chargée, `connector_bizhawk_generic.lua` chargé (un seul BizHawk Client ouvert).
- [ ] BizHawk Client → adresse du serveur → nom du joueur : le client dit qu'il est connecté au jeu.
- [ ] Ouvrir le 1er coffre de l'île d'entraînement : le check part, l'objet d'origine disparaît de l'inventaire.

## 4. Pendant la partie
- [ ] Un objet reçu arrive hors combat (message du client) et apparaît dans l'inventaire.
- [ ] Ki-Blast Fruits : les **utiliser** depuis le menu Objets ; Masque à gaz : l'**équiper**.
- [ ] `key_items` : la Clé du champ de neige / le Sous-marin / le Truc de Bubbles n'apparaissent qu'une fois reçus.
- [ ] DeathLink (si activé) : un Game Over envoie une mort ; une mort reçue fait perdre le combat suivant.
- [ ] Sauvegarder en jeu régulièrement (le compteur d'objets reçus est dans la sauvegarde).
- [ ] Noter l'heure et la zone de tout problème (objet pas reçu, check pas envoyé, blocage d'histoire).

## 5. Fin et après
- [ ] But atteint : le serveur affiche « … has completed their goal » (fin du ch. choisi, ou Broly : scène d'après
      le combat).
- [ ] `!collect` / `!release` se comportent comme prévu.
- [ ] Rapport dans `research/decisions.md` : durée, options, problèmes (avec heure/zone), idées d'amélioration.
