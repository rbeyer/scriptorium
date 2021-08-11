#!/usr/bin/env python
'''Uses the SPICE mkdsk program to convert a .obj file to a .bds file.'''

# Copyright 2019-2021, Ross A. Beyer (rbeyer@rossbeyer.net)
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

# Changing 'spice_path' and the argument defaults for your setup will
# make you much happier.  These are set for my MU69 setup.

import argparse
import subprocess
from pathlib import Path


def main():
    spice_path = Path('/Users/rbeyer/projects/new_horizons/kem_science_spice')

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output',  required=False, default='.bds')
    parser.add_argument('-s', '--surface', required=False, default='2486958')
    parser.add_argument('-c', '--center',  required=False, default='2486958')
    parser.add_argument('-f', '--frame',   required=False, default='MU69_FIXED')
    parser.add_argument('-l', '--lsk',     required=False,
                        default=spice_path / 'lsk' / 'naif0012.tls')
    parser.add_argument('--kernels',       required=False,
                        default=spice_path / 'ggi' / 'nh_mu69.tpc')
    parser.add_argument('-k', '--keep', required=False, default=False)
    parser.add_argument('file', help='.obj file')

    args = parser.parse_args()

    in_obj = Path(args.file)

    out_dsk = None
    if args.output.startswith('.'):
        out_dsk = in_obj.with_suffix(args.output)
    else:
        out_dsk = Path(args.output)

    # Step 1: clean the object file:
    cleaned_obj = in_obj.with_suffix('.obj2dsk.cleaned.obj')
    with open(in_obj, 'r') as f:
        with open(cleaned_obj, 'w') as clean:
            for line in f:
                if line.startswith('v '):
                    clean.write(line)
                elif line.startswith('f'):
                    tokens = line.split()
                    out = 'f'
                    for i in tokens[1:]:
                        v = i.split('/')[0]
                        out += ' ' + v
                    clean.write(out + '\n')

    # Step 2: make the setup file:
    setup_file = in_obj.with_suffix('.obj2dsk.mkdsksetup')
    with open(setup_file, 'w') as s:
        s.write(get_setup(args.surface, args.center, args.frame,
                          args.lsk, args.kernels))

    # Step 3: Run mkdsk:
    subprocess.run(['mkdsk',
                    '-setup', str(setup_file),
                    '-input', str(cleaned_obj),
                    '-output', str(out_dsk)],
                   check=True)

    # Step 4: cleanup
    if not args.keep:
        cleaned_obj.unlink()
        setup_file.unlink()


def get_setup(surfname, centername, refframe, lsk, kernels):
    # LEAPSECONDS_FILE    = '/Users/rbeyer/projects/new_horizons/kem_science_spice/lsk/naif0012.tls'
    # SURFACE_NAME        = '2486958'
    # CENTER_NAME         = '2486958'
    # REF_FRAME_NAME      = 'MU69_FIXED'
    # KERNELS_TO_LOAD = ('/Users/rbeyer/projects/new_horizons/kem_science_spice/ggi/MU69-Ultima.tpc' )

    return (f'''\
\\begindata

COMMENT_FILE        = ' '
SURFACE_NAME        = '{surfname}'
CENTER_NAME         = '{centername}'
REF_FRAME_NAME      = '{refframe}'
START_TIME          = '1950-JAN-1/00:00:00'
STOP_TIME           = '2050-JAN-1/00:00:00'
DATA_CLASS          = 2
INPUT_DATA_UNITS    = ( 'ANGLES    = DEGREES'
                        'DISTANCES = KILOMETERS' )
COORDINATE_SYSTEM   = 'LATITUDINAL'
MINIMUM_LATITUDE    = -90
MAXIMUM_LATITUDE    =  90
MINIMUM_LONGITUDE   = -180
MAXIMUM_LONGITUDE   =  180
DATA_TYPE           = 2
PLATE_TYPE          = 3
FINE_VOXEL_SCALE    = 4.0
COARSE_VOXEL_SCALE  = 5

LEAPSECONDS_FILE    = '{lsk}'
KERNELS_TO_LOAD = ('{kernels}' )
''')


if __name__ == "__main__":
    main()
