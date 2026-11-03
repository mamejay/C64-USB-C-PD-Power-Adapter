#!/bin/bash
# C64 v0.4 board: netlist -> build -> holes -> net classes -> 5 V copper areas -> Freerouting
set -e
S=$(dirname "$(realpath "$0")"); cd "$S/../KiCad"; P="C64 USB-C PD Power Adapter"
kicad-cli sch export netlist -o net.net "$P.kicad_sch" >/dev/null
python3 -I "$S/build_v04.py" . "$S/place_v04.json" >/dev/null 2>&1
python3 -I "$S/add_holes.py" "$P.kicad_pcb" >/dev/null
python3 -I "$S/set_netclasses_v04.py" . >/dev/null
python3 -I "$S/power_planes_v04.py" "$P.kicad_pcb" 2>&1 | grep -v -E "assert|leak" || true
bash "$S/autoroute_v04.sh" "$P.kicad_pcb" ${1:-100} 2>&1 | grep -E "completed|import" | sed 's/.*INFO *\[[^]]*\] //' || true
grep -B1 "unrouted connection" fr.log | grep Net | sort -u || true
