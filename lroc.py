#!/usr/bin/env python
"""A module with some very basic LROC Product ID functionality."""

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

import re

lroc_targets = dict(M="Moon", E="Earth", C="Calibration", S="Star")
lroc_inst = dict(
    R="Right NAC",
    L="Left NAC",
    M="Monochrome WAC",
    C="Color WAC",
    U="UV only WAC",
    V="Visible only WAC"
)
lroc_prod = dict(E="EDR", C="CDR")

# Create some compiled regex Patterns to use in this module.
target_re = re.compile("|".join(lroc_targets.keys()))
met_re = re.compile(r"\d{9}\d*")
inst_re = re.compile("|".join(lroc_inst.keys()))
prod_re = re.compile("|".join(lroc_prod.keys()))

obsid_re = re.compile(
    fr"(?P<target>{target_re.pattern})"
    fr"(?P<met>{met_re.pattern})"
    fr"(?P<instrument>{inst_re.pattern})"
    fr"(?P<product>{prod_re.pattern})"

)


class LROCID:
    """A Class for LROC Observation IDs.

    :ivar target: A single character denoting the observation target,
        (M)oon, (E)arth, (C)alibration or (S)tar.
    :ivar met: an integer reflecting the MET of acquisition
    :ivar instrument: A single character denoting the instrument,
        (R)ight NAC, (L)eft NAC, (M)onochrome WAC, (C)olor WAC,
        (U)V only WAC, or (V)isible only WAC.
    "ivar product: A single character denoting an (E)DR product or
        (C)DR product.
    """

    def __init__(self, arg):

        match = obsid_re.search(str(arg))
        if match:
            parsed = match.groupdict()
            self.target = parsed["target"]
            self.met = int(parsed["met"])
            self.instrument = parsed["instrument"]
            self.product = parsed["product"]
        else:
            raise ValueError(
                f"{arg} did not match regex: {obsid_re.pattern}"
            )

    def __str__(self):
        return f"{self.target}{str(self.met)}{self.instrument}{self.product}"

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.__str__()}')"

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.target == other.target
                and self.met == other.met
                and self.instrument == other.instrument
                and self.product == other.product
            )
        return False

    def __lt__(self, other):
        if isinstance(other, self.__class__):
            return (
                self.target,
                self.met,
                self.instrument,
                self.product
            ) < (
                other.target,
                other.met,
                other.instrument,
                other.product
            )
        else:
            return NotImplemented

    def observation(self):
        return f"{self.target}{str(self.met)}"
