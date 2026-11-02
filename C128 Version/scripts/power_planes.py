"""Reserve the 3 A path before autorouting: B.Cu copper areas for 5V_BUCK (L1 out -> eFuse IN bar) and
+5V (eFuse OUT bar -> DIN pin 1). Freerouting treats them as planes and routes other nets around them.
Polygons are drawn around the eFuse (U4) pads as placed (IN bar x 141.82-142.12, OUT bar 142.31-142.61, bar ends y 122.8).
usage: power_planes.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
u4 = next(f for f in b.GetFootprints() if f.GetReference() == 'U4')
bars = {p.GetNumber(): p.GetBoundingBox() for p in u4.Pads() if p.GetNumber() in ('5', '6')}
assert abs(bars['5'].GetLeft() / 1e6 - 141.82) < 0.02 and abs(bars['6'].GetLeft() / 1e6 - 142.31) < 0.02, 'U4 moved: redraw polygons'
u4.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
def keepout(pts):
    # rule area on B.Cu: no tracks or vias of any net (Freerouting ignores copper zones as obstacles); pours allowed
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetLayer(pcbnew.B_Cu)
    k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowZoneFills(False)
    k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    o = k.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(k)
def zone(net, pts):
    keepout(pts)
    z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetNet(b.FindNet(net))
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    z.SetLocalClearance(mm(0.15)); z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(2); b.Add(z)
zone('/5V_BUCK', [(131.0, 119.6), (133.0, 119.6), (133.0, 117.95), (134.2, 117.95), (134.2, 119.6),   # bump: R6 (FB top)
                  (142.20, 119.6), (142.20, 122.95), (141.80, 122.95), (141.80, 122.55),               # finger: U4 IN bar end
                  (134.0, 122.55), (134.0, 125.8), (134.75, 125.8), (134.75, 129.1), (131.0, 129.1)])  # R13/R15 tops
zone('+5V', [(142.24, 114.6), (146.6, 114.6), (146.6, 119.3), (144.4, 119.3), (144.4, 122.55),
             (142.70, 122.55), (142.70, 122.95), (142.24, 122.95)])
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
