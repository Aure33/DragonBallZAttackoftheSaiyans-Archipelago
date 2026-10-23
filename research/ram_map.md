# Carte mémoire — DBZ: Attack of the Saiyans (EU `BRPP` rév. 0)

Règle : **aucune adresse sans preuve**. Chaque entrée indique comment elle a été trouvée et sur quelle ROM.
Une adresse non confirmée reste dans la section « Hypothèses ».

## Méthode
Depuis le 2026-10-23, les expériences se font aussi avec la **télécommande** (`scripts/remote.lua` dans BizHawk + `scripts/remote.py` côté WSL) : boutons, captures d'écran, photos mémoire et lectures directes, sans manipulation du joueur.

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
| **Zénis** | `0x0CC370` | `0x020CC370` | 4 octets | Valeur directe (little-endian) | ✅ | 160 lu en mémoire (`A0 00 00 00`) juste après l'écran « Objets acquis » qui affichait 160 zénis ; 0 → 160 → 420 → 580 au fil de l'île | 2026-10-23 |

**Numéro interne ≠ numéro de texte.** Dans la ROM, chaque ligne des tables de données (`Use_Item`, `Btl_Acc`, `Pt_Eqp`, `Key_Item`) indique quel texte utiliser comme nom : `(colonne 0 & 0xFFFF) = 2 × n° de texte + 1`. Le texte n° 29 de `use_item_mes` (Méd. de Karine) n'est utilisé par aucune ligne de `Use_Item` : à partir de la ligne 29, le numéro interne = numéro de texte − 1 (ex. Plume de phénix : texte 30, numéro interne 29). Pour `Pt_Eqp` et `Key_Item`, les deux numéros coïncident sur les objets observés.

La **sauvegarde** (`.SaveRAM`, 8 Ko) n'est pas chiffrée : signature `mDBZ`, 2 copies de 0x800 octets (principale + secours), puis d'autres blocs vers `0x1000` et `0x1800`. L'inventaire y est à l'identique : la zone `0x533`–`0x6D7` de la sauvegarde = RAM `0x0CC397`–`0x0CC53B`. Les fiches des personnages, en revanche, y sont rangées autrement (0x40 octets par personnage dans la sauvegarde, 0x24C en mémoire).

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Sens | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|---|
| ~~Fiches des personnages~~ | ~~`0x0CD300`~~ | | | **Faux** : vaut 445 aussi dans une partie où Krillin a 320 PV. Ce sont sans doute des tables de valeurs | ❌ | Lecture par la télécommande | 2026-10-23 |

## 3. Drapeaux de coffres
**Bloc des drapeaux permanents** : Main RAM `0x09F7E8`–`0x09FB47` (DS `0x0209F7E8`), 0x360 octets = 6912 drapeaux d'un bit.
C'est une copie exacte de la zone `0x010`–`0x36F` de la sauvegarde (861/864 octets identiques sur la photo 07, prise au même moment que la sauvegarde).
**N° de drapeau** = (adresse − `0x09F7E8`) × 8 + n° de bit (bit 0 = valeur 0x01).
Le bit passe à 1 **au moment même** où l'on ouvre le coffre (photos 08 → 09, 12 s d'écart : seul ce bit et la quantité de l'objet ont changé dans la zone de jeu).

