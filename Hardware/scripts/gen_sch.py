"""Generate the C64 USB-C PD Power Adapter schematic (KiCad 10) and its project symbol library.

DC-only C64 power supply in the style of the Sordan/RetroJoy adapter: a USB-PD sink (CH224A) asks the
charger for 15 V; one TPS54302 buck makes +5 V for DIN pins 4/5, a second makes a regulated +12 V for
DIN pin 6 (the C64's "9 VAC" input; 12 V DC = the peak of the stock 9 VAC) with pin 7 at GND.
Both outputs stay off until the PD contract is in place: Q1 is switched by CH224A PG, and both bucks have
an EN-pin UVLO (~13.2 V start) so a 5/9/12 V source never powers the C64.
v0.2: J2 is a male DIN-7 soldered straight to the board (as the DeadTest serial board); SMD parts on the back.
Every pin gets a 2.54 mm stub ending in a power symbol or net label; unused pins get a no-connect flag.
usage: python3 -I gen_sch.py <project dir>
"""
import sys, os, uuid, copy, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find, first

OUT = sys.argv[1]
NAME = 'C64 USB-C PD Power Adapter'
LIBNICK = 'C64_PD_PSU'
STD = '/usr/share/kicad/symbols'
ROOT = str(uuid.uuid5(uuid.NAMESPACE_URL, 'c64-pd-psu-root'))
_n = [0]


def uid():
    _n[0] += 1
    return Q(str(uuid.uuid5(uuid.NAMESPACE_URL, 'c64-pd-psu-%d' % _n[0])))


_libcache = {}


def load_lib(path):
    if path not in _libcache:
        tree = parse(open(path).read())[0]
        _libcache[path] = {s[1]: s for s in find(tree, 'symbol')}
    return _libcache[path]


# project symbol name -> (source library file, source symbol name)
SOURCES = {
    'CH224K': (f'{STD}/Interface_USB.kicad_sym', 'CH224K'),       # CH224A is pin-compatible (pin 1 = VHV)
    'TPS54302': (f'{STD}/Regulator_Switching.kicad_sym', 'TPS54302'),
    'AO3401A': (f'{STD}/Transistor_FET.kicad_sym', 'AO3401A'),
    'USB_C_Receptacle_USB2.0_16P': (f'{STD}/Connector.kicad_sym', 'USB_C_Receptacle_USB2.0_16P'),
    'DIN-7': (f'{STD}/Connector.kicad_sym', 'DIN-7'),
    'Polyfuse': (f'{STD}/Device.kicad_sym', 'Polyfuse'),
    'D_Zener': (f'{STD}/Device.kicad_sym', 'D_Zener'),         # unidirectional TVS
    'LED': (f'{STD}/Device.kicad_sym', 'LED'),
    'L': (f'{STD}/Device.kicad_sym', 'L'),
    'R': (f'{STD}/Device.kicad_sym', 'R'),
    'C': (f'{STD}/Device.kicad_sym', 'C'),
    'GND': (f'{STD}/power.kicad_sym', 'GND'),
    '+5V': (f'{STD}/power.kicad_sym', '+5V'),
    '+12V': (f'{STD}/power.kicad_sym', '+12V'),
    'VBUS': (f'{STD}/power.kicad_sym', 'VBUS'),
    'PWR_FLAG': (f'{STD}/power.kicad_sym', 'PWR_FLAG'),
}
FPLIB = LIBNICK + ':'


def lib_symbol(name):
    """Symbol `name` as a bare (library-file) symbol, flattened, sub-units renamed."""
    path, src = SOURCES[name]
    syms = load_lib(path)
    s = copy.deepcopy(syms[src])
    ext = first(s, 'extends')
    if ext:
        parent = copy.deepcopy(syms[ext[1]])
        props = {p[1]: p for p in find(s, 'property')}
        new = [parent[0], Q(src)]
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == 'property' and e[1] in props:
                new.append(props.pop(e[1]))
            elif isinstance(e, list) and e[0] == 'symbol':
                e[1] = Q(e[1].replace(ext[1], src, 1)); new.append(e)
            else:
                new.append(e)
        new.extend(props.values())
        s = new
    s[1] = Q(name)
    for sub in find(s, 'symbol'):
        sub[1] = Q(name + sub[1][len(src):])
    return s


