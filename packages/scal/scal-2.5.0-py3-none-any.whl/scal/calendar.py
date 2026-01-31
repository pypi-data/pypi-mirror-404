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

"""Configuration file and its representation."""

import datetime
import logging
import pathlib
import re
import typing

import yaml

from . import errors, utils
from .template.commands import config_file

LOGGER = logging.getLogger(__name__)

type DateTuple = tuple[int | None, int, int]


def parse_date(text: str) -> DateTuple:
    """Convert a date (with or without year) into a tuple of year, month, day.

    >>> parse_date("2022-03-04")
    (2022, 3, 4)
    >>> parse_date("05-01")
    (None, 5, 1)
    """
    words = text.split("-")
    if len(words) == 2:
        return None, int(words[0]), int(words[1])
    if len(words) == 3:
        return int(words[0]), int(words[1]), int(words[2])
    raise errors.ConfigError(f"Invalid date '{text}'.")


def parse_dates(text: str) -> tuple[DateTuple, DateTuple]:
    """Convert one or two dates (with or without year) into tuples of year, month, day.

    >>> parse_dates("2022-03-04 2022-04-08")
    ((2022, 3, 4), (2022, 4, 8))
    >>> parse_dates("05-01")
    ((None, 5, 1), (None, 5, 1))
    """
    # Would a regexp be easier? Maybe…
    if isinstance(text, datetime.date):
        return tuple(
            (text.year, text.month, text.day) for _ in range(2)
        )  # pyright: ignore
    dates = tuple(parse_date(word) for word in text.strip().split(" "))
    if len(dates) == 1:
        return dates[0], dates[0]
    if len(dates) == 2:
        return dates
    raise errors.ConfigError(f"Invalid date '{text}'.")


def is_between(
    start: datetime.date | None, middle: datetime.date, end: datetime.date | None
) -> bool:
    """Return True if `middle` is between `start` and `end`.

    >>> is_between(datetime.date(1900, 1, 1), datetime.date(1901, 1, 1), datetime.date(1901, 1, 2))
    True
    >>> is_between(datetime.date(1902, 1, 1), datetime.date(1901, 1, 1), datetime.date(1900, 1, 2))
    False
    >>> is_between(None, datetime.date(1900, 1, 1), datetime.date(1900, 1, 2))
    True
    >>> is_between(datetime.date(1900, 1, 1), datetime.date(1900, 1, 2), None)
    True
    """
    return (start is None or start <= middle) and (end is None or middle <= end)


class Period:
    """A (possibly named) period of time"""

    # pylint: disable=too-few-public-methods

    start: datetime.date | None = None
    end: datetime.date | None = None
    name: str | None = None

    def __init__(
        self, start: datetime.date, end: datetime.date, name: str | None = None
    ):
        if start > end:
            raise errors.ConfigError("Start date is older than end date.")
        self.start = start
        self.end = end
        self.name = name

    def __str__(self):
        txt = f"{self.start} --- {self.end}"
        if self.name:
            return f"{txt}: {self.name}"
        return txt

    def is_in(self, day: datetime.date) -> bool:
        """Return True iff ``day`` is in this period."""
        return is_between(self.start, day, self.end)


RE_DATE = re.compile(r"((?P<year>\d{4})-)?(?P<month>\d{2})-(?P<day>\d{})")

WEDNESDAY = 3


def last_day_of_month(mydate: datetime.date) -> datetime.date:
    "Return a date corresponding to the last day of the month of the argument."
    if mydate.month == 12:
        next_month = mydate.replace(mydate.year + 1, 1, 1)
    else:
        next_month = mydate.replace(mydate.year, mydate.month + 1, 1)
    return next_month - datetime.timedelta(days=1)


def weeknumber(day: datetime.date) -> int:
    """Return week number."""
    return day.isocalendar()[1]