| Élément | Drapeau | Adresse (Main RAM) | Bit | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|
| Île d'entraînement : 1er Petit haricot ouvert par le joueur | 1401 | `0x09F897` | 1 | ✅ | 0 → 1 dans les 2 parties (photos 01→03 et 08→09), en même temps que Petit haricot 5 → 6 | 2026-10-23 |
| Île d'entraînement : Plume de phénix | 1402 | `0x09F897` | 2 | 🟡 | 0 → 1 entre les photos 05 et 06, en même temps que Plume de phénix 0 → 1 | 2026-10-23 |
| Île d'entraînement : 4 autres coffres des écrans 1 et 2 (Capsule 50 PV, Petit haricot, Haricot moyen, Petit haricot) | 1400, 1403, 1404, 1405 | `0x09F897` | 0, 3, 4, 5 | 🟡 | À 1 seulement après l'île (photo 07) ; quel bit = quel coffre : pas encore établi | 2026-10-23 |
| Île d'entraînement : 2 coffres après l'appel de Bulma (Masque à gaz, Carte d'obscurité) | 1583, 1584 | `0x09F8AD` / `0x09F8AE` | 7 / 0 | ❓ | Seuls autres drapeaux consécutifs allumés pendant l'île ; l'attribution est une déduction | 2026-10-23 |

Les coffres sont mis en place par les scripts de carte (`script/cf0/<zone>/<carte>.sb`, fonctions `TreasureInit_<zone>` et `TreasureSet_<carte>`). Les décoder donnerait la liste de tous les coffres du jeu avec leur drapeau (phase 6).

Les 6 octets 0 → 1 vus juste après l'inventaire (`0x0CC542`, `0x0CC548`, `0x0CC572`, `0x0CC584`, `0x0CC587`, `0x0CC5E1`) ne sont **pas** des coffres. Ce sont d'autres drapeaux (histoire, tutoriels ?), à classer plus tard.

## 4. Drapeaux d'histoire, quêtes, boss
Même bloc que les coffres (§3). Drapeaux allumés pendant le prologue, hors coffres (photo 01 → photo 07) : 11, 12, 15, 20, 55, 60, 1703, 2529, 2530, 2600, 2601, 2647, 2667, 2683, 4304, 4305, 4312, 4313, 4320–4322, 4328–4330, 4335 (❓, à classer). Déjà allumés avant l'île : 0, 5, 10, 1700, 1701, 2528, 2659, 3200.
Le drapeau de victoire contre Jackie Choun en fait sans doute partie (à isoler).

## 5. Techniques par personnage
_(phase 2)_

## 6. État du jeu (titre / carte / menu / combat)
| Élément | Adresse (Main RAM) | Adresse DS | Sens | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|
| **Code de la carte en cours** | `0x0D226C` | `0x020D226C` | 8 caractères ASCII, ex. `kam01_00` (Kame House), `tut01_00` (Île d'entraînement), `est01_00` (Ville est). **Tout à zéro quand aucune partie n'est chargée** (logos, écran titre) | ✅ | Photos 01, 07, île (carte/combat/menu), écran titre après « Power » | 2026-10-23 |
| **En combat** | `0x09B236` | `0x0209B236` | 2 octets : `FF FF` en combat, `00 00` sur la carte et dans le menu. Vaut aussi `FF FF` sans partie chargée → toujours tester d'abord le code de carte | 🟡 | 3 photos en combat, 9 hors combat, écran titre | 2026-10-23 |
| Menu ouvert | — | — | Aucun indicateur fiable trouvé (1 seule photo du menu) | ❓ | Photo r04_menu | 2026-10-23 |
| Zone de données de combat | `0x0CC600`–`0x0CD200` | `0x020CC600` | Remplie seulement pendant un combat, à zéro sinon | 🟡 | Photos 02, r01_combat | 2026-10-23 |

**Règle pour le client** : « en jeu » = le code de carte à `0x0D226C` est un code valide (3 lettres, 2 chiffres, `_`, 2 chiffres). « Hors combat » = en jeu et `0x09B236` ≠ `FF FF`.

## 7. Zone libre qui survit à la sauvegarde (compteur d'objets reçus)
Le bloc des drapeaux (§3) est enregistré tel quel dans la sauvegarde. Sur toutes les photos d'une partie en cours et dans la sauvegarde d'après le prologue, seuls ses octets `+0x000`–`+0x21D` ont servi (dernier drapeau vu : 4335). **Les 322 derniers octets (`+0x21E`–`+0x35F`, soit `0x09FA06`–`0x09FB47`) sont toujours à zéro.**

| Élément | Adresse (Main RAM) | Adresse DS | Taille | Statut | Comment trouvé | Date |
|---|---|---|---|---|---|---|
| Emplacement **provisoire** du compteur d'objets reçus : les 4 derniers octets du bloc | `0x09FB44` | `0x0209FB44` | 4 octets | ❓ | Toujours à zéro jusqu'ici, mais on n'a vu que le prologue. À confirmer en décodant les scripts (plus grand n° de drapeau utilisé par le jeu) | 2026-10-23 |

En-tête de la sauvegarde : `0x0` = `mDBZ`, `0x4` = compteur de sauvegardes (12 sur la copie 1, 13 sur la copie 2), `0x8` = somme de contrôle (4 octets ?). Le client n'écrit **jamais** dans le fichier : il écrit en mémoire, et c'est le jeu qui recalcule la somme quand le joueur sauvegarde.

## Hypothèses à vérifier
| Hypothèse | Pourquoi on y croit | Comment vérifier |
|---|---|---|
| ~~❓ Copie de l'en-tête vers `0x3FFE00`~~ | Confirmé (voir §1) | — |
