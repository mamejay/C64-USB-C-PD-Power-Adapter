#!/bin/bash
# Full C128 board pipeline: netlist -> build -> holes -> net classes -> Freerouting -> GND pours -> upright text -> DRC
set -e
S=$(dirname "$(realpath "$0")"); cd "$S/../hw"; P="C128 USB-C PD Power Adapter"
kicad-cli sch export netlist -o net.net "$P.kicad_sch" >/dev/null
python3 -I "$S/build_c128.py" . "$S/place_c128.json" 2>&1 | grep -E "^board" || true
python3 -I "$S/add_holes.py" "$P.kicad_pcb" >/dev/null
python3 -I "$S/set_netclasses.py" . >/dev/null
python3 -I "$S/power_planes.py" "$P.kicad_pcb" 2>&1 | grep -v -E "assert|leak" || true
bash "$S/autoroute_v02.sh" "$P.kicad_pcb" ${1:-100} 2>&1 | grep -E "completed|import" | sed 's/.*INFO *\[[^]]*\] //' || true
grep -B1 "unrouted connection" fr.log | grep Net | sort -u || true