def pins_of(sym):
    out = {}
    for sub in find(sym, 'symbol'):
        for p in find(sub, 'pin'):
            at = first(p, 'at')
            out.setdefault(first(p, 'number')[1], []).append((float(at[1]), float(at[2]), float(at[3])))
    return out


# ---------------------------------------------------------------- design
FP = lambda n: FPLIB + n
PWR = {'GND', '+5V', '+12V', 'VBUS'}
two = lambda a, b: {'1': a, '2': b}
R0402, C0402, C0603, C0805 = FP('R_0402_1005Metric'), FP('C_0402_1005Metric'), FP('C_0603_1608Metric'), FP('C_0805_2012Metric')
LCSC = {'1k': 'C11702', '5.1k': 'C25905', '13.3k': 'C122547', '47k': 'C25792', '56k': 'C25796', '100k': 'C25741', '470k': 'C25790',
        '75pF': 'C37809', '100nF': 'C1525', '100nF/50V': 'C14663', '1uF/50V': 'C15849',
        '10uF/25V': 'C15850', '22uF/25V': 'C45783'}
CFP = {'75pF': C0402, '100nF': C0402, '100nF/50V': C0603, '1uF/50V': C0603, '10uF/25V': C0805, '22uF/25V': C0805}


def R(ref, val, xy, a, b, desc=''):
    return (ref, 'R', val, R0402, xy, two(a, b), {'LCSC': LCSC[val], 'Description': desc})


def C(ref, val, xy, a, b, desc=''):
    return (ref, 'C', val, CFP[val], xy, two(a, b), {'LCSC': LCSC[val], 'Description': desc})


usb = {'A1': 'GND', 'A12': 'GND', 'B1': 'GND', 'B12': 'GND', 'SH': 'GND',
       'A4': 'VBUS', 'A9': 'VBUS', 'B4': 'VBUS', 'B9': 'VBUS',
       'A5': 'CC1', 'B5': 'CC2'}   # D+/D- left open: PD needs only CC (v0.2 routing)
