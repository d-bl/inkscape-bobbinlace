#!/usr/bin/env python2

# Copyright (c) 2017, Ben Connors
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
import math
import sys
import os

# Unix
sys.path.append("/usr/share/inkscape/extensions")
# OS X
sys.path.append("/Applications/Inkscape.app/Contents/Resources/extensions")
# Windows
sys.path.append("C:\\Program Files\\Inkscape\\share\\extensions")
sys.path.append("C:\\Program Files (x86)\\share\\extensions")

import inkex
import simplestyle

__author__ = "Ben Connors"
__credits__ = ["Ben Connors", "Veronika Irvine"]
__version__ = "0.0.4"
__status__ = "Development"
__maintainer__ = 'Veronika Irvine'
__license__ = "Simplified BSD"

TAU = 2*math.pi

class Vector:
    def __repr__(self):
        return "Vector(%.4f, %.4f)" % (self.dx,self.dy)

    def __hash__(self):
        return hash((self.x,self.y))

    def rotate(self,theta):
        """ Rotate counterclockwise by theta."""
        return self.mag*Vector(math.cos(self.theta+theta),
                               math.sin(self.theta+theta),
                               _theta=self.theta+theta)

    def __mul__(self,other):
        return Vector(self.dx*other,self.dy*other,_theta=self.theta)

    def __rmul__(self,other):
        return self*other

    def dot(self,other):
        return self.dx*other.dx + self.dy*other.dy

    def angle(self,other):
        """ Angle made by this vector with another."""
        return math.acos(self.dot(other)/(self.mag*other.mag))

    def __init__(self,dx,dy,_theta=None):
        """ Create a vector with the specified components.

        _theta should NOT be passed in normal use - this value is passed by
        vector functions where the angle of the new vector is known in order
        to eliminate that calculation.
        """
        self.dx = float(dx)
        self.dy = float(dy)
        self.mag = math.sqrt(dx**2 + dy**2)
        self.tuple = (dx,dy)
        
        ## Angle to positive X axis
        if _theta == None:
            _theta = math.acos(self.dx/self.mag)
            self.theta = TAU-_theta if self.dy < 0 else _theta
        else:
            self.theta = _theta

def base_vectors(radius,segments):
    """ Create vectors for all vertices on the specified polygon."""
    ## Start at 12 o'clock
    theta = TAU/4
    ## Move clockwise
    dtheta = -TAU/segments

    vector = Vector(0,radius)
    vectors = [vector]
    for i in range(1,segments):
        vector = vector.rotate(dtheta)
        vectors.append(vector)
    return vectors

def fuzzy_eq(a,b):
    if a-b <= 1e-8:
        return True
    return False

def polar_wrap(points,radius,segments,angle=math.pi/4):
    """ Wrap a grid around the origin.
    
    points is a list of 2- or 3-tuples.

        In the case of 3-tuples, they should be laid out like:
            
            (x,y,name)

        Whereas 2-tuples should eliminate the name portion. Only one format
        may be passed; they may not be mixed. 

        x- and y- values are rounded to the nearest integer. If more precision
        is desired, scale up the points before calling this function.

        x-values should be within [0,segments) but values not within that 
        range will be moved within that range. 

        y-values must be greater than 0 - an error will be raised if a y-value
        is less than 0.

        The "name" portion is not touched by this function; it is merely
        passed along. This may be used to identify points or groups of points.

    radius is the inside radius (i.e. distance to origin from a point with
    a y-value of 0).

    segments is the number of segments (sides) of the polygon.

    angle is the angle of the diagonal of the square approximation. It must be
    somewhere on (0,math.pi/2).
    """
    if angle <= 0 or angle >= math.pi/2:
        raise ValueError("Angle must be on (0,math.pi/2)")

    vectors = base_vectors(radius,segments)
    theta = TAU/segments
    
    """
    Determine the coefficient to multiply the vectors by in order to deal
    with a higher x-value.

    With R being the large radius (radius to next y-value) and r being the
    small radius (radius to current y-value):
    
    a^2 = r^2 (1 - math.cos(theta)) ## Cosine law
    b^2 = R^2 (1 - math.cos(theta))

    To get the most square-like trapezoid:

    R - r = 0.5(a+b)

    Subbing in the equations for b^2 and a^2 yields the following lines.
    """
    C = math.sqrt(2*(1-math.cos(theta)))
    val = 2*math.tan(math.pi/2-angle)
    coeff = (val+C)/(val-C)
    diff = coeff-1

    ## Sort points in order of increasing y-value.
    named = False
    if len(points[0]) == 3:
        named = True
        points = [(x,y,name) for x,y,name in sorted(points,key=lambda a: a[1])]
    else:
        points = [(x,y,None) for x,y in sorted(points,key=lambda a: a[1])]

    done = []
    cur_y = 0
    for point in points:
        x,y,name = point

        ## Check constraints
        if y < cur_y:
            raise ValueError("Invalid point (%d,%d)" % (x,y))
        elif y >= cur_y+1:
            ## Multiply vectors accordingly
            delta = math.floor(y-cur_y)
            vectors = [(coeff**delta)*v for v in vectors]
            cur_y = math.floor(y)

        ## Wrap x-value to lie in the proper place
        ## lazy
        while x < 0:
            x += segments
        while x >= segments:
            x -= segments

        if fuzzy_eq(y,int(y)) and fuzzy_eq(x,int(x)):
            x = int(x)
            ## Can do it the quick way
            wx,wy = vectors[x].tuple
        else:
            ## Use vector rotation
            ## Determine nearest vector (counterclockwise)
            pointer = vectors[math.floor(x)]
            ## Scale x and y to be within (0,1)
            x -= int(x)
            y -= int(y)
            c = C*x ## This value is used a lot, cache it
            ## Now the angle of rotation must be determined using cosine law
            factor = 1
            if not fuzzy_eq(x,0):
                ## x isn't equal to 0, must rotate vector
                n2 = 1+c**2-2*c*math.cos((math.pi-theta)/2)
                factor = math.sqrt(n2)
                phi = math.acos((n2+1-c**2)/(2*factor))
                pointer = pointer.rotate(-phi)
            ## Correct vector magnitude
            pointer = (1+y*diff)*factor*pointer
            wx,wy = pointer.tuple
        if named:
            done.append((wx,wy,name))
        else:
            done.append((wx,wy))
    return done

