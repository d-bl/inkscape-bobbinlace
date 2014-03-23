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
import inkex, cubicsuperpath, bezmisc

__author__ = 'Jo Pol'
__credits__ = ['Jo Pol']
__license__ = 'GPL'
__version__ = '${project.version}'
__maintainer__ = 'Jo Pol'
__status__ = 'Development'

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
		self.OptionParser.add_option('-t', '--tolerance', action='store', type='float', dest='tolerance', default=0.0001, help='tolerance (max. distance between segments)')
	
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

	def applyToAdjecent(self, point):
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

	def effect(self):
		"""
		Effect behaviour.
		Overrides base class' method and draws something.
		"""
		if len(self.selected) != 1:
			inkex.debug('no object selected, or more than one selected')
			return
		selected = self.selected.values()[0]
		if not self.isBezier(selected):
			inkex.debug('selected element is not a Bezier curve')
			return
		self.findCandidatesForStyleChange(selected)
		self.style = selected.attrib.get('style', '')
		csp = cubicsuperpath.parsePath(selected.get('d'))
		self.applyToAdjecent(self.startPoint(csp))
		self.applyToAdjecent(self.endPoint(csp))
			
# Create effect instance and apply it.
if __name__ == '__main__':
	ThreadStyle().affect()