PARTS = [
    # ref, symbol, value, footprint, (x, y), {pin: net}, extra fields
    ('J1', 'USB_C_Receptacle_USB2.0_16P', 'USB-C (power in)', FP('USB_C_Receptacle_HRO_TYPE-C-31-M-12'), (38.1, 101.6), usb,
     {'LCSC': 'C165948', 'Description': 'HRO TYPE-C-31-M-12 USB-C receptacle, 5 A. Only VBUS/GND/CC are used; D+/D- are left open (PD only)'}),
    # USB-PD sink: 56k on CFG1 = 15 V request (CH224A single-resistor mode, CFG2/CFG3 float on internal pull-ups)
    ('U1', 'CH224K', 'CH224A', FP('SSOP-10-1EP_3.9x4.9mm_P1mm_EP2.1x3.3mm'), (99.06, 101.6),
     {'1': 'VBUS', '8': 'VBUS', '9': 'CFG1', '7': 'CC1', '6': 'CC2', '10': 'PG', '11': 'GND'},   # DP/DM (BC1.2/QC only) open
     {'LCSC': 'C42459160', 'Description': 'WCH CH224A USB PD3.2 sink, ESSOP-10 (pin-compatible with CH224K; pin 1 is VHV, 32 V tolerant, wired straight to VBUS)'}),
    C('C1', '1uF/50V', (78.74, 127.0), 'VBUS', 'GND', 'U1 VHV decoupling, next to pin 1'),
    R('R1', '56k', (124.46, 127.0), 'CFG1', 'GND', 'CFG1 single-resistor setting: 56k = request 15 V'),
    # output switch: on only while PG is low (PD contract made). Gate divider keeps Vgs at -VBUS/2 (AO3401A Vgs max 12 V)
    ('Q1', 'AO3401A', 'AO3401A', FP('SOT-23'), (167.64, 50.8), {'1': 'GATE', '2': 'VBUS', '3': 'VSW'},
     {'LCSC': 'C15127', 'Description': 'P-MOSFET 30 V 4 A, high-side output switch'}),
    R('R2', '100k', (152.4, 35.56), 'VBUS', 'GATE', 'Q1 gate pull-up (off by default)'),
    R('R3', '100k', (152.4, 66.04), 'GATE', 'PG', 'Q1 gate pull-down when PG asserts'),
    C('C2', '100nF/50V', (182.88, 35.56), 'GATE', 'VSW', 'gate-drain (Miller) cap: ~10 ms output ramp, limits inrush into the C64 bulk caps'),
    # 5 V buck (TI reference design, 400 kHz)
    ('U2', 'TPS54302', 'TPS54302DDCR', FP('TSOT-23-6'), (198.12, 111.76),
     {'3': 'VSW', '1': 'GND', '2': 'SW', '6': 'BOOT', '4': 'FB', '5': 'EN'},
     {'LCSC': 'C311983', 'Description': 'TI 3 A 28 V synchronous buck, TSOT-23-6'}),
    C('C3', '10uF/25V', (157.48, 101.6), 'VSW', 'GND', 'buck input'),
    C('C4', '100nF/50V', (167.64, 101.6), 'VSW', 'GND', 'buck input HF, next to U2 pin 3'),
    R('R4', '470k', (167.64, 127.0), 'VSW', 'EN', 'EN UVLO top: start ~13.2 V, stop ~11.7 V'),
    R('R5', '47k', (167.64, 149.86), 'EN', 'GND', 'EN UVLO bottom'),
    C('C5', '100nF', (226.06, 91.44), 'BOOT', 'SW', 'bootstrap'),
    ('L1', 'L', '10uH', FP('L_Changjiang_FXL0630'), (226.06, 111.76), two('SW', '5V_BUCK'),
     {'LCSC': 'C167223', 'Description': 'cjiang FXL0630-100-M 10 uH 4.5 A / Isat 5.5 A molded, 7x6.6 mm'}),
    C('C6', '22uF/25V', (246.38, 127.0), '5V_BUCK', 'GND', 'buck output'),
    C('C7', '22uF/25V', (256.54, 127.0), '5V_BUCK', 'GND', 'buck output'),
    R('R6', '100k', (226.06, 137.16), '5V_BUCK', 'FB', 'FB top: Vout = 0.596 x (1 + 100k/13.3k) = 5.08 V'),
    R('R7', '13.3k', (226.06, 157.48), 'FB', 'GND', 'FB bottom'),
    C('C8', '75pF', (210.82, 137.16), '5V_BUCK', 'FB', 'feed-forward (TI reference design)'),
    # 12 V buck for DIN pin 6 (same reference design, FB 100k/5.1k)
    ('U3', 'TPS54302', 'TPS54302DDCR', FP('TSOT-23-6'), (198.12, 238.76),
     {'3': 'VSW', '1': 'GND', '2': 'SW2', '6': 'BOOT2', '4': 'FB2', '5': 'EN2'},
     {'LCSC': 'C311983', 'Description': 'TI 3 A 28 V synchronous buck, TSOT-23-6 (12 V rail)'}),
    C('C9', '10uF/25V', (157.48, 228.6), 'VSW', 'GND', 'buck 2 input'),
    C('C10', '100nF/50V', (167.64, 228.6), 'VSW', 'GND', 'buck 2 input HF, next to U3 pin 3'),
    R('R9', '470k', (182.88, 254.0), 'VSW', 'EN2', 'EN2 UVLO top: start ~13.2 V, stop ~11.7 V'),
    R('R10', '47k', (182.88, 269.24), 'EN2', 'GND', 'EN2 UVLO bottom'),
    C('C11', '100nF', (226.06, 226.06), 'BOOT2', 'SW2', 'bootstrap'),
    ('L2', 'L', '10uH', FP('L_Changjiang_FXL0530'), (226.06, 238.76), two('SW2', '12V_BUCK'),
     {'LCSC': 'C177248', 'Description': 'cjiang FXL0530-100-M 10 uH 3.2 A / Isat 3.5 A molded, 5.4x5.2 mm'}),
    C('C12', '22uF/25V', (246.38, 251.46), '12V_BUCK', 'GND', 'buck 2 output'),
    C('C13', '22uF/25V', (256.54, 251.46), '12V_BUCK', 'GND', 'buck 2 output'),
    R('R11', '100k', (226.06, 256.54), '12V_BUCK', 'FB2', 'FB2 top: Vout = 0.596 x (1 + 100k/5.1k) = 12.28 V (7.15k -> 8.9 V if 9 V is ever wanted)'),
    R('R12', '5.1k', (226.06, 271.78), 'FB2', 'GND', 'FB2 bottom'),
    C('C14', '75pF', (210.82, 256.54), '12V_BUCK', 'FB2', 'feed-forward'),
    # output protection
    ('F1', 'Polyfuse', '2A', FP('Fuse_1206_3216Metric'), (60.96, 162.56), two('5V_BUCK', '+5V'),
     {'LCSC': 'C22374899', 'Description': 'LUTE 1206L200/16NR PTC, 2 A hold / 3.5 A trip, 16 V'}),
    ('D1', 'D_Zener', 'SMF5.0A', FP('D_SOD-123F'), (81.28, 175.26), two('+5V', 'GND'),
     {'LCSC': 'C193402', 'Description': 'TVS 5 V standoff: clamps +5 V and trips F1 if the buck ever fails high'}),
    ('F2', 'Polyfuse', '1.1A', FP('Fuse_1206_3216Metric'), (111.76, 162.56), two('12V_BUCK', '+12V'),
     {'LCSC': 'C2798026', 'Description': 'BHFUSE BSMD1206-110-24V PTC, 1.1 A hold / 2.2 A trip, 24 V'}),
    ('D2', 'D_Zener', 'SMF13A', FP('D_SOD-123F'), (132.08, 175.26), two('+12V', 'GND'),
     {'LCSC': 'C353315', 'Description': 'TVS 13 V standoff on the 12 V output'}),
    R('R8', '1k', (101.6, 187.96), '+5V', 'LED_A', 'power LED'),
    ('D3', 'LED', 'GREEN', FP('LED_0805_2012Metric'), (114.3, 187.96), {'1': 'GND', '2': 'LED_A'},
     {'LCSC': 'C2297', 'Description': 'power LED, green 0805'}),
    # C64 power input: male DIN-7 (DIN 45329) soldered straight into the board, plug on the top side
    ('J2', 'DIN-7', 'C64 POWER (DIN-7 male)', FP('DIN-7_Male_PCB_C64'), (66.04, 200.66),
     {'1': 'GND', '2': 'GND', '3': 'GND', '4': '+5V', '5': '+5V', '6': '+12V', '7': 'GND'},
     {'Description': '7-pin DIN (DIN 45329) male plug insert, pins soldered through the board, hand-soldered. 1/2/3/7 GND, 4+5 +5 V, 6 = +12 V DC into the C64 "9 VAC" input.'}),
]
ROT = {'R2': 0, 'R3': 0}

