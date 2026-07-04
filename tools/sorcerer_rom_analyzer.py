# sorcerer_rom_analyzer.py

import hashlib
import os
import sys

# Evita errores de codificacion en consolas que no son UTF-8 (p.ej. cp1252)
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

def parse_md_header(rom_path):
    """Lee la cabecera estandar de Mega Drive (0x100-0x1FF)."""
    with open(rom_path, "rb") as f:
        f.seek(0x100)
        header = f.read(0x100)

    info = {
        "Console": header[0x00:0x10].decode("ascii", errors="replace").strip(),
        "Copyright": header[0x10:0x20].decode("ascii", errors="replace").strip(),
        "ROM Name (domestic)": header[0x20:0x50].decode("ascii", errors="replace").strip(),
        "ROM Name (overseas)": header[0x50:0x80].decode("ascii", errors="replace").strip(),
        "Serial": header[0x80:0x8E].decode("ascii", errors="replace").strip(),
        "Checksum": f"0x{int.from_bytes(header[0x8E:0x90], 'big'):04X}",
        "Region": header[0xF0:0xF3].decode("ascii", errors="replace").strip(),
    }

    if header[0xB0:0xB2] == b"RA":
        sram_start = int.from_bytes(header[0xB4:0xB8], "big")
        sram_end = int.from_bytes(header[0xB8:0xBC], "big")
        info["SRAM"] = f"0x{sram_start:06X}-0x{sram_end:06X}"
    else:
        info["SRAM"] = "no declarada"

    return info

def real_checksum(rom_path):
    """Suma de words desde 0x200 (el checksum estandar de Mega Drive)."""
    with open(rom_path, "rb") as f:
        data = f.read()
    s = 0
    for i in range(0x200, len(data) - 1, 2):
        s = (s + int.from_bytes(data[i:i+2], "big")) & 0xFFFF
    return s

def calculate_hashes(filepath):
    with open(filepath, "rb") as f:
        data = f.read()
        md5 = hashlib.md5(data).hexdigest()
        sha1 = hashlib.sha1(data).hexdigest()
    return md5, sha1, len(data)

def compare_roms(path_a, path_b):
    with open(path_a, "rb") as f:
        data_a = f.read()
    with open(path_b, "rb") as f:
        data_b = f.read()

    size_a, size_b = len(data_a), len(data_b)
    min_size = min(size_a, size_b)
    max_size = max(size_a, size_b)

    diffs = 0
    diff_offsets = []
    for i in range(min_size):
        if data_a[i] != data_b[i]:
            diffs += 1
            if len(diff_offsets) < 5:
                diff_offsets.append((hex(i), data_a[i], data_b[i]))

    if size_a != size_b:
        diffs += max_size - min_size

    return {
        "Size A": size_a,
        "Size B": size_b,
        "Bytes Different": diffs,
        "Sample Offsets": diff_offsets
    }

def summarize_rom(rom_path):
    summary = parse_md_header(rom_path)
    md5, sha1, size = calculate_hashes(rom_path)
    real = real_checksum(rom_path)
    summary["Checksum real"] = f"0x{real:04X} ({'OK' if summary['Checksum'] == f'0x{real:04X}' else 'NO COINCIDE con la cabecera'})"
    summary["MD5"] = md5
    summary["SHA1"] = sha1
    summary["Size"] = size
    return summary

if __name__ == "__main__":
    roms = {
        "USA 1992 (rev00)": "roms/Sorcerer's Kingdom (U) (1992).bin",
        "USA 1993 (rev01)": "roms/Sorcerer's Kingdom (U) (1993) [!].bin",
        "Español (2025)": "roms/Sorcerer's Kingdom (ES).md",
    }

    print("--- ROM Summaries ---")
    for name, path in roms.items():
        if not os.path.exists(path):
            print(f"\n{name}: (ROM no encontrada: {path})")
            continue
        info = summarize_rom(path)
        print(f"\n{name}:")
        for k, v in info.items():
            print(f"  {k}: {v}")

    print("\n--- Binary Comparisons ---")
    comparisons = [
        ("USA 1992 (rev00)", "USA 1993 (rev01)"),
        ("USA 1993 (rev01)", "Español (2025)"),
    ]

    for a, b in comparisons:
        if not (os.path.exists(roms[a]) and os.path.exists(roms[b])):
            print(f"\nComparando {a} vs {b}: (falta alguna ROM, se omite)")
            continue
        result = compare_roms(roms[a], roms[b])
        print(f"\nComparando {a} vs {b}:")
        for k, v in result.items():
            print(f"  {k}: {v}")
