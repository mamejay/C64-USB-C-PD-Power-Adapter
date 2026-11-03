"""Put JLC-friendly net classes into the .kicad_pro (gen_pcb's board.Save resets them).
C64 v0.4: Power 0.5 mm for the input and switch nodes (as v0.3); Bar 0.3 mm for the eFuse IN/OUT nets (the 5 V ones also get copper areas); GND 0.4 mm (pours added after routing). usage: set_netclasses.py <project dir>"""
import sys, json, glob
pro = glob.glob(sys.argv[1] + '/*.kicad_pro')[0]
j = json.load(open(pro))
ns = j.setdefault('net_settings', {})
base = next(c for c in ns['classes'] if c['name'] == 'Default')
base.update(track_width=0.25, clearance=0.15, via_diameter=0.6, via_drill=0.3)
pw = dict(base, name='Power', track_width=0.4, clearance=0.2, via_diameter=0.8, via_drill=0.4, priority=0)
hi = dict(base, name='HighI', track_width=0.9, clearance=0.2, via_diameter=0.8, via_drill=0.4, priority=0)
bar = dict(base, name='Bar', track_width=0.3, clearance=0.15, via_diameter=0.8, via_drill=0.4, priority=0)   # eFuse IN/OUT bars are 0.3 mm wide, 0.19 mm apart; copper zones carry the current
gnd = dict(base, name='GND', track_width=0.3, clearance=0.2, via_diameter=0.8, via_drill=0.4, priority=1)
pw['track_width'] = 0.5
ns['classes'] = [base, pw, bar, gnd]
ns['netclass_patterns'] = [{'netclass': 'Power', 'pattern': p} for p in
                           ('VBUS', '/VSW', '/SW', '/SW2')] + [{'netclass': 'Bar', 'pattern': p} for p in ('/5V_BUCK', '+5V', '/12V_BUCK', '+12V')] + [{'netclass': 'GND', 'pattern': 'GND'}]
json.dump(j, open(pro, 'w'), indent=2)
print('net classes:', [c['name'] for c in ns['classes']])