items, libsyms = [], {}
netmap = {}


def prop(name, val, x, y, hide=False, just=None):
    p = ['property', Q(name), Q(val), ['at', x, y, 0], ['effects', ['font', ['size', 1.27, 1.27]]]]
    if just:
        p[4].append(['justify', just])
    if hide:
        p[4].append(['hide', 'yes'])
    return p


def symbol_inst(name, ref, value, fp, x, y, rot=0, extra=None, pins=(), inbom=True, refat=None, valat=None, onboard=None):
    extra = dict(extra or {})
    rx, ry, rj = refat or (x + 2.54, y - 5.08, None)
    vx, vy, vj = valat or (x + 2.54, y + 5.08, None)
    s = ['symbol', ['lib_id', Q(LIBNICK + ':' + name)], ['at', x, y, rot], ['unit', 1],
         ['exclude_from_sim', 'no'], ['in_bom', 'yes' if inbom else 'no'],
         ['on_board', 'yes' if (inbom if onboard is None else onboard) else 'no'],
         ['dnp', 'no'], ['uuid', uid()],
         prop('Reference', ref, rx, ry, hide=ref.startswith('#'), just=rj),
         prop('Value', value, vx, vy, just=vj),
         prop('Footprint', fp, x, y, hide=True),
         prop('Datasheet', '', x, y, hide=True),
         prop('Description', extra.pop('Description', ''), x, y, hide=True)]
    for k, v in extra.items():
        s.append(prop(k, v, x, y, hide=True))
    for pn in pins:
        s.append(['pin', Q(pn), ['uuid', uid()]])
    s.append(['instances', ['project', Q(NAME), ['path', Q('/' + ROOT), ['reference', Q(ref)], ['unit', 1]]]])
    return s


