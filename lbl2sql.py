#!/usr/bin/env python
"""Reads a PDS3 INDEX or CUMINDEX, and creates an appropriate table or
just inserts."""

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
from shapely import wkt
from sqlalchemy import (
    Table, Column, Float, Integer, String, MetaData, create_engine,
)
from sqlalchemy import insert as sql_insert
from sqlalchemy_utils import database_exists
from geoalchemy2 import Geometry, Geography

corner_keys = ("upper_left", "upper_right", "lower_right", "lower_left")
geotypes = {"Geometry": Geometry, "Geography": Geography}
geotype_default = "Geography"


def arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__,
    )
    parser.add_argument(
        "-a", "--above_lat",
        type=float,
        default=-90,
        help="The value of the latitude of the center of a record "
             "must be greater than or equal to be written to the "
             "database. Default: %(default)s"
    )
    parser.add_argument(
        "-b", "--below_lat",
        type=float,
        default=90,
        help="The value of the latitude of the center of a record "
             "must be less than or equal to be written to the "
             "database. Default: %(default)s"
    )
    parser.add_argument(
        "-e", "--easternmost",
        type=float,
        default=360,
        help="The value of the longitude of the center of a record "
             "must be less than or equal to be written to the "
             "database. Default: %(default)s"
    )
    parser.add_argument(
        "-w", "--westernmost",
        type=float,
        default=-360,
        help="The value of the longitude of the center of a record "
             "must be greater than or equal to be written to the "
             "database. Default: %(default)s"
    )
    parser.add_argument(
        "-c", "--colfile",
        type=Path,
        help="File with one column name per line.  Only those columns will "
             "be ingested. Default is to ingest all columns."
    )
    parser.add_argument(
        "-d", "--dburl",
        default="postgresql://postgres:NotTheDefault@localhost/mydatabase",
        help="Default: %(default)s"
    )
    parser.add_argument(
        "-g", "--get_columns",
        action="store_true",
        help="Will just list the column names found in the label file and "
             "exit. If the output is piped to a file, this file can be "
             "edited and then used for --colfile."
    )
    parser.add_argument(
        "-l", "--label",
        type=Path,
        help="PDS3 Label file.  If not given, this program will look in the "
             "directory with the index file, and see if it can find an "
             "appropriate .LBL file."
    )
    parser.add_argument(
        "-p", "--product",
        help="The product ID of a single product to insert into the database. "
             "If given, assume the db and table already exist, and ignore "
             "-a, -b, -w, -e, and -c options."
    )
    parser.add_argument(
        "-s", "--srid",
        type=int,
        # default=-1,
        default=930100,
        help="SRID to use to insert geometries into the database. "
             "Default: %(default)s"
    )
    parser.add_argument(
        "--table",
        help="Name of the table in the database to create or insert into.  "
             "If not specified, program will try and determine it from the "
             "label."
    )
    parser.add_argument(
        "-t", "--type",
        choices=geotypes.keys(),
        default=geotype_default,
        help="The GIS type that points and polygons will be inserted into the "
             "database as. Default: %(default)s"
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

    if args.get_columns:
        print("\n".join(get_columns(label)))
        return

    if not database_exists(args.dburl):
        print(
            f"""\
            The database ({args.dburl}) does not exist.  Create it, and
            enable postgis: CREATE EXTENSION postgis;
            You will also need to set an appropriate SRID in the new
            database's spatial_ref_sys column.  Here's an example for
            a longlat SRID for the Moon:
            INSERT into spatial_ref_sys (srid, auth_name, auth_srid, proj4text, srtext) values ( 930100, 'iau2000', 30100, '+proj=longlat +a=1737400 +b=1737400 +no_defs ', 'GEOGCS["Moon 2000",DATUM["D_Moon_2000",SPHEROID["Moon_2000_IAU_IAG",1737400.0,0.0]],PRIMEM["Greenwich",0],UNIT["Decimal_Degree",0.0174532925199433]]');
            Then make sure to use 930100 for --srid when you run this program
            again.
            """)
        return 1

    engine = create_engine(args.dburl)
    metadata = MetaData()

    if args.colfile:
        columns = args.colfile.read_text().splitlines()
    else:
        columns = get_columns(label)

    if args.table is None:
        table_name = label["INDEX_TABLE"]["NAME"]
    else:
        table_name = args.table

    if args.product is not None:
        metadata.reflect(bind=engine)
        dbtable = metadata.tables[table_name]
        p = get_product(args.product, label["INDEX_TABLE"], args.index)
        insert_one(
            engine.connect(),
            dbtable,
            p,
            geotype=geotypes[args.type],
            srid=args.srid
        )

    else:

        table, geom_cols = create_table(
            label,
            metadata,
            columns,
            table_name,
            geotype=geotypes[args.type],
            srid=args.srid,
        )
        # for c in table.c:
        #     print(c.key)

        table.create(engine)

        volume, orbit, lastdate = insert(
            engine.connect(),
            table,
            columns,
            geom_cols,
            args.index,
            pvl_table=label["INDEX_TABLE"],
            lower_lat=args.above_lat,
            upper_lat=args.below_lat,
            eastern=args.easternmost,
            western=args.westernmost,
            srid=args.srid
        )

        print("This is the provenance of the CUMINDEX file:")
        print(f"As of PDS Volume {volume}, orbit {orbit}, {lastdate}.")

    return


def get_columns(label: dict, table_name=None, pvl_table="INDEX_TABLE"):
    if table_name is None:
        table_name = label[pvl_table]["NAME"]

    c_list = list()
    for c in label[pvl_table].getall("COLUMN"):
        c_list.append(c["NAME"])
    return c_list


def create_table(
    label: dict,
    metadata,
    columns,
    table_name,
    geotype=Geometry,
    srid=-1,  # Default for geoalchemy, I think.
    pvl_table="INDEX_TABLE"
):
    column_type = {"A": String, "I": Integer, "F": Float, "E": Float}

    possible_lons = dict()
    possible_lats = dict()

    t = Table(table_name, metadata)
    for c in label[pvl_table].getall("COLUMN"):
        if c["NAME"] in columns:
            if c["NAME"].casefold() == "PRODUCT_ID":
                t.append_column(
                    Column(c["NAME"], column_type[c["FORMAT"][0]]),
                    primary_key=True
                )
            else:
                t.append_column(Column(c["NAME"], column_type[c["FORMAT"][0]]))

            if c["NAME"].casefold().endswith("longitude"):
                possible_lons[geo_root(c["NAME"])] = c["NAME"]

            if c["NAME"].casefold().endswith("latitude"):
                possible_lats[geo_root(c["NAME"])] = c["NAME"]

    gc, cols = geom_cols(possible_lons, possible_lats, geotype, srid)
    for c in cols:
        t.append_column(c)

    return t, gc


def geo_root(name: str):
    return name.casefold().rsplit("_", maxsplit=1)[0]


def geom_cols(possible_lons, possible_lats, geotype, srid):

    cols = list()
    gc = dict()
    # See if there's an overall footprint to extract:
    if (
        set(corner_keys) <= set(possible_lons.keys()) and
        set(corner_keys) <= set(possible_lats.keys())
    ):
        n = "footprint_geo"
        cols.append(Column(n, geotype("POLYGON", srid=srid)))
        gc[n] = (
            (possible_lons[corner_keys[0]], possible_lats[corner_keys[0]]),
            (possible_lons[corner_keys[1]], possible_lats[corner_keys[1]]),
            (possible_lons[corner_keys[2]], possible_lats[corner_keys[2]]),
            (possible_lons[corner_keys[3]], possible_lats[corner_keys[3]]),
        )
        for k in corner_keys:
            del possible_lons[k]
            del possible_lats[k]

    if len(possible_lons) > 0:
        for lon_key in possible_lons.keys():
            if lon_key in possible_lats:
                n = f"{lon_key}_geo"
                cols.append(Column(n, geotype("POINT", srid=srid)))
                gc[n] = (possible_lons[lon_key], possible_lats[lon_key])

    return gc, cols


def parse_geom_cols(k, v, row, srid):
    # These must be converted to the -180 to 180 longitude domain,
    # since the Geography column type needs that domain for computations.
    # Its an Earth-centric world after all.
    if len(v) == 4:
        g = (
            f"POLYGON(("
            f"{lon_180(row[v[0][0]])} {row[v[0][1]]}, "
            f"{lon_180(row[v[1][0]])} {row[v[1][1]]}, "
            f"{lon_180(row[v[2][0]])} {row[v[2][1]]}, "
            f"{lon_180(row[v[3][0]])} {row[v[3][1]]}, "
            f"{lon_180(row[v[0][0]])} {row[v[0][1]]}))"
        )

    elif len(v) == 2:
        g = f"POINT({lon_180(row[v[0]])} {row[v[1]]})"

    else:
        raise IndexError(f"The Values in {k} ({v}) are not 2 or 4 coords.")

    if wkt.loads(g).is_valid:
        return f"SRID={srid};{g}"
    else:
        raise ValueError(f"The geometry {g} is invalid.")


def lon_180(longitude):
    lon = float(longitude)
    if lon > 180:
        return lon - 360
    else:
        return lon


def insert(
    conn, table, columns, geom_cols, path, pvl_table,
    lower_lat=-90, upper_lat=90, eastern=360, western=-360, srid=-1
):

    fieldnames = []
    for c in pvl_table.getall("COLUMN"):
        fieldnames.append(c["NAME"])

    if "CENTER_LATITUDE" not in fieldnames:
        raise ValueError("CENTER_LATITUDE not in columns.")

    if "CENTER_LONGITUDE" not in fieldnames:
        raise ValueError("CENTER_LONGITUDE not in columns.")

    lastrow = None
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            lastrow = row
            db_dict = dict()
            for c in columns:
                db_dict[c] = row[c].strip()

            if not (
                lower_lat <= float(row["CENTER_LATITUDE"]) <= upper_lat
            ):
                continue

            if not (
                western <= float(row["CENTER_LONGITUDE"]) <= eastern
            ):
                continue

            for k, v in geom_cols.items():
                try: 
                    db_dict[k] = parse_geom_cols(k, v, row, srid)
                except ValueError as err:
                    print(f"{db_dict}: {err} Skipping.")

            # conn.execute(table.insert(), **db_dict)
            stmt = sql_insert(table).values(**db_dict)
            conn.execute(stmt)
            conn.commit()

    volume = lastrow["VOLUME_ID"].strip('" \'')
    orbit = lastrow["ORBIT_NUMBER"].strip('" \'')
    lastdate = lastrow["START_TIME"].strip('" \'').split()[0]

    return volume, orbit, lastdate


def get_product(pid: str, pvl_table, path: Path):

    fieldnames = []
    for c in pvl_table.getall("COLUMN"):
        fieldnames.append(c["NAME"])

    d = None
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        for row in reader:
            if row["PRODUCT_ID"] == pid:
                d = row
                break

    if d is None:
        raise ValueError(f"The PRODUCT_ID {pid} is not present in {path}")

    return d


def insert_one(conn, table, row, geotype, srid=-1):

    possible_lons = dict()
    possible_lats = dict()

    for c in table.columns:
        if c.name.casefold().endswith("longitude"):
            possible_lons[geo_root(c.name)] = c.name
        elif c.name.casefold().endswith("latitude"):
            possible_lats[geo_root(c.name)] = c.name
        else:
            pass

    gc, _ = geom_cols(possible_lons, possible_lats, geotype, srid)

    db_dict = dict()
    for c in table.columns:
        if c.name in row:
            db_dict[c.name] = row[c.name].strip()
        elif c.name in gc:
            for k, v in gc.items():
                if len(v) == 4:
                    db_dict[k] = (
                        f"SRID={srid};POLYGON(({row[v[0][0]]} {row[v[0][1]]}, "
                        f"{row[v[1][0]]} {row[v[1][1]]}, "
                        f"{row[v[2][0]]} {row[v[2][1]]}, "
                        f"{row[v[3][0]]} {row[v[3][1]]}, "
                        f"{row[v[0][0]]} {row[v[0][1]]}))"
                    )
                elif len(v) == 2:
                    db_dict[k] = f"SRID={srid};POINT({row[v[0]]} {row[v[1]]})"
                else:
                    raise IndexError(
                        f"The Values in {k} ({v}) are not 2 or 4 coords."
                    )
        else:
            pass

    conn.execute(table.insert(), **db_dict)
    return


if __name__ == "__main__":
    sys.exit(main())
