"""Write the C128 power footprint: square 5-pin DIN male plug, soldered straight through the board.

The C128 / Amiga 500 square DIN-5 (Power Dynamics DS-215 socket / DP-215 plug) puts its 5 contacts on
the same grid as a round 8-pin DIN (DIN 45326, 7 pins on a 7.0 mm circle at 45 deg + a centre pin):
the centre pin plus the four diagonal pins. So a genuine square DP-215-style plug insert OR a round
8-pin DIN plug insert with 3 pins pulled both fit this footprint.

Pinout per the user's Drunk'n'Retro C128-to-C64 adapter diagram (female = the C128 socket face), key at the top:
      2 GND        3 9VAC
            5 9VAC
      1 +5V        4 GND/NC
(Ray Carlsen / icomp number the two GND corners the other way round; same physical functions.)
The plug face is the mirror image. The plug sits on the TOP side with its mating face up, so the top
view is the plug face view. At rot 0 the key points to +y (as the C64 DIN-7 footprint).
usage: make_din5sq_fp.py <.pretty dir>"""
import sys, math

D = 3.5 / math.sqrt(2)               # diagonal pins of the DIN-8 7.0 mm circle
DRILL, PAD = 1.6, 2.4                 # same as the C64 board (DeadTest MAB6V drill)
# plug face, key towards +y (KiCad y points down the screen)
POS = {'1': (-D, -D), '4': (D, -D), '3': (D, D), '2': (-D, D), '5': (0.0, 0.0)}
NAMES = {'1': '+5V', '2': 'GND', '3': '9VAC', '4': 'GND/NC', '5': '9VAC'}
H = 4.2                               # half-size of the silk square around the pins only (the plug body may overhang the board edge)

pads = [f'\t(pad "{n}" thru_hole circle (at {x:.4f} {y:.4f}) (size {PAD} {PAD}) (drill {DRILL}) (layers "*.Cu" "*.Mask"))'
        for n, (x, y) in POS.items()]
fab = [f'\t(fp_text user "{n}" (at {x * 1.75:.3f} {y * 1.75:.3f} 0) (layer "F.Fab") (effects (font (size 0.7 0.7) (thickness 0.1))))'
       for n, (x, y) in POS.items()]


def sq(layer, h, w):
    pts = [(-h, -h), (h, -h), (h, h), (-h, h), (-h, -h)]
    return '\n'.join(f'\t(fp_line (start {a[0]} {a[1]}) (end {b[0]} {b[1]}) (stroke (width {w}) (type solid)) (layer "{layer}"))'
                     for a, b in zip(pts, pts[1:]))


fp = f'''(footprint "DIN-5_Square_Male_PCB_C128"
\t(version 20241229)
\t(generator "make_din5sq_fp.py")
\t(layer "F.Cu")
\t(descr "C128 power: square 5-pin DIN (DP-215 type) male plug insert, pins through the board, plug on the top side. Contacts on the DIN-8 grid: centre + 4 diagonals of a 7.0 mm circle (4.95 mm square). Key towards +y. Round DIN-8 insert (7 around + centre) with the 3 unused pins pulled; it has NO key for the square socket, the case must key it.")
\t(tags "square DIN 5-pin male plug C128 Amiga power DS-215 DP-215 DIN-8")
\t(attr through_hole)
\t(property "Reference" "J2" (at 0 -5.6 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "DIN-5 square male" (at 0 5.6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
{sq("F.SilkS", H, 0.12)}
\t(fp_line (start -1.2 {H}) (end 0 {H - 1.2}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_line (start 0 {H - 1.2}) (end 1.2 {H}) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
{sq("F.Fab", H, 0.1)}
{sq("F.CrtYd", H + 0.3, 0.05)}
\t(fp_circle (center 0 0) (end 5.2 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))
\t(fp_text user "KEY" (at 0 {H - 2.2} 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))
''' + '\n'.join(pads + fab) + '\n)\n'
open(sys.argv[1] + '/DIN-5_Square_Male_PCB_C128.kicad_mod', 'w').write(fp)
print('wrote DIN-5_Square_Male_PCB_C128:', {n: (round(x, 3), round(y, 3), NAMES[n]) for n, (x, y) in POS.items()})
