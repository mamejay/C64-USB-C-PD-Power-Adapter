"""C64 v0.4 pours: GND pours both sides (the 5 V areas come from power_planes.py), then refill everything.
usage: pours_v04.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
def zone(layer, net, pts, prio):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet(net))
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(x, y)
    z.SetLocalClearance(mm(0.15 if net != 'GND' else 0.25)); z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.25)); z.SetThermalReliefSpokeWidth(mm(0.5))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); b.Add(z)
P = lambda *xy: [(mm(x), mm(y)) for x, y in xy]
# the 5V_BUCK / +5V copper areas are added before routing by power_planes.py
for fp in b.GetFootprints():
    if fp.GetReference() == 'J1':
        fp.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)   # USB-C GND pads: solid, avoids starved thermals
bb = b.GetBoardEdgesBoundingBox()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    zone(layer, 'GND', [(bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())], 1)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
