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

# The following five lines check to see if tkFile Dialog can 
# be used to select a file


try:
    from Tkinter import *
    import tkFileDialog as tkf
except: tk = False
else: tk = True


import sys
from os import path

# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle
from math import sin, cos, ceil, radians
import pturtle

#inkex.debug("%s"%(sys.version))

__author__ = 'Veronika Irvine'
__credits__ = ['Ben Connors','Veronika Irvine']
__license__ = 'GPL'
__version__ = '0.6.0'
__maintainer__ = 'Veronika Irvine'
__status__ = 'Development'
# 0.6 units for inkscape0.91

class LaceGround(inkex.Effect):
    """
    Create a ground for lace from a text file descriptor 
    using specified angle and spacing
    """
    def __init__(self,fname):
        """
        Constructor.
        """
        # Call the base class constructor.
        inkex.Effect.__init__(self)
        
        # Set the fname variable
        self.fname = fname
        
        # Define string option "--file" with "-f" shortcut and no default value.
        self.OptionParser.add_option('-f', '--file', action='store',
            type='string', dest='file', default='lace_templates/4x4_33.txt',
            help='File containing lace ground description')

        # Define float option "--angle" with "-a" shortcut and default value "45.0".
        self.OptionParser.add_option('-a', '--angle', action='store',
            type='float', dest='angle', default=45.0, help='Grid Angle')
        
        # Define float option "--spacing" with "-s" shortcut and default value "10.0" in mm.
        self.OptionParser.add_option('-s', '--distance', action='store',
            type='float', dest='spacing', default=10.0, help='Distance between grid points')

        # Define float option "--width" with "-w" shortcut and default value "100" in mm.
        self.OptionParser.add_option('-w', '--width', action='store',
            type='float', dest='width', default=100, help='Width of ground pattern')
        
        # Define float option "--height" with "-l" shortcut and default value "100".
        self.OptionParser.add_option('-l', '--height', action='store',
            type='float', dest='height', default=100, help='Height of ground pattern')

        # Define string option "--units" with "-u" shortcut and default value "mm".
        self.OptionParser.add_option('-u', '--units', action = 'store',
            type = 'string', dest = 'units', default = 'mm',
            help = 'The units the measurements are in')
            
        # Define float option "--dotdia" with "-p" shortcut and default value "2".
        self.OptionParser.add_option('-p', '--dotdia', action='store', 
            type='float', dest='dotdia', default=4, help='Diameter of the dots')
        
        # Define string option "--dotcolor" with "-c" shortcut and default value "Grey".      
        self.OptionParser.add_option('-c', '--dotcolor', action = 'store',
            type = 'string', dest = 'dotcolor', default = -1431655936, # Grey
            help = 'The line colour.')
        
        self.OptionParser.add_option("-d", "--drawdots", action="store",
            type="inkbool", dest="drawdots", default=False, help="Draw minimal dot template")
        
        self.turtle = pturtle.pTurtle((100, 100))
        
        
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
    
    def line(self, x1, y1, x2, y2, parent):
        """
        Draw a line from point at (x1, y1) to point at (x2, y2).
        Style of line is hard coded and specified by 's'.
        """
        # define the motions
        self.turtle.penup()
        self.turtle.clean()
        self.turtle.setpos((x1, y1))
        self.turtle.pendown()
        self.turtle.setpos((x2, y2))
        self.turtle.penup()

        # define the stroke style
        s = {'stroke-linejoin': 'miter', 
             'stroke-width': '0.5px',
             'stroke': '#000000', 
             'stroke-linecap': 'butt',
             # 'marker-start':'url(#Arrow1Lend)', # no useful style - need to make manually
             # 'stroke-opacity': '1.0', 
             # 'fill-opacity': '1.0',
             'fill': 'none'
            }
        
        # create attributes from style and path
        attribs = {'style':simplestyle.formatStyle(s), 'd':self.turtle.getPath()}

        # insert path object into current layer
        inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), attribs)


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

    def loadFile(self, fname):
        data = []
        rowCount = 0
        colCount = 0
        with open(fname,'r') as f:
            first = True
            for line in f:
                if first:
                    # first line of file gives row count and column count
                    first = False
                    line = line.rstrip('\n')
                    temp = line.split('\t')
                    type = temp[0]
                    rowCount = int(temp[1])
                    colCount = int(temp[-1])
                
                else:
                    line = line.lstrip('[')
                    line = line.rstrip(']\t\n')
                    rowData = line.split(']\t[')
                    data.append([])
                    for cell in rowData:
                        data[-1].append([float(num) for num in cell.split(',')])
        
        return {"type":type, "rowCount":rowCount, "colCount":colCount, "data":data}

    def drawCheckerGround(self, data, rowCount, colCount, spacing, theta, parent, dotgroup):
        deltaX = spacing*sin(theta) 
        deltaY = spacing*cos(theta)
        maxRows = ceil(self.options.height / deltaY)
        maxCols = ceil(self.options.width  / deltaX)
        
        x = 0.0
        y = 0.0
        repeatY = 0
        repeatX = 0
        dots = {} # remember dots drawn so make unique

        while repeatY * rowCount < maxRows:
            x = 0.0
            repeatX = 0
            
            while repeatX * colCount < maxCols:
                
                for row in data:
                    for coords in row:
                        x1 = x + coords[0]*deltaX
                        y1 = y + coords[1]*deltaY
                        x2 = x + coords[2]*deltaX
                        y2 = y + coords[3]*deltaY
                        x3 = x + coords[4]*deltaX
                        y3 = y + coords[5]*deltaY
                
                        self.line(x1,y1,x2,y2, parent)
                        self.line(x1,y1,x3,y3, parent)
                        # Draw each dot only once
                        if self.options.drawdots:
                            id = "%s %s" % (coords[0], coords[1]) # id based on coord
                            if not dots.has_key(id):
                                x1 = x + coords[0]*deltaX
                                y1 = y + coords[1]*deltaY
                                self.draw_grid_dot(x1, y1, dotgroup)
                                dots[id] = True
                # next line
                repeatX += 1
                x += deltaX * colCount

            repeatY += 1
            y += deltaY * rowCount
    
    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        # Locate and load the file containing the lace ground descriptor
        if self.fname == None:
            self.fname = self.options.file
        
        if self.fname == '': sys.exit(1)
        elif not path.isfile(self.fname): sys.exit(1)
        
        result = self.loadFile(self.fname)
        
        #Convert input from mm or whatever user uses
        conversion = self.getUnittouu("1" + self.options.units)
        self.options.width *= conversion
        self.options.height *= conversion
        self.options.dotdia *= conversion
        # sort out color
        self.options.dotcolor = self.getColorString(self.options.dotcolor)
        
        # users expect spacing to be the vertical distance between footside dots (vertical distance between every other row) 
        # but in the script we use it as as diagonal distance between grid points
        # therefore convert spacing based on the angle chosen
        theta = radians(self.options.angle)
        spacing = self.options.spacing * conversion / cos(theta) #(2.0*cos(theta))
        
        # Top level Group
        t = 'translate(%s,%s)' % (self.view_center[0]-self.options.width/2, self.view_center[1]-self.options.height/2)
        grp_attribs = {inkex.addNS('label','inkscape'):'Lace Grid', 'transform':t}
        topgroup = inkex.etree.SubElement(self.current_layer, 'g', grp_attribs)
        # CReate groups for pattern lines and for dots
        grp_attribs = {inkex.addNS('label','inkscape'):'Pattern'}
        patterngroup = inkex.etree.SubElement(topgroup, 'g', grp_attribs)
        grp_attribs = {inkex.addNS('label','inkscape'):'Dots'}
        dotgroup = inkex.etree.SubElement(topgroup, 'g', grp_attribs)
        
        # Draw a ground based on file description and user inputs
        if (result["type"] == "CHECKER"):
            self.drawCheckerGround(result["data"],result["rowCount"],result["colCount"], spacing, theta, patterngroup, dotgroup)


if tk:
    # Create root window
    root = Tk()
    # Hide it
    root.withdraw()
    # Ask for a file
    fname = tkf.askopenfilename(**{'initialdir' : '~'}) 
else: fname = None

# Create effect instance and apply it.
effect = LaceGround(fname)
effect.affect()
