// C64 USB-C PD Power Adapter v0.3 - 3D printed case (two parts: base + lid)
//
// The board lies flat against the C64's side with the DIN-7 plug pointing into the power socket.
//   base = tray on the board's BOTTOM side (all the SMD parts), faces away from the C64
//   lid  = thin plate on the board's TOP side, faces the C64, with a hole for the DIN plug
// Assembly: drop the PCB into the base (tilt it under nothing - the base is open at the top),
// hook the lid's two tabs into the slots in the base's bottom wall, lay the lid down and fit two
// M2.5 x 8 countersunk self-tapping screws (or M2.5 machine screws into heat-set inserts) through
// the lid, the PCB's mounting holes and into the base standoffs. Screw heads sit flush with the lid,
// so nothing sticks out towards the C64.
//
// Coordinates: case x/y = board coordinates seen from the board TOP, origin at the board's
// bottom-left corner (KiCad x 100.9, y 125.0), +y up. z = 0 is the outside of the base floor.
// KiCad (X, Y) -> case (X - 100.9, 125.0 - Y).
//
// Print: base floor-down, lid inner-face-down. PETG or ABS (the bucks run warm); no supports.
// Before printing, measure your DIN-7 plug insert and set din_hole_d.
// Trim the DIN pins on the solder side to <= 3.5 mm after soldering.

part = "both";            // "base", "lid", "both" (print layout) or "assembly" (fitted, for checking)

// ---------------- board
pcb_w = 46.1;  pcb_h = 30.0;  pcb_t = 1.6;
holes = [[3.4, 26.9], [42.7, 26.9]];          // M2.5 mounting holes (KiCad 104.3/143.6, 98.1)
din   = [38.1, 12.0];                         // DIN-7 centre (KiCad 139, 113)
usb_y = 12.0;                                 // USB-C centre line (KiCad y 113), mouth on the left edge
led   = [14.6, 10.6];                         // D3 power LED on the bottom (KiCad 115.5, 114.4)

// ---------------- case
wall   = 1.6;             // side walls
floor_t = 1.2;            // base floor
gap    = 0.25;            // board-to-wall clearance
under  = 4.5;             // space under the board (USB-C 3.3 mm, inductors 2.8 mm, trimmed DIN pins)
lid_t  = 1.6;             // lid plate (countersunk M2.5 heads are ~1.1 mm deep)
lid_clr = 0.15;           // lid-to-wall clearance
din_hole_d = 14.0;        // DIN plug body clearance hole: MEASURE YOUR PLUG INSERT
corner_r = 1.5;

pcb_z  = floor_t + under;             // underside of the PCB
top_z  = pcb_z + pcb_t + lid_t;       // top of walls = outside face of the lid
in_w = pcb_w + 2*gap;  in_h = pcb_h + 2*gap;
out_w = in_w + 2*wall; out_h = in_h + 2*wall;
ox = -gap - wall;  oy = -gap - wall;  // outer corner, in board coordinates

// PCB edge ledges (only where no part is within 0.9 mm of the edge; from the board courtyards)
ledge = 0.9;
ledges = [  // [x0, y0, x1, y1] in board coordinates
    [0, pcb_h - ledge, pcb_w, pcb_h],             // top edge, full length
    [16.75, 0, pcb_w, ledge],                      // bottom edge, right of U1/C1
    [0, 17.5, ledge, pcb_h],                       // left edge, above the USB-C
    [pcb_w - ledge, 0, pcb_w, pcb_h],              // right edge, full length
];

// USB-C plug overmold opening (left wall), centred on the receptacle (body centre ~1.6 mm below the board)
usb_open_w = 12.6;  usb_open_h = 7.0;  usb_open_r = 3.0;
usb_z = pcb_z - 1.6;

// lid retention tabs (bottom edge) and wall slots
tab_w = 6;  tab_len = 1.0;  tab_t = 0.7;   // tabs on the lid's inner face; 0.8 mm of wall stays above the slot
tab_x = [9, 33];

$fn = 48;

module rrect(w, h, r) { offset(r) offset(-r) square([w, h]); }