def create_ground(unit,rows,cols,scale=1):
    """ Return a lace ground.

    This function returns a list of points and corresponding lines that may
    be transformed or passed to a drawing function (such as draw_image) in
    order to draw a lace ground.

    unit is the pattern for the lace ground, in the format returned by
        load_file.

    rows and cols are integers and represent the number of horizontal repeats
        and vertical repeats of the pattern, respectively.

    scale is an optional value that can be used to scale the pattern before it
        is repeated. Note that this comes with some constraints - the
        template's rows and cols after scaling (i.e. unit["rows"]*scale) must
        be an integer. For example, a template with 4 rows and 4 cols before
        scaling may be scaled by any integer value above 1 and select values
        between 1 and 0 (namely 0.25,0.5,0.75). A scale value of "True" may be
        passed if each repeat of the template should fit within a 1x1 square.
    """
    data = unit["data"]
    unit_rows = unit["rows"]
    unit_cols = unit["cols"]
    if scale <= 0:
        raise ValueError("Scale must be greater than zero")
    elif scale != 1:
        ## The user wants to scale the template
        _data = []
        for row in data:
            _row = []
            for c in row:
                if scale == True:
                    _row.append([i for n in zip([a/unit_cols for a in c[::2]],[a/unit_rows for a in c[1::2]]) for i in n])
                else:
                    _row.append([a*scale for a in c])
            _data.append(_row)
        data = _data
        unit_rows *= scale
        unit_cols *= scale
        ## Catching invalid input
        if not fuzzy_eq(unit_rows,int(unit_rows)):
            raise ValueError("Scale factor must result in an integer value for template rows")
        if not fuzzy_eq(unit_cols,int(unit_cols)):
            raise ValueError("Scale factor must result in an integer value for template cols")
        unit_rows = int(unit_rows)
        unit_cols = int(unit_cols)
    line_num = 0
    points = []
    for c in range(cols):
        ## Do each column first
        x = c*unit_cols
        for r in range(rows):
            y = r*unit_rows
            for row in data:
                for x1,y1,x2,y2,x3,y3 in row:
                    ## In order to draw lines in the correct order, an extra
                    ## point must be added
                    p1 = (x+x1,y+y1,"%09da,1"%line_num)
                    p2 = (x+x2,y+y2,"%09da,2"%line_num)
                    p1a = (x+x1,y+y1,"%09db,1"%line_num)
                    p3 = (x+x3,y+y3,"%09db,3"%line_num)
                    points.extend([p1,p2,p1a,p3])
                    line_num += 1
    return points

def load_file(fname):
    """ Load the specification for the unit cell from the file given.

    Note that the specification should be in the following format:

    TYPE    ROWS    COLS
    [x1,y1,x2,y2,x3,y3] [x4,y4,x5 ...

    And so on. The TYPE is always CHECKER and is ignored by this program.
    ROWS specifies the height of the     unit cell (i.e. max_y - min_y) 
    and COLS specifies the same for the width (i.e. max_x - min_x). 
    Note that this is not enforced when drawing the unit cell - points 
    may be outside this range. These values are used to determine the 
    distance between unit cells (i.e. unit cells may overlap).
    """

    data = []
    rows, cols = -1, -1
    with open(fname,'r') as f:
        for line in f:
            line = line.rstrip("\r\n \t")
            ## If rows is not a positive integer, we're on the first line
            if rows == -1:
                tmp = line.split('\t')
                _type,cols,rows = tmp[0],int(tmp[1]),int(tmp[2])
            else:
                data.append([])
                for cell in line[1:-1].split("]\t["):
                    ## The pattern must be rotated 90 degrees clockwise. It's
                    ## simplest to just do that here
                    tmp = [float(n) for n in cell.split(',')]
                    data[-1].append([a for b in zip([rows-i for i in tmp[1::2]],[cols-i for i in tmp[::2]]) for a in b])
    return {"type": _type, "rows": rows, "cols": cols, "data" : data}

