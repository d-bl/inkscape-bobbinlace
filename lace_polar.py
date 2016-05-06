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
from math import pi, sin, cos, tan, radians


# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle

__author__ = 'Jo Pol'
__credits__ = ['Veronika Irvine']
__license__ = 'GPLv3'
__version__ = '0.6.0'
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

		# parse the options
		self.OptionParser.add_option('-a', '--angle', action='store', type='float', dest='angleOnFootside', default=45, help='grid angle (degrees)')
		self.OptionParser.add_option('-d', '--dots', action='store', type='int', dest='dotsPerCircle', default=180, help='number of dots on a circle')
		self.OptionParser.add_option('-o', '--outerDiameter', action='store', type='float', dest='outerDiameter', default=160, help='outer diameter (mm)')
		self.OptionParser.add_option('-i', '--innerDiameter', action='store', type='float', dest='innerDiameter', default=100, help='minimum inner diameter (mm)')
		self.OptionParser.add_option('-f', '--fill', action='store', type='string', dest='dotFill', default='-6711040', help='dot color')
		self.OptionParser.add_option('-A', '--alignment', action='store', type='string', dest='alignment', default='outside', help='exact diameter on [inside|outside]')
		self.OptionParser.add_option('-s', '--size', action='store', type='float', dest='dotSize', default=0.5, help='dot diameter (mm)')
		self.OptionParser.add_option('-v', '--variant', action='store', type='string', dest='variant', default='', help='omit rows to get [|rectangle|hexagon1]')
		self.OptionParser.add_option('-u', '--units', action = 'store', type = 'string', dest = 'units', default = 'mm', help = 'The units the measurements are in')

	def group(self, diameter):
		"""
		Create a group labeled with the diameter
		"""
		label = 'diameter: {0:.2f} mm'.format(diameter)
		attribs = {inkex.addNS('label', 'inkscape'):label}
		return inkex.etree.SubElement(self.gridContainer, inkex.addNS('g', 'svg'), attribs)

	def dots(self, diameter, circleNr, group):
		"""
		Draw dots on a grid circle
		"""
		offset = (circleNr % 2) * 0.5
		for dotNr in range (0, self.options.dotsPerCircle):
			a = (dotNr + offset) * self.alpha
			x = (diameter / 2.0) * cos(a)
			y = (diameter / 2.0) * sin(a)
			attribs = {'style':self.dotStyle, 'cx':str(x * self.scale), 'cy':str(y * self.scale), 'r':self.dotR}
			inkex.etree.SubElement(group, inkex.addNS('circle', 'svg'), attribs)

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

	def iterate(self, diameter, circleNr):
		"""
		Create a group with a ring of dots.
		Returns half of the arc length between the dots
		which becomes the distance to the next ring.
		"""
		group = self.group(diameter)
		self.dots(diameter, circleNr, group)
		self.generatedCircles.append(group)
		return diameter * self.change

	def generate(self):
		"""
		Generate rings with dots, either inside out or outside in
		"""
		circleNr = 0
		minimum = 2 * self.options.dotSize * self.options.dotsPerCircle /pi
		if minimum < self.options.innerDiameter:
			minimum = 	self.options.innerDiameter
		if self.options.alignment == 'outside':
			diameter = self.options.outerDiameter
			while diameter > minimum:
				diameter -= self.iterate(diameter, circleNr)
				circleNr += 1
		else:
			diameter = minimum
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
		start = len(dots) - 1 - offset
		for j in range(start, -1, 0-step):
			group.remove(dots[j])

	def computations(self, angle):
		self.alpha = radians(360.0 / self.options.dotsPerCircle)
		correction = pi / (4 * self.options.dotsPerCircle)
		correction *= tan(angle*0.93)
		self.change = tan(angle - correction) * pi / self.options.dotsPerCircle

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""

		# color
		self.options.dotFill = self.getColorString(self.options.dotFill)
		# constants
		self.dotStyle = simplestyle.formatStyle({'fill': self.options.dotFill,'stroke':'none'})
		self.scale = self.getUnittouu("1" + self.options.units)
		self.dotR = str(self.options.dotSize * (self.scale/2))
		self.computations(radians(self.options.angleOnFootside))

		# processing variables
		self.generatedCircles = []
		self.gridContainer =  self.current_layer

		self.generate()

		if self.options.variant == 'rectangle':
			self.removeGroups(1, 2)
		elif self.options.variant == 'hexagon1':
			self.removeGroups(0, 3)
		elif self.options.variant == 'hexagon2' or self.options.variant == 'snow2':
			for i in range(0, len(self.generatedCircles), 1):
				self.removeDots(i, (((i%2)+1)*2)%3, 3)
		elif self.options.variant == 'hexagon3':
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, (i//2+1)%2, 2)
		elif self.options.variant == 'hexagon4':
			self.removeGroups(0, 4)
		elif self.options.variant == 'hexagon5' or self.options.variant == 'snow1':
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, 1, 2)

		self.dotStyle = simplestyle.formatStyle({'fill': 'none','stroke':self.options.dotFill,'stroke-width':0.7})
		self.dotR = str((((self.options.innerDiameter * pi) / self.options.dotsPerCircle) / 2) * self.scale)
		self.generatedCircles = []
		if self.options.variant == 'snow2':
			self.options.dotsPerCircle = self.options.dotsPerCircle // 3
			self.computations(radians(self.options.angleOnFootside))
			self.generate()
		elif self.options.variant == 'snow1':
			self.generate()
			self.removeGroups(1, 2)
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, i%4, 2)
			for i in range(0, len(self.generatedCircles), 2):
				self.removeDots(i, (i+1)%2, 2)
			for i in range(2, len(self.generatedCircles), 4):
				self.removeDots(i, 0, self.options.dotsPerCircle)

# Create effect instance and apply it.
if __name__ == '__main__':
	PolarGrid().affect()