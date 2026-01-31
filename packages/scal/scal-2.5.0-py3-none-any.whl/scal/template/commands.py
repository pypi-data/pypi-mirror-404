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

"""Tools used by scal subcommands."""

import pathlib
import pkgutil
import typing

DATADIR = pathlib.Path(pkgutil.resolve_name("scal.data").__path__[0])


def list_templates() -> typing.Iterator[pathlib.Path]:
    """Iterate over the list of built-in templates."""
    for template in (DATADIR / "templates").glob("*.tex"):
        yield template.relative_to(DATADIR / "templates")


def config_file(template: str) -> pathlib.Path:
    """Return the name of the example configuration file for the given template."""
    filename = DATADIR / "config" / template
    if filename.exists():
        return filename
    raise FileNotFoundError(f"Template {template} does not exist.")
