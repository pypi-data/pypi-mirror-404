#!/usr/bin/env python3

# Copyright Louis Paternault 2011-2026
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 1

"""Produce a monthly calendar with pictures."""

import argparse
import datetime
import pathlib
import shutil
import subprocess
import tempfile

import papersize
from PIL import Image

from .. import calendar, template


def argument_parser() -> argparse.ArgumentParser:
    """Return a command line parser."""
    # pylint: disable=line-too-long

    parser = argparse.ArgumentParser(
        prog="scal",
        description="A year calendar producer.",
    )

    parser.add_argument(
        "-y",
        "--year",
        type=int,
        default=datetime.datetime.today().year,
        help=f"Year of the calendar (e.g. {datetime.datetime.today().year})",
    )
    parser.add_argument(
        "-l",
        "--language",
        type=str,
        default="english",
        help="""Calendar language (e.g. "french", "english", "spanish"…).""",
    )
    parser.add_argument(
        "-p",
        "--papersize",
        default="A4",
        type=papersize.parse_papersize,
        help="""Size of the paper (e.g. "A4", "21cm×297mm", etc.).""",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        type=pathlib.Path,
        help="""Output file. Default is the year, given by option `--year` (e.g. "{datetime.datetime.today().year}.pdf").""",
    )
    parser.add_argument(
        "PICTURE",
        type=pathlib.Path,
        nargs=12,
        help="File names of twelve pictures (one for each month).",
    )

    return parser


def _parse_picture(filename: pathlib.Path) -> dict[str, str | pathlib.Path]:
    # Look for credits
    if filename.with_suffix(".mdwn").exists():
        credit = subprocess.run(
            [
                "pandoc",
                "--from",
                "markdown",
                "--to",
                "latex",
                filename.with_suffix(".mdwn"),
            ],
            stdin=subprocess.DEVNULL,
            check=True,
            stdout=subprocess.PIPE,
            text=True,
        ).stdout
    else:
        credit = ""

    image = Image.open(filename)
    if image.size[0] > image.size[1]:
        orientation = "horizontal"
    else:
        orientation = "vertical"
    # Check image size
    return {
        "filename": filename.resolve(),
        "orientation": orientation,
        "credit": credit,
    }


def main() -> None:
    """Main function."""
    # Get command line options
    options = argument_parser().parse_args()
    if options.output is None:
        options.output = pathlib.Path(f"{options.year}.pdf")

    with tempfile.TemporaryDirectory() as tempdir:
        # Build LaTeX file
        with open(
            pathlib.Path(tempdir) / f"{options.year}.tex", mode="w", encoding="utf8"
        ) as file:
            file.write(
                template.generate_tex(
                    calendar.Calendar(
                        {
                            "calendar": {
                                "template": "monthly.tex",
                                "start": datetime.date(
                                    year=options.year, month=1, day=1
                                ),
                                "end": datetime.date(
                                    year=options.year, month=12, day=1
                                ),
                            },
                            "variables": {
                                # pylint: disable=line-too-long
                                "language": options.language,
                                "papersize": f"paperwidth={round(options.papersize[0])}pt, paperheight={round(options.papersize[1])}pt",
                                "pictures": [
                                    _parse_picture(filename)
                                    for filename in options.PICTURE
                                ],
                            },
                        }
                    )
                )
            )
        # Compile file
        for _ in range(3):
            subprocess.run(
                ["lualatex", str(options.year)],
                cwd=tempdir,
                stdin=subprocess.DEVNULL,
                check=True,
            )

        # Get resulting file
        shutil.move(pathlib.Path(tempdir) / f"{options.year}.pdf", options.output)


if __name__ == "__main__":
    main()
