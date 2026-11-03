"""C64 v0.4: reserve the 5 V current path before autorouting. B.Cu copper areas for 5V_BUCK (R6/C8 arm ->
C7/C6 -> L1 output -> band -> U4 IN bar, plus R13/R15 tops) and +5V (U4 OUT bar -> D1 -> DIN pin 5), each with a
matching rule-area keepout (no tracks/vias) because Freerouting ignores copper zones as obstacles.
U4 at (141.6, 122.6) rot 0 on B.Cu: IN bar x 141.22-141.52, OUT bar x 141.71-142.01, bars y 121.4-123.8 (both
areas join the bars at their top end). The 12 V eFuse (U5) nets are routed as 0.3 mm tracks (<= 1.5 A).
usage: power_planes_v04.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
u4 = next(f for f in b.GetFootprints() if f.GetReference() == 'U4')
bars = {p.GetNumber(): p.GetBoundingBox() for p in u4.Pads() if p.GetNumber() in ('5', '6')}
assert abs(bars['5'].GetLeft() / 1e6 - 141.22) < 0.02 and abs(bars['6'].GetLeft() / 1e6 - 141.71) < 0.02, 'U4 moved: redraw polygons'
assert abs(bars['5'].GetTop() / 1e6 - 121.4) < 0.02, 'U4 moved: redraw polygons'
u4.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)


def keepout(pts):
    k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetLayer(pcbnew.B_Cu)
    k.SetDoNotAllowTracks(True); k.SetDoNotAllowVias(True); k.SetDoNotAllowZoneFills(False)
    k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
    o = k.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    b.Add(k)


def zone(net, pts, prio):
    keepout(pts)
    z = pcbnew.ZONE(b); z.SetLayer(pcbnew.B_Cu); z.SetNet(b.FindNet(net))
    o = z.Outline(); o.NewOutline()
    for x, y in pts: o.Append(mm(x), mm(y))
    z.SetLocalClearance(mm(0.15)); z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS); z.SetAssignedPriority(prio); b.Add(z)


zone('/5V_BUCK', [(123.2, 115.0), (124.3, 115.0), (124.3, 116.0), (127.4, 116.0),          # arm over R6 / C8 5 V pads
                  (127.4, 115.55), (131.4, 115.55), (131.4, 118.2),                          # C7 / C6 5 V pads
                  (141.0, 118.2), (141.0, 120.6), (141.55, 120.6), (141.55, 121.6),          # band -> U4 IN bar top end
                  (141.05, 121.6), (141.05, 121.3),
                  (137.2, 121.3), (137.2, 121.75), (136.4, 121.75), (136.4, 121.3),          # tab: R15 top pad
                  (133.8, 121.3), (133.8, 121.75), (133.0, 121.75), (133.0, 121.3),          # tab: R13 top pad
                  (131.6, 121.3), (131.6, 122.0), (129.4, 122.0),                            # L1 output pad
                  (129.4, 119.25), (127.4, 119.25), (127.4, 117.0),
                  (124.3, 117.0), (124.3, 117.8), (123.2, 117.8)], 2)
zone('+5V', [(140.45, 114.6), (146.5, 114.6), (146.5, 119.55), (143.1, 119.55),               # DIN pin 5, D1 cathode
             (143.1, 121.2), (142.05, 121.2), (142.05, 121.6), (141.68, 121.6),               # -> U4 OUT bar top end
             (141.68, 117.9), (140.45, 117.9)], 3)
# J2 pin 2 (GND) sits between the two 5 V areas: keep the B.Cu GND pour off it (F.Cu pour connects it)
k = pcbnew.ZONE(b); k.SetIsRuleArea(True); k.SetLayer(pcbnew.B_Cu)
k.SetDoNotAllowTracks(False); k.SetDoNotAllowVias(False); k.SetDoNotAllowZoneFills(True)
k.SetDoNotAllowPads(False); k.SetDoNotAllowFootprints(False)
o = k.Outline(); o.NewOutline()
for x, y in [(137.8, 114.5), (140.35, 114.5), (140.35, 118.05), (137.8, 118.05)]: o.Append(mm(x), mm(y))
b.Add(k)
pads = {(f.GetReference(), p.GetNumber()): p for f in b.GetFootprints() for p in f.Pads()}
def track(a, b_, pts, w, layer, net):
    pp = [pads[a].GetPosition()] + [pcbnew.VECTOR2I(mm(x), mm(y)) for x, y in pts] + ([pads[b_].GetPosition()] if b_ else [])
    for s_, e_ in zip(pp, pp[1:]):
        t = pcbnew.PCB_TRACK(b); t.SetStart(s_); t.SetEnd(e_); t.SetWidth(mm(w)); t.SetLayer(layer)
        t.SetNet(b.FindNet(net)); t.SetLocked(True); b.Add(t)
def via(x, y, net):
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y))); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3))
    v.SetNet(b.FindNet(net)); v.SetLocked(True); b.Add(v)
# fixed (pre-routed) links: J2 pin 4 <-> pin 5 on F.Cu, arched over GND pin 2
track(('J2', '4'), ('J2', '5'), [(137.4, 114.55), (140.6, 114.55)], 0.5, pcbnew.F_Cu, '+5V')
# eFuse GND pins: tie to the ILM resistor's GND end and a via to the F.Cu GND pour
track(('U4', '8'), ('R17', '2'), [(143.2, 122.375)], 0.25, pcbnew.B_Cu, 'GND')
track(('R17', '2'), None, [(145.1, 122.3)], 0.3, pcbnew.B_Cu, 'GND')
track(('D1', '2'), None, [(145.1, 122.3)], 0.3, pcbnew.B_Cu, 'GND')
via(145.1, 122.3, 'GND')
track(('U5', '8'), ('R22', '2'), [(143.2, 103.775)], 0.25, pcbnew.B_Cu, 'GND')
track(('R22', '2'), None, [(143.85, 102.3)], 0.3, pcbnew.B_Cu, 'GND')
via(143.85, 102.3, 'GND')
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); sys.stdout.flush(); os._exit(0)
