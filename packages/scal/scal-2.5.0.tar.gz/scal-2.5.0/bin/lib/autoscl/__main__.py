# Copyright 2019-2026 Louis Paternault
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

"""Download holiday dates from the internet, and generate the relevant .scl file.

`autoscl --help` for more information.
"""

import argparse
import datetime
import json
import logging
import operator
import pathlib
import re
import sys
import textwrap
import time
import urllib.request

import jinja2
from jours_feries_france import JoursFeries

SCHOOLYEAR = re.compile(r"(\d{4})-(\d{4})", re.ASCII)
ONEDAY = datetime.timedelta(days=1)
DEFAULT_TEMPLATE = "calendar"
START_OF_TIME = datetime.date.fromisoformat("0001-01-01")
END_OF_TIME = datetime.date.fromisoformat("9999-01-01")
ENVIRONMENT = jinja2.Environment(loader=jinja2.PackageLoader("autoscl"))

logging.basicConfig(level=logging.INFO)


class Error(Exception):
    """Exceptions to be catched and nicely formatted to the user."""


def download_json(url):
    """Download a json file from the internet, and return it as a Python object."""
    logging.info("Downloading: %s", url)
    with urllib.request.urlopen(url) as request:
        time.sleep(0.5)
        return json.loads(request.read().decode())


def fromisoformat(text):
    """Parse date or time."""
    try:
        return datetime.date.fromisoformat(text)
    except ValueError:
        pass

    try:
        return datetime.datetime.fromisoformat(text).date()
    except ValueError:
        pass

    raise ValueError(f"Could not parse date: {text}")


################################################################################
# Some stuff specifict to "fr.educnat" (French ministry of national education).
# Might be moved later in another module, if another country is ever supported.

URL_SCHOOL_HOLIDAYS = "https://data.education.gouv.fr/api/records/1.0/search/?dataset=fr-en-calendrier-scolaire&lang=fr&rows=100&facet=description&facet=start_date&facet=end_date&facet=location&facet=zones&facet=annee_scolaire&refine.annee_scolaire={schoolyear}&refine.location={location}"  # pylint: disable=line-too-long


def parse_school_holidays(raw, *, limits=None):
    """Parse holidays, as received from the URL URL_SCHOOL_HOLIDAYS."""
    holidays = {}
    if limits is None:
        start = START_OF_TIME
        end = END_OF_TIME
    else:
        start, end = limits
    for entry in raw["records"]:
        fields = entry["fields"]

        try:
            startdate = fromisoformat(fields["start_date"])
        except KeyError:
            startdate = START_OF_TIME
        try:
            enddate = fromisoformat(fields["end_date"])
        except KeyError:
            enddate = END_OF_TIME

        if not (start <= startdate <= end or start <= enddate <= end):
            continue

        description = fields["description"]
        if description in holidays:
            holidays[description] = [
                max(startdate + ONEDAY, holidays[description][0]),
                max(enddate - ONEDAY, holidays[description][1]),
            ]
        else:
            holidays[description] = [startdate + ONEDAY, enddate - ONEDAY]
        if holidays[description][0].strftime("%w") == "0":
            # Dimanche
            holidays[description][0] -= ONEDAY
    return holidays


def get_school_start(year, city):
    """Get start date of school (for students)."""
    holidays = parse_school_holidays(
        download_json(
            URL_SCHOOL_HOLIDAYS.format(schoolyear=f"{year-1}-{year}", location=city)
        )
    )
    return holidays["Vacances d'Été"][1] + 2 * ONEDAY


def get_school_end(year, city):
    """Get end date of school (for students)."""
    holidays = parse_school_holidays(
        download_json(
            URL_SCHOOL_HOLIDAYS.format(schoolyear=f"{year-1}-{year}", location=city)
        )
    )
    for ete in ("Début des Vacances d'Été", "Vacances d'Été"):
        try:
            return holidays[ete][0]
        except KeyError:
            pass
    raise Error("""Could not find start of summer holidays (vacances d'été)""")


def get_work_holidays(year: int):
    """Iterate over holidays for given year"""
    for name, date in JoursFeries.for_year(year).items():
        yield (
            name,
            date,
            date,
        )


def get_holidays(startyear, endyear, city, start, end):
    """Download holidays, parse them, and return them.

    The returned dictionary is:
    - keys: holiday names;
    - values: tuple (start, end).
    """
    holidays = parse_school_holidays(
        download_json(
            URL_SCHOOL_HOLIDAYS.format(
                schoolyear=f"{startyear}-{endyear}", location=city
            )
        ),
        limits=(start, end),
    )

    for year in (startyear, endyear):
        for entry in get_work_holidays(year):
            if entry[0] == "Ascension" and "Pont de l'Ascension" in holidays:
                pont = holidays["Pont de l'Ascension"]
                if pont[0] <= entry[1] <= pont[1]:
                    # Le jour férié est dans le pont de l'Ascension. Inutile de l'ajouter
                    continue
                if entry[1] + ONEDAY == pont[0]:
                    # Le jour férié est la veille du pont de l'Ascension. On l'intègre au pont.
                    pont[0] -= ONEDAY
                    continue
            if start <= entry[1] <= end and start <= entry[2] <= end:
                holidays[entry[0]] = (entry[1], entry[2])

    return holidays


