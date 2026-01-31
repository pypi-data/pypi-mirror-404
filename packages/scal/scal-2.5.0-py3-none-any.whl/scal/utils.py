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

"""Some random tools useful for scal."""


def fill_default(data: dict, *, default: dict) -> dict:
    """Fill missing values in data with values of default.

    Both arguments are expected to be dict of dict of dict of ... of objects
    (for an arbitrary depth of nested dicts).

    There will probably be bugs of arguments do not have the same structure
    (the same depth of dict, for instance).

    For instance, with:

    data = {
        "a": {"aa": 0, "ab": 2},
        "b": {"bb": 2},
        "c": 5,
        }
    default = {
        "a": {"aa": 0, "ab": 1},
        "b": {"ba":0 , "bb": 1},
        "c": 0,
        "d": {"dd": 0},
        }

    The returned dictionary will be:

    {
        "a": {"aa": 0, "ab": 2},
        "b": {"ba": 0, "bb": 2},
        "c": 5,
        "d": {"dd": 0},
        }
    """
    new = {}
    for key, value in default.items():
        if key in data:
            if isinstance(data[key], dict):
                new[key] = fill_default(data[key], default=value)
            else:
                new[key] = data[key]
        else:
            new[key] = value
    return new
