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


# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle
from math import sin, cos, radians, ceil

__author__ = 'Veronika Irvine'
__credits__ = ['Veronika Irvine']
__license__ = 'GPL'
__version__ = '${project.version}'
__maintainer__ = 'Veronika Irvine'
__status__ = 'Development'

class LaceGrid(inkex.Effect):
	"""
	Create a grid for lace with angle as specified
	"""
	def __init__(self):
		"""
		Constructor.
		Defines the options of the script.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)
	
		self.OptionParser.add_option('-a', '--angle', action='store', type='float', dest='angle', default=45.0, help='Grid Angle')
		self.OptionParser.add_option('-d', '--distance', action='store', type='float', dest='spacing', default=10.0, help='Distance between grid dots in mm')
		self.OptionParser.add_option('-w', '--width', action='store', type='float', dest='width', default=100, help='Width of grid')
		self.OptionParser.add_option('-l', '--height', action='store', type='float', dest='height', default=100, help='Height of grid')
		self.OptionParser.add_option('-s', '--size', action='store', type='float', dest='size', default=1, help='Size of dots')
		self.OptionParser.add_option('-c', '--color', action='store', type='string', dest='color', default='#FF0000', help='Color of dots')

	def getUnittouu(self, param):
		" compatibility between inkscape 0.48 and 0.91 "
		try:
			return inkex.unittouu(param)
		except AttributeError:
			return self.unittouu(param)

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

	def drawGridPoint(self, x, y):
		self.circle(x, y, self.options.size, self.options.color)
    										 
	def draw_grid(self, width, height, spacing):
		
		theta = radians(self.options.angle)
		
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
				self.drawGridPoint(x, y)
				x += 2.0*hgrid;
				
			y += vgrid;

	def unsignedLong(self, signedLongString):
		longColor = long(signedLongString)
		if longColor < 0:
			longColor = longColor & 0xFFFFFFFF
		return longColor

	def getColorString(self, longColor):
		"""
		Convert numeric color value to hex string using formula A*256^0 + B*256^1 + G*256^2 + R*256^3
		From: http://www.hoboes.com/Mimsy/hacks/parsing-and-setting-colors-inkscape-extensions/
		"""
		longColor = self.unsignedLong(longColor)
		hexColor = hex(longColor)[2:-3]
		hexColor = hexColor.rjust(6, '0')
		return '#' + hexColor.upper()

    
	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		#Convert input from mm or whatever user uses
		conversion = self.getUnittouu("1" + "mm")# self.options.units)
		width = self.options.width * conversion
		height = self.options.height * conversion
		self.options.size = self.options.size * conversion
		
		# Users expect spacing to be the vertical distance between footside pins (vertical distance between every other row) 
		# but in the script we use it as as diagonal distance between grid points
		# therefore convert spacing based on the angle chosen
		theta = radians(self.options.angle)
		spacing = self.options.spacing * conversion/(2.0*cos(theta))
		
		# Convert color from long integer to hexidecimal string
		self.options.color = self.getColorString(self.options.color)
		
		# Draw a grid of dots based on user inputs
		self.draw_grid(width, height, spacing)

# Create effect instance and apply it.
effect = LaceGrid()
effect.affect()