def generate_fr_educnat(years: tuple[int, int], more):
    """Get holiday information from the Internet, and parse them.

    The returned dictionary is suited to be passed to :fun:`generatescl`
    (it is the dictionary of jinja2 variables).
    """
    city = more[0]
    start = get_school_start(years[0], city)
    end = get_school_end(years[1], city)

    # Réception des vacances, et tri chronologique
    holidays = sorted(
        [
            (description, limits[0], limits[1])
            for (description, limits) in get_holidays(*years, city, start, end).items()
        ],
        key=operator.itemgetter(1),
    )

    return {
        "start": start,
        "end": end,
        "language": "french",
        "papersize": "a4paper",
        "holidays": holidays,
        "weeks": {
            "work": "true",
            "iso": "true",
        },
    }


# End of stuff specific to fr.educnat
################################################################################


################################################################################
# Some stuff specific to en
def generate_en(years, more):
    """Generate data to populate calendar template (English)."""
    # pylint: disable=unused-argument
    return {
        "start": datetime.date(years[0], 7, 1),
        "end": datetime.date(years[1], 6, 30),
        "language": "english",
        "papersize": "letterpaper",
        "holidays": {},
    }


# End of stuff specific to fr.educnat
################################################################################

COUNTRIES = {
    "fr.educnat": generate_fr_educnat,
    "en": generate_en,
}
TEMPLATES = [
    pathlib.Path(filename).stem
    for filename in ENVIRONMENT.list_templates(extensions=".scl")
]


def _type_country(text):
    """Check that country is supported."""
    if text in COUNTRIES:
        return text
    raise argparse.ArgumentTypeError(
        # pylint: disable=consider-using-f-string
        "{} is not a valid country. Choose a string among: {}.".format(
            text, ", ".join(COUNTRIES.keys())
        )
    )


def _type_years(text):
    try:
        years = tuple(int(year) for year in SCHOOLYEAR.match(text).groups())  # type: ignore
    except AttributeError as exception:
        raise argparse.ArgumentTypeError(
            """School year must be of the form YYYY-YYYY (e.g. "2019-2020")."""
        ) from exception
    if years[1] - years[0] != 1:
        raise argparse.ArgumentTypeError("""School year must be one year long.""")
    return years


def argumentparser():
    """Return an argument parser."""
    # pylint: disable=line-too-long
    parser = argparse.ArgumentParser(
        description="Generate a .scl file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
                Example: 'autoscl fr.educnat 2019-2020 Paris' generates the .scl file for official school year 2019-2020, in Paris.

                <french>
                Pour générer les calendriers des trois zones, depuis la racine du projet, utiliser :

                ./bin/autoscl fr.educnat 2019-2020 Grenoble > doc/examples/fr_20192020_A.scl
                ./bin/autoscl fr.educnat 2019-2020 Rennes > doc/examples/fr_20192020_B.scl
                ./bin/autoscl fr.educnat 2019-2020 Paris > doc/examples/fr_20192020_C.scl
                ./bin/generate_examples.sh

                Pour faire encore plus court, utiliser `autoautoscl` :

                ./bin/autoautoscl
                ./bin/generate_examples.sh

                </french>
                """),
    )
    parser.add_argument(
        "-t",
        "--templates",
        help="Template to use: comma separated list of templates among"
        + ", ".join(TEMPLATES),
        type=str,
        nargs="+",
        choices=("weekly", "calendar"),
        default=DEFAULT_TEMPLATE,
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file",
    )
    parser.add_argument("country", help="Country of calendar.", type=_type_country)
    parser.add_argument("years", help="Calendar school years.", type=_type_years)
    parser.add_argument("more", nargs="*", help="More options (country specific).")
    return parser


def generatescl(variables, *, template):
    """Load relevant template, and generate the .scl file.

    The file is not written (it is printed to standard output).

    The arguments are passed to the jinja2 template.
    """
    return ENVIRONMENT.get_template(f"{template}.scl").render(**variables)


def main():
    """Main function."""
    args = argumentparser().parse_args()
    for template in args.templates:
        data = COUNTRIES[args.country](years=args.years, more=args.more)
        with open(
            args.output.format(template=template), mode="w", encoding="utf-8"
        ) as output:
            output.write(generatescl(data, template=template))


if __name__ == "__main__":
    try:
        main()
    except Error as error:
        logging.error(str(error))
        sys.exit(1)
