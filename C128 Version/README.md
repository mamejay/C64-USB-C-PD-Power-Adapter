# C128 USB-C PD Power Adapter (v0.1)

The Commodore 128 variant of the C64 adapter. It plugs straight into the C128's square 5-pin power socket and runs from a USB-C PD charger offering 15 V (45 W or more).

**Status: v0.1, routed, JLCPCB files generated, not yet built or tested.**

![bottom](Docs/bottom_3d.png)

## What it does
| Output | DIN pin | Source |
|---|---|---|
| +5.10 V, ~3 A (5 A part) | 1 | SY8205 buck (U2), 4.7 µH 8x8 mm inductor |
| +12.3 V DC | 3 (one leg of the C128's "9 VAC" input) | TPS54302 buck (U3) |
| GND | 2, 4, 5 (5 = the other 9 VAC leg) | |

It shares its input side with the C64 board:
- **PD sink:** a CH224A requests 15 V.
- **Output switch:** a P-MOSFET (Q1) connects the 15 V only once the PD contract is made.
- **Lockout:** both bucks have an EN-pin UVLO that starts at about 13.3 V.

## Power connector (J2)
- **Socket grid:** the C128 socket (the same square shell the Amiga 500 uses) puts its 5 contacts on the **round 8-pin DIN grid**: the centre pin plus the 4 diagonal pins of the 7.0 mm circle.
- **J2 is a round 8-pin DIN male insert** (7 around plus a centre pin) with the 3 unused pins pulled. It is soldered through the board from the top side, like the C64 version.
- **Pinout:** taken from the Drunk'n'Retro C128-to-C64 adapter diagram. Looking at the plug face, key up:
  ```
    3 (+12V)    2 (GND)
          5 (GND)
    4 (GND)     1 (+5V)
  ```
- **Position:** the DIN centre is 4.5 mm from the board's right edge, so the board stays clear of the C128's power switch.
- **Keying warning:** a round insert has **no key in the square socket**. Rotated 90°, it would put 12 V on the C128's +5 V rail. Use a keyed shroud or case, and mark the top. No case is provided yet.

## Protection
- **USB-PD gating and UVLO:** nothing is powered unless a 15 V contract is made.
- **Current limit:** both bucks have current limiting and thermal shutdown.
- **TVS:** an SMF5.0A on +5 V and an SMF13A on +12 V.
- **Not included yet:**
  - A dedicated over-voltage cutoff on +5 V.
  - A fuse on +5 V. No JLC-stocked 3 A PTC is rated above 8 V.

## Before the first power-up
Leave the adapter **unplugged from the C128**. Pin 1 should read 5.1 V, pin 3 should read 12.3 V, and pins 2/4/5 should read 0 V.

Also check JLC's placement preview for **U2**: the SOIC-8-EP rotation hasn't been confirmed yet.

## Files
- `KiCad/`: KiCad 10 project.
- `scripts/`: the generators and the routing pipeline (`rebuild_route.sh`, then `pours_c128.py`, `texts_upright.py`, `make_fab.py`). Freerouting 2.5.0 runs through `FREEROUTING_JAR`.
- `JLCPCB Output/`: Gerbers, BOM, CPL and `ORDER NOTES.txt`.
- `Docs/`: schematic PDF and renders.
