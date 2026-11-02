"""Add GND pours on F.Cu and B.Cu (2-layer board), fill, drop islands.
usage: gnd_pours.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
bb = b.GetBoardEdgesBoundingBox()
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    z = pcbnew.ZONE(b); z.SetLayer(layer); z.SetNet(b.FindNet('GND'))
    o = z.Outline(); o.NewOutline()
    for x, y in ((bb.GetLeft(), bb.GetTop()), (bb.GetRight(), bb.GetTop()), (bb.GetRight(), bb.GetBottom()), (bb.GetLeft(), bb.GetBottom())):
        o.Append(x, y)
    z.SetLocalClearance(mm(0.2)); z.SetMinThickness(mm(0.2))
    z.SetThermalReliefGap(mm(0.2)); z.SetThermalReliefSpokeWidth(mm(0.25))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    z.SetAssignedPriority(1)
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
