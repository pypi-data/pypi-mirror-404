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

"""Calendar generation"""

import typing

import jinja2

from .. import __DATE__, VERSION

if typing.TYPE_CHECKING:
    from ..calendar import Calendar


def generate_tex(calendar: "Calendar") -> str:
    """Generate TeX code producing calendar represented in argument.

    :arg Calendar calendar: A :class:`Calendar` object.
    """
    loader = jinja2.ChoiceLoader(
        [
            jinja2.PackageLoader("scal.data"),
            jinja2.FileSystemLoader("."),
        ]
    )

    environment = jinja2.Environment(loader=loader)
    environment.block_start_string = "(*"
    environment.block_end_string = "*)"
    environment.variable_start_string = "(("
    environment.variable_end_string = "))"
    environment.comment_start_string = "(% comment %)"
    environment.comment_end_string = "(% endcomment %)"
    environment.line_comment_prefix = "%!"
    # environment.filters['escape_tex'] = _escape_tex
    environment.trim_blocks = True
    environment.lstrip_blocks = True
    return environment.get_template(calendar.template).render(
        {  # pylint: disable=maybe-no-member
            "start": calendar.start,
            "end": calendar.end,
            "count": {
                "months": calendar.months_count(),
                "weeks": calendar.weeks_count(),
            },
            "holidays": calendar.holidays,
            "weeks": calendar.weeks,
            "years": calendar.year_boundaries(),
            "version": f"`scal` version {VERSION}",
            "variables": calendar.variables,
            "copyrightdate": __DATE__,
        }
    )
