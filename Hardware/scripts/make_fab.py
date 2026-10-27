"""JLCPCB outputs for the routed v0.2 board: 2-layer gerbers + drill (zipped), BOM and CPL.
J2 (DIN-7) is hand-soldered and the M2.5 holes are board-only, so neither is in the BOM/CPL.
Every assembled part is on the BOTTOM side.
usage: python3 -I make_fab.py <routed project dir> <out dir>"""
import sys, os, csv, subprocess, zipfile, glob, shutil, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import parse, find, first

D, OUT = map(os.path.abspath, sys.argv[1:3])
N = 'C64 USB-C PD Power Adapter'
PCB, SCH = f'{D}/{N}.kicad_pcb', f'{D}/{N}.kicad_sch'
HAND = {'J2'}
os.makedirs(OUT, exist_ok=True)
G = f'{OUT}/gerbers'; shutil.rmtree(G, ignore_errors=True); os.makedirs(G)
run = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)

layers = 'F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts'
run('kicad-cli', 'pcb', 'export', 'gerbers', '-o', G + '/', '-l', layers, '--subtract-soldermask',
    '--no-protel-ext', '--use-drill-file-origin', PCB)
run('kicad-cli', 'pcb', 'export', 'drill', '-o', G + '/', '--format', 'excellon', '--excellon-units', 'mm',
    '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', '--drill-origin', 'absolute', PCB)
zp = f'{OUT}/{N} - Gerbers.zip'
with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
    for f in sorted(glob.glob(G + '/*')):
        z.write(f, os.path.basename(f))

# ---- BOM from the schematic fields
sch = parse(open(SCH).read())[0]
parts = {}
for s in find(sch, 'symbol'):
    p = {q[1]: q[2] for q in find(s, 'property')}
    ref = p['Reference']
    if ref.startswith('#') or first(s, 'in_bom')[1] != 'yes' or ref in HAND:
        continue
    parts[ref] = p
def fpname(p):
    f = p['Footprint'].split(':')[1]
    m = re.search(r'(0402|0603|0805|1206|SOD-123F|TSOT-23-6|SOT-23|SSOP-10|FXL0630|FXL0530|TYPE-C-31-M-12)', f)
    return m.group(1) if m else f
groups = {}
for ref, p in parts.items():
    groups.setdefault((p['Value'], fpname(p), p.get('LCSC', '')), []).append(ref)
nat = lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r)))
with open(f'{OUT}/{N} - BOM.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
    for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda g: nat(sorted(g[1], key=nat)[0])):
        assert lcsc, (val, refs)
        w.writerow([val, ','.join(sorted(refs, key=nat)), fp, lcsc])

# ---- CPL from KiCad positions. JLC's bottom-side models need extra rotations for some parts.
# LED / diode +180 comes from the C64 mouse v1.1 board (same KiCad footprint conventions, confirmed in JLC's
# preview 2026-10-23: SOD-323 and LED_0805 both +180). Everything else: raw KiCad rotation, check the preview.
JLC_ROT_FIX = {'D1': 180, 'D2': 180, 'D3': 180}
raw = f'{OUT}/pos_raw.csv'
run('kicad-cli', 'pcb', 'export', 'pos', '-o', raw, '--format', 'csv', '--units', 'mm', '--side', 'both', PCB)
with open(raw) as f, open(f'{OUT}/{N} - CPL.csv', 'w', newline='') as g:
    w = csv.writer(g); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
    rows = [r for r in csv.DictReader(f) if r['Ref'] in parts]
    for r in sorted(rows, key=lambda r: nat(r['Ref'])):
        w.writerow([r['Ref'], '%.4fmm' % float(r['PosX']), '%.4fmm' % float(r['PosY']),
                    'Top' if r['Side'] == 'top' else 'Bottom', '%g' % ((float(r['Rot']) + JLC_ROT_FIX.get(r['Ref'], 0)) % 360)])
missing = set(parts) - {r['Ref'] for r in rows}
sides = {r['Side'] for r in rows}
print('gerbers:', len(glob.glob(G + '/*')), 'files ->', os.path.basename(zp))
print('BOM lines:', len(groups), ' parts:', len(parts), ' CPL rows:', len(rows), ' sides:', sides, ' missing from CPL:', sorted(missing))
