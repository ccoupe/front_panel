// cut two vertical holes for switch wires and
// two horizontal channels for them on the bottom
$fn=20;
hole_d = 1.75;
hole_h = 30;
left_x = -2.5;
right_x = 2.5;
left_y = 2;
right_y = 4;
chan_d = 2;
chan_h = 16;
chan_base = -16.5;
led_r = 2.65;

fl = "/home/ccoupe/Projects/3d/Portal/Button/base-normal-v1.stl";

 difference() {
    import(fl);
    union() {
        // Cut hole under switch
        translate([-8.5, -4, chan_base-2]) {
            cube([17.8, 22.8, 8]);
        }
        
        // Left LED, Chamber, wire channels
        translate([-20, 19, chan_base+4]) {
            cylinder(r=led_r, h=8);
        }
        // indent around hole
        translate([-20, 19, chan_base+4]) {
            cylinder(r=led_r+0.5, h=5);
        }
        // Chamber
        translate([-22,12,chan_base-2]) {
            cube([14,15,10]);
        }
        translate([-10,18,chan_base]) {
            rotate([0,90,0]) {
                cylinder(r=hole_d, h=8);
            }
        }
        // Right LED, Chamber, wire channels
        translate([20, 19, chan_base+4]) {
            cylinder(r=led_r, h=8);
        }
        // indent around hole
        translate([20, 19, chan_base+4]) {
            cylinder(r=led_r+0.5, h=5);
        }
        translate([8,12,chan_base-2]) {
            cube([14,15,10]);
        }
        translate([2,18,chan_base]) {
            rotate([0,90,0]) {
                cylinder(r=hole_d, h=8);
            }
        }
        // More room for the Left LED under deck
        translate([-23.75,16.5,chan_base-2]) {
            cube([2,6,10]);
        }
        // More room for the Right LED under deck
        translate([21.5,16.5,chan_base-2]) {
            cube([2,6,10]);
        }
        // Exit hole
        translate([0,16.5,chan_base]) {
            rotate([-90]) {
                cylinder(r=3, h=20);
            }
        }
    } 
}
