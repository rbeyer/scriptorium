#!/usr/bin/env python

# Copyright 2013, Ross A. Beyer (rbeyer@seti.org)
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

import optparse, numpy, re, sys;

def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program parses standard input, mostly passing to standard
output, but looking for a coordinate string written by gdalinfo and
converting it from degress, minutes, seconds to decimal degrees.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def convert2dd(coord):
    pattern = re.compile(r"""(\d+)d\s*(\d+)'\s*(\d+.\d+)"([NSEW])""")
    match = pattern.search( coord )
    (degrees, minutes, seconds, cardinal) = match.groups()
    decimal = int(degrees)
    decimal += int(minutes)/60.0
    decimal += float(seconds)/3600.0
    if( cardinal is 'S' or cardinal is 'W' ): decimal *= -1
    return decimal

def parse_line( line, decimals, lon360 ):
    last_left_paren = line.rfind('(')
    last_right_paren = line.rfind(')')

    prefix = line[:last_left_paren]
    (lon,lat) = line[last_left_paren:last_right_paren].strip().split(', ')
    # print "test lon: "+ lon
    ddlon = convert2dd( lon )
    # print "test ddlon: "+ str(ddlon)
    # print "test lat: "+ lat
    ddlat = convert2dd( lat )
   
    format_str =  "{:."+str(decimals)+"f}"
    if( lon360 and ddlon < 0): ddlon += 360
    outline = prefix + '( ' + format_str.format(ddlon) +' E, '+ format_str.format(ddlat) + ' )'
    return outline

def main():
    try:
        try:
            usage = "usage: dms2dd.py [--help][--manual]"
            parser = optparse.OptionParser(usage=usage)
            parser.set_defaults(decimals=5)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")
            parser.add_option("--dms", "-d", dest="dms", action="store_true",
                              help="Output in degrees, minutes, seconds also.")
            parser.add_option("--format", "-f", dest="decimals", 
                              help="Number of digits past the decimal, default is 5.")
            parser.add_option("--lon360", "-l", dest="lon360", action="store_true", 
                              help="Change longitudes to 0 to 360 range, default is -180 to 180.")

            (options, args) = parser.parse_args()

        except optparse.OptionError, msg:
            raise Usage(msg)

        prefix_tuple = 'Upper Left  (','Lower Left  (','Upper Right (','Lower Right (','Center      ('

        for line in sys.stdin:
            if line.startswith( prefix_tuple ):
                if(options.dms): print line.strip()
                print parse_line( line.strip(), options.decimals, options.lon360 )
            else: print line.strip()
            
    except Usage, err:
        print >>sys.stderr, err.msg
        # print >>sys.stderr, "for help use --help"
        return 2
    

if __name__ == "__main__":
    sys.exit(main())
