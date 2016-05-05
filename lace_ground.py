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
import sys
from os import path

try:
	from Tkinter import *
	import tkFileDialog as tkf
except: tk = False
else: tk = True

# We will use the inkex module with the predefined 
# Effect base class.
import inkex, simplestyle, simpletransform
from math import sin,cos,radians, degrees, atan2, ceil

__author__ = 'Veronika Irvine'
__credits__ = ['Ben Connors','Veronika Irvine']
__license__ = 'GPL'
__version__ = '${project.version}'
__maintainer__ = 'Veronika Irvine'
__status__ = 'Development'

def calc_angle_between_points(p1x, p1y, p2x, p2y):
	" return ngle in degrees "
	xDiff = p2x - p1x
	yDiff = p2y - p1y
	return degrees(atan2(yDiff, xDiff))

class LaceGround(inkex.Effect):
	"""
	Create a ground for lace from a text file descriptor 
	using specified angle and spacing
	"""
	def __init__(self,fname):
		"""
		Constructor.
		Defines the "--centerx" option of the script.
		"""
		# Call the base class constructor.
		inkex.Effect.__init__(self)
		
		# Set the fname variable
		self.fname = fname
		
		self.OptionParser.add_option('-f', '--file', action='store', type='string', dest='file', help='File containing lace ground description', default='lace_templates/4x4_33.txt')
		self.OptionParser.add_option('-a', '--angle', action='store', type='float', dest='angle', default=45.0, help='Grid Angle')
		self.OptionParser.add_option('-d', '--distance', action='store', type='float', dest='spacing', default=10.0, help='Distance between grid points in mm')
		self.OptionParser.add_option('-w', '--width', action='store', type='float', dest='width', default=100, help='Width of ground pattern')
		self.OptionParser.add_option('-l', '--height', action='store', type='float', dest='height', default=100, help='Height of ground pattern')
		self.OptionParser.add_option('-s', '--size', action='store', type='float', dest='size', default=1, help='Width of lines')
		self.OptionParser.add_option('-c', '--linecolor', action='store', type='string', dest='linecolor', default='#FF0000', help='Color of lines')
		self.OptionParser.add_option('-u', '--units', action = 'store', type = 'string', dest = 'units', default = 'mm', help = 'The units the measurements are in')
		self.OptionParser.add_option("-z", "--drawdots", action="store", type="inkbool", dest="drawdots", default=False, help="Draw minimal dot template")
		self.OptionParser.add_option('-p', '--dotdia', action='store', type='float', dest='dotdia', default=4, help='Diameter of the dots')
		self.OptionParser.add_option('-y', '--guidecolor', action='store', type='string', dest='guidecolor', default=0, help='Color of guides')
		# dummy for notebook
		self.OptionParser.add_option("", "--active-tab", action="store", type="string", dest="active_tab", default='pattern', help="Active tab. Not used now.")
        
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

	def circle(self, x, y, r, fill, parent):
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
		# insert path object
		inkex.etree.SubElement(parent, inkex.addNS('circle', 'svg'), attribs)

	def draw_grid_dot(self, x, y, parent):
		" Draw a single grid dot "
		dot_radius = self.options.dotdia/2
		fill = self.options.guidecolor
		self.circle(x, y, dot_radius, fill, parent)

	def line(self, x1, y1, x2, y2, parent, draw_arrows, arrow_length, dotgroup):
		"""
		Draw a line from point at (x1, y1) to point at (x2, y2).
		Style of line is hard coded and specified by 's'.
		"""
		# define the motions
		path = "M %s,%s L %s,%s" %(x1,y1,x2,y2)
		# define the stroke style
		s = {'stroke-linejoin': 'miter', 
			'stroke-width': self.options.size,
			'stroke-opacity': '1.0', 
			'fill-opacity': '1.0',
			'stroke': self.options.linecolor, 
			'stroke-linecap': 'round',
			'fill': 'none' }
		# create attributes from style and path
		attribs = {'style':simplestyle.formatStyle(s), 'd':path}
		# insert path object into current layer
		inkex.etree.SubElement(parent, inkex.addNS('path', 'svg'), attribs)
		# Draw Arrows ?
		if draw_arrows: # Put them in dotgroup
			path = "M 0,0 L %4.2f,%4.2f M 0,0 L %4.2f,%4.2f" % (arrow_length, arrow_length/2, arrow_length, -arrow_length/2)
			arrowX = x1 + (x2-x1)/2.2
			arrowY = y1 + (y2-y1)/2.2
			angle = calc_angle_between_points(x2,y2,x1,y1)
			s = {'stroke-linejoin': 'miter', 
				 'stroke-width': self.options.size/2,
				 'stroke': self.options.guidecolor, 
				 'stroke-linecap': 'round',
				 'fill': 'none' }
			# rotate arrow
			t = 'rotate(%f)' % (angle)
			attribs = {'style':simplestyle.formatStyle(s), 'd':path, 'transform':t}
			arrow = inkex.etree.SubElement(dotgroup, inkex.addNS('path', 'svg'), attribs)
			# transform arrow into correct spot
			scale_matrix = [[1, 0.0, arrowX], [0.0, 1, arrowY]]
			simpletransform.applyTransformToNode(scale_matrix, arrow)

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
		arrow_length = spacing/6.0

		while repeatY * rowCount < maxRows:
			x = 0.0
			repeatX = 0
			
			while repeatX * colCount < maxCols:
				# only draw arrows in first pattern
				draw_arrows = (repeatX==0 and repeatY==0 and self.options.drawdots)
				for row in data:
					for coords in row:
						x1 = x + coords[0]*deltaX
						y1 = y + coords[1]*deltaY
						x2 = x + coords[2]*deltaX
						y2 = y + coords[3]*deltaY
						x3 = x + coords[4]*deltaX
						y3 = y + coords[5]*deltaY
						
						self.line(x1,y1,x2,y2, parent, draw_arrows, arrow_length, dotgroup)
						self.line(x1,y1,x3,y3, parent, draw_arrows, arrow_length, dotgroup)
						
						# Draw each dot only once
						if repeatX==0 and repeatY==0 and self.options.drawdots: # reduce redraws
							id = "%s %s" % (coords[0], coords[1]) # id based on coord
							if not dots.has_key(id): # draw it once
								x1 = x + coords[0]*deltaX
								y1 = y + coords[1]*deltaY
								self.draw_grid_dot(x1, y1, dotgroup)
								dots[id] = True
				
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
		label = path.splitext(path.basename(self.fname))[0]
		
		#Convert input from mm to pixels, assuming 90 dpi
		conversion = self.getUnittouu("1" + self.options.units)
		self.options.width *= conversion
		self.options.height *= conversion
		self.options.size *= conversion
		self.options.dotdia *= conversion
		# sort out color
		self.options.linecolor = self.getColorString(self.options.linecolor)
		self.options.guidecolor = self.getColorString(self.options.guidecolor)
		
		# Users expect spacing to be the vertical distance between footside pins (vertical distance between every other row) 
		# but in the script we use it as as diagonal distance between grid points
		# therefore convert spacing based on the angle chosen
		theta = radians(self.options.angle)
		spacing = self.options.spacing * conversion/(2.0*cos(theta))
		
		# Top level Group
		t = 'translate(%s,%s)' % (self.view_center[0]-self.options.width/2, self.view_center[1]-self.options.height/2)
		grp_attribs = {inkex.addNS('label','inkscape'):'Lace Pattern %s'%(label), 'transform':t}
		topgroup = inkex.etree.SubElement(self.current_layer, 'g', grp_attribs)
		dotgroup = None
		if self.options.drawdots:
			grp_attribs = {inkex.addNS('label','inkscape'):'Dots'}
			dotgroup = inkex.etree.SubElement(topgroup, 'g', grp_attribs)
		# Draw a ground based on file description and user inputs
		# For now, assume style is Checker but could change in future
		self.drawCheckerGround(result["data"],result["rowCount"],result["colCount"], spacing, theta, topgroup, dotgroup)


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
