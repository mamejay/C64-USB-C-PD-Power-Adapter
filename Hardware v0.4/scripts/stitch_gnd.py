"""Stitch isolated B.Cu GND pour islands to the F.Cu GND pour with a via each (GND is not autorouted).
usage: stitch_gnd.py board.kicad_pcb"""
import sys, os, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); mm = pcbnew.FromMM
gnd = b.FindNet('GND')
zb = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.B_Cu][0]
zf = [z for z in b.Zones() if not z.GetIsRuleArea() and z.GetNetname() == 'GND' and z.GetLayer() == pcbnew.F_Cu][0]
fb, ff = zb.GetFilledPolysList(pcbnew.B_Cu), zf.GetFilledPolysList(pcbnew.F_Cu)
VIA_R = 0.4
added = 0
for k in range(fb.OutlineCount()):
    isl = pcbnew.SHAPE_POLY_SET(fb.Outline(k))
    if abs(fb.Outline(k).Area()) / 1e12 < 0.5:
        continue
    # does any existing GND via / THT pad already sit in this island?
    hit = False
    for t in b.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T and t.GetNetname() == 'GND' and isl.Contains(t.GetPosition()):
            hit = True; break
    if not hit:
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetname() == 'GND' and p.HasHole() and isl.Contains(p.GetPosition()):
                    hit = True
    if hit:
        continue
    # pick a grid point well inside both the B.Cu island and the F.Cu pour
    bb = fb.Outline(k).BBox(); best = None
    for ix in range(int(bb.GetLeft() / 1e5), int(bb.GetRight() / 1e5)):
        for iy in range(int(bb.GetTop() / 1e5), int(bb.GetBottom() / 1e5)):
            pt = pcbnew.VECTOR2I(ix * 100000, iy * 100000)
            ok = all(isl.Contains(pcbnew.VECTOR2I(pt.x + dx, pt.y + dy)) and ff.Contains(pcbnew.VECTOR2I(pt.x + dx, pt.y + dy))
                     for dx in (-mm(VIA_R), 0, mm(VIA_R)) for dy in (-mm(VIA_R), 0, mm(VIA_R)))
            if ok:
                best = pt; break
        if best: break
    if best is None:
        print('island', k, 'no via spot, bbox', bb.GetLeft() / 1e6, bb.GetTop() / 1e6); continue
    v = pcbnew.PCB_VIA(b); v.SetPosition(best); v.SetWidth(mm(0.6)); v.SetDrill(mm(0.3)); v.SetNet(gnd)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); b.Add(v); added += 1
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(sys.argv[1]); print('stitching vias added:', added); sys.stdout.flush(); os._exit(0)
