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
import simplestyle, random # for color

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

    def random_color(self):
        red = random.uniform(0.2, 1)
        grn = random.uniform(0.2, 1)
        blu = random.uniform(0.2, 1)
        return '#%02x%02x%02x' % (red*255, grn*255, blu*255)

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

    # def findCandidatesForStyleChange(self, skip):
        # """
        # collect the document items that are a Bezier curve
        # """
        # candidates = []
        # for item in self.document.getiterator():
            # if self.isBezier(item) and item != skip:
                # csp = cubicsuperpath.parsePath(item.get('d'))
                # s = self.startPoint(csp)
                # e = self.endPoint(csp)
                # candidates.append({'s':s, 'e':e, 'i':item})
        # return candidates

    def find_threads(self, names):
        """ Collect items with a class.
            - return a dict of item, start, end points
        """
        # inkex.debug("sel names = %s"%(names))
        candidates = []
        for item in self.document.getiterator():
            if item.get('class') in names:
                csp = cubicsuperpath.parsePath(item.get('d'))
                s = self.startPoint(csp)
                e = self.endPoint(csp)
                candidates.append({'s':s, 'e':e, 'i':item})
        return candidates
    
    def change_style(self, items, style_fields, colors):
        " change only the aspects of style in style_fields "
        if colors: # use a color chosen for each thread.
            names, colors = zip(*colors) # unzip
        for item in items:
            name = item['i'].get('class')
            mystyle = simplestyle.parseStyle(item['i'].get('style'))
            for s,v in style_fields:
                mystyle[s] = str(v)
            if colors:
                pos = names.index(name)
                mystyle['stroke'] = colors[pos]
            item['i'].attrib['style'] = simplestyle.formatStyle(mystyle)
    
    def gather_thread_names(self):
        """ Gather all threadnames in a unique list
            - ignore "link" on its own (end of thread)
        """
        names = []
        for item in self.document.getiterator():
            if item.tag == inkex.addNS('path', 'svg'):
                name = item.get('class')
                if name and name != 'link' and name not in names:
                    names.append(name)
        return names
    
    # def applyStyle(self, item):
        # """
        # Change the style of the item and remove it form the candidates
        # """
        # item['i'].attrib['style'] = self.style
        # self.candidates.remove(item)

    # def applyToAdjacent(self, point):
        # while point != None:
            # p = (point[0], point[1])
            # next = None
            # for item in self.candidates:
                # if  bezmisc.pointdistance(p, (item['s'][0], item['s'][1])) < self.options.tolerance:
                    # self.applyStyle(item)
                    # next = item['e']
                    # break
                # elif bezmisc.pointdistance(p, (item['e'][0], item['e'][1])) < self.options.tolerance:
                    # self.applyStyle(item)
                    # next = item['s']
                    # break
            # point = next



    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        ids = self.options.ids
        self.options.color = self.getColorString(self.options.color)
        conversion = self.getUnittouu("1" + self.options.units)
        threadnames = self.gather_thread_names()
        # inkex.debug("%s, %s"%(ids, threadnames))
        selected = self.selected.values()#[0]
        # if len(self.selected) != 1:
            # inkex.debug('no object selected, or more than one selected')
            # return
        # if not self.isBezier(selected):
            # inkex.debug('selected element is not a Bezier curve')
            # return
        if selected: # if we have a selection - apply color to all selected
            names = [item.get('class') for item in selected if item.get('class')]
            colors = False
        else: # if no selection - apply random color to all threads
            names = threadnames
            colors = zip(names, [self.random_color() for n in names])
        candidates = self.find_threads(names)
        # inkex.debug("%s, %s"%(len(candidates), candidates[0]))
        style_changes = [('stroke',self.options.color), ('stroke-width',self.options.width*conversion)]
        self.change_style(candidates, style_changes, colors)
        # self.style = 'fill:none;stroke:{1};stroke-width:{0}'.format(self.options.width*conversion, self.options.color)
        # csp = cubicsuperpath.parsePath(selected.get('d'))
        # self.selected.values()[0].attrib['style'] = self.style
        # self.applyToAdjacent(self.startPoint(csp))
        # self.applyToAdjacent(self.endPoint(csp))
        self.options.ids = ids # ! failed experiment to pass selection back
            
# Create effect instance and apply it.
if __name__ == '__main__':
    ThreadStyle().affect()

### todo:
# selection changing:
# - can we send a selection back to calling program - self.options.ids
# drawing over/under
# - traverse the lines with markers trying to get under/over correct
# - problem with marker approach is that on top isn't possible for everyone
#   - try diff marker options
#   - try non-marker soln using small circles in between and draw order(tricky)