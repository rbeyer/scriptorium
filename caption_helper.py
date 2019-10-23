#!/usr/bin/env python
'''This program just reads some meta-data from the label of
an ISIS cube file and presents the text in a way that might help
someone get started on writing a figure caption.'''

# Copyright 2019, Ross A. Beyer (rbeyer@seti.org)
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

# This program was motivated by this Issue from Laszlo Kestay:
# https://github.com/USGS-Astrogeology/ISIS3/issues/1588
# He says:
# It is a royal pain to find all the data to put in the caption for
# a figure for a paper. It would be lovely if ISIS would make
# publication-ready figures. One part of this would be to pull the
# key data out of the labels and present the user with a simple pile
# of text that they can cut-paste (or put in a text file) for the
# caption. Would be good to be able to select what information you
# wanted in the caption too.
#
# Optional things to add: local time of day, season, type of SPICE used. If
# not map projected, give information on the viewing geometry.
#
# You will need to install the pvl library at the very least, and can install
# the kalasiris library (and ISIS) to get some additional information.

import argparse
import datetime
import math
import os
import subprocess
import sys

import pvl


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cube', help='Cube file(s) to read.')

    args = parser.parse_args()

    # Gather data elements into elem:
    elem = dict()
    label = pvl.load(args.cube)['IsisCube']

    elem.update(get_instrument(label.get('Instrument')))

    elem['productid'] = None
    if label.get('Archive') is not None:
        elem['productid'] = label['Archive'].get('ProductId')

    elem.update(get_mapping(label.get('Mapping')))

    elem.update(get_campt(args.cube))

    # Print out results.
    for k in elem.keys():
        print('{}: {}'.format(k, elem.get(k)))
    print('')
    print(' '.join(get_sentences(elem)))

    return


def get_instrument(label: dict) -> dict:
    d = dict(scname=None, instrument=None, time=None)

    if label is None:
        return d

    d['scname'] = label.get('SpacecraftName')
    d['instrument'] = label.get('InstrumentId')
    t = label.get('StartTime')
    if t is not None:
        if isinstance(t, datetime.datetime):
            d['time'] = str(t)
        else:
            d['time'] = str(t[0])
    return d


def get_mapping(label: dict) -> dict:
    d = dict(pixelres=None, projection=None)

    if label is None:
        return d

    pr = label.get('PixelResolution')
    if pr is not None:
        d['pixelres'] = '{} {}'.format(*pr)

    d['projection'] = label.get('ProjectionName')

    return d


def get_campt(path: os.PathLike) -> dict:
    d = dict(northaz=None, subsolargroundaz=None, abovehoriz=None)

    try:
        import kalasiris as isis
        cpvl = pvl.loads(isis.campt(path).stdout)['GroundPoint']

        d['northaz'] = cpvl.get('NorthAzimuth')
        d['subsolargroundaz'] = cpvl.get('SubSolarGroundAzimuth')

        incid = cpvl.get('Incidence')
        if incid is not None:
            d['abovehoriz'] = pvl.Units(str(90 - float(incid[0])), incid[1])

    except subprocess.CalledProcessError:
        # Couln't get any data from campt, maybe it was a level 2 image?
        pass
    except ModuleNotFoundError:
        # To get some additional functionality,
        # install the kalasiris library.
        pass

    return d


def inst_sentence(scname=None, instrument=None, time=None, productid=None) -> str:
    if all(x is None for x in (scname, instrument, time, productid)):
        raise ValueError('All passed elements were None, '
                         'at least one of them should have a string.')

    sent = 'This image contains data acquried'
    if scname is not None or instrument is not None:
        sent += ' by'
        if instrument is not None:
            sent += f' {instrument}'
            if scname is not None:
                sent += f' onboard {scname}'
        else:
            sent += f' {scname}'
    if time is not None:
        sent += f' on {time}'
    if productid is not None:
        sent += f' with the Product ID, {productid}'
    sent += '.'

    return sent


def mapping_sentence(projection=None, pixelres=None) -> str:
    if all(x is None for x in (projection, pixelres)):
        raise ValueError('All passed elements were None, '
                         'at least one of them should have a string.')
    sent = 'The image'
    prep = 'has'
    if projection is not None:
        sent += f' is a {projection} projection'
        prep = 'with'
    if pixelres is not None:
        sent += f' {prep} a ground sample distance of {pixelres}'
    sent += '.'

    return sent


def f_pair(pair: list) -> tuple:
    units = pair[1]

    if units.casefold().startswith('degree'):
        units = 'degrees'

    return (float(pair[0]), units)


def campt_sentence(northaz=None, subsolargroundaz=None, abovehoriz=None) -> str:
    # Assumes the arguments are either None or pvl.Units objects.
    if all(x is None for x in (northaz, subsolargroundaz, abovehoriz)):
        raise ValueError('All passed elements were None, '
                         'at least one of them should have a string.')

    sents = list()
    if northaz is not None:
        s = 'North'
        if math.floor(float(northaz[0])) == 270:
            s += ' is up.'
        else:
            units = northaz[1]
            if units.casefold().startswith('degree'):
                units = 'degrees'
            s += ' azimuth is {:.2f} {} from the +x direction.'.format(*f_pair(northaz))
        sents.append(s)

    if subsolargroundaz is not None or abovehoriz is not None:
        s = 'The Sun is'
        if abovehoriz is not None:
            s += ' {:.2f} {} above the horizon'.format(*f_pair(abovehoriz))
        if subsolargroundaz is not None:
            s += ' at an azimuth of {:.2f} {} from North'.format(*f_pair(subsolargroundaz))
        s += '.'
        sents.append(s)

    return ' '.join(sents)


def get_sentences(elem: dict) -> list:
    s = list()
    try:
        s.append(inst_sentence(elem.get('scname'),
                               elem.get('instrument'),
                               elem.get('time'),
                               elem.get('productid')))
    except ValueError:
        pass

    try:
        s.append(mapping_sentence(elem.get('projection'),
                                  elem.get('pixelres')))
    except ValueError:
        pass

    try:
        s.append(campt_sentence(elem.get('northaz'),
                                elem.get('subsolargroundaz'),
                                elem.get('abovehoriz')))
    except ValueError:
        pass

    return s


if __name__ == "__main__":
    sys.exit(main())
