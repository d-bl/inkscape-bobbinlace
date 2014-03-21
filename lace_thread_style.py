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
import inkex, simplestyle, simplepath, math, cubicsuperpath, bezmisc

__author__ = 'Jo Pol'
__credits__ = ['Jo Pol']
__license__ = 'GPL'
__version__ = '0.1.0'
__maintainer__ = 'Jo Pol'
__status__ = 'Development'

class ThreadStyle(inkex.Effect):
	"""
	Apply stroke style of selected path to connected paths
	"""
	def startPoint(self, parsedCubicsuperpath):
		return parsedCubicsuperpath[0][0][0]

	def endPoint(self, parsedCubicsuperpath):
		# TODO fix for curves with additional nodes
		return parsedCubicsuperpath[0][1][len(parsedCubicsuperpath[0][1]) - 1]

	def applyStroke (self, item, newStyle):
		parsedStyle = simplestyle.parseStyle(item.attrib.get('style', ''))
		# TODO apply other properties that start with 'stroke-' too
		parsedStyle['stroke'] = newStyle.get('stroke', None)
		item.attrib['style'] = simplestyle.formatStyle(parsedStyle)
		
	def applyToAdjecent(self, parsedStyle, point, skip):
		# TODO optimize with dictionaries (start/end-point:item) 
		for item in self.document.getiterator():
			if item.tag == inkex.addNS('path', 'svg'):
				if item != skip:
					p = cubicsuperpath.parsePath(item.get('d'))
					s = self.startPoint(p)
					e = self.endPoint(p)
					ds = bezmisc.pointdistance((point[0], point[1]), (s[0], s[1]))
					de = bezmisc.pointdistance((point[0], point[1]), (e[0], e[1]))
					if ds < 0.0001:
						self.applyStroke(item, parsedStyle)
						self.applyToAdjecent(parsedStyle, e, item)
					elif de < 0.0001:
						self.applyStroke(item, parsedStyle)
						self.applyToAdjecent(parsedStyle, s, item)
		
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
			parsedStyle = simplestyle.parseStyle(selected.attrib.get('style', ''))
			p = cubicsuperpath.parsePath(selected.get('d'))
			self.applyToAdjecent(parsedStyle, self.startPoint(p), selected)
			self.applyToAdjecent(parsedStyle, self.endPoint(p), selected)
			
# Create effect instance and apply it.
effect = ThreadStyle()
effect.affect()
