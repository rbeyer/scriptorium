#!/usr/bin/env python
'''Cleans a .obj file, stripping out everything except v and f lines, and cleans the f lines to only contain vertex reference numbers so the file can be read by mkdsk.'''

# Copyright 2019, Ross A. Beyer (rbeyer@rossbeyer.net)
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

# Of course, if mkdsk would just read the .obj file format and
# ignore the stuff it doesn't need, this cleaning wouldn't be needed.

import argparse

def main():
    parser = argparse.ArgumentParser( description=__doc__ )
    parser.add_argument('file', help='.obj file' )

    args = parser.parse_args()

    with open(args.file, 'r') as f:
        for line in f:
            if line.startswith('v '):
                print( line, end='' )
            elif line.startswith('f'):
                tokens = line.split()
                out = 'f'
                for i in tokens[1:]:
                    v = i.split('/')[0]
                    out += ' '+v
                print( out )
        
if __name__ == "__main__":
    main()
