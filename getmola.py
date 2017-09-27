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
# Node's Granular Data System REST interface, and then pulling down the MOLA PEDRs that are
# within the bounding box.
#
# Thanks to Scott McMichael for getting me started with some example code we wrote for LOLA.


import os, sys, optparse, subprocess, ConfigParser
import json
import urllib2


def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program queries the PDS Geoscience Node's REST system to download MOLA PEDR data.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

# Retrieves MOLA data from the WUSTL REST web interface, http://oderest.rsl.wustl.edu/
def retrieveMOLAfile(minLat, maxLat, minLon, maxLon, outputFolder=".", padAmount=0.25):

    pminlat = float(minLat)-padAmount
    pmaxlat = float(maxLat)+padAmount
    pminlon = float(minLon)-padAmount
    pmaxlon = float(maxLon)+padAmount

    # The MOLA is all positive East longitudes, so tidy up:
    if( pminlon < 0): pminlon += 360
    if( pmaxlon < 0): pmaxlon += 360

    # Build a query to the WUSTL REST interface for MOLA data
    baseUrl = 'http://oderest.rsl.wustl.edu/livegds'
    query   = '?output=JSON&query=molapedr&results=v&'
    locationParams = ( 'minlat='  + str(pminlat) +
                      '&maxlat='  + str(pmaxlat) +
                      '&westlon=' + str(pminlon) +
                      '&eastlon=' + str(pmaxlon))

    outputPath = os.path.join(outputFolder, 'molaPEDR.csv')
    if os.path.exists(outputPath):
        return True

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
        if '_topo_csv.csv' in d['URL']:
            cmd = "wget --output-document="+ outputPath +"  "+ d['URL']
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
            usage = "usage: getmola.py [--help][--manual] <W/E/S/N>"
            parser = optparse.OptionParser(usage=usage)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")

            (options, args) = parser.parse_args()

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

        retrieveMOLAfile(minLat, maxLat, minLon, maxLon)

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
