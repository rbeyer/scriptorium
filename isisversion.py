#!/usr/bin/env python

# Copyright 2013,2018, Ross A. Beyer (rbeyer@seti.org)
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

import os, optparse, re, sys, string;

def man(option, opt, value, parser):
    print >>sys.stderr, parser.usage
    print >>sys.stderr, '''\
This program returns the version number of ISIS.

If the optional version-number is given, the program will
determine whether the version given is greater than or less
than the found ISIS version.  This is mostly for debugging.
'''
    sys.exit()

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def isisversionparse( version ):
    alphaend = version.lstrip(string.digits+'.')
    #version_numbers = version.rstrip(string.ascii_letters);
    #version_strings = version_numbers.split('.')
    version_strings = version.split('.')
    version_list = []
    for item in version_strings:
        try: version_list.append( int(item) )
        except ValueError: version_list.append( item )
    if( alphaend ): version_list.append( alphaend )
    # for item in version_strings: version_list.append( int(item) )
    #     # Not sure if the code below which kind of deals with 
    #     #   funny number-string combos should be implemented.
    #     # try: version_list.append( int(item) )
    #     # except ValueError, msg:
    #     #     # # This will handle things like 21beta
    #     #     # matchobj = re.match(r"^(\d+)",item)
    #     #     # if( matchobj ):
    #     #     #     leading_number = matchobj.group(1)
    #     #     #     version_list.append( int(leading_number) )
    #     #     #     version_list.append( item[len(leading_number):] )
    #     #     # else: version_list.append( item )
    #     #     version_list.append( item )
    version_tuple = tuple( version_list )
    return version_tuple

def isisversion(verbose=False):
    path = '/usr/local/isis3/isis/' # default spot to try
    try:               path = os.environ['ISISROOT']
    except KeyError:   pass

    # if( verbose ): print path
    
    version = None
    if os.path.exists( path+'/version' ):
        v = open( path+"/version", 'r')
        #version = v.readline().strip()
        version = v.readline().split()[0]
        v.close()
    else:
        f = open(path+"/inc/Constants.h",'r');
        for line in f:
             if ( line.rfind("std::string version(") > 0 ):
                index = line.find("version(\"");
                index_e = line.rfind("|");
                version = line[index+9:index_e].rstrip()
                #version = version +'b'
        f.close()

    if( version ):
        if( verbose ): print("\tFound Isis Version: "+version+ " at "+path)
        return isisversionparse( version )

    raise Exception( "Could not find a version string in " + f.str() )
    return False
	

#----------------------------

def main():
    try:
        try:
            usage = "usage: isisversion.py [--help][--manual] [version_number]"
            parser = optparse.OptionParser(usage=usage)
            parser.add_option("--manual", action="callback", callback=man,
                              help="Read the manual.")

            (options, args) = parser.parse_args()

        except optparse.OptionError as error:
            raise Usage(error)

        version = isisversion( True )

        if( len(args) > 0 ):
            test_list = []
            
            # for item in args[0].split('.'): 
            #     try: test_list.append( int(item) )
            #     except ValueError, msg: 
            #         # # This will handle things like 21beta
            #         # matchobj = re.match(r"^(\d+)",item)
            #         # if( matchobj ):
            #         #     leading_number = matchobj.group(1)
            #         #     test_list.append( int(leading_number) )
            #         #     test_list.append( item[len(leading_number):] )
            #         # else: test_list.append( item )
            #         test_list.append( item )
            test_tuple = isisversionparse( args[0] )

            comp = ''
            if( test_tuple < version ):     comp = ' is less than '
            elif( test_tuple == version ):  comp = ' is equal to '
            elif( test_tuple > version):    comp = ' is greater than '
            else: comp = ' is not known in relation to '
                
            print( str(test_tuple) + comp + str(version) )
        

    except Usage as error:
        print( error, file=sys.stderr )
        # print >>sys.stderr, "for help use --help"
        return 2
    

if __name__ == "__main__":
    sys.exit(main())
