# Carte mémoire — DBZ: Attack of the Saiyans (EU `BRPP` rév. 0)

Règle : **aucune adresse sans preuve**. Chaque entrée indique comment elle a été trouvée et sur quelle ROM.
Une adresse non confirmée reste dans la section « Hypothèses ».

## Méthode
Photos de la mémoire prises par `scripts/dump_ram.lua` à chaque état de sauvegarde, puis analysées avec `scripts/ram_diff.py` et numpy (environnement `research/.venv`). Les photos sont dans `C:\Users\Aurelien\Desktop\archipelago\dbz_research\dumps\` (hors Git).
Série du 2026-10-23 : photos 01–06 = 2e passage dans l'île depuis l'état 2 (01 avant l'île, 02 en combat contre les serpents, puis 1er Petit haricot avant 03 et Plume de phénix avant 06) ; photo 07 = état 4 chargé (1er passage : île finie, Jackie Choun battu, au même moment que la sauvegarde en jeu).

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

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Sens | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|---|
| Copie de l'en-tête ROM | `0x3FFE00` | `0x023FFE00` | 0x200 | Commence par `DB KAI RPG\0\0BRPPAF` | ✅ | Recherche du texte dans les photos 01 à 07 (2 parties différentes) | 2026-10-23 |
| 2e copie de l'en-tête | `0x3FFA80` | `0x023FFA80` | 0x180 ? | Même début | ✅ | Idem | 2026-10-23 |

Taille du domaine `Main RAM` dans BizHawk 2.11.1 (melonDS) : **4 194 304 octets (4 Mio)**, constatée sur les photos.

## 2. Inventaire, zénis, équipement
**1 octet = la quantité d'un objet**, rangé par **numéro interne**. Les 4 catégories se suivent (128 + 128 + 48 + 108 = 412 octets).

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Sens / valeurs | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|---|
| Objets utilisables (table ROM `Use_Item`) | `0x0CC398` | `0x020CC398` | 128 × 1 octet | Quantité de l'objet n° *i* à `0x0CC398 + i` | ✅ | Photos 01→07 : Petit haricot 5 (Roshi) → 6 → 8 (+3 coffres), Plume de phénix 0 → 1, Récup. poison 5 → 6 (butin des serpents), Récup. mouvements 5 (Roshi), Fruit chance 1 (tiroir) ; même résultat dans les 2 parties | 2026-10-23 |
| Accessoires de combat (`Btl_Acc`) | `0x0CC418` | `0x020CC418` | 128 × 1 octet | Idem | 🟡 | Déduit de la suite des tables ; aucun accessoire possédé, donc pas encore observé | 2026-10-23 |
| Capsules (`Pt_Eqp`) | `0x0CC498` | `0x020CC498` | 48 × 1 octet | Idem | ✅ | Masque à gaz (n° 30) et Carte d'obscurité (n° 37) à 1 après l'île | 2026-10-23 |
| Objets clés (`Key_Item`) | `0x0CC4C8` | `0x020CC4C8` | 108 × 1 octet | Idem | ✅ | Boule de la Voyante (n° 0) à 1 après l'île | 2026-10-23 |
| Compteur croissant (zénis ? expérience ?) | `0x0CC370` | `0x020CC370` | 2 ou 4 octets | 0 → 160 → 420 → 580 au fil de l'île ; 1740 après le prologue | ❓ | Photos 01→07 | 2026-10-23 |

**Numéro interne ≠ numéro de texte.** Dans la ROM, chaque ligne des tables de données (`Use_Item`, `Btl_Acc`, `Pt_Eqp`, `Key_Item`) indique quel texte utiliser comme nom : `(colonne 0 & 0xFFFF) = 2 × n° de texte + 1`. Le texte n° 29 de `use_item_mes` (Méd. de Karine) n'est utilisé par aucune ligne de `Use_Item` : à partir de la ligne 29, le numéro interne = numéro de texte − 1 (ex. Plume de phénix : texte 30, numéro interne 29). Pour `Pt_Eqp` et `Key_Item`, les deux numéros coïncident sur les objets observés.

La **sauvegarde** (`.SaveRAM`, 8 Ko) n'est pas chiffrée : signature `mDBZ`, 2 copies de 0x800 octets (principale + secours), puis d'autres blocs vers `0x1000` et `0x1800`. L'inventaire y est à l'identique : la zone `0x533`–`0x6D7` de la sauvegarde = RAM `0x0CC397`–`0x0CC53B`. Les fiches des personnages, en revanche, y sont rangées autrement (0x40 octets par personnage dans la sauvegarde, 0x24C en mémoire).

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Sens | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|---|
| Fiches des personnages | `0x0CD300` (+ `0x24C` par personnage) | `0x020CD300` | 0x24C par personnage | Commence par PV actuels, PV max, ki actuel, ki max (4 octets chacun) | 🟡 | PV/ki de la sauvegarde (445/148, 290/95, 660/225) retrouvés dans la photo 07 | 2026-10-23 |

## 3. Drapeaux de coffres
Pas encore trouvés. Il y a 6 octets drapeaux (0 → 1) juste après l'inventaire : `0x0CC542`, `0x0CC548`, `0x0CC572`, `0x0CC584`, `0x0CC587`, `0x0CC5E1`. C'est trop peu pour 8 coffres + l'histoire de l'île. `0x0CC584` passe à 1 au moment du 1er Petit haricot (❓). Pour la Plume de phénix, aucun drapeau propre n'a été trouvé dans la zone de la partie en cours. Prochaine expérience : 3 photos rapprochées autour d'un seul coffre, puis en quittant l'écran (le drapeau n'est peut-être écrit qu'au changement d'écran).

## 4. Drapeaux d'histoire, quêtes, boss
_(phase 2)_

## 5. Techniques par personnage
_(phase 2)_

## 6. État du jeu (titre / carte / menu / combat)
| Élément | Adresse (Main RAM) | Adresse DS | Sens | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|
| Zone de données de combat | `0x0CC600`–`0x0CD200` | `0x020CC600` | Remplie seulement pendant un combat (photo 02), à zéro sinon | ❓ | Photos 01→07 | 2026-10-23 |

## 7. Zone libre qui survit à la sauvegarde (compteur d'objets reçus)
_(phase 2)_

## Hypothèses à vérifier
| Hypothèse | Pourquoi on y croit | Comment vérifier |
|---|---|---|
| ~~❓ Copie de l'en-tête vers `0x3FFE00`~~ | Confirmé (voir §1) | — |
