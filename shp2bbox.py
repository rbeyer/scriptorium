#!/usr/bin/env python

# Copyright 2017, Ross A. Beyer (rbeyer@seti.org)
# The functions orientation(), hulls(), rotatingCalipers(), and diameter()
#    are Copyright 2002, David Eppstein, under a Python Software License.
# The function haversine() is derived from algorithms which
#   are Copyright 2002-2017, Chris Veness, under an MIT license
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# The copyright status of the orientation, hulls, rotatingCalipers, and diameter 
# functions by David Eppstein are uncertain.  The margin of the webpage referenced 
# indicates that the code may be under a Python Software License, and this work assumes
# that is their copyright status.  The Python Software License is compatible with the
# Apache 2 License, and can be found at 
# https://opensource.org/licenses/PythonSoftFoundation.php

# This program is for reading a Shapefile, exracting feature information,
# and computing centroid and bounding box and some other characteristics for each feature.


import os, sys, optparse, ConfigParser, math
from osgeo import ogr, osr
from geopy import distance


def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program extracts shapes and their boundaries from a Shapefile.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

# The next four functions (orientation, hulls, rotatingCalipers, and diameter) are
# from David Eppstein at https://code.activestate.com/recipes/117225/ with a minor change
# to diameter to also return the 'diam' parameter (which is the diameter squared).
#
# convex hull (Graham scan by x-coordinate) and diameter of a set of points
# David Eppstein, UC Irvine, 7 Mar 2002

#from __future__ import generators

def orientation(p,q,r):
    '''Return positive if p-q-r are clockwise, neg if ccw, zero if colinear.'''
    return (q[1]-p[1])*(r[0]-p[0]) - (q[0]-p[0])*(r[1]-p[1])

def hulls(Points):
    '''Graham scan to find upper and lower convex hulls of a set of 2d points.'''
    U = []
    L = []
    Points.sort()
    for p in Points:
        while len(U) > 1 and orientation(U[-2],U[-1],p) <= 0: U.pop()
        while len(L) > 1 and orientation(L[-2],L[-1],p) >= 0: L.pop()
        U.append(p)
        L.append(p)
    return U,L

def rotatingCalipers(Points):
    '''Given a list of 2d points, finds all ways of sandwiching the points
between two parallel lines that touch one point each, and yields the sequence
of pairs of points touched by each pair of lines.'''
    U,L = hulls(Points)
    i = 0
    j = len(L) - 1
    while i < len(U) - 1 or j > 0:
        yield U[i],L[j]
        
        # if all the way through one side of hull, advance the other side
        if i == len(U) - 1: j -= 1
        elif j == 0: i += 1
        
        # still points left on both lists, compare slopes of next hull edges
        # being careful to avoid divide-by-zero in slope calculation
        elif (U[i+1][1]-U[i][1])*(L[j][0]-L[j-1][0]) > \
                (L[j][1]-L[j-1][1])*(U[i+1][0]-U[i][0]):
            i += 1
        else: j -= 1

def diameter(Points):
    '''Given a list of 2d points, returns the pair that's farthest apart.'''
    diam,pair = max([((p[0]-q[0])**2 + (p[1]-q[1])**2, (p,q))
                     for p,q in rotatingCalipers(Points)])
    return diam, pair

def haversine( lon1, lat1, lon2, lat2, radius):
    # The material from which this haversine() function was created is
    # Copyright 2002-2017 by Chris Veness under an MIT license, and is 
    # available on his website at: http://www.movable-type.co.uk/scripts/latlong.html
    phi1 = math.radians( float(lat1) )
    phi2 = math.radians( float(lat2) )
    dlat = math.radians( float(lat2) - float(lat1) )
    dlon = math.radians( float(lon2) - float(lon1) )

    a = math.pow( math.sin(dlat/2),2 ) + ( math.cos( phi1 ) * math.cos( phi2 ) * math.pow( math.sin(dlon/2), 2 ) )
    c = 2 * math.atan2( math.sqrt(a), math.sqrt(1-a) )
    distance = radius * c
    return distance



