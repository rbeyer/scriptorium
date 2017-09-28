#!/usr/bin/env python

# Copyright 2017, Ross A. Beyer (rbeyer@seti.org)
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

# This program is for taking in a lon/lat bounding box, making a query to the PDS Geoscience
# Node's Granular Data System REST interface, and then pulling down the MOLA PEDR points or LOLA
# RDR points that are within the bounding box.
#
# Thanks to Scott McMichael for getting me started with some example code we wrote for LOLA.


import os, sys, optparse, subprocess, ConfigParser
import json
import urllib2


def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program queries the PDS Geoscience Node's REST system to download laser altimeter data.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

# Retrieves MOLA or LOLA data from the WUSTL REST web interface, http://oderest.rsl.wustl.edu/
def retrieveLAfile(minLat, maxLat, minLon, maxLon, whichLA, padAmount=0.1, output=None):

    pminlat = float(minLat)-padAmount
    pmaxlat = float(maxLat)+padAmount
    pminlon = float(minLon)-padAmount
    pmaxlon = float(maxLon)+padAmount

    # Should be all positive East longitudes, so tidy up:
    if( pminlon < 0): pminlon += 360
    if( pmaxlon < 0): pmaxlon += 360

    # Build a query to the WUSTL REST interface for MOLA data
    baseUrl = 'http://oderest.rsl.wustl.edu/livegds'
    if whichLA is 'MOLA': 
        query   = '?output=JSON&query=molapedr&results=v&'
        filestring = '_topo_csv.csv'
    elif whichLA is 'LOLA': 
        query   = '?output=JSON&query=lolardr&results=u&'
        filestring = '_topo_simple_csv.csv'
    else: raise ValueError("Don't have a query for "+whichLA)
    locationParams = ( 'minlat='  + str(pminlat) +
                      '&maxlat='  + str(pmaxlat) +
                      '&westlon=' + str(pminlon) +
                      '&eastlon=' + str(pmaxlon))

    if output and os.path.exists(output): return True

    queryUrl = baseUrl + query + locationParams
    #print queryUrl

    # Parse the response
    r = json.load(urllib2.urlopen(queryUrl))
    #print r
    if 'Success' not in r['GDSResults']['Status']:
        raise ValueError(r['GDSResults']['StateSummary']['StatusNote'])
    else: print 'PDS Geosciences REST: '+r['GDSResults']['StateSummary']['StatusNote']

    # Find the link containing '_topo_csv.csv' and download it

    found = False
    for d in r['GDSResults']['ResultFiles']['ResultFile']:
        if filestring in d['URL']:
            cmd = 'wget '
            if output: cmd += '--output-document='+ outputPath +' '
            cmd += d['URL']
            print cmd
            os.system( cmd )
            return True

    return found

def getkey( cube, grpname, keyword ):
    # getkey grpname= ? keyword= ? from= ?
    print 'Running getkey'
    getkey_path = os.environ['ISISROOT']+'/bin/getkey'
    result = subprocess.Popen([getkey_path, "from= "+ cube, "grpname= "+ grpname, "keyword= "+keyword], stdout=subprocess.PIPE).communicate()[0].strip()
    return result

def main():
    try:
        try:
            usage = "usage: getla.py [--help][--manual] <-m|-l> <W/E/S/N|isis.cub>"
            parser = optparse.OptionParser(usage=usage)
            parser.set_defaults(mola=False)
            parser.set_defaults(lola=False)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")
            parser.add_option("--lola", "-l", dest="lola", action="store_true",
                              help="Get LOLA data.")
            parser.add_option("--mola", "-m", dest="mola", action="store_true",
                              help="Get MOLA data.")

            (options, args) = parser.parse_args()

            if not (options.mola or options.lola): parser.error("Must either specify -m or -l")

            if not args: parser.error("need bounding box coordinates")

            if len(args) == 1:
                # assume it is an ISIS cub file and find its boundaries
                minLon = getkey( args[0], 'Mapping', 'MinimumLongitude' )
                maxLon = getkey( args[0], 'Mapping', 'MaximumLongitude' )
                minLat = getkey( args[0], 'Mapping', 'MinimumLatitude' )
                maxLat = getkey( args[0], 'Mapping', 'MaximumLatitude' )

            elif len(args) == 4:
                (minLon,maxLon,minLat,maxLat) = args
            else: parser.error("couldn't get bounding box from "+args)

        except optparse.OptionError, msg:
            raise Usage(msg)

        if( options.mola ):   retrieveLAfile(minLat, maxLat, minLon, maxLon, 'MOLA' )
        elif( options.lola ): retrieveLAfile(minLat, maxLat, minLon, maxLon, 'LOLA' )
        else: raise NotImplementedError("Don't know what kind of data to request.")

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
