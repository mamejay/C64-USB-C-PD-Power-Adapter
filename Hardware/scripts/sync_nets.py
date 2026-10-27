"""Set every pad's net in the board from the kicad-cli netlist (text edit: KiCad 10 stores net names on pads).
usage: sync_nets.py board.kicad_pcb net.net"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, dump, Q, find, first
brd, netf = sys.argv[1:3]
n = parse(open(netf).read())[0]
pin = {}
for net in find(first(n, 'nets'), 'net'):
    for nd in find(net, 'node'):
        pin[(first(nd, 'ref')[1], first(nd, 'pin')[1])] = first(net, 'name')[1]
tree = parse(open(brd).read())[0]
changed = 0
for fp in find(tree, 'footprint'):
    ref = next((p[2] for p in find(fp, 'property') if p[1] == 'Reference'), None)
    for pad in find(fp, 'pad'):
        want = pin.get((ref, pad[1]))
        if want is None:
            continue
        cur = first(pad, 'net')
        if cur is None:
            pad.append(['net', Q(want)]); changed += 1
        elif cur[1] != want:
            cur[1] = Q(want); changed += 1
open(brd, 'w').write(dump(tree) + '\n')
print('sync_nets: %d pad nets changed' % changed)
