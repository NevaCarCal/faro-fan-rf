# faro-fan-rf

Control a **Faro Barcelona** ceiling fan with an **AS-3DN** RF receiver (Air-Supply
Technology) from a Flipper Zero, ESPHome or Home Assistant. You don't need the original remote.

| | |
|---|---|
| Receiver | AS-3DN (Air-Supply), US FCC ID [`SQ8AS-3DN`](https://fccid.io/SQ8AS-3DN) |
| Frequency | 315 MHz, OOK (EU unit) |
| Protocol | Holtek HT12-style, 12 bits: 8-bit address and 4-bit command |
| Buttons | Light, fan low / medium / high, fan off |

## What's the fan model?

It's lost to time. I genuinely looked everywhere, short of actually unbolting the fan from the ceiling and looking under the mounting plate, and saw no serial / part number. Even if I did, I already checked the Faro website manually to see if I could find it there, and it seems it's been discontinued. Or maybe I'm just awful at searching for stuff. Either or. 

In any case, This should hopefully work for any ceiling fan / light of this brand with this exact receiver. Hopefully.

## Quick start (For a Flipper Zero)

1. Copy `codes/*.sub` to `SD/subghz/` on the Flipper.
2. Open **Sub-GHz → Saved**, pick a file and press **Send**.

If nothing happens, your remote /receiver probably used a different address. See the next section.

## My address

The remote and receiver each have a 4-position DIP block. The reference unit (Mine) has all four set to OFF, which gives address 0xAF. Switches 1–4 set the low four address bits (ON = 0), and the upper four bits are fixed at 0xA. At least, this is what I could infer from digging around in the fan. Set the remote and receiver to the same position.

## Here is an example of this receiver with all dips set to ON
### Please mind that this is not the configuration I had for testing / working, and is just illustrative to visualize what the dip switch states are / mean. My actual configuration is all switches set down, away from the "ON" text on the blue switch carrier.
<img width="459" height="850" alt="image" src="https://github.com/user-attachments/assets/235b8faf-159b-42ee-8395-f5ac7f4dba71" />


## Codes for your own address

Capture any button from your remote with **Sub-GHz → Read** at 315 MHz. It should
decode as `Holtek_HT12X`. The first two hex digits of the 12-bit key are your address.

```bash
python3 tools/ht12.py decode 0xAFE          # explain a key
python3 tools/ht12.py all --address 0xAF    # write .sub files for every button to ./out
python3 tools/ht12.py esphome --address 0xAF --button light
python3 tools/ht12.py selftest
```

The script needs only Python 3.9+ and has no dependencies.

## Button codes (address 0xAF)

| Button     | Key     | Flipper file              |
|------------|---------|---------------------------|
| Light      | `0xAFE` | `captures/light.sub`      |
| Fan low    | `0xAFD` | `captures/fan_low.sub`    |
| Fan medium | `0xAFB` | `captures/fan_medium.sub` |
| Fan high   | `0xAF7` | `captures/fan_high.sub`   |
| Fan off    | `0xAF1` | `captures/fan_off.sub`    |

[PROTOCOL.md](PROTOCOL.md) documents the full frame layout and timings.

## Repository layout

```
codes/                  Codes found to work with receiver (Holtek_HT12X key files)
integrations/flipper/   RAW .sub versions, for tools that don't decode HT12X
integrations/esphome/   ESP32 + 315 MHz transmitter config; exposes buttons to Home Assistant
tools/ht12.py           Encoder/decoder and .sub/ESPHome generator
docs/hardware.md        Receiver label, MCU photo, FCC filing, retail kit notes
```

## ESPHome / Home Assistant

`integrations/esphome/faro-fan.yaml` sets up an ESP32 with a cheap **315 MHz** ASK
transmitter module on GPIO4. The fan's buttons show up as entities in Home
Assistant. Check that you have a 315 MHz module and not the more common 433 MHz one.

## Legal and safety

- This project documents signals captured from hardware that I myself PURCHASED and OWN, to make it
  work with home automation. No firmware, manuals or other manufacturer material is included.
- Faro Barcelona and Air-Supply are trademarks of their owners. This project is not
  affiliated with or endorsed by either company.
- Transmitting radio signals is regulated. 315 MHz is not a harmonised short-range-device
  band in the EU. Transmit only at power levels like the original remote's, and check your
  local rules. You use this project at your own risk. I'm not liable for your local military
  showing up at your doorstep.
- The receiver switches mains voltage. Turn off the circuit breaker before you open or rewire it.
  Most probe points and the dip switches should be fine to work around, but again. NEVER operate on
  live electronics.

## Contributing

Captures from other switch settings, other Faro models, the dimmer/timer variants,
or an identification of the `HT48R06A-1` MCU are all welcome. Please open an issue or a pull request.
I can't promise to keep this updated or anything tho. This is a personal project and nothing more.

## License

MIT, see [LICENSE](LICENSE).