class Calendar:
    """A calendar, that is, a start date, an end date, and holidays."""

    def __init__(self, config: dict):
        self.holidays: list[Period] = []

        if "calendar" not in config:
            raise errors.ConfigError(
                "The configuration must have a 'calendar' section."
            )

        # Template
        self.template = config["calendar"].get("template", "calendar.tex")

        # Read start date
        try:
            self.start: datetime.date = config["calendar"]["start"]
        except KeyError as error:
            raise errors.ConfigError("Missing start date.") from error
        if not isinstance(self.start, datetime.date):
            raise errors.ConfigError(f"Start date '{self.start}' is not a date.")

        # Read end date
        try:
            self.end: datetime.date = config["calendar"]["end"]
        except KeyError as error:
            raise errors.ConfigError("Missing end date.") from error
        if not isinstance(self.end, datetime.date):
            raise errors.ConfigError(f"End date '{self.end}' is not a date.")

        # Read holidays
        for dates, name in config.get("holidays", {}).items():
            self.add_holidays(dates, name)

        # Read more template variables
        default = None
        try:
            configfile = config_file(self.template)
            with open(configfile, encoding="utf8") as file:
                default = yaml.load(file, Loader=yaml.Loader)["variables"]
        except FileNotFoundError:
            pass

        if default is None:
            self.variables = config.get("variables", {})
        else:
            self.variables = utils.fill_default(
                config.get("variables", {}),
                default=default,
            )

        # Read weeks
        self.weeks = self._weeks(
            iso=config["calendar"].get("weeks", {}).get("iso", True),
            work=config["calendar"].get("weeks", {}).get("work", False),
        )

        # Filling first and last month
        if self.start.day != 1:
            self.holidays.append(
                Period(
                    datetime.date(self.start.year, self.start.month, 1),
                    self.start - datetime.timedelta(days=1),
                )
            )
        if self.end != last_day_of_month(self.end):
            self.holidays.append(
                Period(
                    self.end + datetime.timedelta(days=1), last_day_of_month(self.end)
                )
            )

    @classmethod
    def from_stream(cls, file: typing.TextIO) -> "Calendar":
        """Create an object from an object file (as returned by open())."""
        try:
            return cls(yaml.load(file.read(), Loader=yaml.Loader))
        except yaml.YAMLError as error:
            if file.name:
                raise errors.ScalError(
                    f"Error while parsing YAML file '{file.name}'."
                ) from error
            raise errors.ScalError("Error while parsing YAML file.") from error

    @classmethod
    def from_file(cls, filename: str | pathlib.Path) -> "Calendar":
        """Create an object from a filename."""
        with open(filename, encoding="utf8") as file:
            return cls.from_stream(file)

    def add_holidays(self, dates: str, name: str | None = None):
        """Add a named holiday, starting on `date0` and ending on `date1`."""
        if name is None:
            name = ""
        date0, date1 = parse_dates(dates)
        year0, month0, day0 = date0
        year1, month1, day1 = date1
        if ((year0 is None) and (year1 is not None)) or (
            (year0 is not None) and (year1 is None)
        ):
            raise errors.ConfigError(
                f"Either none or both years may be omitted ('{dates}')."
            )
        if year0 is None:
            for year in range(self.start.year, self.end.year + 1):
                try:
                    if is_between(
                        self.start, datetime.date(year, month0, day0), self.end
                    ) and is_between(
                        self.start, datetime.date(year, month1, day1), self.end
                    ):
                        self.holidays.append(
                            Period(
                                datetime.date(year, month0, day0),
                                datetime.date(year, month1, day1),
                                name,
                            )
                        )
                except errors.ConfigError:
                    LOGGER.warning(
                        "Ignored period %s--%s (invalid or outside calendar boundaries).",
                        datetime.date(year, month0, day0),
                        datetime.date(year, month1, day1),
                    )
        else:
            # If we reach this code, `year1` cannot be `None`.
            try:
                self.holidays.append(
                    Period(
                        datetime.date(year0, month0, day0),
                        datetime.date(year1, month1, day1),  # type: ignore
                        name,
                    )
                )
            except errors.ConfigError:
                LOGGER.warning(
                    "Ignored period %s--%s (invalid or outside calendar boundaries).",
                    datetime.date(year0, month0, day0),
                    datetime.date(year1, month1, day1),  # type: ignore
                )

    def is_holiday(self, day: datetime.date) -> bool:
        """Return True iff ``day`` is in a holiday."""
        return len([None for holiday in self.holidays if holiday.is_in(day)]) > 0

    def weeks_count(self) -> int:
        """Return the number of weeks of the calendar."""
        # Monday of the week of the start date
        start = self.start - datetime.timedelta(days=self.start.weekday())
        # Sunday of the week of the end date
        end = self.end - datetime.timedelta(days=self.end.weekday() - 7)

        return (end - start).days // 7

    def months_count(self) -> int:
        """Return the number of months of the calendar."""
        return (
            12 * (self.end.year - self.start.year)
            + self.end.month
            - self.start.month
            + 1
        )

    def year_boundaries(self) -> dict[int, tuple[int, int]]:
        """Return the first and last month of each year, as a dictionary.

        This is important for the first and last years, which can
        start or end by something else than January or December.
        """
        years = {}
        for year in range(self.start.year, self.end.year + 1):
            if self.start.year == self.end.year:
                boundaries = (self.start.month, self.end.month)
            elif year == self.start.year:
                boundaries = (self.start.month, 12)
            elif year == self.end.year:
                boundaries = (1, self.end.month)
            else:
                boundaries = (1, 12)
            years[year] = tuple(format(i, "02d") for i in boundaries)
        return years

    def is_workingweek(self, wednesday: datetime.date) -> bool:
        """Return True iff week of argument is a working week."""
        all_holiday = True
        for day in range(wednesday.toordinal() - 2, wednesday.toordinal() + 3):
            all_holiday = all_holiday and self.is_holiday(
                datetime.date.fromordinal(day)
            )
        return not all_holiday

    def week_iterator(self) -> typing.Iterator[tuple[datetime.date, int | None, int]]:
        """Iterate over weeks of self."""
        # Looking for first wednesday
        wednesday = self.start
        for day in range(self.start.toordinal(), self.start.toordinal() + 7):
            if datetime.date.fromordinal(day).isoweekday() == WEDNESDAY:
                wednesday = datetime.date.fromordinal(day)
                break

        workweek = 0
        while (wednesday.year, wednesday.month) <= (
            self.end.year,
            self.end.month,
        ):  # pylint: disable=used-before-assignment
            if self.is_workingweek(wednesday) and wednesday <= self.end:
                workweek += 1
                maybe_workweek = workweek
            else:
                maybe_workweek = None
            yield wednesday, maybe_workweek, weeknumber(wednesday)
            wednesday += datetime.timedelta(days=7)

    def _weeks(self, work: bool, iso: bool) -> list[dict[str, str]]:
        """Return the list of weeks, processed by template."""
        weeks = []
        for day, work_number, iso_number in self.week_iterator():
            week = {"date": day, "work": None, "iso": None}
            if work:
                week["work"] = work_number
            if iso:
                week["iso"] = iso_number
            weeks.append(week)
        return weeks

    def __str__(self):
        return f"From {self.start} to {self.end}\n" + "\n".join(
            [str(holiday) for holiday in self.holidays]
        )
