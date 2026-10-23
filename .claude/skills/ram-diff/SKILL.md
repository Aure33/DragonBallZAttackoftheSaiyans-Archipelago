---
name: ram-diff
description: Procédure pas à pas pour trouver une adresse mémoire de DBZ Attack of the Saiyans dans BizHawk (état de sauvegarde, comparaison avant/après, validation, notation dans research/ram_map.md). À utiliser dès qu'on cherche où le jeu stocke une valeur (coffre ouvert, objet, zénis, drapeau d'histoire, état du jeu).
---

# Trouver une adresse mémoire (méthode « avant / après »)

Idée : on prend une photo de la mémoire, on fait **une seule** action dans le jeu, on reprend une photo,
et on garde seulement les adresses qui ont changé comme prévu. On recommence jusqu'à n'en avoir plus que quelques-unes.

## 0. Préparer
1. Écrire la cible en une phrase : « l'octet qui passe de X à Y quand j'ouvre le coffre Z ».
2. Deviner le type de valeur :
   - nombre connu à l'écran (zénis, quantité d'objet) → recherche par **valeur exacte** ;
   - drapeau (coffre, quête) → recherche par **changement** (« a changé » / « n'a pas changé »), en taille 1 octet.
3. Se placer juste avant l'action et faire un état de sauvegarde (BizHawk : `Shift+F1` = sauver dans l'emplacement 1, `F1` = recharger).

## 1. Chercher (BizHawk → Tools → RAM Search)
1. Domaine : `Main RAM`. Taille : 1 octet (drapeaux) ou 4 octets (zénis, souvent). Affichage : hexadécimal.
2. Cliquer **New** (repart de toute la mémoire).
3. Faire l'action dans le jeu (ouvrir le coffre), puis filtrer avec **Not Equal / Changed** par rapport à la valeur précédente → **Search**.
4. Laisser passer quelques secondes **sans rien faire**, puis filtrer avec **Equal / Unchanged** → **Search**. Ça élimine les compteurs qui bougent tout seuls.
5. Recharger l'état (`F1`), refaire l'action, recommencer les étapes 3–4.
6. Pour une valeur connue (zénis = 1250) : filtrer **Equal to specific value 1250**, dépenser ou gagner, filtrer avec la nouvelle valeur.

Arrêter quand il reste moins d'environ 10 candidats.

## 2. Valider
1. Ajouter les candidats à **RAM Watch** (Tools → RAM Watch).
2. Pour chaque candidat : recharger l'état, faire l'action, vérifier que la valeur change exactement comme prévu.
3. Test inverse (si c'est sans risque) : dans **Hex Editor**, modifier la valeur à la main et regarder l'effet dans le jeu. Exemple : remettre le bit du coffre à 0, le coffre doit réapparaître fermé après un changement de zone. Toujours partir d'un état de sauvegarde.
4. Test de persistance : sauvegarder **en jeu**, redémarrer l'émulateur, recharger la partie. L'adresse est-elle toujours la même, avec la même valeur ?
5. Pour un drapeau : noter l'**octet** et le **bit** (bit 0 = valeur 0x01, bit 7 = valeur 0x80).

## 3. Noter (obligatoire)
Dans `research/ram_map.md`, dans la bonne section :

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Sens / valeurs | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|---|
| Coffre 1 de la zone X | `0x0A1234` bit 3 | `0x020A1234` | 1 bit | 0 = fermé, 1 = ouvert | 🟡 | RAM Search, 2 passes, test inverse OK | 2026-… |

Statut ✅ seulement après au moins 2 essais concordants, dont un après rechargement de la partie.
Si plusieurs candidats restent, les noter tous en ❓ dans « Hypothèses à vérifier ».

## Pièges connus
- Un même octet peut contenir les drapeaux de 8 coffres : regarder **quel bit** change, pas seulement l'octet.
- Les valeurs à l'écran peuvent être stockées autrement (ex. zénis × 1, ou en BCD, c'est-à-dire chaque chiffre décimal codé à part).
- Certaines données sont copiées à plusieurs endroits (sauvegarde vs partie en cours) : préférer celle qui **pilote** le jeu (le test inverse le montre).
- Une adresse qui change entre deux chargements = donnée allouée dynamiquement. Il faudra chercher un **pointeur** (adresse qui contient l'adresse). C'est à noter comme découverte durable.
