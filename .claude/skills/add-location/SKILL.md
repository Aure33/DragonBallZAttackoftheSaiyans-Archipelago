---
name: add-location
description: Ajouter un lieu (coffre, boss, quête) au world dbz_aots de bout en bout : donnée de recherche, drapeau mémoire, locations.py, région, règle, client, test.
---

# Ajouter un lieu

1. **Donnée de recherche** : le lieu est dans `research/game_data.md` avec une source (zone, emplacement, contenu
   d'origine). Sinon, s'arrêter et le rechercher d'abord.
2. **Drapeau** : son n° de drapeau est dans `research/ram_map.md` (§3/§4), statut 🟡 ou ✅. Sinon, le trouver
   (skill `ram-diff`, ou télécommande `research/scripts/remote.py` : photo avant/après l'ouverture, puis
   `research/scripts/ram_diff.py flags`). Drapeau n = bit `n % 8` de `0x09F7E8 + n // 8`.
3. **`worlds/dbz_aots/locations.py`** : ajouter `"<Nom anglais>": LocationData(<région>, <drapeau>)` dans
   `LOCATIONS` (ID = 100000 + drapeau, calculé automatiquement), et son contenu d'origine dans le pool.
4. **Région** : si la zone n'existe pas, la créer dans `regions.py` et la relier, avec sa règle d'accès.
5. **Règle** : si le lieu demande un objet (rocher Ki Blast niveau 2/3, Gas Mask…), l'écrire dans `rules.py`.
6. **Client** : rien à faire si c'est un coffre à drapeau (le client lit tout le bloc). Sinon, adapter `client.py`.
7. **Test** : le lieu est atteignable avec ce qu'il faut et pas sans (`assertAccessDependency`), puis skill
   `build-and-test`.
