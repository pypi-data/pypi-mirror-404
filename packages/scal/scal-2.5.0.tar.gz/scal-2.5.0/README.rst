scal 📅 School year (and other) calendar generator
==================================================

I use this program about once a year to print a one-page school-year
calendar. But it can be used to represent any calendar.

The first template is heavily inspired by the simple yet powerful Robert Krause's `calendar <http://www.texample.net/tikz/examples/a-calender-for-doublesided-din-a4/>`_, itself using the complex yet powerful Till Tantau's `TikZ <http://www.ctan.org/pkg/pgf>`_ LaTeX package. Other templates are mine, with help from the well writen TikZ documentation.

Examples
--------

- One-page calendar of a school year

  - English:
    `2025-2026 <https://spalax.frama.io/scal/examples/calendar-en-20252026.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-en-20252026.scl>`__).
    `2026-2027 <https://spalax.frama.io/scal/examples/calendar-en-20262027.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-en-20262027.scl>`__).

  - French

    - 2025-2026:
      `Zone A <https://spalax.frama.io/scal/examples/calendar-fr-20252026-A.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20252026-A.scl>`__);
      `Zone B <https://spalax.frama.io/scal/examples/calendar-fr-20252026-B.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20252026-B.scl>`__);
      `Zone C <https://spalax.frama.io/scal/examples/calendar-fr-20252026-C.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20252026-C.scl>`__).
    - 2026-2027:
      `Zone A <https://spalax.frama.io/scal/examples/calendar-fr-20262027-A.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20262027-A.scl>`__);
      `Zone B <https://spalax.frama.io/scal/examples/calendar-fr-20262027-B.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20262027-B.scl>`__);
      `Zone C <https://spalax.frama.io/scal/examples/calendar-fr-20262027-C.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/calendar-fr-20262027-C.scl>`__).

- Weekly planners (`How to print? <https://scal.readthedocs.io/en/latest/#examples>`__)

  - English:
    `2025-2026 <https://spalax.frama.io/scal/examples/weekly-en-20252026.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-en-20252026.scl>`__ ; `imposed <https://spalax.frama.io/scal/examples/weekly-en-20252026-impose.pdf>`__).
    `2026-2027 <https://spalax.frama.io/scal/examples/weekly-en-20262027.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-en-20262027.scl>`__ ; `imposed <https://spalax.frama.io/scal/examples/weekly-en-20262027-impose.pdf>`__).

  - French

    - 2025-2026:
      `Zone A <https://spalax.frama.io/scal/examples/weekly-fr-20252026-A.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20252026-A.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20252026-A-impose.pdf>`__);
      `Zone B <https://spalax.frama.io/scal/examples/weekly-fr-20252026-B.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20252026-B.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20252026-B-impose.pdf>`__);
      `Zone C <https://spalax.frama.io/scal/examples/weekly-fr-20252026-C.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20252026-C.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20252026-C-impose.pdf>`__).
    - 2026-2027:
      `Zone A <https://spalax.frama.io/scal/examples/weekly-fr-20262027-A.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20262027-A.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20262027-A-impose.pdf>`__);
      `Zone B <https://spalax.frama.io/scal/examples/weekly-fr-20262027-B.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20262027-B.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20262027-B-impose.pdf>`__);
      `Zone C <https://spalax.frama.io/scal/examples/weekly-fr-20262027-C.pdf>`__ (`source <https://framagit.org/spalax/scal/-/raw/main/doc/examples/weekly-fr-20262027-C.scl>`__ ; `imposé <https://spalax.frama.io/scal/examples/weekly-fr-20262027-C-impose.pdf>`__).

- Monthly calendar with pictures. You can choose your own pictures; here are some examples with `pictures from Wikipedia <https://en.wikipedia.org/wiki/Wikipedia:Picture_of_the_day>`__.

  - 2026: `english <https://spalax.frama.io/scal/examples/monthly-english-2026-compressed.pdf>`__, `french <https://spalax.frama.io/scal/examples/monthly-french-2026-compressed.pdf>`__
  - 2027: `english <https://spalax.frama.io/scal/examples/monthly-english-2027-compressed.pdf>`__, `french <https://spalax.frama.io/scal/examples/monthly-french-2027-compressed.pdf>`__


What's new?
-----------

See `changelog <https://git.framasoft.org/spalax/scal/blob/main/CHANGELOG.md>`_.

Download and install
--------------------

See the end of list for a (quick and dirty) Debian package.

* Non-Python dependencies.
  This program produces LuaLaTeX code, but does not compile it. So, LaTeX is not
  needed to run this program. However, to compile the generated code, you will
  need a working LaTeX installation, with ``lualatex``, and LuaLaTeX packages
  `geometry <http://www.ctan.org/pkg/geometry>`_,
  `babel <http://www.ctan.org/pkg/babel>`_,
  `tikz <http://www.ctan.org/pkg/pgf>`_,
  `fontspec <http://www.ctan.org/pkg/fontspec>`_,
  and `translator` (provided by the `beamer <http://www.ctan.org/pkg/beamer>`_ package).
  Those are provided by `TeXLive <https://www.tug.org/texlive/>`_ on GNU/Linux, `MiKTeX <http://miktex.org/>`_ on Windows, and `MacTeX <https://tug.org/mactex/>`_ on MacOS.

* From sources:

  * Download: https://pypi.python.org/pypi/scal
  * Install (in a `virtualenv`, if you do not want to mess with your distribution installation system)::

        python3 setup.py install

* From pip::

    pip install scal

* Quick and dirty Debian (and Ubuntu?) package

  This requires `stdeb <https://github.com/astraw/stdeb>`_ to be installed::

      python3 setup.py --command-packages=stdeb.command bdist_deb
      sudo dpkg -i deb_dist/scal-<VERSION>_all.deb

Documentation
-------------

* The compiled documentation is available on `readthedocs <http://scal.readthedocs.io>`_

* To compile it from source, download and run::

      cd doc && make html

Developpers
-----------

A partially supported `autoscl <https://framagit.org/spalax/scal/blob/main/bin/autoscl>`_ script is available in the `bin` directory. It can automatically download holiday dates from the internet, and generate the relevant `.scl` file. See `autoscl --help` for more information.
