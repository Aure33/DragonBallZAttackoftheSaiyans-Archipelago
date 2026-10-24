"""Faux 2e joueur DeathLink : « listen » affiche les morts reçues, « kill » envoie une mort puis quitte."""
import asyncio, json, sys, time, uuid
import websockets


async def main(mode: str) -> None:
    async with websockets.connect("ws://localhost:38281") as ws:
        await ws.recv()  # RoomInfo
        await ws.send(json.dumps([{
            "cmd": "Connect", "game": "APQuest", "name": "Ami", "password": "", "uuid": str(uuid.uuid4()),
            "version": {"major": 0, "minor": 6, "build": 8, "class": "Version"},
            "items_handling": 0, "tags": ["DeathLink"], "slot_data": False,
        }]))
        while True:
            for packet in json.loads(await ws.recv()):
                if packet["cmd"] in ("Connected", "ConnectionRefused"):
                    print(packet["cmd"], packet.get("errors", ""), flush=True)
                    if mode == "kill":
                        await ws.send(json.dumps([{"cmd": "Bounce", "tags": ["DeathLink"], "data": {
                            "time": time.time(), "source": "Ami", "cause": "Ami tombe au combat (essai)"}}]))
                        await asyncio.sleep(1)
                        print("mort envoyée", flush=True)
                        return
                elif packet["cmd"] == "Bounced" and "DeathLink" in packet.get("tags", []):
                    print("MORT REÇUE :", packet["data"], flush=True)


asyncio.run(main(sys.argv[1]))
