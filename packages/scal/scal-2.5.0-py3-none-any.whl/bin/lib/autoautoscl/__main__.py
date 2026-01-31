# Copyright 2019-2023 Louis Paternault
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero Public License for more details.
#
# You should have received a copy of the GNU Affero Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Automatically generate and overwrite examples of .scl files.

`autoautoscl --help` for more information.
"""

import argparse
import datetime
import logging
import os
import re
import shlex
import subprocess
import sys
import textwrap
import time

logging.basicConfig(level=logging.INFO)

RE_YEARRANGE = re.compile(r"(\d{4})-(\d{4})", re.ASCII)

REPOROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

CURRENTYEAR = int(datetime.date.today().strftime("%Y"))


class Error(Exception):
    """Exceptions to be catched and nicely formatted to the user."""


def auto_fr_educnat(years):
    """Iterate over commands and destination files to run (French Éducation nationale)

    Yields command to run, as a list to be passed to subprocess.run()
      (working directory being the repository root).
    """
    for year in years:
        for zone, ville in (("A", "Grenoble"), ("B", "Rennes"), ("C", "Paris")):
            yield [
                "./bin/autoscl",
                "--templates",
                "calendar",
                "weekly",
                "--output",
                f"doc/examples/{{template}}-fr-{year}{year+1}-{zone}.scl",
                "fr.educnat",
                f"{year}-{year+1}",
                ville,
            ]


def auto_en(years):
    """Iterate over commands and destination files to run (English)"""
    for year in years:
        yield [
            "./bin/autoscl",
            "--templates",
            "calendar",
            "weekly",
            "--output",
            f"doc/examples/{{template}}-en-{year}{year+1}.scl",
            "en",
            f"{year}-{year+1}",
        ]


COUNTRIES = {
    "fr.educnat": auto_fr_educnat,
    "en": auto_en,
}


def _type_country(text):
    """Check that country is supported."""
    if text in COUNTRIES:
        return text
    raise argparse.ArgumentTypeError(
        # pylint: disable=consider-using-f-string
        "{} is not a valid countries. Choose a string among: {}.".format(
            text, ", ".join(COUNTRIES.keys())
        )
    )


def _type_yearrange(text):
    """Check that year is a range of years (e.g. "2015-2020")."""
    match = RE_YEARRANGE.match(text)
    if not match:
        raise argparse.ArgumentTypeError(
            f"{text} is not a valid year range: it must be of the form YYYY-YYYY (e.g. 2015-2020)."
        )
    start, end = int(match.groups()[0]), int(match.groups()[1])
    return list(range(start, end))


def argumentparser():
    """Return an argument parser."""
    # pylint: disable=line-too-long
    parser = argparse.ArgumentParser(
        description="Generate and overwrite .scl examples.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
                Example: 'autoautoscl -c fr.educnat 2017-2020' generates the .scl files for French official school years, from 2017 to 2020.

                <french>
                Pour générer les calendriers des trois zones, depuis la racine du projet, utiliser (ajouter éventuellement les années):

                ./bin/autoautoscl
                ./bin/generate_examples.sh

                </french>
                """),
    )
    parser.add_argument(
        "-c",
        "--countries",
        help="Countries of calendar.",
        type=_type_country,
        nargs="+",
        default=list(COUNTRIES.keys()),
    )
    parser.add_argument(
        "years",
        help="Calendar school years.",
        nargs="?",
        type=_type_yearrange,
        default=f"{CURRENTYEAR}-{CURRENTYEAR+1}",
    )
    return parser


def main():
    """Main function."""
    args = argumentparser().parse_args()
    for country in args.countries:
        print("Country:", country)
        for command in COUNTRIES[country](args.years):
            print(shlex.join(command), end=" # ")
            if subprocess.call(command, cwd=REPOROOT) == 0:
                print("SUCCESS")
            else:
                print("ERROR")
            time.sleep(2)  # Be kind to the opendata servers.


if __name__ == "__main__":
    try:
        if sys.version_info < (3, 8):
            raise Error("This program requires python version 3.8 or above.")
        main()
    except Error as error:
        logging.error(str(error))
        sys.exit(1)