def use(name):
    if name not in libsyms:
        libsyms[name] = lib_symbol(name)
    return libsyms[name]


pwr_n = [0]
pwr_ends = []


def power(net, x, y, outdir):
    sym = use(net)
    if net == 'GND':
        rot = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[outdir]
    else:
        rot = {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[outdir]
    pwr_n[0] += 1
    d = 3.81 if outdir[1] else 5.08
    crowded = any(abs(px - x) < 3.0 and abs(py - y) < 0.1 for px, py in pwr_ends)
    items.append(symbol_inst(net, '#PWR%02d' % pwr_n[0], net, '', x, y, rot, pins=list(pins_of(sym)), inbom=False,
                             valat=(round(x + outdir[0] * d, 2), round(y + outdir[1] * d, 2), None)))
    if crowded:     # neighbouring pin already shows the same rail name
        items[-1][10][4].append(['hide', 'yes'])
    pwr_ends.append((x, y))


def label(net, x, y, outdir):
    rot, just = {(1, 0): (0, 'left'), (-1, 0): (180, 'right'), (0, -1): (90, 'left'), (0, 1): (270, 'right')}[outdir]
    items.append(['label', Q(net), ['at', x, y, rot],
                  ['effects', ['font', ['size', 1.27, 1.27]], ['justify', just, 'bottom']], ['uuid', uid()]])


for ref, name, value, fp, (sx, sy), nets, extra in PARTS:
    sym = use(name)
    pins = pins_of(sym)
    rot = ROT.get(ref, 0)
    def place(px, py):
        a = math.radians(rot)
        return sx + px * math.cos(a) - py * math.sin(a), sy - (px * math.sin(a) + py * math.cos(a))
    P = [place(px, py) for pl in pins.values() for (px, py, _) in pl]
    if all(abs(x - sx) < 0.01 for x, _ in P):       # vertical 2-pin part: text to the right
        refat, valat = (sx + 2.54, sy - 1.27, 'left'), (sx + 2.54, sy + 1.27, 'left')
    else:                                            # text above / below the pin field
        refat = (sx, round(min(y for _, y in P) - 3.81, 2), None)
        valat = (sx, round(max(y for _, y in P) + 3.81, 2), None)
    items.append(symbol_inst(name, ref, value, fp, sx, sy, rot, extra=extra, pins=list(pins), refat=refat, valat=valat,
                             inbom=True, onboard=True))
    for pn, plist in pins.items():
        net = nets.get(pn)
        netmap[(ref, pn)] = net
        seen = set()
        for (px, py, ang) in plist:
            a = math.radians(rot)   # symbol rotation (CCW in lib coords, y up)
            rx, ry = px * math.cos(a) - py * math.sin(a), px * math.sin(a) + py * math.cos(a)
            X, Y = round(sx + rx, 4), round(sy - ry, 4)
            if (X, Y) in seen:      # stacked pins (e.g. USB VBUS/GND) share one stub
                continue
            seen.add((X, Y))
            if net is None:
                items.append(['no_connect', ['at', X, Y], ['uuid', uid()]])
                continue
            pa = math.radians(ang + rot)   # pin points inward at `ang`; stub goes outward
            dx, dy = -round(math.cos(pa)), round(math.sin(pa))
            L = 2.54
            if net in PWR and dx:                    # horizontal power stub: clear of labels / neighbours
                L = 7.62
                while any(abs(px - (X + dx * L)) < 0.1 and abs(py - Y) < 3.0 for px, py in pwr_ends):
                    L += 5.08
            ex, ey = round(X + dx * L, 4), round(Y + dy * L, 4)
            items.append(['wire', ['pts', ['xy', X, Y], ['xy', ex, ey]],
                          ['stroke', ['width', 0], ['type', 'default']], ['uuid', uid()]])
            (power if net in PWR else label)(net, ex, ey, (dx, dy))
    for pn in nets:
        assert pn in pins, (ref, pn)

use('PWR_FLAG')
for i, net in enumerate(['VBUS', 'GND', 'VSW', '+5V', '+12V']):
    x, y = 236.22 + i * 10.16, 22.86
    items.append(symbol_inst('PWR_FLAG', '#FLG%02d' % (i + 1), 'PWR_FLAG', '', x, y, 0, pins=['1'], inbom=False,
                             valat=(x, y - 6.35, None)))
    if net in PWR:
        power(net, x, y, (0, 1))
    else:
        items.append(['wire', ['pts', ['xy', x, y], ['xy', x, y + 2.54]],
                      ['stroke', ['width', 0], ['type', 'default']], ['uuid', uid()]])
        label(net, x, y + 2.54, (0, 1))

NOTE = ('C64 USB-C PD Power Adapter v0.2 (DC only, no 50/60 Hz: the C64 TOD clock will not tick from mains)\n'
        'Needs a USB-C PD charger offering 15 V (>= 3 A / 45 W recommended). U1 (CH224A) requests 15 V via R1 = 56k.\n'
        'Q1 connects the 15 V rail only after the PD contract (PG low). U2 and U3 start only above ~13.2 V (EN UVLO),\n'
        'so a plain 5 V charger, or one that falls back to 9/12 V, never powers the C64.\n'
        'DIN: 4+5 = +5.08 V (U2, F1 2 A PTC, D1 TVS), 6 = +12.3 V DC (U3, F2 1.1 A PTC, D2 TVS) into the C64 "9 VAC" bridge, 1/2/3/7 = GND.\n'
        '12 V DC = the peak of the stock 9 VAC, so user port pins 10/11 see no more than an original PSU gives (but DC, not AC).')
items.append(['text', Q(NOTE), ['exclude_from_sim', 'no'], ['at', 25.4, 22.86, 0],
              ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'bottom']], ['uuid', uid()]])

