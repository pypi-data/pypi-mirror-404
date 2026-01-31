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

"""Produce a calendar."""

import logging
import sys

import argdispatch

import scal
from scal import monthly

from . import VERSION, calendar, errors, template
from .template import commands

LOGGER = logging.getLogger(scal.__name__)
LOGGER.addHandler(logging.StreamHandler())


def _subcommand_templates_list(args: list[str]) -> None:
    """List built-in templates."""
    parser = argdispatch.ArgumentParser(
        prog="scal templates list",
        description="List built-in templates.",
    )

    parser.parse_args(args)

    for name in commands.list_templates():
        print(name)


def _subcommand_templates_config(args: list[str]) -> None:
    """Display an example configuration file for a given built-in template."""
    parser = argdispatch.ArgumentParser(
        prog="scal templates config",
        description="Display an example configuration file default for a given built-in template.",
    )

    parser.add_argument(
        "TEMPLATE",
        help="Template name",
    )

    arguments = parser.parse_args(args)

    with open(commands.config_file(arguments.TEMPLATE), encoding="utf8") as file:
        print(file.read().strip())


def _subcommand_templates(args: list[str]) -> None:
    """Manage 'scal' templates."""
    parser = argdispatch.ArgumentParser(
        prog="scal templates",
        description="Manage 'scal' templates.",
    )

    subparser = parser.add_subparsers()
    subparser.add_function(_subcommand_templates_list, command="list")
    subparser.add_function(_subcommand_templates_config, command="config")

    parser.parse_args(args)


def _subcommand_generate(args: list[str]) -> None:
    """Generate calendar."""
    parser = argdispatch.ArgumentParser(
        prog="scal generate",
        description="A year calendar producer.",
        formatter_class=argdispatch.RawTextHelpFormatter,
    )

    parser.add_argument(
        "FILE",
        help="Configuration file",
        type=argdispatch.FileType("r"),
        default=sys.stdin,
    )

    arguments = parser.parse_args(args)

    try:
        inputcalendar = calendar.Calendar.from_stream(arguments.FILE)
    except errors.ConfigError as error:
        LOGGER.error("Configuration error in file %s: %s", arguments.FILE.name, error)
        sys.exit(1)
    print(template.generate_tex(inputcalendar))


DEFAULT_SUBCOMMAND = "generate"


def argument_parser() -> argdispatch.ArgumentParser:
    """Return a command line parser."""

    parser = argdispatch.ArgumentParser(
        prog="scal",
        description="A year calendar producer.",
        formatter_class=argdispatch.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--version",
        help="Show version",
        action="version",
        version="%(prog)s " + VERSION,
    )

    subparser = parser.add_subparsers(
        required=True,
        title="Subcommands",
        description="""If no subcommand is given, "generate" is used by default.""",
    )

    subparser.add_module(monthly, command="monthly")
    subparser.add_function(_subcommand_generate, command="generate")
    subparser.add_function(_subcommand_templates, command="templates")

    return parser


def main() -> None:
    """Main function."""
    args = sys.argv[1:]
    parser = argument_parser()

    if not args:
        parser.parse_args()
    if args[0] in ("-h", "--help", "--version"):
        parser.parse_args(args)
    if args[0] in ("monthly", "generate", "templates"):
        parser.parse_args(args)
    parser.parse_args([DEFAULT_SUBCOMMAND] + args)


if __name__ == "__main__":
    main()
