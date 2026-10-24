# Guide d'installation de Dragon Ball Z - Attack of the Saiyans

Ce world mélange les coffres de toute l'histoire (voir la page du jeu pour le détail).

## Logiciels nécessaires

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.8 ou plus récent
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.10 ou plus récent (testé avec la 2.11.1)
- Votre propre copie de la version européenne de Dragon Ball Z: Attack of the Saiyans (code du jeu `BRPP`)

## Installation

1. Installez `dbz_aots.apworld` : Launcher Archipelago > « Install APWorld » (ou copiez-le dans le dossier
   `custom_worlds` de votre installation d'Archipelago).
2. Générez une partie avec un fichier YAML pour « Dragon Ball Z - Attack of the Saiyans ». Pour obtenir un modèle
   avec toutes les options et leur description, ouvrez le Launcher et cliquez sur « Generate Template Options »
   (après l'étape 1). Seule la personne qui génère la partie a besoin du `.apworld` ; les autres joueurs non.

## Se connecter

La génération produit un fichier patch pour vous, `AP_..._<votre nom>.apdbzaots` (dans le zip de sortie, ou envoyé
par la personne qui héberge). Il ne modifie pas le jeu : il permet seulement au BizHawk Client de tout lancer.

1. Double-cliquez sur le fichier `.apdbzaots` (si Windows demande avec quel programme l'ouvrir, choisissez le
   Launcher Archipelago), ou ouvrez le Launcher, cliquez sur « Open Patch » et choisissez-le.
2. La première fois, indiquez où se trouve votre ROM (et `EmuHawk.exe` s'il n'est pas encore réglé). La ROM est
   vérifiée : ce doit être la version européenne (code `BRPP`, révision 0).
3. BizHawk démarre avec la ROM et le script de connexion, et le BizHawk Client s'ouvre. Tapez l'adresse du serveur
   (`adresse:port`) en haut et connectez-vous, puis tapez votre nom de joueur (le `name` de votre YAML).

Sans le fichier patch : ouvrez la ROM dans BizHawk (cœur melonDS), chargez `data/lua/connector_bizhawk_generic.lua`
de votre installation d'Archipelago dans `Outils > Console Lua`, puis ouvrez le BizHawk Client depuis le Launcher et
connectez-vous.

Un seul BizHawk Client peut parler à BizHawk à la fois : fermez d'abord toute autre fenêtre de BizHawk Client.

## Votre sauvegarde

La ROM obtenue avec le fichier patch (`AP_..._<votre nom>.nds`, à côté du fichier patch) a sa propre sauvegarde dans
BizHawk : vos autres sauvegardes du jeu ne sont pas touchées. Commencez une nouvelle partie dedans, et rouvrez le même
fichier patch à chaque fois que vous jouez à ce multiworld.

Recharger votre dernière sauvegarde (après un Game Over, par exemple) ne pose pas de problème : les coffres rouverts
ne sont pas envoyés deux fois, et le client vous rend les objets reçus depuis cette sauvegarde.

## Tracker

Un pack PopTracker avec les cartes du jeu peut être construit à partir de votre propre ROM : voir le README du dépôt
du world.

## Limites connues

- Les coffres et les objets cachés affichent toujours leur objet d'origine ; le client le retire aussitôt de votre
  inventaire. Si vous en prenez un pendant que le client n'est pas connecté, vous gardez cet objet d'origine.
- Les objets reçus arrivent quand vous êtes sur le terrain ; pendant un combat, ils attendent la fin du combat.
- Les objets reçus sont seulement ajoutés à l'inventaire : utilisez vous-même les Ki-Blast Fruits et équipez le
  Masque à gaz.
- Avec `key_items`, le client ne laisse la Clé du champ de neige, le Sous-marin et le Truc de Bubbles dans
  l'inventaire qu'une fois reçus : les scènes qui les donnent dans le jeu d'origine ne les donnent plus.
- Avec DeathLink, ne chargez jamais une ancienne sauvegarde ou un état de sauvegarde pour annuler une défaite : le
  client n'envoie une mort que quand le jeu redémarre après un Game Over.
