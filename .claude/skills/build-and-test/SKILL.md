---
name: build-and-test
description: Lancer les tests du world dbz_aots, générer une seed de test et construire (ou déployer côté Windows) le .apworld. À utiliser après toute modification de worlds/dbz_aots/.
---

# Construire et tester le world

Toutes les commandes se lancent depuis `~/Coding/ArchipelagoRom/Archipelago` (sources 0.6.8, venv `.venv`).
Le world y est relié par le lien symbolique `worlds/dbz_aots` → `<ce dépôt>/worlds/dbz_aots`.

## 1. Tests (obligatoire avant chaque commit)
```bash
# Tests génériques d'Archipelago appliqués au world + tests du world
AP_TEST_WORLDS=dbz_aots .venv/bin/python -m pytest -q -n auto -p no:cacheprovider
# Seulement les tests du world, en détail
AP_TEST_WORLDS=dbz_aots .venv/bin/python -m pytest worlds/dbz_aots -v -m "" -p no:cacheprovider
```
Piège connu : `test/webhost/test_docs.py` peut échouer avec `FileNotFoundError` en parallèle (`-n auto`), car
plusieurs processus copient les docs en même temps. Le relancer seul : `... pytest test/webhost/test_docs.py`.

## 2. Générer une seed de test
YAML minimal : `name: Aure` / `game: Dragon Ball Z - Attack of the Saiyans` / `Dragon Ball Z - Attack of the Saiyans: {}`.
Ajouter un autre jeu sans ROM (ChecksFinder, APQuest) pour vérifier le mélange.
```bash
.venv/bin/python Generate.py --player_files_path <dossier_yaml> --outputpath <dossier_sortie> --seed 42 --spoiler 2
```
Vérifier dans `*_Spoiler.txt` que les lieux « Training Island Chest N » contiennent des objets des autres joueurs.

## 3. Construire / déployer le .apworld
```bash
<ce dépôt>/tools/build_apworld.sh            # -> build/apworlds/dbz_aots.apworld
<ce dépôt>/tools/build_apworld.sh --deploy   # + copie dans C:\ProgramData\Archipelago\custom_worlds
```
Pour tester l'archive elle-même (et pas le dossier), retirer temporairement le lien `worlds/dbz_aots`, copier
l'archive dans `custom_worlds/` du clone, générer, puis **remettre le lien** :
`ln -s ../../DragonBallZAttackoftheSaiyans-Archipelago/worlds/dbz_aots worlds/dbz_aots`.
