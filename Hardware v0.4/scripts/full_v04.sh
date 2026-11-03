#!/bin/bash
# Route -> pours -> GND stitching -> DRC, repeated until DRC reports 0 unconnected pads (Freerouting varies run to run).
S=$(dirname "$(realpath "$0")"); cd "$S/../KiCad"; P="C64 USB-C PD Power Adapter"
for i in $(seq 1 ${1:-8}); do
  FR_EXTRA="--router.autorouter.ignore_net_classes=GND" "$S/rebuild_route_v04.sh" 300 >/dev/null 2>&1
  cp "$P.kicad_pcb" routed_nopour.kicad_pcb
  python3 -I "$S/pours_v04.py" "$P.kicad_pcb" >/dev/null 2>&1
  python3 -I "$S/stitch_gnd.py" "$P.kicad_pcb" 2>&1 | grep -E "stitch|island" | tr '\n' ' '
  python3 -I "$S/texts_upright.py" "$P.kicad_pcb" >/dev/null 2>&1
  kicad-cli pcb drc --schematic-parity --refill-zones -o drc.rpt "$P.kicad_pcb" >/dev/null
  u=$(grep -oE "Found [0-9]+ unconnected" drc.rpt | grep -oE "[0-9]+")
  echo "run $i: unconnected $u"
  [ "$u" = 0 ] && break
done
python3 -I "$S/drop_dangling_vias.py" "$P.kicad_pcb" drc.rpt 2>&1 | grep removed
kicad-cli pcb drc --schematic-parity --refill-zones -o drc.rpt "$P.kicad_pcb" >/dev/null
grep -E "^\[|Found" drc.rpt | sort | uniq -c
