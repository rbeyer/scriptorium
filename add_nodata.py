#!/usr/bin/env python
"""This program takes one GeoTIFF and one regular TIFF which is assumed to be
a mask (just pixels of 255 and 0), and for those pixels which are 0, converts
those pixels in the GeoTIFF to that GeoTIFF's nodata value.
"""

# Copyright 2023, Ross A. Beyer (rbeyer@seti.org)
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

import argparse
import sys

import numpy as np
from pathlib import Path
import rasterio


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "-m", "--mask",
        type=Path,
        help="Mask file, must be same size as main GeoTIFF."
    )
    parser.add_argument(
        "geotiff",
        type=Path,
        help="Input GeoTIFF with a nodata value."
    )
    parser.add_argument(
        "outtiff",
        type=Path,
        help="Output GeoTIFF."
    )

    return parser


def main():
    parser = arg_parser()
    args = parser.parse_args()

    dataset = rasterio.open(args.geotiff)
    mask = rasterio.open(args.mask)

    if dataset.width != mask.width or dataset.height != mask.height:
        raise ValueError(
            f"The GeoTIFF and the mask do not have the same dimensions."
        )

    band1 = dataset.read(1)
    maskband = mask.read(1)

    print(f"First band of input type: {band1.dtype}")  # float32
    print(f"First band of mask type: {maskband.dtype}")  # uint8
    # print(dataset.nodata.dtype)  # Python float

    print(f"Upper left pixel value of input: {band1[0, 0]}")
    print(f"Upper left pixel value of mask: {maskband[0, 0]}")

    print(maskband.min())
    print(maskband.max())

    masked = np.where(maskband == 0, dataset.nodata, band1)

    print(f"Input no-data value: {dataset.nodata}")
    # print(masked.dtype)
    print(f"Upper left pixel of output after masking: {masked[0, 0]}")

    with rasterio.Env():
        with rasterio.open(args.outtiff, 'w', **dataset.profile) as dst:
            dst.write(masked.astype(rasterio.float32), 1)


if __name__ == "__main__":
    sys.exit(main())
