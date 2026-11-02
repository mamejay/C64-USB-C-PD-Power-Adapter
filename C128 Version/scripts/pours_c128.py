"""C128 pours: a +5V copper area on B.Cu from L1's output to DIN pin 1 (3 A path), then GND pours both sides.
usage: pours_c128.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def zone(layer, net, pts, prio):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet(net))
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(x, y)
    z.SetLocalClearance(mm(0.25)); z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); b.Add(z)
P = lambda *xy: [(mm(x), mm(y)) for x, y in xy]
# +5V: L1 right pad (x ~131-134, y 120-127), C18, D1, J2 pin 1 (145.0, 115.5)
zone(pcbnew.B_Cu, '+5V', P((131.0, 119.8), (142.7, 119.8), (142.7, 114.0), (146.6, 114.0), (146.6, 128.9), (131.0, 128.9)), 2)
for fp in b.GetFootprints():
    if fp.GetReference() == 'J1':
        fp.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)   # USB-C GND pads: solid, avoids starved thermals
bb = b.GetBoardEdgesBoundingBox()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone(layer, 'GND', [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())], 1)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
