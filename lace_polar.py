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

from __future__ import division
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
		Draw a circle with origin at (x, y) in the group
		"""
		attribs = {'style':self.dotStyle, 'cx':str(x * self.scale), 'cy':str(y * self.scale), 'r':self.dotR}
		inkex.etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

	def group(self, diameter, superGroup):
		"""
		Create a group labeled with the diameter
		"""
		label = 'diameter: {0:.2f} mm'.format(diameter)
		attribs = {inkex.addNS('label', 'inkscape'):label}
		return inkex.etree.SubElement(superGroup, inkex.addNS('g', 'svg'), attribs)

	def dots(self, diameter, circleNr, group):
		"""
		Draw dots on a grid circle
		"""
		offset = (circleNr % 2) * 0.5
		for dotNr in range (0, self.options.dotsPerCircle):
			a = (dotNr + offset) * self.alpha
			x = (diameter / 2) * cos(a)
			y = (diameter / 2) * sin(a)
			self.dot(x, y, group)

	def getColorString(self):
		"""
		Convert numeric color value to hex string using formula A*256^0 + B*256^1 + G*256^2 + R*256^3
		From: http://www.hoboes.com/Mimsy/hacks/parsing-and-setting-colors-inkscape-extensions/
		"""
		longColor = long(self.options.dotFill)
		if longColor < 0:
			longColor = longColor & 0xFFFFFFFF
		hexColor = hex(longColor)[2:-3]
		hexColor = hexColor.rjust(6, '0')
		return '#' + hexColor.upper()

	def iterate(self, diameter, circleNr):
		"""
		Create a group with a ring of dots.
		Returns half of the arc length between the dots
		which becomes the distance to the next ring.
		"""
		group = self.group(diameter, self.current_layer)
		self.dots(diameter, circleNr, group)
		self.generatedCircles.append(group)
		return diameter * self.change

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

	def removeGroups(self, start, increment):
		"""
		Remove complete rings with dots
		"""
		for i in range(start, len(self.generatedCircles), increment):
			self.current_layer.remove(self.generatedCircles[i])

	def removeDots(self, i, offset, step):
		"""
		Remove dots from one circle
		"""
		group = self.generatedCircles[i]
		dots = list(group)
		start = self.options.dotsPerCircle - 1 - offset
		for j in range(start, -1, 0-step):
			group.remove(dots[j])

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		self.dotStyle = simplestyle.formatStyle({'fill': self.getColorString()})
		self.scale = (90/25.4) # 90 DPI / mm
		self.dotR = str(self.options.dotSize * (self.scale/2))
		self.change = tan(radians(self.options.angleOnFootside)) * pi / self.options.dotsPerCircle
		self.alpha = radians(360.0 / self.options.dotsPerCircle)

		self.generatedCircles = []
		self.generate()

		if self.options.variant == 'rectangle':
			self.removeGroups(1, 2)
		elif self.options.variant == 'hexagon1':
			self.removeGroups(2, 3)
		elif self.options.variant == 'hexagon2':
			for i in range(1, len(self.generatedCircles), 1):
				self.removeDots(i, (i%2)*2, 3)
		elif self.options.variant == 'hexagon3':
			for i in range(1, len(self.generatedCircles), 2):
				self.removeDots(i, (i//2)%2, 2)
		elif self.options.variant == 'hexagon4':
			self.removeGroups(2, 4)
		elif self.options.variant == 'hexagon5':
			for i in range(1, len(self.generatedCircles), 2):
				self.removeDots(i, 0, 2)

# Create effect instance and apply it.
if __name__ == '__main__':
	PolarGrid().affect()