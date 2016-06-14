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
import math, simpletransform
from copy import deepcopy

__author__ = 'Jo Pol'
__credits__ = ['Jo Pol']
__license__ = 'GPL'
__version__ = '${project.version}'
__maintainer__ = 'Jo Pol'
__status__ = 'Development'

bobbin_path = "m -1.252711,0.01361042 c -2.0058699,0.0161 -3.29569,3.17466998 -0.37998,3.60203998 0,0 \
               0.066682,11.5542496 -0.17607,17.7028296 -0.031037,0.78614 0.35211,1.57119 -0.7908199,2.22383 \
               -2.4753801,1.3408 -0.42951,4.9472 -0.3608,7.1695 1.0825399,4.117205 1.0596899,8.408805 \
               0.3478,12.585505 -1.64596,10.564 -2.2015401,21.6357 1.2555199,31.9161 0.3219301,0.5457 \
               0.69042007,2.8026 1.40054007,2.7636 0.71047,0.04 1.07854993,-2.2177 1.40056993,-2.7636 \
               3.45706,-10.2804 2.9029,-21.3521 1.25695,-31.9161 -0.7119,-4.1767 -0.73619,-8.4683 \
               0.34636,-12.585505 0.0687,-2.2223 2.11603,-5.8287 -0.35934,-7.1695 C 1.295109,22.80648 \
               1.6393471,21.992097 1.6152571,21.205711 1.428631,15.113557 1.719679,3.6156504 1.719679,3.6156504 \
               c 2.66285,-0.25962 1.46385,-3.61810998 -0.54202,-3.60203998 z"

def calc_angle_between_points(p1, p2):
    xDiff = p2[0] - p1[0]
    yDiff = p2[1] - p1[1]
    return math.degrees(math.atan2(yDiff, xDiff))
def make_vector(p1,p2, normalise=False):
    vector = [b-a for a,b in zip(p1,p2)]
    if normalise:
        v_mag = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2)
        return [n/v_mag for n in vector]
    else:
        return vector
def dot(a,b, normalise=True):
    " a,b must be unit vectors "
    if normalise:
        a_mag = math.sqrt(a[0]*a[0] + a[1]*a[1])#sum(a)
        a = [ n/a_mag for n in a]
        b_mag = math.sqrt(b[0]*b[0] + b[1]*b[1])#sum(b)
        b = [ n/b_mag for n in b]
    #inkex.debug("compare = %s %s"%(a,b))
    return sum(p*q for p,q in zip(a, b))
def close_to(p1, p2, eps=5):
    " are they nearly coincident "
    x1,y1 = p1
    x2,y2 = p2
    if abs(max(x1,x2)-min(x1,x2)) < eps and abs(max(y1,y2)-min(y1,y2)) < eps:
        return True
    else:
        return False
