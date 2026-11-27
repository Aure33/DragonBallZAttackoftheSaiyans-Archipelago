# À corriger plus tard

Retours de la première partie à plusieurs (du 22 au 27 novembre 2026, room archipelago.gg avec TUNIC, XCOM 2,
Minecraft et Hollow Knight). Bilan général : la partie s'est bien passée. Broly a été battu, l'objectif a été validé,
et la `release` automatique a envoyé tous les objets restants aux autres joueurs.

Rien n'est corrigé ici : la liste sert de point de départ pour plus tard.

---

## 1. PopTracker : disponibilité des lieux fausse (surtout derrière les objets cassables)

**Constat de l'utilisateur.** Le pack se trompe dans les deux sens :
- il montre comme accessibles des lieux qu'on ne peut pas encore atteindre ;
- il montre comme inaccessibles des lieux qu'on peut déjà atteindre.

La cause principale semble être les **objets cassables de niveau 1, 2 ou 3**. Ce sont des rochers et des obstacles
qu'il faut détruire avec le tir de Ki chargé : il faut maintenir B, et le tir monte d'un niveau à chaque Ki-Blast
Fruit.

**Ce qu'on sait déjà :**
- Le niveau du tir de Ki est l'octet `0x09F7CB` (C50, `ram_map.md`).
- Chaque objet cassable a un niveau, donné par le 5e argument de `SetBreak` dans les scripts des cartes (C50). Par
  exemple, le coffre 1431 de la Tour du Muscle 6 est caché sous un rocher de niveau 1.
- La logique du world raisonne **par chapitre**, pas par lieu (`worlds/dbz_aots/rules.py`) :
  - à partir du chapitre 8 : 1 Ki-Blast Fruit ;
  - à partir du chapitre 13 : 2 Ki-Blast Fruit.
- Le pack reprend exactement ces règles par chapitre (`CHAPTER_RULES` dans `tools/build_poptracker.py`). Il ne sait
  donc pas qu'**un lieu précis** est derrière un objet cassable d'un certain niveau.

**Pistes :**
1. Extraire de la ROM, pour chaque carte, les objets cassables (position, niveau). Le script `SetBreak` /
   `BreakObjSet` donne ces deux informations. Les relier aux coffres qu'ils bloquent, par leur position ou par la
   lecture des scripts.
2. Donner à ces lieux une règle propre (`kiblast:N`) dans le world **et** dans le pack. Le world et le tracker
   doivent garder la même logique.
3. Vérifier aussi l'autre sens : pourquoi certains lieux s'affichent comme accessibles trop tôt. Par exemple, un
   chapitre atteint par le compteur d'objets reçus mais pas encore par l'histoire, ou un rocher de niveau 2 avant le
   chapitre 13.
4. Avant de coder, demander à l'utilisateur quelques **exemples précis**, avec la zone et le coffre : il n'en a pas
   noté pendant la partie.

---

## 2. DeathLink : parfois, une mort reçue est renvoyée à tout le monde

**Constat de l'utilisateur.** Quand un ami meurt, on meurt bien au combat suivant (Game Over immédiat). Mais
**parfois**, sans qu'il trouve dans quel cas, cette mort est renvoyée et tue à nouveau tous les autres joueurs.

**Ce que montrent les logs du client** (`C:\ProgramData\Archipelago\logs\BizHawkClient_2026_11_25_*.txt` et
`…_2026_11_26_*.txt`) :
- Toute la partie a été jouée avec le **client 0.16.2**. La **0.16.3**, qui corrige ce problème, n'a jamais été
  installée : l'apworld de `custom_worlds` est resté en 0.16.2.
- Le renvoi a toujours le même déroulé : « Game Over from the received death, nothing sent » (correct), puis
  **5 à 15 secondes plus tard**, sans nouvelle défaite, « Sending death to your friends... ». Exemples :

| Game Over (mort reçue) | Mort renvoyée en trop |
|---|---|
| 25/11 19:43:27 | 19:43:40 |
| 25/11 19:57:28 | 19:57:38 |
| 25/11 22:34:57 | 22:35:05 |
| 25/11 23:32:24 | 23:32:31 **et** 23:32:45 (deux fois) |
| 26/11 18:37:08 | 18:37:13 |

  La plupart des autres Game Over reçus n'ont rien renvoyé. Le renvoi semble dépendre de ce qui se passe à
  l'écran titre, par exemple du temps passé avant de choisir « Continuer ».

**Explication la plus probable** (C65, pas encore vérifiée en jeu). Après le Game Over, le jeu repasse par les logos,
puis par l'écran titre. Cet écran affiche un aperçu avec d'autres personnages (Goku, Gohan, Piccolo : C37). Le client
croit brièvement être « en jeu » avec une équipe à 0 PV, puis voit le jeu « s'arrêter » : il compte un 2e Game Over et
l'envoie.

**Correctif déjà écrit, mais pas installé ni vérifié** (world 0.16.3, D58). Après un Game Over, le client ne retient
plus aucune défaite tant qu'il ne t'a pas revu en jeu avec un combattant à plus de 0 PV.

**Le double renvoi du 25/11 à 23:32 laisse un doute.** Si l'aperçu de l'écran titre montre aussi des personnages
**debout**, le client se « réarme » et le problème peut revenir. À faire :
1. Installer la 0.16.3 (`tools/build_apworld.sh --deploy`, BizHawk Client fermé).
2. Vérifier en jeu, sur un état de Claude, ce que lit le client pendant les logos et l'écran titre, pendant une
   minute environ, sans appuyer sur rien :
   - `0x0AF1E4` (partie en cours) ;
   - le code de carte `0x0D226C` ;
   - les cases d'équipe `0x0CC374` ;
   - les PV des fiches.
   S'il voit des personnages debout puis à 0 PV, trouver un signal plus sûr de « vraie partie chargée ». Par exemple :
   ne se réarmer que si la carte et l'équipe sont celles d'avant le Game Over, ou seulement après un « Continuer »
   repéré en mémoire.
3. Refaire l'essai réel avec `tools/friend.py`, en restant volontairement 30 à 60 secondes sur l'écran titre après le
   Game Over.
