"""Désassemble une fonction d'un script .sb (lecture approximative : empilements, appels, sauts).

    research/.venv/bin/python research/scripts/sbdis.py <ROM> <chemin du script dans la ROM> <fonction> [...]
"""
import struct
import sys

import ndspy.rom

from extract_chests import parse_script


def disassemble(natives, functions, code, name):
    ordered = sorted(functions)
    k = [i for i, f in enumerate(ordered) if f[1] == name][0]
    body = code[ordered[k][0]:ordered[k + 1][0] if k + 1 < len(ordered) else len(code)]
    table = [f for _, f in functions]  # ordre de la table (instruction 0x46)
    out, i = [], 0
    while i < len(body):
        op = body[i]
        if op == 0x13:
            out.append(f"push {struct.unpack('>i', body[i + 1:i + 5])[0]}"); i += 5
        elif op == 0x14:
            out.append(f"push {struct.unpack('b', body[i + 1:i + 2])[0]}"); i += 2
        elif op == 0x15:
            out.append(f"push {struct.unpack('>h', body[i + 1:i + 3])[0]}"); i += 3
        elif 0x16 <= op <= 0x1F:
            out.append(f"push {op - 0x17}"); i += 1
        elif op == 0x4A:
            out.append(f"CALL {natives[body[i + 1]] if body[i + 1] < len(natives) else body[i + 1]}"); i += 2
        elif op == 0x46:
            out.append(f"call {table[body[i + 1]] if body[i + 1] < len(table) else body[i + 1]}"); i += 2
        elif op in (0x41, 0x42):
            out.append(f"jump{op:02x} {struct.unpack('>h', body[i + 1:i + 3])[0]}"); i += 3
        elif op in (0x20, 0x24, 0x26, 0x27, 0x29, 0x38, 0x39):
            out.append(f"op{op:02x}.{body[i + 1]:02x}"); i += 2
        else:
            out.append(f"{op:02x}"); i += 1
    return out


if __name__ == "__main__":
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    parsed = parse_script(bytes(rom.getFileByName(sys.argv[2])))
    for name in sys.argv[3:]:
        print(f"== {name}\n" + " | ".join(disassemble(*parsed, name)))
