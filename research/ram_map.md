# Carte mémoire — DBZ: Attack of the Saiyans (EU `BRPP` rév. 0)

Règle : **aucune adresse sans preuve**. Chaque entrée indique comment elle a été trouvée et sur quelle ROM.
Une adresse non confirmée reste dans la section « Hypothèses ».

## Conventions
- Émulateur : BizHawk 2.11.1, cœur melonDS.
- Domaine mémoire principal : `Main RAM` (4 Mio en mode DS, taille à confirmer dans BizHawk ; correspond aux adresses DS à partir de `0x02000000`).
  Une adresse « Main RAM `0x123456` » = adresse DS `0x02123456`.
- Ordre des octets : little-endian (octet de poids faible en premier), comme tout le DS.
- Statut : ✅ confirmé (≥ 2 essais concordants) · 🟡 probable (1 essai) · ❓ hypothèse.

## 1. Identification de la ROM
Source : lecture directe de l'en-tête du fichier ROM (`dd`), 2026-10-23.

| Champ | Offset dans la ROM | Valeur |
|---|---|---|
| Titre | `0x000` (12 octets) | `DB KAI RPG` |
| Code du jeu | `0x00C` (4 octets) | `BRPP` (`P` = Europe) |
| Code éditeur | `0x010` (2 octets) | `AF` (Namco Bandai) |
| Version ROM | `0x01E` (1 octet) | `0x00` (rév. 0) |
| Taille du fichier | — | 134 217 728 octets (128 Mio) |
| MD5 | — | `45ba1dcbca2f3646fa01a52de82b6f73` |
| SHA-1 | — | `38514326cb14ab397028e80d8c093749940ef5be` |

- [ ] Comparer MD5/SHA-1 avec la base No-Intro (datomatic.no-intro.org).

Pour que le client reconnaisse le jeu, on comparera les 18 premiers octets de l'en-tête
(`DB KAI RPG\0\0BRPPAF`) avec ce que le jeu a en mémoire.

## 2. Inventaire, zénis, équipement
_(phase 2)_

## 3. Drapeaux de coffres
_(phase 2)_

## 4. Drapeaux d'histoire, quêtes, boss
_(phase 2)_

## 5. Techniques par personnage
_(phase 2)_

## 6. État du jeu (titre / carte / menu / combat)
_(phase 2)_

## 7. Zone libre qui survit à la sauvegarde (compteur d'objets reçus)
_(phase 2)_

## Hypothèses à vérifier
| Hypothèse | Pourquoi on y croit | Comment vérifier |
|---|---|---|
| ❓ Une copie de l'en-tête de la cartouche se trouve en Main RAM vers `0x3FFE00` | Comportement standard du DS. Le world `pokemon_bw` lit l'en-tête en `0x3FFA80`, mais c'est un jeu « DSi Enhanced », donc pas forcément pareil | Hex Editor BizHawk, domaine `Main RAM`, chercher `DB KAI RPG` |
