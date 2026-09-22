# Protocol: AS-3DN fan receiver

## Radio

| Parameter   | Value                                   |
|-------------|-----------------------------------------|
| Frequency   | 315.000 MHz (EU unit; the US FCC version is 303 MHz) |
| Modulation  | OOK / ASK                               |
| Encoding    | Holtek HT12-style PWM, 12 bits          |
| TE (base)   | ~433 µs (Proven working with Flipper Zero, could be different from factory) |
| Repeats     | The remote repeats the frame while a button is held. ~10 repeats is reliable. |

## Frame

```
 sync gap      start   bit 11 ................................ bit 0
 LOW 36·TE    HIGH TE  [A0][A1][A2][A3][A4][A5][A6][A7][D8][D9][D10][D11]
```

Bits are sent MSB first. On a Flipper this is the `Holtek_HT12X` protocol, and the
`Key:` field holds the 12 bits in its last 1½ bytes.

| Symbol | Low    | High   |
|--------|--------|--------|
| sync   | 36 TE  | 1 TE   |
| bit 1  | 2 TE   | 1 TE   |
| bit 0  | 1 TE   | 2 TE   |

One frame lasts about 36 + 1 + 12×3 = 73 TE ≈ 31.6 ms.

## Address (8 bits)

The upper 8 bits are the address set by the code switches. HT12-type encoders
read a floating address pin as `1` and a pin tied to ground (switch ON) as `0`.

The reference unit uses address **`0xAF`** (`1010 1111`). The Flipper shows this as
`DIP: 01010000`, where `1` means that pin is tied low.

Receiver and remote only need to match each other. If your codes differ only
in the first byte, you have a different switch setting, not a different protocol.

## Command (4 bits, active-low)

Each button pulls one data line low. **Off** pulls three lines low at once.

| Button     | Nibble | Binary (D8 D9 D10 D11) | Full key (addr 0xAF) |
|------------|--------|------------------------|----------------------|
| Fan high   | `0x7`  | `0111`                 | `0xAF7`              |
| Fan medium | `0xB`  | `1011`                 | `0xAFB`              |
| Fan low    | `0xD`  | `1101`                 | `0xAFD`              |
| Light      | `0xE`  | `1110`                 | `0xAFE`              |
| Fan off    | `0x1`  | `0001`                 | `0xAF1`              |

The light button toggles. The receiver keeps track of on/off itself, so the
command carries no state.

## Untested

- Other nibble values (for example `0x0`, `0x3`, `0x5`) might trigger dimming,
  timers or reverse on receivers that support them. Pull requests with results are welcome.
  This specific unit has none of those features from factory, so even tho I tested a bunch of them, I couldn't find anything useful.
