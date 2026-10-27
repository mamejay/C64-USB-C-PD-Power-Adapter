"""Write the C64 power DIN-7 footprint: a DIN 45329 male plug insert soldered straight through the board.
Pin geometry from the Hirschmann MAS 70 S drawing (plug face): 7 pins on a 7.0 mm circle, 45 deg apart,
pin 2 opposite the key notch; face view = 5 2 4 / 3 . 1 / 7 6. The plug sits on the TOP side (mating face
up), so the top view is the face view. Key notch towards +y (board bottom edge) at rot 0.
usage: make_din_fp.py <.pretty dir>"""
import sys, math
R, DRILL, PAD = 3.5, 1.6, 2.4        # pin circle radius, hole, pad: same 1.6 mm drill as the DeadTest serial board (Eagle 25% restring -> 2.4 mm)
ANG = {'1': 0, '4': 45, '2': 90, '5': 135, '3': 180, '7': 225, '6': 315}   # CCW from +x, plug face
pads = []
for n, a in ANG.items():
    x, y = R * math.cos(math.radians(a)), -R * math.sin(math.radians(a))
    shape = 'circle'      # pin 1 round too: a 2.4 mm square would sit 0.07 mm from pins 4/6
    pads.append(f'\t(pad "{n}" thru_hole {shape} (at {x:.4f} {y:.4f}) (size {PAD} {PAD}) (drill {DRILL}) (layers "*.Cu" "*.Mask"))')
fp = f'''(footprint "DIN-7_Male_PCB_C64"
\t(version 20241229)
\t(generator "make_din_fp.py")
\t(layer "F.Cu")
\t(descr "C64 power: 7-pin DIN 45329 male plug insert, pins through the board, plug on the top side. Pin circle 7.0 mm, 45 deg pitch, notch towards +y. Verify drill against the actual insert pins.")
\t(tags "DIN 45329 7-pin male plug C64 power")
\t(attr through_hole)
\t(property "Reference" "J2" (at 0 -8.2 0) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
\t(property "Value" "DIN-7 male" (at 0 8.6 0) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
\t(fp_circle (center 0 0) (end 6.6 0) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS"))
\t(fp_line (start -1.2 6.6) (end 0 5.4) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_line (start 0 5.4) (end 1.2 6.6) (stroke (width 0.12) (type solid)) (layer "F.SilkS"))
\t(fp_circle (center 0 0) (end 6.6 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab"))
\t(fp_circle (center 0 0) (end 7.0 0) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd"))
\t(fp_circle (center 0 0) (end 5.2 0) (stroke (width 0.05) (type solid)) (fill no) (layer "B.CrtYd"))
\t(fp_text user "KEY" (at 0 4.1 0) (layer "F.Fab") (effects (font (size 0.6 0.6) (thickness 0.1))))
''' + '\n'.join(pads) + '\n)\n'
open(sys.argv[1] + '/DIN-7_Male_PCB_C64.kicad_mod', 'w').write(fp)
print('wrote DIN-7_Male_PCB_C64')
