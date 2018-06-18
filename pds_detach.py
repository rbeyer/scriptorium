#!/usr/bin/env python

# Copyright 2018, Ross A. Beyer (rbeyer@seti.org)
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

# This program is for dealing with .img files that come out of isis2pds and splitting them
# into detached labels for PDS3.

import os, sys, optparse
import pvl


def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program works with PDS images and labels.
'''
    sys.exit()

class UsageError(Exception):
    def __init__(self, msg):
        self.msg = msg

def main():
    parser = optparse.OptionParser(usage="usage %prog [--help] [-o outname][-i isis2pds commands][-e] <file.img|file.cub>")
    parser.add_option("-o","--output", dest="outname", help="output will be written to FILE.lbl and FILE.img", metavar="FILE")
    parser.add_option("-i","--isis2pds", dest="isis2pds", help="string of options to pass to pds2isis")
    parser.add_option("-e", "--edit", action="store_true", dest="edit", default=False,
                  help="The program will attempt to edit the labels.")
    

    (options, args) = parser.parse_args()

    if not args: parser.error("need an .img or .cub file")

    imgfilename = args[0]

    (root, ext) = os.path.splitext( imgfilename )

    if( ext == '.cub' ):
        # Run isis2pds
        imgfilename = 'isis2pds.img'
        cmd = 'isis2pds fr= '+args[0]+' to= '+imgfilename
        if options.isis2pds: cmd += ' '+options.isis2pds
        print( cmd )
        os.system(cmd)

    label = pvl.load( imgfilename )

    label_file = root+'-det.lbl'
    data_file  = root+'-det.img'

    if options.outname:
        label_file = options.outname+'.lbl'
        data_file = options.outname+'.img'
        if( os.path.exists(label_file) ):
            parser.error(label_file+' exists!')
        if( os.path.exists(data_file) ):
            parser.error(data_file+' exists!')

    with open( imgfilename, 'rb') as infile:
        with open( label_file, 'wb') as outfile:
            ## outfile.write( infile.read( label['LABEL_RECORDS'].value ) )
            # It sure would be nice to perform this manipulation with the pvl library,
            # but it parses input values instead of preserving the bytes, so we'll have
            # to do this the heavy-handed way:
            label_lines = infile.read( label['LABEL_RECORDS'].value ).split(b'\r\n')
            for line in label_lines:
                #print( line )
                if( label['RECORD_TYPE'] == 'UNDEFINED' and line.startswith( b'RECORD_TYPE' ) ):
                   outfile.write( line.replace(b'UNDEFINED',b'FIXED_LENGTH')+b'\r\n' )
                   i = line.find(b'=')
                   outfile.write( b'FILE_RECORDS'.ljust(i)+b'= '+str( 
                       label['IMAGE']['LINES'] ).encode('ascii') + b'\r\n' )
                   outfile.write( b'RECORD_BYTES'.ljust(i)+b'= '+ str(
                       int( (label['IMAGE']['SAMPLE_BITS'] / 8) * label['IMAGE']['LINE_SAMPLES'] )
                       ).encode('ascii') + b'\r\n' )
                elif( line.startswith( b'LABEL_RECORDS' ) ): continue
                elif( line.startswith( b'^IMAGE' ) ):
                    outfile.write( b'^IMAGE'.ljust(i)+b'= "'+os.path.basename(data_file).encode('ascii')+b'"\r\n' )
                elif( options.edit ):
                    if( label['IMAGE']['OFFSET'] != 0.0 and line.lstrip().startswith( b'OFFSET' ) ):
                        i = line.find(b'=')
                        outfile.write( b'OFFSET'.ljust(i)+b'= 0.0\r\n' )
                    elif( label['IMAGE']['SCALING_FACTOR'] != 1.0 and line.lstrip().startswith( b'SCALING_FACTOR' ) ):
                        i = line.find(b'=')
                        outfile.write( b'SCALING_FACTOR'.ljust(i)+b'= 1.0\r\n' )
                    elif( line.lstrip().startswith( b'CORE_NULL' ) ):
                        outfile.write( line.replace(b'CORE_NULL       ',b'MISSING_CONSTANT')+b'\r\n' )
                    elif( line.lstrip().startswith( b'CORE_LOW_REPR_SATURATION' ) ): continue
                    elif( line.lstrip().startswith( b'CORE_LOW_INSTR_SATURATION' ) ): continue
                    elif( line.lstrip().startswith( b'CORE_HIGH_REPR_SATURATION' ) ): continue
                    elif( line.lstrip().startswith( b'CORE_HIGH_INSTR_SATURATION' ) ): continue
                    else: outfile.write( line + b'\r\n' )

                else: outfile.write( line + b'\r\n' )

        with open( data_file, 'wb') as outfile:
            outfile.write( infile.read() )
   
    if( ext == '.cub' ): os.remove( imgfilename )


    #print( pvl.dumps( label ) )
    #print( str( pvl.dumps( label ), 'ascii') )

    # # label_file
    # outfile = 'label.lbl'
    # ascii_label = pvl.dumps(label)
    # with open( outfile, 'wb') as f:
    #     f.write(ascii_label)


if __name__ == "__main__":
    sys.exit(main())
