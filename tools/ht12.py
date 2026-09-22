#!/usr/bin/env python3
"""
HT12-style encoder/decoder for the Air-Supply AS-3DN ceiling fan receiver
(sold in Spain with Faro Barcelona fans).

Frame layout (12 bits, sent MSB first, same convention as Flipper's
Holtek_HT12X protocol):

    [ A0 A1 A2 A3 A4 A5 A6 A7 | D8 D9 D10 D11 ]
      8-bit address (DIP)       4-bit command, active-low

Waveform (TE ~= 433 us on the original remote):
    sync : LOW 36*TE, HIGH 1*TE
    bit 1: LOW 2*TE,  HIGH 1*TE
    bit 0: LOW 1*TE,  HIGH 2*TE

Usage:
    ht12.py list
    ht12.py key   --address 0xAF --button light          # Flipper key .sub to stdout
    ht12.py raw   --address 0xAF --button light          # Flipper RAW .sub to stdout
    ht12.py esphome --address 0xAF --button light        # ESPHome transmit_raw list
    ht12.py decode 0xAFE                                 # explain a 12-bit key
    ht12.py all   --address 0xAF --out ./out             # write every button as .sub
"""
import argparse
import os
import sys

FREQUENCY_HZ = 315_000_000
PRESET = "FuriHalSubGhzPresetOok650Async"
DEFAULT_TE = 433
SYNC_TE = 36

# Command nibble as it appears in the Flipper key (D8..D11, MSB first).
# Each button pulls one data line low; OFF pulls three low at once.
BUTTONS = {
    "fan_high":   0x7,  # 0111 -> D8 low
    "fan_medium": 0xB,  # 1011 -> D9 low
    "fan_low":    0xD,  # 1101 -> D10 low
    "light":      0xE,  # 1110 -> D11 low
    "fan_off":    0x1,  # 0001 -> D8+D9+D10 low
}
BY_CODE = {v: k for k, v in BUTTONS.items()}


def parse_int(s: str) -> int:
    return int(s, 0)


def key_for(address: int, button: str) -> int:
    if not 0 <= address <= 0xFF:
        raise ValueError("address must be 0x00..0xFF")
    if button not in BUTTONS:
        raise ValueError(f"unknown button {button!r}; choose from {', '.join(BUTTONS)}")
    return (address << 4) | BUTTONS[button]


def dip_string(address: int) -> str:
    """Flipper-style DIP view, A0..A7. '1' = pin tied low (switch ON)."""
    return "".join("0" if address & (1 << (7 - i)) else "1" for i in range(8))


def pulses(key: int, te: int = DEFAULT_TE, repeats: int = 10) -> list[int]:
    """Signed durations in microseconds: +high, -low."""
    frame = [-SYNC_TE * te, te]
    for i in range(11, -1, -1):
        if (key >> i) & 1:
            frame += [-2 * te, te]
        else:
            frame += [-te, 2 * te]
    return frame * repeats


def decode_pulses(durations: list[int], te: int = DEFAULT_TE) -> list[int]:
    """Minimal decoder used by the self-test; returns every key found."""
    keys, i, n = [], 0, len(durations)
    while i < n:
        if durations[i] < -20 * te and i + 1 < n and durations[i + 1] > 0:
            i += 2
            bits = []
            while len(bits) < 12 and i + 1 < n:
                lo, hi = -durations[i], durations[i + 1]
                bits.append(1 if lo > hi else 0)
                i += 2
            if len(bits) == 12:
                keys.append(int("".join(map(str, bits)), 2))
        else:
            i += 1
    return keys


def key_sub(key: int, te: int = DEFAULT_TE) -> str:
    return (
        "Filetype: Flipper SubGhz Key File\n"
        "Version: 1\n"
        f"Frequency: {FREQUENCY_HZ}\n"
        f"Preset: {PRESET}\n"
        "Protocol: Holtek_HT12X\n"
        "Bit: 12\n"
        f"Key: 00 00 00 00 00 00 {key >> 8:02X} {key & 0xFF:02X}\n"
        f"TE: {te}\n"
    )


def raw_sub(key: int, te: int = DEFAULT_TE, repeats: int = 10) -> str:
    d = pulses(key, te, repeats)
    lines = [
        "Filetype: Flipper SubGhz RAW File",
        "Version: 1",
        f"Frequency: {FREQUENCY_HZ}",
        f"Preset: {PRESET}",
        "Protocol: RAW",
    ]
    for j in range(0, len(d), 512):
        lines.append("RAW_Data: " + " ".join(str(x) for x in d[j:j + 512]))
    return "\n".join(lines) + "\n"


def describe(key: int) -> str:
    addr, cmd = key >> 4, key & 0xF
    name = BY_CODE.get(cmd, "unknown")
    return (f"key=0x{key:03X}  address=0x{addr:02X} (DIP A0..A7 {dip_string(addr)})  "
            f"command=0x{cmd:X} ({cmd:04b}) -> {name}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    for name in ("key", "raw", "esphome"):
        p = sub.add_parser(name)
        p.add_argument("--address", type=parse_int, required=True)
        p.add_argument("--button", required=True, choices=BUTTONS)
        p.add_argument("--te", type=int, default=DEFAULT_TE)
        if name != "key":
            p.add_argument("--repeats", type=int, default=10 if name == "raw" else 1)
    p = sub.add_parser("decode"); p.add_argument("key", type=parse_int)
    p = sub.add_parser("all")
    p.add_argument("--address", type=parse_int, required=True)
    p.add_argument("--out", default="out")
    p.add_argument("--te", type=int, default=DEFAULT_TE)
    sub.add_parser("selftest")
    a = ap.parse_args()

    if a.cmd == "list":
        for n, c in BUTTONS.items():
            print(f"{n:<11} 0x{c:X}  {c:04b}")
    elif a.cmd == "key":
        sys.stdout.write(key_sub(key_for(a.address, a.button), a.te))
    elif a.cmd == "raw":
        sys.stdout.write(raw_sub(key_for(a.address, a.button), a.te, a.repeats))
    elif a.cmd == "esphome":
        # ESPHome wants the list to start with a mark, so rotate the sync gap to the end.
        frame = pulses(key_for(a.address, a.button), a.te, 1)
        frame = frame[1:] + frame[:1]
        print("[" + ", ".join(str(x) for x in frame * a.repeats) + "]")
    elif a.cmd == "decode":
        print(describe(a.key))
    elif a.cmd == "all":
        os.makedirs(a.out, exist_ok=True)
        for n in BUTTONS:
            k = key_for(a.address, n)
            with open(os.path.join(a.out, f"{n}.sub"), "w") as f:
                f.write(key_sub(k, a.te))
            with open(os.path.join(a.out, f"{n}_raw.sub"), "w") as f:
                f.write(raw_sub(k, a.te))
        print(f"wrote {2 * len(BUTTONS)} files to {a.out}/")
    elif a.cmd == "selftest":
        for addr in range(256):
            for n in BUTTONS:
                k = key_for(addr, n)
                got = decode_pulses(pulses(k, repeats=3))
                assert got == [k] * 3, (hex(k), got)
        print("selftest ok: 256 addresses x 5 buttons round-trip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
