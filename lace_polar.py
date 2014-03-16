#!/usr/bin/env python
# Copyright 2014 Jo Pol
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see http://www.gnu.org/licenses/.

from math import *

# These lines are only needed if you don't put the script directly into
# the installation directory
import sys
from os import path
# Unix
sys.path.append('/usr/share/inkscape/extensions')
# OS X
sys.path.append('/Applications/Inkscape.app/Contents/Resources/extensions')
# Windows
sys.path.append('C:\Program Files\Inkscape\share\extensions')
sys.path.append('C:\Program Files (x86)\share\extensions')

# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle, math, pturtle

__author__ = 'Jo Pol'
__credits__ = ['Veronika Irvine']
__license__ = 'GPL'
__version__ = '0.1.0'
__maintainer__ = 'Jo Pol'
__status__ = 'Development'

class PolarGrid(inkex.Effect):
	"""
	Create a dotted polar grid where distance between the circles 
	increase with the distance between the dots on the circles
	"""
	def __init__(self):
		"""
		Constructor.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)
		self.OptionParser.add_option('-a', '--angle', action='store', type='float', dest='angleOnFootside', default=45, help='grid angle (degrees)')
		self.OptionParser.add_option('-d', '--dots', action='store', type='int', dest='dotsPerCircle', default=180, help='number of dots on a circle')
		self.OptionParser.add_option('-o', '--outerDiameter', action='store', type='float', dest='outerDiameter', default=160, help='outer diameter (mm)')
		self.OptionParser.add_option('-i', '--innerDiameter', action='store', type='float', dest='innerDiameter', default=100, help='minimum inner diameter (mm)')
		self.OptionParser.add_option('-f', '--fill', action='store', type='string', dest='dotFill', default='#FF9999', help='dot color')
		self.OptionParser.add_option('-s', '--size', action='store', type='float', dest='dotSize', default=0.2, help='dot size (mm)')

	def dot(self, x, y, group):
		"""
		Draw a circle of radius 'options.dotSize' and origin at (x, y)
		"""
		s = simplestyle.formatStyle({'fill': self.options.dotFill})
		attribs = {'style':s, 'cx':str(x), 'cy':str(y), 'r':str(self.options.dotSize)}
		
		# insert path object into te group
		inkex.etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

	def group(self, diameter, distance):
		"""
		Create a group for the dots on a circle of the grid
		"""
		f = "{0} mm per dot, diameter: {1} mm"
		s = f.format(distance, diameter)
		attribs = {inkex.addNS('label', 'inkscape'):s}
		
		# insert group object into current layer
		return inkex.etree.SubElement(self.current_layer, inkex.addNS('g', 'svg'), attribs)

	def dots(self, diameter, circleNr, group):
		"""
		Draw dots on a grid circle
		"""
		offset = (circleNr % 2) * 0.5
		aRadians = radians(360 / self.options.dotsPerCircle)
		for dotNr in range (0, self.options.dotsPerCircle):
			a = (dotNr + offset) * aRadians
			x = (diameter / 2) * cos(a)
			y = (diameter / 2) * sin(a)
			self.dot(x, y, group)

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		diameter = self.options.outerDiameter
		circleNr = 0 
		t = tan(radians(self.options.angleOnFootside))
		while diameter > self.options.innerDiameter:
			distance = t * ((diameter * pi) / self.options.dotsPerCircle)
			self.dots(diameter, circleNr, self.group(diameter, distance))
			diameter -= distance
			circleNr += 1

# Create effect instance and apply it.
effect = PolarGrid()
effect.affect()
