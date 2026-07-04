#!/usr/bin/env python3
"""Diagnostico de archivos .srm de Sorcerer's Kingdom (Mega Drive).

Modo simple (un archivo):
    python tools/srm_diagnose.py partida.srm
  - Normaliza el formato (8 KB empaquetado o 16 KB intercalado).
  - Comprueba la firma "TECHNICAL-WAVE!!" que el juego escribe al
    inicializar la SRAM.
  - Lista el directorio de Cronicas (slots) con sus 3 bytes de checksum.

Modo comparacion (sano vs corrupto):
    python tools/srm_diagnose.py sano.srm corrupto.srm
  - Muestra los bytes de SRAM que difieren y estadisticas de bits
    alterados. Un fallo electrico (PCB) suele manifestarse como bits o
    bytes sueltos alterados sin estructura; un bug de software dejaria
    bloques sobreescritos con datos reconocibles.

El juego guarda en 8 KB de SRAM mapeados en los bytes impares de
$200001-$203FFF. Layout (offsets en bytes de SRAM):
    0x10-0x1F : firma "TECHNICAL-WAVE!!"
    0x40+4*n  : registro de la Cronica n (3 sumas de verificacion)
    0x80+     : datos de las partidas
"""

import argparse
import sys

# Evita errores de codificacion en consolas que no son UTF-8 (p.ej. cp1252)
try:
    sys.stdout.reconfigure(errors="replace")
except AttributeError:
    pass

SIGNATURE = b"TECHNICAL-WAVE!!"
SIG_OFFSET = 0x10
SLOT_DIR = 0x40
NUM_SLOTS = 3
SRAM_SIZE = 8192


def load_sram(path: str) -> bytes:
    """Carga un .srm y lo normaliza a los 8 KB de bytes de SRAM reales."""
    data = open(path, "rb").read()
    if len(data) == SRAM_SIZE:
        return data
    if len(data) in (2 * SRAM_SIZE, 8 * SRAM_SIZE):
        # Formato intercalado (byte de SRAM en offsets impares o pares).
        odd = data[1::2][:SRAM_SIZE]
        even = data[0::2][:SRAM_SIZE]
        if odd[SIG_OFFSET:SIG_OFFSET + 16] == SIGNATURE:
            return odd
        if even[SIG_OFFSET:SIG_OFFSET + 16] == SIGNATURE:
            return even
        # sin firma reconocible: se asume el convenio habitual (impares)
        return odd
    raise SystemExit(f"Tamaño de .srm no reconocido: {len(data)} bytes (se esperan 8/16/64 KB)")


def diagnose(path: str) -> bytes:
    sram = load_sram(path)
    print(f"== {path} ==")
    sig = sram[SIG_OFFSET:SIG_OFFSET + 16]
    if sig == SIGNATURE:
        print("  Firma TECHNICAL-WAVE!!: OK")
    else:
        print(f"  Firma TECHNICAL-WAVE!!: DAÑADA -> {sig!r}")
        print("  (el juego reformateara la SRAM al arrancar)")
    for n in range(NUM_SLOTS):
        rec = sram[SLOT_DIR + 4 * n: SLOT_DIR + 4 * n + 4]
        empty = all(b == 0 for b in rec)
        state = "vacia" if empty else f"checksums = {rec[0]:02X} {rec[1]:02X} {rec[2]:02X}"
        print(f"  Cronica {n + 1}: {state}")
    used = sum(1 for b in sram if b not in (0x00, 0xFF))
    print(f"  Bytes de SRAM con contenido: {used}/{SRAM_SIZE}")
    return sram


def region_of(offset: int) -> str:
    if SIG_OFFSET <= offset < SIG_OFFSET + 16:
        return "FIRMA"
    if SLOT_DIR <= offset < SLOT_DIR + 4 * NUM_SLOTS:
        return f"DIRECTORIO (Cronica {(offset - SLOT_DIR) // 4 + 1})"
    if offset >= 0x80:
        return "datos de partida"
    return "reservado"


def compare(path_a: str, path_b: str) -> None:
    a = diagnose(path_a)
    print()
    b = diagnose(path_b)
    print()
    diffs = [i for i in range(SRAM_SIZE) if a[i] != b[i]]
    print(f"== Comparacion: {len(diffs)} bytes de SRAM difieren ==")
    if not diffs:
        return
    single_bit = 0
    bits_total = 0
    for i in diffs[:40]:
        x = a[i] ^ b[i]
        nbits = bin(x).count("1")
        bits_total += nbits
        if nbits == 1:
            single_bit += 1
        print(f"  0x{i:04X} ({region_of(i)}): {a[i]:02X} -> {b[i]:02X}  (XOR={x:02X}, {nbits} bit/s)")
    if len(diffs) > 40:
        print(f"  ... y {len(diffs) - 40} diferencias mas")
        for i in diffs[40:]:
            x = a[i] ^ b[i]
            bits_total += bin(x).count("1")
            if bin(x).count("1") == 1:
                single_bit += 1
    print()
    print(f"  Diferencias de un solo bit: {single_bit}/{len(diffs)} "
          f"({100 * single_bit // len(diffs)}%) - una proporcion alta apunta a fallo electrico")
    print(f"  Bits alterados en total: {bits_total}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Diagnostica archivos .srm de Sorcerer's Kingdom (o compara sano vs corrupto)"
    )
    parser.add_argument("srm", help="Archivo .srm a diagnosticar (referencia sana en modo comparacion)")
    parser.add_argument("srm_corrupto", nargs="?", help="Segundo .srm (presuntamente corrupto) a comparar")
    args = parser.parse_args()

    if args.srm_corrupto:
        compare(args.srm, args.srm_corrupto)
    else:
        diagnose(args.srm)


if __name__ == "__main__":
    main()
