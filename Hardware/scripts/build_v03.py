"""Rebuild the board from the schematic + netlist with a saved placement (v0.3: 0603 passives, FXL0530 for L1).
Placement, orientation and side for every part come from place.json (dumped from the user-oriented v0.2 board by
dump_place.py); an optional overrides.json nudges parts whose bigger 0603 footprints now collide.
Board outline = the v0.2 rectangle (with the mounting-hole strip); holes are added afterwards by add_holes.py.
usage: python3 -I build_v03.py <project dir> <place.json> [overrides.json]"""
import sys, os, json
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, first

D = os.path.abspath(sys.argv[1])
NAME = 'C64 USB-C PD Power Adapter'
LIB = 'C64_PD_PSU'
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))
J = json.load(open(sys.argv[2]))
OVR = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
X0, Y0, X1, Y1 = 100.9, 95.0, 147.0, 125.0
PLACE = {r: tuple(v) for r, v in J['fps'].items() if not r.startswith('H')}
for r, v in OVR.items():
    PLACE[r] = tuple(v)
SILK = [(t.replace('v0.2', 'v0.3'), x, y, 'F', size) for t, x, y, layer, size in J['texts']]

sch = parse(open(f'{D}/{NAME}.kicad_sch').read())[0]
syms = {}
for s in find(sch, 'symbol'):
    props = {p[1]: p[2] for p in find(s, 'property')}
    if props['Reference'].startswith('#'):
        continue
    syms[props['Reference']] = dict(uuid=first(s, 'uuid')[1], fp=props['Footprint'], value=props['Value'],
                                    lcsc=props.get('LCSC', ''), desc=props.get('Description', ''),
                                    ds=props.get('Datasheet', ''), inbom=first(s, 'in_bom')[1] == 'yes')
pinnet = {}
n = parse(open(f'{D}/net.net').read())[0]
for net in find(first(n, 'nets'), 'net'):
    name = first(net, 'name')[1]
    for node in find(net, 'node'):
        pinnet[(first(node, 'ref')[1], first(node, 'pin')[1])] = name

board = pcbnew.BOARD()
board.SetCopperLayerCount(2)
nets = {}
def getnet(name):
    if name not in nets:
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
    return nets[name]

assert set(syms) == set(PLACE), (set(syms) ^ set(PLACE))
for ref in sorted(syms):
    s = syms[ref]
    lib, fpname = s['fp'].split(':'); assert lib == LIB, s['fp']
    fp = pcbnew.FootprintLoad(f'{D}/{LIB}.pretty', fpname); assert fp, s['fp']
    fp.thisown = False
    fp.SetFPID(pcbnew.LIB_ID(lib, fpname))
    fp.SetReference(ref); fp.SetValue(s['value'])
    if s['lcsc']:
        fp.SetField('LCSC', s['lcsc']); f = fp.GetField('LCSC'); f.SetVisible(False); f.SetLayer(pcbnew.F_Fab)
    fp.SetPath(pcbnew.KIID_PATH('/' + s['uuid']))
    fp.GetField('Description').SetText(s['desc']); fp.GetField('Datasheet').SetText(s['ds'])
    fp.SetExcludedFromBOM(not s['inbom'])
    fp.SetSheetfile(f'{NAME}.kicad_sch'); fp.SetSheetname('Root')
    board.Add(fp)
    x, y, rot, back = PLACE[ref]
    if back:
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
    for pad in fp.Pads():
        nn = pinnet.get((ref, pad.GetNumber()))
        if nn:
            pad.SetNet(getnet(nn))
        elif ref == 'U1' and pad.GetNumber() == '':     # EP paste-only sub-pads
            pad.SetNet(getnet('GND'))
    fp.SetPosition(V(x, y))
    fp.SetOrientationDegrees(rot)
    # small reference on the fab layer, value hidden (keeps JLC silk minimums out of the way)
    r = fp.Reference(); r.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
    r.SetTextSize(V(0.5, 0.5)); r.SetTextThickness(mm(0.08)); r.SetPosition(fp.GetPosition())
    fp.Value().SetVisible(False)

R = 1.0   # corner radius, all four corners
def seg(a, b):
    l = pcbnew.PCB_SHAPE(board); l.SetShape(pcbnew.SHAPE_T_SEGMENT)
    l.SetStart(V(*a)); l.SetEnd(V(*b)); l.SetLayer(pcbnew.Edge_Cuts); l.SetWidth(mm(0.1)); board.Add(l)
seg((X0 + R, Y0), (X1 - R, Y0)); seg((X1, Y0 + R), (X1, Y1 - R)); seg((X1 - R, Y1), (X0 + R, Y1)); seg((X0, Y1 - R), (X0, Y0 + R))
for c, st in (((X0 + R, Y0 + R), (X0, Y0 + R)), ((X1 - R, Y0 + R), (X1 - R, Y0)), ((X1 - R, Y1 - R), (X1, Y1 - R)), ((X0 + R, Y1 - R), (X0 + R, Y1))):
    a = pcbnew.PCB_SHAPE(board); a.SetShape(pcbnew.SHAPE_T_ARC); a.SetLayer(pcbnew.Edge_Cuts); a.SetWidth(mm(0.1))
    a.SetCenter(V(*c)); a.SetStart(V(*st)); a.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(90, pcbnew.DEGREES_T), True); board.Add(a)

for txt, x, y, layers, size, *ang in SILK:
    for L in layers:
        t = pcbnew.PCB_TEXT(board); t.SetText(txt)
        t.SetLayer(pcbnew.F_SilkS if L == 'F' else pcbnew.B_SilkS)
        t.SetPosition(V(x, y)); t.SetTextSize(V(size, size)); t.SetTextThickness(mm(0.15))
        if L == 'B': t.SetMirrored(True)
        if ang: t.SetTextAngleDegrees(ang[0])
        board.Add(t)

# no zones here: GND is routed as tracks first, gnd_pours.py adds the pours after routing
board.Save(f'{D}/{NAME}.kicad_pcb')
print('board %.2f x %.2f mm' % (X1 - X0, Y1 - Y0))
for fp in board.GetFootprints():
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd).BBox()
    print('%-4s %s  x %.2f..%.2f  y %.2f..%.2f' % (fp.GetReference(), 'B' if fp.IsFlipped() else 'F',
          cy.GetLeft() / 1e6, cy.GetRight() / 1e6, cy.GetTop() / 1e6, cy.GetBottom() / 1e6))
sys.stdout.flush(); os._exit(0)
