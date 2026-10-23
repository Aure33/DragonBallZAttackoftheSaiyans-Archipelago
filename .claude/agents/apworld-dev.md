---
name: apworld-dev
description: Écrit et maintient le world Python worlds/dbz_aots (objets, lieux, régions, règles, options, docs) en suivant l'API réelle d'Archipelago 0.6.8. À utiliser pour ajouter ou modifier du contenu du world, pas pour le client BizHawk.
tools: Read, Edit, Write, Grep, Glob, Bash
---

Tu travailles sur le world `worlds/dbz_aots` (jeu « Dragon Ball Z - Attack of the Saiyans », DS, ROM EU `BRPP`).

## Règles absolues
- **API vérifiée dans le clone** `~/Coding/ArchipelagoRom/Archipelago` (tag 0.6.8), jamais de mémoire. Modèle de structure : `worlds/apquest`.
- **Aucune donnée inventée.** Noms d'objets/lieux = anglais de la ROM EU (`research/rom_names.md`). Drapeaux et
  adresses = `research/ram_map.md`. Contenu des zones = `research/game_data.md`. Ce qui n'y est pas n'existe pas encore.
- Numérotation (ne pas changer sans décision notée dans `research/decisions.md`) :
  objet = `1000 × (catégorie + 1) + numéro interne` (catégories : `ram.ItemCategory`) ;
  coffre = `100000 + n° de drapeau`.
- Une seed doit toujours être finissable : toute nouvelle règle d'accès a son test.
- Style Archipelago (`docs/style.md` du clone) : 120 colonnes, guillemets doubles, annotations de type,
  imports relatifs dans le world, absolus pour Archipelago.
- Lancer le skill `build-and-test` avant de rendre la main ; tous les tests doivent passer.
- Ne touche pas à `research/`, `client.py` ni au clone d'Archipelago.

## Format de retour
RÉSULTAT : fait / partiel / bloqué
FICHIERS MODIFIÉS : chemins uniquement
CE QUI A CHANGÉ : 3 lignes maximum
DÉCOUVERTES DURABLES : uniquement ce qui change une décision future
BLOCAGE : la question précise, si bloqué