def find_similar_direction(direction, threads, linkid):
    angle = 0
    thread = None
    for t_dir, t in threads:
        t_angle = abs(dot(direction, t_dir)) #using ABS to simplify test
        #inkex.debug("compare = %s"%(t_angle))
        if t_angle > angle:
            # 0 = right angles
            # 1 = same direction
            inkex.debug("compare = %s %s, %s"%(angle, t_angle, t.get('class')))
            angle = t_angle
            thread = t
    return thread


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
        self.OptionParser.add_option('-b', '--bobbin', action="store", type="inkbool", dest="bobbin", default=True, help="Show a bobbin shape at end of thread")
        #
        self.bobbin = {inkex.addNS('label','inkscape'):'Bobbin',
                       inkex.addNS('transform-center-y', 'inkscape') : '39',
                       inkex.addNS('transform-center-x', 'inkscape') : '0',
                       'd' : bobbin_path,
                       'style' : 'fill:#88c831;stroke:#000000;stroke-width:0.17;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill-opacity:1'
                       }

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

    def substitute_bobbin(self, link_ids, parent):
        """ Loop over the link_id paths,
            - replace marker with directed bobbin shape
            - rotate towards vertical (gravity)
            - set thread class for later recolor
        """
        # Delete the old circles
        for circle_id in self.find_ids_by_class(['node'], tagtype=inkex.addNS('circle', 'svg')):
            circle_node = self.getElementById(circle_id)
            circle_node.getparent().remove( circle_node )
        bobbins = [] # collect to pass on
        for idx in link_ids:
            link = self.getElementById(idx)
            threadname = link.get('class')
            csp = cubicsuperpath.parsePath(link.get('d'))
            end = self.endPoint(csp)
            start = self.startPoint(csp)
            bobbin = deepcopy(self.bobbin)
            # color = simplestyle.parseStyle(link.get('style'))['stroke']
            # style = simplestyle.parseStyle(bobbin['style'])
            # style['fill'] = color
            # bobbin['style'] = simplestyle.formatStyle(style)
            # droop the bobbins towards the vertical.
            angle = calc_angle_between_points(end, start)+90
            if angle > 180: angle -= 360
            bobbin['transform'] = 'rotate(%f)'%(angle*0.6) # droop factor
            id = self.uniqueId("bobbin", True) # make a new unique id
            bobbin['id'] = id
            bobbin['class'] = threadname
            ell = inkex.etree.SubElement(parent, inkex.addNS('path','svg'), bobbin )
            # ell.attrib['class'] = threadname
            # place it
            repos = [[1, 0.0, end[0]], [0.0, 1, end[1]]]
            simpletransform.applyTransformToNode(repos, ell)
            # gather the ids for later recolor
            bobbins.append(id)
        return bobbins
        
    def random_color(self):
        red = random.uniform(0.2, 1)
        grn = random.uniform(0.2, 1)
        blu = random.uniform(0.2, 1)
        return '#%02x%02x%02x' % (red*255, grn*255, blu*255)

    def startPoint(self, cubicSuperPath):
        " Returns the first point of a CubicSuperPath "
        return cubicSuperPath[0][0][0]

    def endPoint(self, csp):
        " Returns the last point of a CubicSuperPath "
        return csp[0][len(csp[0]) - 1][len(csp[0][1]) - 1]


    def find_ids_by_class(self, names, tagtype=inkex.addNS('path', 'svg')):
        candidates = []
        for item in self.document.getiterator():
            id = "bar"#item.get('id')
            classid = "foo"#item.get('class')
            if type(classid) != type("foo"): classid = "no"
            if type(id) != type("foo"): id = "nope"
            # inkex.debug(" %s class = %s"%(id, classid))
            if item.get('class') in names and item.tag == tagtype:
                id = item.get('id')
                if id: candidates.append(id) #!! simplify
        # inkex.debug(" %s "%(candidates))
        return candidates
            
    def change_style(self, item_ids, style_fields, colors=False):
        " change only the aspects of style in style_fields "
        if colors: # use a color chosen for each thread.
            names, colors = zip(*colors) # unzip
        for id in item_ids:
            item = self.getElementById(id)
            name = item.get('class')
            mystyle = simplestyle.parseStyle(item.get('style'))
            if item.get('id').find('bobbin') == -1:
                for s,v in style_fields:
                    mystyle[s] = str(v)
                if colors and name in names:
                    color_index = names.index(name)
                    mystyle['stroke'] = colors[color_index]
            else: # its a bobbin use fill instead of stroke
                if colors and name in names:
                    color_index = names.index(name)
                    inkex.debug(" %s %s "%(name, color_index))
                    mystyle['fill'] = colors[color_index]
            item.attrib['style'] = simplestyle.formatStyle(mystyle)
            
    
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
    

    # def recolor_link(self, link, thread):
        # " take color from thread and apply to link"
        # t_style = simplestyle.parseStyle(thread.get('style'))
        # color = t_style['stroke']
        # width = t_style['stroke-width'] 
        # linkstyle = simplestyle.parseStyle(link.get('style'))
        # linkstyle['stroke'] = color
        # linkstyle['stroke-width'] = width
        # link.attrib['style'] = simplestyle.formatStyle(linkstyle)

    def connect_links(self, thread_ids, link_ids):
        """ for each link, find the two threads that it might be
            - match the ones pointing closest to each other
            - set the classes the same so link has proper thread class name
        """
        # Gather links [pt, direction, node] into possibles
        possibles = []
        for id in link_ids:
            node = self.getElementById(id)
            path = cubicsuperpath.parsePath(node.get('d'))
            start = self.startPoint(path)
            vector = make_vector(start, self.endPoint(path))#, True)
            possibles.append([start, vector, node])
        possibles.sort(key=lambda x: x[0][0]) # sort into X ascending order
        # find threads
        inkex.debug("ymin = %s"%([possibles[0][0][1], math.sqrt(possibles[0][1][0]**2 + possibles[0][1][0]**2) ]))
        ymin = possibles[0][0][1] - math.sqrt(possibles[0][1][0]**2 + possibles[0][1][0]**2) # try to limit to threads near links
        threads = []
        # holds [end, direction vector, node] for each thread
        for id in thread_ids:
            node = self.getElementById(id)
            path = cubicsuperpath.parsePath(node.get('d'))
            end = self.endPoint(path)
            if end[1] >= ymin:
                # inkex.debug(" end = %s"%(end[1]))
                vector = make_vector(self.startPoint(path), end)#, True)
                threads.append([end, vector, node])
        inkex.debug("thread count = %d"%(len(threads)))
        # Restructure into connections
        # - group into pairs that share a connection point
        connections = []
        link_data = {}
        last_pt = [-1,-1]
        idx = 0
        while idx < len(possibles):
            link_pt, link_dir, link_node = possibles[idx]
            # inkex.debug("%s %s, %s"%(idx, link_pt, link_dir))
            if not close_to(last_pt, link_pt): 
                # start new one
                connections.append(link_data)
                link_data = {'link' : [[link_dir, link_node]] }
                last_pt = link_pt
                # find the connected threads (max 2)
                count = 0
                for (pt, t_dir, thread) in threads:
                    if close_to(pt, link_pt):
                        if count == 0:
                            link_data['thread'] = [[t_dir, thread]]
                            count += 1
                        else:
                            link_data['thread'].append([t_dir, thread])
                            #inkex.debug("%s"%([count, start, pt]))
                            break
            else: # same point so add to link
                link_data['link'].append([link_dir, link_node])
            idx += 1
        connections.append(link_data) # get the last one
        # now have list of links with one or two possible threads.
        # inkex.debug("thread0 = %s"%(threads[0]))
        for conn in connections[1:]:
            links = conn['link']
            # inkex.debug(" links = %s %s %s"%(len(links), links[0][0:1], conn.has_key('thread')))
            if len(links) == 1 and conn.has_key('thread'):
                # only one link
                link = links[0]
                threads = conn['thread']
                # inkex.debug(" threads = %s %s"%(len(threads), threads[0][0:1]))
                thread = find_similar_direction(link[0], threads, link[1])
                # set class to same as threadnames
                link[-1].attrib['class'] = thread.get('class')
            elif len(links) == 2 and conn.has_key('thread'):
                # has two links and two threads.
                threads = conn['thread']
                closest_link = None #link[0][1]
                closest_thread = None #threads[0][1]
                closest = 0
                # find the best fitting pair (closest angle)
                for l_dir, link in links:
                    for t_dir, thread in threads:
                        cos_angle = abs(dot(l_dir, t_dir))
                        if cos_angle > closest:
                            closest = cos_angle
                            closest_link = link
                            closest_thread = thread
                # set class to same as threadnames
                closest_link.attrib['class'] = closest_thread.get('class')
                # find the other one
                for l_dir, link in links:
                    if link != closest_link:
                        closest_link = link
                        break
                for t_dir, thread in threads:
                    if thread != closest_thread:
                        closest_thread = thread
                        break
                # set class to same as threadnames
                closest_link.attrib['class'] = closest_thread.get('class')
        # return the link ids we changed
        changed = [link[-1].get('id') for conn in connections[1:] for link in conn['link']]
        return changed #!! do not need this

    def find_parent(self, link_id):
        " move up until find parent that is a group "
        grptype = inkex.addNS('g', 'svg')
        # doctype = inkex.addNS('svg2', 'svg')
        node = self.getElementById(link_id)
        # inkex.debug("%s"%(link_id))
        while node.tag != grptype:
            # get parent
            node = self.getParentNode(node)
        return node
        

    def effect(self):
        """
        Effect behaviour.
        Overrides base class' method and draws something.
        """
        ids = self.options.ids
        self.options.color = self.getColorString(self.options.color)
        show_bobbin = self.options.bobbin
        conversion = self.getUnittouu("1" + self.options.units)
        all_threadnames = self.gather_thread_names()
        # inkex.debug("%s, %s"%(ids, all_threadnames))
        selected = self.selected.values()#[0]
        # if len(self.selected) != 1:
            # inkex.debug('no object selected, or more than one selected')
            # return
        # if not self.isBezier(selected):
            # inkex.debug('selected element is not a Bezier curve')
            # return
        if selected: # if we have a selection - apply color to all selected
            threadnames = [item.get('class') for item in selected if item.get('class')]
            colors = False
        else: # if no selection - apply random color to all threads
            threadnames = all_threadnames
            colors = zip(threadnames, [self.random_color() for n in threadnames])
        threads = self.find_ids_by_class(threadnames)
        links = self.find_ids_by_class(['link'])
        parent_node = self.find_parent(threads[0])
        # relink the links onto threads
        if links:
            newlinks = self.connect_links(threads, links)
            threads.extend(newlinks)
            if show_bobbin:
                bobbins = self.substitute_bobbin(links, parent_node)
                threads.extend(bobbins)
        elif not show_bobbin:
            for bobbin_id in self.find_ids_by_class(['bobbin'], tagtype=inkex.addNS('circle', 'svg')):
                bobbin_node = self.getElementById(bobbin_id)
                bobbin_node.getparent().remove( bobbin_node )
        inkex.debug("%s"%(len(threads)))
        style_changes = [('stroke',self.options.color), ('stroke-width',self.options.width*conversion)]
        self.change_style(threads, style_changes, colors)
 
        self.options.ids = ids # ! failed experiment to pass selection back

		
# Create effect instance and apply it.
if __name__ == '__main__':
    ThreadStyle().affect()

###
# User may select an original groundforge diagram or one that this tool has modified.
# - Make it work on both.
