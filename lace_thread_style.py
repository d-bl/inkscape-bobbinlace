#!/usr/bin/env python
# Copyright 2014 Jo Pol
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
#########################################################################


import inkex, cubicsuperpath, bezmisc

__author__ = 'Jo Pol'
__credits__ = ['Jo Pol','Mark Shafer']
__license__ = 'GPLv3'

class ThreadStyle(inkex.Effect):
	"""
	Apply stroke style of selected path to connected paths
	"""
	def __init__(self):
		"""
		Constructor.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)
		self.OptionParser.add_option('-t', '--tolerance', action='store', type='float', dest='tolerance', default=0.05, help='tolerance (max. distance between segments)')
		self.OptionParser.add_option('-u', '--units', action = 'store', type = 'string', dest = 'units', default = 'mm', help = 'The units the measurements are in')
		self.OptionParser.add_option('-w', '--width', action='store', type='float', dest='width', default='1', help='thread width')
		self.OptionParser.add_option('-c', '--color', action='store', type='string', dest='color', default='#FF9999', help='thread color')

	def getUnittouu(self, param):
		" compatibility between inkscape 0.48 and 0.91 "
		try:
			return inkex.unittouu(param)
		except AttributeError:
			return self.unittouu(param)

	def startPoint(self, cubicSuperPath):
		"""
		returns the first point of a CubicSuperPath
		"""
		return cubicSuperPath[0][0][0]

	def endPoint(self, csp):
		"""
		returns the last point of a CubicSuperPath
		"""
		return csp[0][len(csp[0]) - 1][len(csp[0][1]) - 1]

	def isBezier(self, item):
		return item.tag == inkex.addNS('path', 'svg') and item.get(inkex.addNS('connector-curvature', 'inkscape'))

	def findCandidatesForStyleChange(self, skip):
		"""
		collect the document items that are a Bezier curve
		"""
		self.candidates = []
		for item in self.document.getiterator():
			if self.isBezier(item) and item != skip:
				csp = cubicsuperpath.parsePath(item.get('d'))
				s = self.startPoint(csp)
				e = self.endPoint(csp)
				self.candidates.append({'s':s, 'e':e, 'i':item})

	def applyStyle(self, item):
		"""
		Change the style of the item and remove it form the candidates
		"""
		item['i'].attrib['style'] = self.style
		self.candidates.remove(item)

	def applyToAdjacent(self, point):
		while point != None:
			p = (point[0], point[1])
			next = None
			for item in self.candidates:
				if  bezmisc.pointdistance(p, (item['s'][0], item['s'][1])) < self.options.tolerance:
					self.applyStyle(item)
					next = item['e']
					break
				elif bezmisc.pointdistance(p, (item['e'][0], item['e'][1])) < self.options.tolerance:
					self.applyStyle(item)
					next = item['s']
					break
			point = next

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

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		self.options.color = self.getColorString(self.options.color)
		conversion = self.getUnittouu("1" + self.options.units)
		if len(self.selected) != 1:
			inkex.debug('no object selected, or more than one selected')
			return
		selected = self.selected.values()[0]
		if not self.isBezier(selected):
			inkex.debug('selected element is not a Bezier curve')
			return
		self.findCandidatesForStyleChange(selected)
		self.style = 'fill:none;stroke:{1};stroke-width:{0}'.format(self.options.width*conversion, self.options.color)
		csp = cubicsuperpath.parsePath(selected.get('d'))
		self.selected.values()[0].attrib['style'] = self.style
		self.applyToAdjacent(self.startPoint(csp))
		self.applyToAdjacent(self.endPoint(csp))
			
# Create effect instance and apply it.
if __name__ == '__main__':
	ThreadStyle().affect()
