"""Build the unrouted C64 USB-C PD Power Adapter board (v0.2) from the schematic + netlist.
2-layer. The male DIN-7 (J2) sits on the TOP side with its pins soldered through, like the DeadTest serial
board; every SMD part is on the BOTTOM so JLC can assemble the whole board in one pass (J2 hand-soldered).
The board lies flat against the C64's side: DIN at the front end, USB-C mouth at the rear end.
usage: python3 -I gen_pcb.py <project dir>     (needs <project dir>/net.net from kicad-cli)"""
import sys, os
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, first

D = os.path.abspath(sys.argv[1])
NAME = 'C64 USB-C PD Power Adapter'
LIB = 'C64_PD_PSU'
mm = pcbnew.FromMM
V = lambda x, y: pcbnew.VECTOR2I(mm(x), mm(y))

X0, Y0, Y1 = 100.0, 100.0, 124.0
JX = 142.4                      # USB-C centre; flipped + rot 270 puts the mouth on +x
X1 = round(JX + 4.2 - 0.5, 2)   # mouth 0.5 mm over the rear edge
DINX, DINY = 108.0, 112.0       # plug body (r 6.6) 1.4 mm inside the front edge
B = True
# ref: (x, y, rot, bottom)   coordinates are seen from the top
PLACE = {
    'J2': (DINX, DINY, 0, False),       # notch towards the board's bottom edge (+y)
    'J1': (JX, DINY, 270, B),
    # output protection in the corners above / below the DIN (its solder side is ringed by a 5.2 mm B.CrtYd)
    'F1': (104.4, 102.2, 0, B), 'D1': (110.2, 102.2, 0, B),
    'F2': (104.4, 121.8, 0, B), 'D2': (110.2, 121.8, 0, B),
    # 5 V buck, top half
    'L1': (118.6, 104.4, 0, B),
    'U2': (126.0, 103.0, 180, B),
    'C5': (125.9, 106.0, 0, B),
    'C3': (130.6, 102.2, 90, B),
    'C4': (129.4, 106.0, 0, B),
    'R4': (132.6, 102.2, 90, B), 'R5': (133.8, 102.2, 90, B),
    'C6': (116.0, 109.6, 0, B), 'C7': (120.0, 109.6, 0, B),
    'R6': (124.8, 109.6, 0, B), 'R7': (127.2, 109.6, 0, B), 'C8': (126.0, 110.9, 0, B),
    # 12 V buck, bottom half
    'L2': (117.6, 118.6, 0, B),
    'U3': (124.0, 120.0, 180, B),
    'C11': (124.0, 117.2, 0, B),
    'C9': (128.6, 121.6, 0, B),
    'C10': (128.6, 118.6, 0, B),
    'R9': (131.6, 120.0, 90, B), 'R10': (132.8, 120.0, 90, B),
    'C12': (116.0, 113.8, 0, B), 'C13': (120.0, 113.8, 0, B),
    'R11': (124.0, 114.4, 0, B), 'R12': (126.4, 114.4, 0, B), 'C14': (125.2, 115.7, 0, B),
    # power LED
    'D3': (131.5, 110.6, 0, B), 'R8': (131.5, 112.8, 0, B),
    # PD sink above the USB-C, output switch below it
    'U1': (142.0, 103.6, 0, B),
    'C1': (136.6, 101.6, 0, B),
    'R1': (136.6, 104.2, 0, B),
    'Q1': (141.0, 120.6, 0, B),
    'R2': (136.6, 119.4, 0, B), 'R3': (136.6, 121.0, 0, B),
    'C2': (133.2, 117.0, 0, B),
}
SILK = [  # text, x, y, layers, size[, angle]   (top side is empty apart from the DIN)
    ('C64 USB-C PD PSU v0.2', 128.0, 104.0, 'F', 1.0),
    ('DIN: GND 1237  +5V 45  +12V 6', 125.5, 107.0, 'F', 0.8),
    ('USB-C PD 15V in', 133.0, 112.0, 'F', 0.8),
]

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

for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(board); z.SetLayer(layer); z.SetNet(getnet('GND')); z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)):
        ol.Append(mm(x), mm(y))
    board.Add(z)

board.Save(f'{D}/{NAME}.kicad_pcb')
print('board %.2f x %.2f mm' % (X1 - X0, Y1 - Y0))
for fp in board.GetFootprints():
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd).BBox()
    print('%-4s %s  x %.2f..%.2f  y %.2f..%.2f' % (fp.GetReference(), 'B' if fp.IsFlipped() else 'F',
          cy.GetLeft() / 1e6, cy.GetRight() / 1e6, cy.GetTop() / 1e6, cy.GetBottom() / 1e6))
sys.stdout.flush(); os._exit(0)
