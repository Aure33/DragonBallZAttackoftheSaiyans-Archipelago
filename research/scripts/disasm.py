"""Désassemble une fonction de l'ARM9 de la ROM (capstone), avec les valeurs des littéraux chargés par « ldr [pc] ».

    research/.venv/bin/python research/scripts/disasm.py <ROM> <adresse hex> [nombre d'instructions]
"""
import struct
import sys

import capstone
import ndspy.rom

rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
arm9, base = bytes(rom.arm9), rom.arm9RamAddress
start, count = int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 60
md = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
for n, ins in enumerate(md.disasm(arm9[start - base:start - base + count * 4], start)):
    extra = ""
    if ins.mnemonic.startswith("ldr") and "[pc" in ins.op_str:
        off = int(ins.op_str.split("#")[-1].rstrip("]"), 16) if "#" in ins.op_str else 0
        lit = struct.unpack_from("<I", arm9, ins.address + 8 + off - base)[0]
        extra = f"  ; ={lit:#x}"
        if base <= lit < base + len(arm9):
            z = arm9.find(b"\0", lit - base)
            text = arm9[lit - base:z]
            if 2 < len(text) < 40 and all(32 <= c < 127 for c in text):
                extra += f' "{text.decode()}"'
    print(f"{ins.address:#x} {ins.mnemonic} {ins.op_str}{extra}")
