"""Plot a placed board seen from the top: bottom pads/courtyards solid, top pads outlined, holes, edge.
usage: render_place.py board.kicad_pcb out.png"""
import sys, pcbnew
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle, Rectangle
b = pcbnew.LoadBoard(sys.argv[1]); MM = 1e-6
fig, ax = plt.subplots(figsize=(11, 11), dpi=100)
def poly(item, L, **kw):
    ps = pcbnew.SHAPE_POLY_SET(); item.TransformShapeToPolygon(ps, L, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
    for k in range(ps.OutlineCount()):
        o = ps.Outline(k); ax.add_patch(Polygon([(o.CPoint(i).x*MM, o.CPoint(i).y*MM) for i in range(o.PointCount())], closed=True, **kw))
for fp in b.GetFootprints():
    back = fp.IsFlipped()
    for p in fp.Pads():
        for L, kw in ((pcbnew.B_Cu, dict(fc='#e8a33d', ec='k', lw=0.3, alpha=0.9)), (pcbnew.F_Cu, dict(fc='none', ec='#c33', lw=0.8))):
            if p.IsOnLayer(L): poly(p, L, **kw); break
        if p.HasHole():
            q = p.GetPosition(); ax.add_patch(Circle((q.x*MM, q.y*MM), p.GetDrillSize().x*MM/2, fc='w', ec='k', lw=0.4))
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if back else pcbnew.F_CrtYd)
    for k in range(cy.OutlineCount()):
        o = cy.Outline(k); ax.add_patch(Polygon([(o.CPoint(i).x*MM, o.CPoint(i).y*MM) for i in range(o.PointCount())], closed=True, fc='none', ec='#36c' if back else '#c33', lw=0.6, ls='-' if back else '--'))
    q = fp.GetPosition(); ax.text(q.x*MM, q.y*MM, fp.GetReference(), fontsize=8 if back else 10, ha='center', va='center', color='navy' if back else 'darkred', weight='bold')
for d in b.GetDrawings():
    if d.GetLayer() == pcbnew.Edge_Cuts:
        poly(d, pcbnew.Edge_Cuts, fc='none', ec='k', lw=1.2)
bb = b.GetBoardEdgesBoundingBox()
ax.set_xlim(bb.GetLeft()*MM - 2, bb.GetRight()*MM + 2); ax.set_ylim(bb.GetBottom()*MM + 2, bb.GetTop()*MM - 2)
ax.set_aspect('equal'); ax.grid(True, lw=0.2); ax.set_title('seen from top: bottom parts solid/blue, top parts red outline')
fig.savefig(sys.argv[2], bbox_inches='tight')
