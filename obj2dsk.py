#!/usr/bin/env python
'''Uses the SPICE mkdsk program to convert a .obj file to a .bds file.

Requires that the SPICE toolkit be installed on your system.  This
program will create a "cleaned" version of the .obj file (since a
.obj file can contain "more" than what the mkdsk program needs to
operate), it will create a mkdsksetup file that can be given to the
SPICE mkdsk program, and then it will run mkdsk for you.
'''

print("""This program is now maintained at the PlanetaryPy Scriptorium at
https://github.com/planetarypy/scriptorium
""")
