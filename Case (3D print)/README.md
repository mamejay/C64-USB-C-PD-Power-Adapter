# Case (3D print), for C64 USB-C PD Power Adapter v0.3

OpenSCAD source: `c64_pd_psu_case.scad`. Set `part` to "base", "lid", "both" or "assembly".

**Not test-printed yet.**

| Part | Size | Print |
|---|---|---|
| Base (tray on the parts side, faces away from the C64) | 49.8 x 33.7 x 8.9 mm | floor down, no supports |
| Lid (faces the C64, DIN plug pokes through) | 46.3 x 31.2 x 1.6 mm | inner face (tabs) down, no supports |

Use **PETG or ABS**, not PLA, because the two bucks get warm. Walls are 1.6 mm and the floor 1.2 mm.

## What's in it
- **USB-C opening** in the left wall, 12.6 x 7 mm, for the cable's plug overmold.
- **Supports under the PCB:**
  - two screw standoffs at the M2.5 holes;
  - a ring under the DIN-7 solder joints, which carries the plug-in force;
  - edge ledges wherever no part is within 0.9 mm of the board edge.
- **LED window** (2.4 mm) under D3.
- **Vent slots** under the two bucks.
- **Label** on the base: "C64 USB-C PD / 15V PD in".
- **Lid:**
  - DIN hole, 14 mm by default;
  - two countersunk M2.5 holes, so the heads sit flush and nothing sticks out towards the C64;
  - "+5V 4/5 +12V 6" legend;
  - two tabs that hook into slots in the base's bottom wall.

## Assembly
1. Solder J2 (DIN-7) from the top. **Trim its pins on the solder side to 3.5 mm or less.** There is 4.5 mm under the board.
2. Drop the PCB into the base, parts side down.
3. Hook the lid's tabs into the bottom-wall slots, lay the lid flat, and fit 2x **M2.5 x 8 countersunk** self-tapping screws. Standoff pilots are 2.2 mm.
   - For heat-set inserts instead, change the pilot to 3.6 mm in the .scad and use M2.5 machine screws.

## Check before printing
- **`din_hole_d`:** measure your DIN-7 plug insert and set this. The default is 14 mm.
- **DIN reach:** the lid is 1.6 mm thick, which takes 1.6 mm off how far the plug sticks out. Check the plug still seats fully in the C64's socket.
