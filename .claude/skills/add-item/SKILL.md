---
name: add-item
description: Ajouter un objet au world dbz_aots de bout en bout : nom officiel, numéro interne, classification, items.py, client, test.
---

# Ajouter un objet

1. **Nom** : nom anglais de la ROM EU, colonne « EN (EU) » de `research/rom_names.md`.
2. **Catégorie et numéro interne** : catégorie = table de la ROM (`Use_Item`, `Btl_Acc`, `Pt_Eqp`, `Key_Item` →
   `ram.ItemCategory`). Le numéro interne est la **ligne de la table de données**, pas celle du texte (décalage
   après le texte n° 29 des objets utilisables : voir `research/ram_map.md` §2). Le vérifier en mémoire si possible :
   quantité à `ram.inventory_address(catégorie, numéro)`.
3. **Classification** : `progression` s'il ouvre un accès (sources : `research/game_data.md`, `research/decisions.md`),
   `useful` pour l'équipement et les objets rares, `filler` pour les consommables, `trap` pour un piège.
4. **`worlds/dbz_aots/items.py`** : ajouter l'entrée dans `ITEMS` (ID = 1000 × (catégorie + 1) + numéro, automatique).
5. **Client** : rien à faire pour un objet d'inventaire (le client ajoute 1 à la bonne case). Un objet spécial
   (zénis, technique, piège) demande du code dans `client.py`.
6. **Test** : ajouter l'objet au test des adresses (`test_training_island.py`, `test_item_id_gives_the_inventory_slot`)
   si son emplacement a été vu en mémoire, puis skill `build-and-test`.
