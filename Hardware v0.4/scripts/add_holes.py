"""Add the two M2.5 mounting holes (board-only) to a board by text edit, at the v0.2 positions.
usage: add_holes.py board.kicad_pcb"""
import sys, os, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find, first
brd = sys.argv[1]
HOLES = {'H1': (104.3, 98.1), 'H2': (143.6, 98.1)}
U = lambda s: Q(str(uuid.uuid5(uuid.NAMESPACE_URL, 'c64-pd-psu-edge-' + s)))
tree = parse(open(brd).read())[0]
tree[:] = [e for e in tree if not (isinstance(e, list) and e and e[0] == 'footprint' and any(
    p[1] == 'Reference' and p[2] in HOLES for p in find(e, 'property')))]
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
print('holes added', HOLES)