def draw_image(points,draw_line=lambda a: None):
    """ Draw the image.

    points is a list of points, as returned by create_ground.

    draw_line is a function that draws a line connecting all points in the
        passed list in order.
    """
    groups = {}
    ## This loop scales points, sorts them into groups, and gets image parameters
    xs = []
    ys = []
    for x,y,n in points:
        xs.append(x)
        ys.append(y)
        sn = n.split(',',1)
        ident = 0
        if len(sn) == 2:
            ident = int(sn[1])
            n = sn[0]
        if n not in groups:
            groups[n] = []
        groups[n].append((x,y,ident))
    max_x = max(xs)
    min_x = min(xs)
    max_y = max(ys)
    min_y = min(ys)
    ## Sort all groups to draw lines in order
    for group in groups:
        groups[group].sort(key=lambda a:a[2])
    ## Sort all groups to draw groups in order
    groups = sorted([(name,pts) for name,pts in groups.iteritems()],key=lambda a:a[0])
    ## Draw lines
    for name,pts in groups:
        _pts = []
        for p in pts:
            _pts.append([p[0]-min_x,p[1]-min_y])
        draw_line(_pts)

class PolarGround(inkex.Effect):
    def unit_to_uu(self,param):
        """ Convert units.

        Converts a number in some units into the units used internally by 
        Inkscape.
        
        param is a string representing a number with units attached. An 
            example would be "3.8mm". Any units supported by Inkscape
            are supported by this function.
        
        This wrapper function catches changes made to the location
        of the function between Inkscape versions.
        """
        try:
            return self.unittouu(param)
        except:
            return inkex.unittouu(param)

    def draw_line(self,points):
        """ Draw a line connecting points in order.

        Points may be a 2- or 3-tuple (third part is ignored).
        """

        ## Path is simple
        path = ("M%.4f,%.4fL" % tuple(points[0][:2])) + 'L'.join([("%f,%f" % tuple(a[:2])) for a in points[1:]])

        ## Hardcoded style, with options
        s = {"stroke-linejoin": "miter", 
             "stroke-width": self.unit_to_uu(str(self.options.size)+"mm"),
             "stroke-opacity": "1.0", 
             "fill-opacity": "1.0",
             "stroke": self.options.color, 
             "stroke-linecap": "butt",
             "fill": "none"}

        ## Attributes for new element
        attribs = {"style" : simplestyle.formatStyle(s),
                   "d" : path}

        ## Add new element
        inkex.etree.SubElement(self.current_layer, inkex.addNS("path", "svg"), attribs)

    def effect(self):
        """ Draw the ground. """
        ## Convert color to hexadecimal string (ignoring alpha)
        color = long(self.options.color)
        color = color & 0xFFFFFFFF if color < 0 else color
        self.options.color = "#%06x" % (color >> 8)

        ## Correct the radius
        self.options.radius = self.unit_to_uu(str(self.options.radius)+"mm")
        
        ## Convert the angle
        self.options.angle = math.radians(self.options.angle)

        ## Load the file
        unit = load_file(self.options.file)

        ## Ensure no y-values are below 0
        min_y = min([b for a in [i[1::2] for row in unit["data"] for i in row] for b in a]) 
        if min_y < 0:
            data = []
            for row in unit["data"]:
                _row = []
                for c in row:
                    _row.append([a for b in zip(c[::2],[i-min_y for i in c[1::2]]) for a in b])
                data.append(_row)
            unit["data"] = data

        ## Create the ground
        points = create_ground(unit,self.options.rows,self.options.cols)

        ## Debug rings
        #for r in range(self.options.rows*unit["rows"]):
        #    for c in range(self.options.cols*unit["cols"]+1):
        #        points.append((c,r,"%05d,%05d" % (r,c)))

        ## Wrap it around a polygon
        points = polar_wrap(points,self.options.radius,self.options.cols*unit["cols"],angle=self.options.angle)

        ## Draw everything
        draw_image(points,draw_line=lambda a: self.draw_line(a))

        
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--file",
                                     action="store",
                                     type="string",
                                     dest="file")
        self.OptionParser.add_option("--radius",
                                     action="store",
                                     type="float",
                                     dest="radius")
        self.OptionParser.add_option("--rows",
                                     action="store",
                                     type="int",
                                     dest="rows")
        self.OptionParser.add_option("--cols",
                                     action="store",
                                     type="int",
                                     dest="cols")
        self.OptionParser.add_option("--angle",
                                     action="store",
                                     type="int",
                                     dest="angle")
        self.OptionParser.add_option("--size",
                                     action="store",
                                     type="float",
                                     dest="size")
        self.OptionParser.add_option("--color",
                                     action="store",
                                     type="string",
                                     dest="color")

effect = PolarGround()
effect.affect()
