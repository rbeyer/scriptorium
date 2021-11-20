#!/usr/bin/env python
"""This program queries the PDS Geoscience Node's REST system to download laser
altimeter data."""

# Copyright 2017, 2021, Ross A. Beyer (rbeyer@seti.org)
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

# This program is for taking in a lon/lat bounding box, making a query
# to the PDS Geoscience Node's Granular Data System REST interface,
# and then pulling down the MOLA PEDR points or LOLA RDR points that
# are within the bounding box.

# Thanks to Scott McMichael for getting me started with some example
# code we wrote for LOLA.

import argparse
import os
import json
import subprocess
import sys
import urllib.request

from pathlib import Path
from urllib.parse import urlparse


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "-l", "--lola",
        action="store_true",
        help="Get LOLA data."
    )
    parser.add_argument(
        "-m", "--mola",
        action="store_true",
        help="Get MOLA data."
    )
    parser.add_argument(
        "boundingbox",
        help="A W/E/S/N string"
    )
    return parser


def retrieve_file(
    minlat, maxlat, minlon, maxlon, which, pad=0.1, output=None
):
    """Retrieves MOLA or LOLA data from the WUSTL REST web interface,
    http://oderest.rsl.wustl.edu/ ."""

    pminlat = float(minlat) - pad
    pmaxlat = float(maxlat) + pad
    pminlon = float(minlon) - pad
    pmaxlon = float(maxlon) + pad

    # Should be all positive East longitudes, so tidy up:
    if pminlon < 0:
        pminlon += 360
    if pmaxlon < 0:
        pmaxlon += 360

    # Build a query to the WUSTL REST interface for MOLA data
    baseurl = 'http://oderest.rsl.wustl.edu/livegds'
    if which is 'MOLA':
        query = '?output=JSON&query=molapedr&results=v&'
        filestring = '_topo_csv.csv'
    elif which is 'LOLA':
        # Simple topography per row (Lon, Lat, Topo (m above datum)
        # query = '?output=JSON&query=lolardr&results=u&'
        # filestring = '_topo_simple_csv.csv'

        # Topography per row
        query = '?output=JSON&query=lolardr&results=t&'
        filestring = '_topo_csv.csv'
    else:
        raise ValueError(f"Don't have a query for {which}")

    location_params = (
        f"""minlat={pminlat}&maxlat={pmaxlat}&westlon={pminlon}&eastlon={pmaxlon}"""
    )

    if output and os.path.exists(output):
        return True

    queryurl = baseurl + query + location_params
    # print queryUrl

    # Parse the response
    with urllib.request.urlopen(queryurl) as f:
        r = json.load(f)

    # print r

    if 'Success' not in r['GDSResults']['Status']:
        raise ValueError(r['GDSResults']['Error'])
    else:
        print(
            'PDS Geosciences REST: ' +
            r['GDSResults']['StateSummary']['StatusNote']
        )

    # Find the link containing '_topo_csv.csv' and download it

    found = False
    for d in r['GDSResults']['ResultFiles']['ResultFile']:
        if filestring in d['URL']:
            parsed = urlparse(d["URL"])
            urlpath = Path(parsed[2])
            lblpath = urlpath.with_suffix(".lbl")
            lblurlparts = list(parsed)
            lblurlparts[2] = str(lblpath)
            lblurl = urllib.parse.urlunparse(lblurlparts)

            urllib.request.urlretrieve(lblurl, lblpath.name)
            urllib.request.urlretrieve(d["URL"], urlpath.name)

            # cmd = 'wget '
            # if output:
            #     cmd += f'--output-document={outputPath}'
            # cmd += d['URL']
            # print(cmd)
            # os.system(cmd)
            return True

    return found


# def getkey( cube, grpname, keyword ):
#     # getkey grpname= ? keyword= ? from= ?
#     print 'Running getkey'
#     getkey_path = os.environ['ISISROOT']+'/bin/getkey'
#     result = subprocess.Popen([getkey_path, "from= "+ cube, "grpname= "+ grpname, "keyword= "+keyword], stdout=subprocess.PIPE).communicate()[0].strip()
#     return result


def main():
    parser = arg_parser()
    args = parser.parse_args()

    if not (args.mola or args.lola):
        parser.error("Must either specify -m or -l")

    # if len(args.boundingbox) == 1:
        # assume it is GDAL-readable:
        #   try:
        #       dataset = rasterio.open(args.boundingbox)
        #       bbox = dataset.bounds
        #   minLon = getkey( args[0], 'Mapping', 'MinimumLongitude' )
        #   maxLon = getkey( args[0], 'Mapping', 'MaximumLongitude' )
        #   minLat = getkey( args[0], 'Mapping', 'MinimumLatitude' )
        #   maxLat = getkey( args[0], 'Mapping', 'MaximumLatitude' )
    minlon, maxlon, minlat, maxlat = args.boundingbox.split("/")
    # else:
    #     parser.error(f"Couldn't get bounding box from {args.boundingbox}")

    if args.mola:
        retrieve_file(minlat, maxlat, minlon, maxlon, 'MOLA')
    elif args.lola:
        retrieve_file(minlat, maxlat, minlon, maxlon, 'LOLA')
    else:
        raise NotImplementedError("Shouldn't be able to get here.")


if __name__ == "__main__":
    sys.exit(main())
