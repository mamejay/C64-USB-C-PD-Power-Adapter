"""v0.2 board prep on the user's re-oriented board (whole board rotated 180, DIN notch up).
Step 1 (pcbnew): every text upright, J2 holes 1.6 mm / 2.4 mm pads (same as the DeadTest serial adapter).
Step 2 (text edit): 6 mm strip added along the top edge with two M2.5 holes for a future case; GND pours
removed for routing. Done as text because after any RemoveNative/new FOOTPRINT this KiCad 10 build's
SWIG hands back untyped objects.
usage: prep_v02.py board.kicad_pcb"""
import sys, os, re, uuid, subprocess
brd = os.path.abspath(sys.argv[1])

if len(sys.argv) == 2:          # step 1 in its own process, then step 2
    subprocess.run([sys.executable, '-I', __file__, brd, 'pcbnew'], check=True)
else:
    import pcbnew
    b = pcbnew.LoadBoard(brd); mm = pcbnew.FromMM
    V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
    u1 = b.FindFootprintByReference('U1')    # CC pins (6/7) to face the USB-C instead of the board edge
    u1.SetOrientationDegrees((u1.GetOrientationDegrees() + 180) % 360)
    j2 = b.FindFootprintByReference('J2')
    for p in j2.Pads():
        p.SetDrillSize(V(1.6, 1.6)); p.SetSize(pcbnew.PADSTACK.ALL_LAYERS, V(2.4, 2.4))
        p.SetShape(pcbnew.PADSTACK.ALL_LAYERS, pcbnew.PAD_SHAPE_CIRCLE)   # square pin 1 would be 0.07 mm from pins 4/6
    n = 0
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT):
            d.SetTextAngleDegrees(0); n += 1
    for fp in b.GetFootprints():
        for t in [fp.Reference(), fp.Value()] + [g for g in fp.GraphicalItems() if isinstance(g, pcbnew.PCB_TEXT)]:
            t.SetTextAngleDegrees(0); n += 1
    jp = j2.GetPosition()
    j2.Reference().SetPosition(pcbnew.VECTOR2I(jp.x, jp.y + mm(8.4)))   # below the plug ring, notch is now up
    b.Save(brd)
    print('step 1: %d texts upright, J2 drill 1.6 / pad 2.4' % n)
    sys.stdout.flush(); os._exit(0)

# ---------------- step 2: text edits
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find, first
tree = parse(open(brd).read())[0]
xs, ys = [], []
for g in find(tree, 'gr_line') + find(tree, 'gr_arc'):
    if first(g, 'layer')[1] == 'Edge.Cuts':
        for k in ('start', 'end', 'mid'):
            e = first(g, k)
            if e:
                xs.append(float(e[1])); ys.append(float(e[2]))
X0, X1, Y1 = min(xs), max(xs), max(ys)
Y0 = round(min(ys) - 6.0, 2)
HOLES = {'H1': (round(X0 + 3.4, 2), round(Y0 + 3.1, 2)), 'H2': (round(X1 - 3.4, 2), round(Y0 + 3.1, 2))}
keep = []
for e in tree:
    if isinstance(e, list) and e and e[0] in ('gr_line', 'gr_arc', 'gr_rect') and first(e, 'layer')[1] == 'Edge.Cuts':
        continue
    if isinstance(e, list) and e and e[0] == 'zone':
        continue
    if isinstance(e, list) and e and e[0] == 'footprint' and any(
            p[1] == 'Reference' and p[2] in HOLES for p in find(e, 'property')):
        continue
    keep.append(e)
tree[:] = keep
U = lambda s: Q(str(uuid.uuid5(uuid.NAMESPACE_URL, 'c64-pd-psu-edge-' + s)))
R = 1.0
st = ['stroke', ['width', 0.1], ['type', 'solid']]
def line(a, c, tag):
    tree.append(['gr_line', ['start', a[0], a[1]], ['end', c[0], c[1]], st, ['layer', Q('Edge.Cuts')], ['uuid', U(tag)]])
def arc(s_, m, e, tag):
    tree.append(['gr_arc', ['start', s_[0], s_[1]], ['mid', m[0], m[1]], ['end', e[0], e[1]], st, ['layer', Q('Edge.Cuts')], ['uuid', U(tag)]])
line((X0 + R, Y0), (X1 - R, Y0), 't'); line((X1, Y0 + R), (X1, Y1 - R), 'r'); line((X1 - R, Y1), (X0 + R, Y1), 'b'); line((X0, Y1 - R), (X0, Y0 + R), 'l')
k = R * (1 - 0.70710678)
arc((X0, Y0 + R), (X0 + k, Y0 + k), (X0 + R, Y0), 'a1'); arc((X1 - R, Y0), (X1 - k, Y0 + k), (X1, Y0 + R), 'a2')
arc((X1, Y1 - R), (X1 - k, Y1 - k), (X1 - R, Y1), 'a3'); arc((X0 + R, Y1), (X0 + k, Y1 - k), (X0, Y1 - R), 'a4')
# mounting holes from the stock footprint, board-only and out of BOM / CPL
mh = parse(open('/usr/share/kicad/footprints/MountingHole.pretty/MountingHole_2.7mm_M2.5.kicad_mod').read())[0]
for ref, (x, y) in HOLES.items():
    f = ['footprint', Q('C64_PD_PSU:MountingHole_2.7mm_M2.5'), ['layer', Q('F.Cu')], ['uuid', U(ref)], ['at', x, y]]
    for e in mh[2:]:
        if not isinstance(e, list) or e[0] in ('version', 'generator', 'generator_version', 'layer', 'embedded_fonts'):
            continue
        e = [x_ for x_ in e]
        if e[0] == 'attr':
            e = ['attr', 'exclude_from_pos_files', 'exclude_from_bom', 'board_only']
        if e[0] == 'property' and e[1] == 'Reference':
            e[2] = Q(ref)
        if e[0] == 'property' and e[1] == 'Value':
            e[2] = Q('M2.5')
        f.append(e)
    tree.append(f)
open(brd, 'w').write(dump(tree) + '\n')
print('step 2: outline %.2f..%.2f x %.2f..%.2f (%.1f x %.1f mm), holes %s' % (X0, X1, Y0, Y1, X1 - X0, Y1 - Y0, HOLES))
