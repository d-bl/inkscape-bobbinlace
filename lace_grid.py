#!/usr/bin/env python
# Copyright 2014 Veronika Irvine
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

import sys

# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle, pturtle
from math import sin, cos, radians, ceil

__author__ = 'Veronika Irvine'
__credits__ = ['Veronika Irvine']
__license__ = 'GPL'
__version__ = '0.6.0'
__maintainer__ = 'Veronika Irvine'
__status__ = 'Development'
# V0.6 - 0.91 units compatibility, color added.


class LaceGrid(inkex.Effect):
    """
    Create a grid for lace with angle as specified
    """
    def __init__(self):
        """
        Constructor.
        Defines the "--centerx" option of the script.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)

        # Define float option "--angle" with "-a" shortcut and default value "45.0".
        self.OptionParser.add_option('-a', '--angle', action='store',
            type='float', dest='angle', default=45.0, help='Grid Angle')
        
        # Define float option "--spacing" with "-s" shortcut and default value "10.0" in mm.
        self.OptionParser.add_option('-s', '--distance', action='store',
            type='float', dest='spacing', default=10.0, help='Distance between grid points.')

        # Define float option "--width" with "-w" shortcut and default value "100" in mm.
        self.OptionParser.add_option('-w', '--width', action='store', 
            type='float', dest='width', default=100, help='Width of entire ground pattern')
        
        # Define float option "--height" with "-l" shortcut and default value "100".
        self.OptionParser.add_option('-l', '--height', action='store', 
            type='float', dest='height', default=100, help='Height of entire ground pattern')
        
        # Define string option "--units" with "-u" shortcut and default value "mm".
        self.OptionParser.add_option('-u', '--units', action = 'store',
            type = 'string', dest = 'units', default = 'mm',
            help = 'All measurements are in these units.')
            
        # Define float option "--dotdia" with "-p" shortcut and default value "2".
        self.OptionParser.add_option('-p', '--dotdia', action='store', 
            type='float', dest='dotdia', default=2, help='Diameter of the dots')
        
        # Define string option "--dotcolor" with "-c" shortcut and default value "Grey".      
        self.OptionParser.add_option('-c', '--dotcolor', action = 'store',
            type = 'string', dest = 'dotcolor', default = -1431655936, # Grey
            help = 'The line colour.')

    def getUnittouu(self, param):
        " compatibility between inkscape 0.48 and 0.91 "
        try:
            return inkex.unittouu(param)
        except AttributeError:
            return self.unittouu(param)

    def getColorString(self, longColor, verbose=False):
        """ Convert the long into a #RRGGBB color value
            - verbose=true pops up value for us in defaults
            conversion back is A + B*256^1 + G*256^2 + R*256^3
        """
        if verbose: inkex.debug("%s ="%(longColor))
        longColor = long(longColor)
        if longColor <0: longColor = long(longColor) & 0xFFFFFFFF
        hexColor = hex(longColor)[2:-3]
        hexColor = '#' + hexColor.rjust(6, '0').upper()
        if verbose: inkex.debug("  %s for color default value"%(hexColor))
        return hexColor

    def circle(self, x, y, r, fill, stroke, strokeWidth, parent):
        """
        Draw a circle of radius 'r' and origin at (x, y)
        """
        # define the stroke style
        style = {'stroke-width': strokeWidth,
                 'stroke': stroke,
                 'stroke-linecap': 'butt',
                 'stroke-linejoin': 'miter',
                 # 'fill-opacity': '1.0',
                 # 'stroke-opacity': '1.0',
                 'fill': fill
                }
        # create attributes from style and define path
        attribs = {'style':simplestyle.formatStyle(style), 
                   'cx':str(x),
                   'cy':str(y),
                   'r':str(r)
                  }
        # insert path object into current layer
        inkex.etree.SubElement(parent, inkex.addNS('circle', 'svg'), attribs)

    def draw_grid_dot(self, x, y, parent):
        " Draw a single grid dot "
        dot_radius = self.options.dotdia/2
        fill = self.options.dotcolor
        self.circle(x, y, dot_radius, fill, 'none',  '0.1mm', parent)

    def draw_grid(self, width, height, spacing, theta, parent):
        " Draw a grid of dots "
        hgrid = spacing*sin(theta);
        vgrid = spacing*cos(theta)
        rows = int(height / vgrid) + 1
        cols = int(width  / hgrid)
        y = 0.0
        for r in range(rows):
            x = 0.0
            if (r % 2 == 1):
                x += hgrid
            for c in range(cols/2):
                self.draw_grid_dot(x, y, parent)
                x += 2.0*hgrid;
            y += vgrid;
    
    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        #Convert input from mm or whatever user uses
        conversion = self.getUnittouu("1" + self.options.units)
        width = self.options.width * conversion
        height = self.options.height * conversion
        # sort out color
        self.options.dotcolor = self.getColorString(self.options.dotcolor)
        self.options.dotdia = self.options.dotdia * conversion
        # users expect spacing to be the vertical distance between footside dots (vertical distance between every other row) 
        # but in the script we use it as as diagonal distance between grid points
        # therefore convert spacing based on the angle chosen
        theta = radians(self.options.angle)
        spacing = self.options.spacing * conversion/(2.0*cos(theta))

        # Top level Group
        t = 'translate(%s,%s)' % (self.view_center[0]-width/2, self.view_center[1]-height/2)
        grp_attribs = {inkex.addNS('label','inkscape'):'Lace Grid', 'transform':t}
        grp = inkex.etree.SubElement(self.current_layer, 'g', grp_attribs)
        # draw a grid of dots based on user inputs
        self.draw_grid(width, height, spacing, theta, grp)

# Create effect instance and apply it.
effect = LaceGrid()
effect.affect()