sch = ['kicad_sch', ['version', 20250114], ['generator', Q('eeschema')], ['generator_version', Q('10.0')],
       ['uuid', Q(ROOT)], ['paper', Q('A3')],
       ['title_block', ['title', Q('C64 USB-C PD Power Adapter')], ['date', Q('2026-10-27')], ['rev', Q('0.2')],
        ['comment', 1, Q('USB-C PD 15 V -> C64 7-pin DIN: +5 V and +12 V DC (on the 9 VAC input), two TPS54302 bucks')]],
       ['lib_symbols'] + [[s[0], Q(LIBNICK + ':' + s[1])] + s[2:] for s in libsyms.values()]] + items + \
      [['sheet_instances', ['path', Q('/'), ['page', Q('1')]]], ['embedded_fonts', 'no']]
open(os.path.join(OUT, NAME + '.kicad_sch'), 'w').write(dump(sch) + '\n')

lib = ['kicad_symbol_lib', ['version', 20241209], ['generator', Q('kicad_symbol_editor')], ['generator_version', Q('10.0')]] + \
      [copy.deepcopy(s) for s in libsyms.values()]
open(os.path.join(OUT, LIBNICK + '.kicad_sym'), 'w').write(dump(lib) + '\n')
json.dump({f'{r}.{p}': n for (r, p), n in netmap.items()}, open(os.path.join(OUT, 'intended_nets.json'), 'w'), indent=0)
print('wrote', len(items), 'items;', len(libsyms), 'symbols')
