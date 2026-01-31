#!/usr/bin/env python3

# Copyright Louis Paternault 2013-2026
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

"""Generate the configuration file to build a calendar with Wikimedia images"""

# pylint: disable=invalid-name

import argparse
import contextlib
import datetime
import pathlib
import random
import subprocess
import sys
import tempfile
import textwrap
import time

import jinja2
import requests
from rich.console import Console
from rich.progress import track

PROGRAM_NAME = __file__
MAX_RETRYS = 10
WIKIMEDIA_API_URL = (
    "https://api.wikimedia.org/feed/v1/wikipedia/{language}/featured/{date}"
)

USAGE = textwrap.dedent(f"""\
        {__doc__}

        Usage:

        {PROGRAM_NAME} LANGUAGE YEAR

        The output is a configuration file to be processed by `scal`…
        """)

TEMPLATE = jinja2.Template(textwrap.dedent("""\
    calendar:
      template: monthly.tex
      start: {{ year }}-01-01
      end: {{ year }}-12-31

    variables:
      language: {{ language }}
      pictures:
        {{ pictures }}
    """))

CONSOLE = Console(stderr=True)

# The wikimedia API has a limit of 500 requests per hour, or one request every 7.2 seconds
# Let's use 8 seconds to be safe.
# https://api.wikimedia.org/wiki/Rate_limits
MINIMUM_DELAY = 8


class WikimediaDownloader:
    """Download data from Wikimedia."""

    def __init__(self, dest):
        self.dest = dest
        dest.mkdir(exist_ok=True)
        self._last_call = datetime.datetime.now() - datetime.timedelta(
            seconds=MINIMUM_DELAY
        )

    @contextlib.contextmanager
    def sleep(self):
        """Wait `MINIMUM_DELAY` between two calls."""
        sleep = max(
            0,
            (
                self._last_call
                + datetime.timedelta(seconds=MINIMUM_DELAY)
                - datetime.datetime.now()
            ).total_seconds(),
        )
        time.sleep(sleep)
        yield from [None]
        self._last_call = datetime.datetime.now()

    @property
    def missing(self):
        """Return number of missing images.

        We want 12 pictures in the destination directory (one per month).
        """
        return 12 - len(list(self.dest.glob("*.jpg")))

    def picturename(self, date, suffix):
        """Retun the name of the file in which the picture of the given date is stored."""
        return (self.dest / date.strftime("%Y%m%d")).with_suffix(suffix)

    def download_picture(self):
        """Download the picture of the day of a random date.

        Save the image in file given by :func:`picturename`.
        Return the (date, credit) of the picture.
        """
        errors = 0

        while True:
            # Repeat until image have been successfully downloaded
            date = random_date()
            if self.picturename(date, ".jpg").exists():
                continue

            try:
                # Download image metadata
                CONSOLE.log(f"""Downloading image metadata for date {date}.""")
                response = self.download(
                    WIKIMEDIA_API_URL.format(
                        language="en", date=date.strftime("%Y/%m/%d")
                    )
                ).json()

                # pylint: disable=line-too-long, consider-using-f-string
                credit = """*{title}*, by {artist}, published under licence {licence}\n\n[{url}]({url})""".format(
                    title=response["image"]["description"]["text"],
                    artist=response["image"]["artist"]["text"],
                    licence=response["image"]["license"]["type"],
                    url=response["image"]["file_page"],
                )

                if (
                    response["image"]["image"]["width"]
                    > 2 * response["image"]["image"]["height"]
                ):
                    # Images much wider than tall won't render well in the calendar
                    CONSOLE.log(
                        # pylint: disable=line-too-long
                        f"Image too wide ({response["image"]["image"]["width"]}x{response["image"]["image"]["height"]}). Trying another image…"
                    )
                    continue

                if (
                    response["image"]["image"]["width"] > 32000
                    or response["image"]["image"]["height"] > 32000
                ):
                    # Mogrify (called later) cannot process images too big.
                    CONSOLE.log(
                        # pylint: disable=line-too-long
                        f"Image too big ({response["image"]["image"]["width"]}x{response["image"]["image"]["height"]}). Trying another image…"
                    )
                    continue

                # Download actual image
                CONSOLE.log(f"""Downloading image for date {date}.""")
                with tempfile.NamedTemporaryFile(
                    delete_on_close=False,
                    suffix=pathlib.Path(response["image"]["image"]["source"]).suffix,
                ) as file:
                    # Download file
                    for chunk in self.download(
                        response["image"]["image"]["source"], stream=True
                    ).iter_content(chunk_size=128):
                        file.write(chunk)
                    file.close()

                    # Rename it to a proper image, while:
                    # - converting it to jpg (with a ".jpg" suffix),
                    # - reducing it if too big,
                    # - setting density to 300dpi (this should be useless, because the image is resized anyway, but some image have a faulty density of 1dpi, which give huge dimensions, which exceeds LaTeX maximum dimension).
                    subprocess.run(
                        [
                            "convert",
                            file.name,
                            "-resize",
                            "2000x2000>",
                            "-density",
                            "300",
                            self.picturename(date, ".jpg"),
                        ],
                        stderr=subprocess.PIPE,
                        check=True,
                    )
                # Write credit into an associated markdown file
                with open(
                    self.picturename(date, ".mdwn"), mode="w", encoding="utf8"
                ) as file:
                    file.write(credit)
            except (KeyError, requests.exceptions.HTTPError) as error:
                CONSOLE.log(
                    f"Error while downloading picture of the day {date}: {error}."
                )
                if errors >= MAX_RETRYS:
                    CONSOLE.log("Too many errors. Aborting.")
                    sys.exit(1)
                continue

            # Image downloaded sucessfully
            break

        # Build attribution text (in LaTeX)
        # pylint: disable=line-too-long
        return (date, credit)

    def download(self, url, stream=False):
        """Download the content at the given URL."""
        with self.sleep():
            response = requests.get(
                url,
                stream=stream,
                headers={"User-Agent": PROGRAM_NAME},
                timeout=60,
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                if response.status_code == 429:
                    CONSOLE.log(
                        # pylint: disable=line-too-long
                        f"""Error 429: Server is asking us to wait {response.headers["retry-after"]} seconds…"""
                    )
                    # The server kindly requests us to stop downloading for a while.
                    time.sleep(float(response.headers["retry-after"]))
                raise
            return response


def random_date():
    """Returns a random date since Wikipedia started having "pictures of the day"."""
    # I do not know exactly what is the oldest available data
    lower = datetime.date(2016, 1, 1)
    upper = datetime.date.today()
    return lower + datetime.timedelta(days=random.randint(0, (upper - lower).days))


def escape(string):
    """Escape the HTML string so that it can be rendered by LaTeX."""
    return string.replace("%", r"\%").replace("&amp;", r"\&").replace("&nbsp;", " ")


def main():
    """Main function"""

    # Downloading pictures
    downloader = WikimediaDownloader(argument_parser().parse_args().DEST)
    for _ in track(
        range(downloader.missing),
        description="Downloading images…",
        console=CONSOLE,
        transient=True,
    ):
        downloader.download_picture()


def argument_parser():
    """Return a command line parser."""
    parser = argparse.ArgumentParser(
        prog=__file__,
        description="Download random pictures of the day from Wikimedia",
    )

    parser.add_argument(
        "DEST",
        type=pathlib.Path,
        default=".",
        help="Destination directory.",
    )

    return parser


if __name__ == "__main__":
    main()