def format_coord( coord, decimals, lon360 ):
    lon = coord[0]
    lat = coord[1]

    format_str =  "{:."+str(decimals)+"f}"

    if( lon360 and lon < 0): lon += 360
    #outline = format_str.format(lon) +' E, '+ format_str.format(lat)
    formatted = (format_str.format(lon) +' E', format_str.format(lat))
    return formatted

def main():
    try:
        try:
            usage = "usage: shp2bbox.py [--help][--manual][--format <n>][--lon360] <Shapefile(s)>"
            parser = optparse.OptionParser(usage=usage)
            parser.set_defaults(decimals=2)
            parser.set_defaults(lon360=0)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")
            parser.add_option("--format", "-f", dest="decimals", 
                              help="Number of digits past the decimal, default is 2.")
            parser.add_option("--lon360", "-l", dest="lon360", action="store_true", 
                              help="Change longitudes to 0 to 360 range, default is -180 to 180.")
            parser.add_option("--proposal", "-p", dest="listing", action="store_true", 
                              help="List parameters out atomically.")

            (options, args) = parser.parse_args()

            if not args: parser.error("need Shapefile file")

            for filename in args:
                if not os.path.exists( filename ): parser.error( filename+" is not a file.")

        except optparse.OptionError, msg:
            raise Usage(msg)

        for shp in args:
            driver = ogr.GetDriverByName("ESRI Shapefile")
            try: 
                dataSource = driver.Open(shp, 0)
            except optparse.OptionError, msg:
                raise Usage(msg)
            layer = dataSource.GetLayer()

            for feature in layer:
                try: 
                    name = feature.GetField("Name")
                    desc = feature.GetField("Descriptor")
                except ValueError:
                    name = 'Feature'
                    for i in range(layer.GetLayerDefn().GetFieldCount()):
                        name += ' '+str( feature.GetField(i) )
                    desc = ''
                geom = feature.GetGeometryRef()
                spatialRef = geom.GetSpatialReference()

                longlat_srs = osr.SpatialReference()
                longlat_srs.ImportFromProj4('+proj=longlat')
                ct = osr.CoordinateTransformation(spatialRef, longlat_srs)

                # This may be problematic for concave shapes.  Trent recommends using a geodesic centroid,
                # for now, we'll just do it like this.  Trent says:
                # See Jenness: http://www.jennessent.com/downloads/Graphics_Shapes_Online.pdf
                # although this post has some concerns on how Jenness does it:
                # https://gis.stackexchange.com/questions/43505/calculating-a-spherical-polygon-centroid

                centroid_lon_lat = ct.TransformPoint( geom.Centroid().GetX(), geom.Centroid().GetY() )

                envelope = geom.GetEnvelope()
                bbox_lon_lat_min = ct.TransformPoint( envelope[0], envelope[2] )
                bbox_lon_lat_max = ct.TransformPoint( envelope[1], envelope[3] )

                print name+' '+desc+': '
                #print geom.Centroid()
                centroid = format_coord( centroid_lon_lat, options.decimals, options.lon360 )
                min_point = format_coord( bbox_lon_lat_min, options.decimals, options.lon360 )
                max_point = format_coord( bbox_lon_lat_max, options.decimals, options.lon360 )
                if options.listing:
                    print 'Center latitude: '+centroid[1]
                    print 'Center longitude: '+centroid[0]
                    print 'Northernmost latitude: '+ max_point[1]
                    print 'Southernmost latitude: '+ min_point[1]
                    print 'Westernmost longitude: '+ min_point[0]
                    print 'Easternmost longitude: '+ max_point[0]
                else:
                    print '        Centroid: '+centroid[0]+', '+centroid[1]
                    #print envelope
                    print '    Bounding box: '+min_point[0]+', '+min_point[1]+' and '+max_point[0]+', '+max_point[1]

                format_str =  "{:."+str(options.decimals)+"f}"

                # We are going to transform the geometry to a projection centered at the 
                # centroid, so that we can more accurately compute the area and longest dimension:
                xform_srs = osr.SpatialReference()
                xform_srs.ImportFromProj4('+proj=ortho +lat_0='+str(centroid_lon_lat[1])+' +lon_0='+str(centroid_lon_lat[0])+' +a='+str(spatialRef.GetSemiMajor())+' +b='+str(spatialRef.GetSemiMinor()))
                #xform_srs.ImportFromProj4('+proj=sinu +lat_0='+str(centroid_lon_lat[1])+' +lon_0='+str(centroid_lon_lat[0])+' +a='+str(spatialRef.GetSemiMajor())+' +b='+str(spatialRef.GetSemiMinor()))
                xform = osr.CoordinateTransformation(spatialRef, xform_srs)

                geom.Transform(xform)

                if options.listing:
                    print 'Area: '+format_str.format( geom.GetArea()/1000000 )+' km2'
                else:
                    print '            Area: '+format_str.format( geom.GetArea()/1000000 )+' km^2'

                ring = geom.GetGeometryRef(0)
                pairs = []
                for p in range( ring.GetPointCount() ):
                    x, y, z = ring.GetPoint(p)
                    pairs.append( [x, y] )

                diam, pair = diameter( pairs )
                print 'Orthographic dist: '+format_str.format( (math.sqrt(diam))/1000 )+' km'

                xtoll = osr.CoordinateTransformation(xform_srs, longlat_srs)

                #geom.Transform( xtoll )
                #geom.Transform( ct )
                #llring = geom.GetGeometryRef(0)
                #llpairs = []
                #for p in range( llring.GetPointCount() ):
                #    x, y, z = llring.GetPoint(p)
                #    llpairs.append( [x, y] )

                #lldiam, llpair = diameter( llpairs )

                llpoint1 =  xtoll.TransformPoint( pair[0][0], pair[0][1] )
                llpoint2 =  xtoll.TransformPoint( pair[1][0], pair[1][1] )

                haverdist = haversine( llpoint1[0], llpoint1[1], llpoint2[0], llpoint2[1], spatialRef.GetSemiMajor() )
                print 'Haversine dist: '+format_str.format( haverdist/1000 )+' km'

                print 'Vincenty dist: '+str(distance.vincenty( llpoint1, llpoint2, ellipsoid=(spatialRef.GetSemiMajor()/1000, spatialRef.GetSemiMinor()/1000,spatialRef.GetInvFlattening()) ) )
                #print 'Vincenty dist: '+format_str.format( distance.vincenty( llpair[0], llpair[1], ellipsoid=(spatialRef.GetSemiMajor(), spatialRef.GetSemiMinor(),spatialRef.GetInvFlattening()) )/1000 )+' km'
                print llpoint1 
                print llpoint2
           
                ## # Brute force to find the longest span:
                ## geom.Transform(ct)

                ## ring = geom.GetGeometryRef(0)
                ## pairs = []
                ## for p in range( ring.GetPointCount() ):
                ##     x, y, z = ring.GetPoint(p)
                ##     pairs.append( [x, y] )

                ## max_vincenty = 0
                ## pair_vincenty = []
                ## max_haver = 0
                ## pair_vincenty = []
                ## for p in pairs:
                ##     for q in pairs:
                ##         l_vincenty = distance.vincenty( p, q, ellipsoid=(spatialRef.GetSemiMajor()/1000, spatialRef.GetSemiMinor()/1000,spatialRef.GetInvFlattening()) ).km
                ##         if l_vincenty > max_vincenty:
                ##             max_vincenty = l_vincenty
                ##             pair_vincenty = (p,q)
                ##         l_haver = haversine( p[0], p[1], q[0], q[1], spatialRef.GetSemiMajor() )/1000
                ##         if l_haver> max_haver:
                ##             max_haver= l_haver
                ##             pair_haver = (p,q)
                ## print 'Max Haversine: '+str(max_haver)
                ## print pair_haver
                ## print 'Max Vincenty: '+str(max_vincenty)
                ## print pair_vincenty


    except Usage, err:
        print >>sys.stderr, err.msg
        # print >>sys.stderr, "for help use --help"
        return 2

    # # To more easily debug this program, comment out this catch block.
    # except Exception, err:
    #     sys.stderr.write( str(err) + '\n' )
    #     return 1

if __name__ == "__main__":
    sys.exit(main())
