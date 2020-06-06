#!/usr/bin/env python
'''You can easily read off two sample,line coordinates from qview, but ISIS
crop wants one sample,line and then offsets.  This just takes two coordinates,
does the math, and then calls crop.'''

# Copyright 2016, 2019, Ross A. Beyer (rbeyer@seti.org)
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


# The arguments to ISIS crop require a sample/line pair and then a set of offsets.
# I typically have two sample/line pairs read from qview, and got tired of always
# bringing up the calculator to compute the offsets.

import argparse
import subprocess
import sys
from pathlib import Path


def crop(fr, to, samp, line, nsamp, nline):
    cmd = ('crop', f'from= {fr}', f'to= {to}',
           f'samp= {samp}', f'line= {line}',
           f'nsamp= {nsamp}', f'nline= {nline}')
    return subprocess.run(cmd, check=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE,
                          universal_newlines=True)


def calcoffset(first, second):
    (f_samp, f_line) = first.split(':')
    (s_samp, s_line) = second.split(':')
    nsamp = int(s_samp) - int(f_samp)
    nline = int(s_line) - int(f_line)
    return(f_samp, f_line, str(nsamp), str(nline))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', help="The output filename.")
    parser.add_argument('-f', '--first',
                        help='The sample and line of the first point, '
                        'separated by a colon, like -f 3:10')
    parser.add_argument('-s', '--second',
                        help='The sample and line of the second point, '
                        'separated by a colon.')
    parser.add_argument('cube', help='Cube file(s) to crop.', nargs='+')

    args = parser.parse_args()

    for cub in args.cube:
        in_p = Path(cub)
        if(args.output):
            out_p = Path(args.output)
        else:
            out_p = in_p.with_suffix('.crop.cub')

        (samp, line, nsamp, nline) = calcoffset(args.first, args.second)

        print(crop(in_p, out_p, samp, line, nsamp, nline).args)

        if(args.output):
            # If there's a specific output filename, only do one.
            break


if __name__ == "__main__":
    sys.exit(main())