module base() {
    difference() {
        union() {
            // shell
            difference() {
                translate([ox, oy, 0]) linear_extrude(top_z) rrect(out_w, out_h, corner_r);
                translate([-gap, -gap, floor_t]) cube([in_w, in_h, top_z]);
            }
            // edge ledges under the PCB
            for (l = ledges)
                translate([l[0] - (l[0] == 0 ? gap : 0), l[1] - (l[1] == 0 ? gap : 0), floor_t])
                    cube([l[2] - l[0] + (l[0] == 0 ? gap : 0) + (l[2] >= pcb_w ? gap : 0),
                          l[3] - l[1] + (l[1] == 0 ? gap : 0) + (l[3] >= pcb_h ? gap : 0), under]);
            // screw standoffs
            for (h = holes) translate([h[0], h[1], floor_t]) cylinder(d = 5.5, h = under);
            // DIN support ring: takes the plug-in force straight through to the solder side of J2
            translate([din[0], din[1], floor_t]) difference() {
                cylinder(r = 6.1, h = under);
                translate([0, 0, -1]) cylinder(r = 5.3, h = under + 2);
            }
        }
        // screw pilots (2.2 mm for self-tapping M2.5; use 3.6 mm for M2.5 heat-set inserts)
        for (h = holes) translate([h[0], h[1], floor_t + 0.6]) cylinder(d = 2.2, h = top_z);
        // USB-C opening in the left wall
        translate([ox - 1, usb_y, usb_z]) rotate([0, 90, 0])
            linear_extrude(wall + 2) offset(usb_open_r) offset(-usb_open_r)
                square([usb_open_h, usb_open_w], center = true);
        // LED window
        translate([led[0], led[1], -1]) cylinder(d = 2.4, h = floor_t + 2);
        // vent slots under the two bucks / inductors
        for (x = [20, 23, 26, 29, 32]) {
            translate([x, 2.5, -1]) cube([1.2, 7, floor_t + 2]);
            translate([x, 18.5, -1]) cube([1.2, 7, floor_t + 2]);
        }
        // lid tab slots in the bottom wall
        for (x = tab_x) translate([x - tab_w/2 - 0.2, -gap - tab_len - 0.2, top_z - lid_t - 0.1])
            cube([tab_w + 0.4, tab_len + 0.2 + 0.01, tab_t + 0.2]);
        // label on the outside of the floor (mirrored so it reads correctly from outside)
        translate([pcb_w / 2, 14.5, -0.01]) mirror([1, 0, 0]) linear_extrude(0.4)
            text("C64 USB-C PD", size = 3.6, halign = "center", valign = "center", font = "Liberation Sans:style=Bold");
        translate([pcb_w / 2 + 5, 9.5, -0.01]) mirror([1, 0, 0]) linear_extrude(0.4)
            text("15V PD in", size = 2.6, halign = "center", valign = "center", font = "Liberation Sans");
    }
}

module lid() {
    lw = in_w - 2*lid_clr;  lh = in_h - 2*lid_clr;
    difference() {
        union() {
            translate([-gap + lid_clr, -gap + lid_clr, 0]) linear_extrude(lid_t) rrect(lw, lh, 0.6);
            // tabs on the bottom edge, they hook into the base wall slots
            for (x = tab_x) translate([x - tab_w/2, -gap + lid_clr - tab_len, 0]) cube([tab_w, tab_len + 0.5, tab_t]);
        }
        // DIN plug hole
        translate([din[0], din[1], -1]) cylinder(d = din_hole_d, h = lid_t + 2);
        // countersunk M2.5 (head 4.7 mm, 90 deg) - countersink on the OUTSIDE face (z = lid_t)
        for (h = holes) translate([h[0], h[1], 0]) {
            translate([0, 0, -1]) cylinder(d = 2.8, h = lid_t + 2);
            translate([0, 0, lid_t - 1.25]) cylinder(d1 = 2.2, d2 = 4.9, h = 1.35);
        }
        // pin-function legend next to the DIN hole (debossed on the outside face)
        translate([din[0] - 13.5, din[1] + 9.5, lid_t - 0.4]) linear_extrude(1)
            text("+5V 4/5  +12V 6", size = 2.2, halign = "center", font = "Liberation Sans");
    }
}

module pcb_ghost() {
    color("green", 0.5) translate([0, 0, pcb_z]) difference() {
        cube([pcb_w, pcb_h, pcb_t]);
        for (h = holes) translate([h[0], h[1], -1]) cylinder(d = 2.7, h = 4);
    }
    color("silver", 0.6) translate([-0.5, usb_y - 4.47, pcb_z - 3.26]) cube([7.35, 8.94, 3.26]);
    color("black", 0.6) translate([din[0], din[1], pcb_z + pcb_t]) cylinder(d = 13, h = 12);
}

if (part == "base") base();
else if (part == "lid") lid();                       // print inner face down (tabs on the bed, countersinks open upwards)
else if (part == "both") { base(); translate([0, out_h + 6, 0]) lid(); }
else if (part == "assembly") { base(); translate([0, 0, pcb_z + pcb_t]) lid(); pcb_ghost(); }
