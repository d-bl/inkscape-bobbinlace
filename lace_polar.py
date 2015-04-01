#!/usr/bin/env python
# Copyright 2015 Jo Pol
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
__license__ = 'GPLv3'
__version__ = '${project.version}'
__maintainer__ = 'Jo Pol'
__status__ = 'Development'

class PolarGrid(inkex.Effect):
	"""
	Creates a dotted polar grid where distance between the circles 
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
		self.OptionParser.add_option('-A', '--alignment', action='store', type='string', dest='alignment', default='outside', help='exact diameter on [inside|outside]')
		self.OptionParser.add_option('-s', '--size', action='store', type='float', dest='dotSize', default=0.5, help='dot diameter (mm)')
		self.OptionParser.add_option('-v', '--variant', action='store', type='string', dest='variant', default='', help='omit rows to get [|rectangle|hexagon1]')

	def dot(self, x, y, group):
		"""
		Draw a circle of radius 'options.dotSize' and origin at (x, y)
		"""
		s = simplestyle.formatStyle({'fill': self.dotFill})
		scale = 7.08677 # tested with a dot of 2 mm at 160 mm with a 5000% scale
		attribs = {'style':s, 'cx':str(x*scale), 'cy':str(y*scale), 'r':str(self.options.dotSize*1.775)}
		
		# insert path object into te group
		inkex.etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

	def group(self, diameter, distance):
		"""
		Create a labeled group for the dots on a circle of the grid
		"""
		f = "{0} mm per dot, diameter: {1} mm"
		s = f.format(distance, diameter)
		attribs = {inkex.addNS('label', 'inkscape'):s}
		
		# insert group object into current layer and remeber it
		return inkex.etree.SubElement(self.current_layer, inkex.addNS('g', 'svg'), attribs)

	def dots(self, diameter, circleNr, group):
		"""
		Draw dots on a grid circle
		"""
		offset = (circleNr % 2) * 0.5
		aRadians = radians(360.0 / self.options.dotsPerCircle)
		for dotNr in range (0, self.options.dotsPerCircle):
			a = (dotNr + offset) * aRadians
			x = (diameter / 2) * cos(a)
			y = (diameter / 2) * sin(a)
			self.dot(x, y, group)

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

	def iterate(self, diameter, circleNr):
		"""
		Create a group with a ring of dots, the distance between the dots is the distance to the next ring
		"""
		distance = self.tan * diameter * pi / self.options.dotsPerCircle
		group = self.group(diameter, distance)
		self.dots(diameter, circleNr, group)
		self.generatedCircles.append(group)
		return distance

	def generate(self):
		"""
		Generate rings with dots, either inside out or outside in
		"""
		circleNr = 0
		if self.options.alignment == 'outside':
			diameter = self.options.outerDiameter
			while diameter > self.options.innerDiameter:
				diameter -= self.iterate(diameter, circleNr)
				circleNr += 1
		else:
			diameter = self.options.innerDiameter
			while diameter < self.options.outerDiameter:
				diameter += self.iterate(diameter, circleNr)
				circleNr += 1

	def variantRectangle(self):
		"""
		Remove dots 
		"""
		i = 1
		while (i < self.nrOfGeneratedCircles):
			self.current_layer.remove(self.generatedCircles[i])
			i += 2

	def variantHexagon1(self):
		"""
		Remove dots 
		"""
		i = 2
		while (i < self.nrOfGeneratedCircles):
			self.current_layer.remove(self.generatedCircles[i])
			i += 3

	def variantHexagon2(self):
		"""
		Remove dots 
		"""
		i = 1
		while (i < self.nrOfGeneratedCircles):
			j = 0
			for dot in self.generatedCircles[i].iterchildren():
				if ((((i+1) % 2) + j) % 3) == 0 :
					self.generatedCircles[i].remove(dot)
				j += 1
			i += 1

	def variantHexagon3(self):
		"""
		Remove dots 
		"""
		i = 1
		while (i < self.nrOfGeneratedCircles):
			if ((i%2) == 1 ):
				j = 0
				for dot in self.generatedCircles[i].iterchildren():
					if (((((i+1) % 4)/2) + j) % 2) == 0 :
						self.generatedCircles[i].remove(dot)
					j += 1
			i += 1

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		self.tan = tan(radians(self.options.angleOnFootside))
		self.dotFill = self.getColorString(self.options.dotFill)
		self.generatedCircles = []
		self.generate()
		self.nrOfGeneratedCircles = len(self.generatedCircles)
		if self.options.variant == 'rectangle':
			self.variantRectangle()
		elif self.options.variant == 'hexagon1':
			self.variantHexagon1()
		elif self.options.variant == 'hexagon2':
			self.variantHexagon2()
		elif self.options.variant == 'hexagon3':
			self.variantHexagon3()

# Create effect instance and apply it.
if __name__ == '__main__':
	PolarGrid().affect()
