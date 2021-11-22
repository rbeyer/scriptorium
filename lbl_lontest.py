#!/usr/bin/env python
"""Reads a PDS3 INDEX or CUMINDEX, and helps determine what longitude system
it might be in."""

# Copyright 2021, Ross A. Beyer (rbeyer@rossbeyer.net)
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
import csv
import sys
from pathlib import Path

import pvl

from lbl2sql import get_columns


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Completely check the file instead of failing fast."
    )
    parser.add_argument(
        "-l", "--label",
        type=Path,
        help="PDS3 Label file.  If not given, this program will look in the "
             "directory with the index file, and see if it can find an "
             "appropriate .LBL file."
    )
    parser.add_argument(
        "index",
        type=Path,
        help="A PDS index.tab or a cumindex.tab file."
    )
    return parser


def main():
    args = arg_parser().parse_args()

    if args.label is None:
        for suffix in (".LBL", ".lbl"):
            p = args.index.with_suffix(".LBL")
            if p.exists():
                args.label = p
                break
        else:
            print(
                "Could not guess an appropriate LBL file, please "
                "use -l explicitly."
            )
            sys.exit(1)

    label = pvl.load(args.label)

    columns = get_columns(label)

    if "CENTER_LONGITUDE" not in columns:
        print("CENTER_LONGITUDE not in columns. Quitting.")
        return -1

    with open(args.index, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=columns)
        if args.all:
            lon360 = None
            lon180 = None
            for row in reader:
                lon = float(row["CENTER_LONGITUDE"])
                if lon > 180:
                    lon360 = row["CENTER_LONGITUDE"]
                elif lon < 0:
                    lon180 = row["CENTER_LONGITUDE"]

            if lon360 and lon180 is None:
                print("Found longitudes greater than 180. Probably Lon360.")
            elif lon180 and lon360 is None:
                print("Found longitudes less than 0. Probably Lon180.")
            elif lon180 is not None and lon360 is not None:
                print(
                    "Found longitudes less than 0 and greater than 180, "
                    "which is messed up."
                )
            else:
                print("All longitudes were between 0 and 180, weird.")

        else:
            for row in reader:
                lon = float(row["CENTER_LONGITUDE"])
                if lon > 180 or lon < 0:
                    print(f'Found CENTER_LONGITUDE of {row["CENTER_LONGITUDE"]}')
                    return 0


if __name__ == "__main__":
    sys.exit(main())
