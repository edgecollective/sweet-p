// CSG.scad - Basic example of CSG usage

smidge=3;
modem_depth=2*25.4; //in to mm
modem_length=3*25.4;
screw_x=3.5*25.4;
screw_y=20;
y_buffer=5;
x_buffer=5;
plate_y=screw_y+2*y_buffer;
plate_x=screw_x+2*x_buffer;
plate_thickness=3;
screw_r=2;
screw_h=10;
basin_buffer_x=x_buffer+smidge;
//basin_buffer_y=y_buffer+smidge;
basin_buffer_y=0;
basin_depth=modem_depth+3*smidge;
basin_length=modem_length+2*smidge;
basin_height=plate_y;

cable_depth=6;
//holder
module basin() {
    
difference() {
//basin
translate([basin_buffer_x,basin_buffer_y,0])
cube(size=[basin_length,basin_height,basin_depth],center=false);

//basin cavity
translate([basin_buffer_x+smidge/2,basin_buffer_y+smidge,smidge])
cube(size=[modem_length+smidge,basin_height,modem_depth+smidge],center=false);

//cable gap
translate([basin_buffer_x+smidge*1.1,-5,modem_depth])
cube(size=[modem_length*2/3,basin_height,cable_depth],center=false);
}
}


//backplate
module backplate() {
difference() {
cube(size=[plate_x,plate_y,plate_thickness],center=false);

//bottom left screw
translate([x_buffer,y_buffer,0])
cylinder(h = screw_h, r = screw_r, center = true);

//bottom left screw
translate([x_buffer+screw_x,y_buffer,0])
cylinder(h = screw_h, r = screw_r, center = true);

//top right screw
translate([x_buffer+screw_x,y_buffer+screw_y,0])
cylinder(h = screw_h, r = screw_r, center = true);

//top left screw
translate([x_buffer,y_buffer+screw_y,0])
cylinder(h = screw_h, r = screw_r, center = true);
    
}
}



backplate();
basin();

echo(basin_depth);
