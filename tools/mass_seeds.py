"""Generate many varied seeds and report every one that fails (phase 7).

Each seed mixes 1 to 3 DBZ players with random options (goal, included locations, DeathLink...) and 0 to 2
players of games without a ROM (APQuest, ChecksFinder). Generate.py runs in full: it fails when a seed is
unbeatable, and logs a warning when a player with full accessibility cannot reach all their locations; both count as
failures here.

Usage (any Python 3.10+, from anywhere):
    python3 tools/mass_seeds.py [--count 200] [--start 1] [--jobs 8]
"""
from __future__ import annotations

import argparse
import os
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ARCHIPELAGO = Path(os.environ.get("ARCHIPELAGO", Path.home() / "Coding/ArchipelagoRom/Archipelago"))
GAME = "Dragon Ball Z - Attack of the Saiyans"
OTHER_GAMES = ("APQuest", "ChecksFinder")
ACCESSIBILITY_WARNING = "Location Accessibility requirements not fulfilled"


def dbz_yaml(name: str, rng: random.Random) -> str:
    return (f"name: {name}\ngame: {GAME}\n{GAME}:\n"
            f"  goal_chapter: {rng.choice([15, rng.randint(1, 14)])}\n"
            f"  hidden_items: {rng.choice(['true', 'false'])}\n"
            f"  chapter_checks: {rng.choice(['true', 'false'])}\n"
            f"  key_items: {rng.choice(['true', 'false'])}\n"
            f"  death_link: {rng.choice(['true', 'false'])}\n"
            f"  east_city_ruins: {rng.choice(['true', 'false'])}\n"
            f"  experience_multiplier: {rng.randint(1, 10)}\n"
            f"  accessibility: {rng.choice(['full', 'minimal'])}\n"
            f"  progression_balancing: {rng.randint(0, 99)}\n")


def write_players(seed: int, folder: Path) -> str:
    """Write the YAMLs of a seed and return a short description of its players."""
    rng = random.Random(seed)
    players = []
    for n in range(rng.randint(1, 3)):
        (folder / f"dbz{n}.yaml").write_text(dbz_yaml(f"Dbz{n}", rng))
        players.append("DBZ")
    for n in range(rng.randint(0, 2)):
        game = rng.choice(OTHER_GAMES)
        (folder / f"other{n}.yaml").write_text(f"name: Other{n}\ngame: {game}\n{game}: {{}}\n")
        players.append(game)
    return "+".join(players)


def run_seed(seed: int) -> tuple[int, str, str | None]:
    """Generate one seed; return (seed, players, None) if it worked, or the end of its output if not."""
    with tempfile.TemporaryDirectory(prefix=f"dbz_seed{seed}_") as temp:
        yamls, output = Path(temp, "players"), Path(temp, "output")
        yamls.mkdir()
        players = write_players(seed, yamls)
        result = subprocess.run(
            [str(ARCHIPELAGO / ".venv/bin/python"), "Generate.py", "--player_files_path", str(yamls),
             "--outputpath", str(output), "--seed", str(seed), "--spoiler", "2"],
            cwd=ARCHIPELAGO, capture_output=True, text=True,
        )
    log = result.stdout + result.stderr
    if result.returncode != 0 or ACCESSIBILITY_WARNING in log:
        return seed, players, "\n".join(log.strip().splitlines()[-15:])
    return seed, players, None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--count", type=int, default=200)
    parser.add_argument("--start", type=int, default=1, help="first seed number")
    parser.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    args = parser.parse_args()

    failures = []
    with ThreadPoolExecutor(args.jobs) as pool:
        for done, (seed, players, error) in enumerate(
                pool.map(run_seed, range(args.start, args.start + args.count)), start=1):
            if error:
                failures.append(seed)
                print(f"ÉCHEC seed {seed} ({players}) :\n{error}\n", flush=True)
            elif done % 25 == 0:
                print(f"{done}/{args.count} seeds faites, {len(failures)} échec(s)", flush=True)
    print(f"Résultat : {args.count - len(failures)}/{args.count} seeds réussies"
          + (f", échecs : {failures}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
