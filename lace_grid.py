#!/usr/bin/env python

# Copyright (c) 2017, Veronika Irvine
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from math import sin, cos, radians, ceil
import inkex, simplestyle

__author__ = 'Veronika Irvine'
__credits__ = ['Ben Connors', 'Veronika Irvine', 'Mark Shafer']
__license__ = 'Simplified BSD'

class LaceGrid(inkex.Effect):        
    """
    Create a grid for lace with angle as specified
    """

    def unitToUu(self,param):
        """ Convert units.
        Converts a number in some units into the units used internally by 
        Inkscape.
        
        param is a string representing a number with units attached. An 
            example would be '3.8mm'. Any units supported by Inkscape
            are supported by this function.
        
        This wrapper function catches changes made to the location
        of the function between Inkscape versions.
        """
        try:
            return self.unittouu(param)
        except:
            return inkex.unittouu(param)

    def getColorString(self, longColor):
        """ Convert the long into a #RRGGBB color value
            conversion back is A + B*256^1 + G*256^2 + R*256^3
        """
        longColor = long(longColor)
        if longColor <0: longColor = long(longColor) & 0xFFFFFFFF
        hexColor = hex(longColor)[2:-3]
        hexColor = '#' + hexColor.rjust(6, '0').upper()
        return hexColor

    def circle(self, x, y, r, fill):
        """
        Draw a circle of radius 'r' and origin at (x, y)
        """
        
        # define the stroke style
        s = {'fill': fill}
     
        # create attributes from style and define path
        attribs = {'style':simplestyle.formatStyle(s), 
                    'cx':str(x),
                    'cy':str(y),
                    'r':str(r)}
        
        # insert path object into current layer
        inkex.etree.SubElement(self.current_layer, inkex.addNS('circle', 'svg'), attribs)

    def drawDot(self, x, y):
        self.circle(x, y, self.options.dotwidth, self.options.dotcolor)

    def draw(self):
        
        a = self.options.spacing
        theta = self.options.angle
        
        hgrid = a*sin(theta);
        vgrid = a*cos(theta)
        rows = int(ceil(self.options.height / vgrid))
        cols = int(ceil(self.options.width  / hgrid))
        y = 0.0
        
        for r in range(rows):
            x = 0.0
            if (r % 2 == 1):
                x += hgrid
            
            for c in range(cols/2):
                self.drawDot(x, y)
                x += 2.0*hgrid;
                
            y += vgrid;

    def __init__(self):
        """
        Constructor.
        Defines the options of the script.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)
        # Grid description
        self.OptionParser.add_option('--angle',
                                     action='store',
                                     type='float',
                                     dest='angle')
        self.OptionParser.add_option('--distance',
                                     action='store',
                                     type='float',
                                     dest='spacing')
        self.OptionParser.add_option('--pinunits',
                                     action='store',
                                     type='string',
                                     dest='pinunits')
        # Patch description
        self.OptionParser.add_option('--width',
                                     action='store',
                                     type='float',
                                     dest='width')
        self.OptionParser.add_option('--patchwidthunits',
                                     action='store',
                                     type='string',
                                     dest='patchwidthunits')
        self.OptionParser.add_option('--height',
                                     action='store',
                                     type='float',
                                     dest='height')
        self.OptionParser.add_option('--patchheightunits',
                                     action='store',
                                     type='string',
                                     dest='patchheightunits')
        # Dot description
        self.OptionParser.add_option('--dotwidth',
                                     action='store',
                                     type='float',
                                     dest='dotwidth')
        self.OptionParser.add_option('--dotunits',
                                     action='store',
                                     type='string',
                                     dest='dotunits')
        self.OptionParser.add_option('--dotcolor',
                                     action='store',
                                     type='string',
                                     dest='dotcolor')

    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        # Convert user input to universal units
        self.options.width = self.unitToUu(str(self.options.width)+self.options.patchwidthunits)
        self.options.height = self.unitToUu(str(self.options.height)+self.options.patchheightunits)
        self.options.spacing = self.unitToUu(str(self.options.spacing)+self.options.pinunits)
        # Convert from diameter to radius
        self.options.dotwidth = self.unitToUu(str(self.options.dotwidth)+self.options.dotunits)/2
        # Users expect spacing to be the vertical distance between footside pins 
        # (vertical distance between every other row) but in the script we use it 
        # as as diagonal distance between grid points
        # therefore convert spacing based on the angle chosen
        self.options.angle = radians(self.options.angle)
        self.options.spacing = self.options.spacing/(2.0*cos(self.options.angle))
        
        # Convert color from long integer to hexidecimal string
        self.options.dotcolor = self.getColorString(self.options.dotcolor)
        
        # Draw a grid of dots based on user inputs
        self.draw()

# Create effect instance and apply it.
effect = LaceGrid()
effect.affect()
