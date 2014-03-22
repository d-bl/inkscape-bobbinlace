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
import inkex, simplestyle, simplepath, math, cubicsuperpath, bezmisc

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
		self.tolerance = 0.0001
	
	def startPoint(self, cubicSuperPath):
		"""
		returns the first point of a Cubicsuperpath
		"""
		return cubicSuperPath[0][0][0]

	def endPoint(self, csp):
		"""
		returns the last point of a CubicSuperPath
		"""
		return csp[0][len(csp[0]) - 1][len(csp[0][1]) - 1]

	def findCandidatesToChangeTheStyle(self):
		"""
		collect the document items that are a path
		"""
		# TODO store (start/end-point) along with the item
		self.candidates = []
		for item in self.document.getiterator():
			if item.tag == inkex.addNS('path', 'svg'):
				self.candidates.append(item)

	def applyStyle(self, style, item):
		item.attrib['style'] = style
		self.candidates.remove(item)

	def applyToAdjecent(self, style, point):
		while point != None:
			next = None
			for item in self.candidates:
				csp = cubicsuperpath.parsePath(item.get('d'))
				s = self.startPoint(csp)
				e = self.endPoint(csp)
				p = (point[0], point[1])
				if  bezmisc.pointdistance(p, (s[0], s[1])) < self.tolerance:
					self.applyStyle(style, item)
					next = e
					break
				elif bezmisc.pointdistance(p, (e[0], e[1])) < self.tolerance:
					self.applyStyle(style, item)
					next = s
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
		for id, selected in self.selected.iteritems():
			if selected.tag != inkex.addNS('path', 'svg'):
				inkex.debug('selected element is not a path')
				return
			self.findCandidatesToChangeTheStyle()
			self.candidates.remove(selected)
			style = selected.attrib.get('style', '')
			csp = cubicsuperpath.parsePath(selected.get('d'))
			self.applyToAdjecent(style, self.startPoint(csp))
			self.applyToAdjecent(style, self.endPoint(csp))
			
# Create effect instance and apply it.
effect = ThreadStyle()
effect.affect()
