#!/usr/bin/env python

# Copyright 2016, Ross A. Beyer (rbeyer@seti.org)
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


# The arguments to ISIS crop require a sample/line pair and then a set of offsets.  I typically
# have two sample/line pairs read from qview, and got tired of always bringing up the calculator
# to compute the offsets.
# Warning: very Ross-specific.


import os, sys, optparse

def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program performs map projection photrim and mosaicking.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def crop( fr, to, samp, line, nsamp, nline ):
    cmd = 'crop from= '+fr+' to= '+to+' samp= '+samp+' line= '+line+' nsamp= '+nsamp+' nline= '+nline
    print cmd
    os.system(cmd)

def calcoffset( first, second ):
    (first_samp, first_line) = first.split(':')
    (second_samp, second_line) = second.split(':')
    nsamp = int(second_samp) - int(first_samp)
    nline = int(second_line) - int(first_line)
    return( first_samp, first_line, str(nsamp), str(nline) )

def main():
    try:
        try:
            usage = "usage: cropsl.py [--help][--manual] [--output <filename>] --first <samp:line> --second <samp:line> <cube file>"
            parser = optparse.OptionParser(usage=usage)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")
            parser.add_option("-o", "--output", dest="output",
                              help="The output filename.")
            parser.add_option("-f", "--first", dest="first",
                              help="The sample and line of the first point.")
            parser.add_option("-s", "--second", dest="second",
                              help="The sample and line of the second point.")

            (options, args) = parser.parse_args()

            if not args: parser.error("need .cub file")

        except optparse.OptionError, msg:
            raise Usage(msg)

        for cub in args:
            if( options.output ): outfile = options.output
            else:
                base = os.path.basename( cub )
                (root, ext) = os.path.splitext(base)
                outfile = root+'.crop.cub'

            (samp, line, nsamp, nline) = calcoffset( options.first, options.second )

            crop( cub, outfile, samp, line, nsamp, nline )

            if( options.output): break


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
