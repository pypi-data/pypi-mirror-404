=======================================
Welcome to `papersize`'s documentation!
=======================================

.. currentmodule:: papersize

Paper size related data and functions.

This module provides tools to manipulate paper sizes, that is:

- a dictionary of several named standard names (e.g. A4, letter) , with their
  respective sizes (with and height);
- functions to convert sizes between units;
- functions to manipulate paper orientation (portrait or landscape);
- tools to parse paper sizes, so that you do not have to worry about the format
  of paper sizes provided by your user, it being `a4` or `21cm x 29.7cm`.

.. contents::
   :local:

Download and install
====================

See the `main project page <http://git.framasoft.org/spalax/papersize>`_ for
instructions, and `changelog
<https://git.framasoft.org/spalax/papersize/blob/main/CHANGELOG.md>`_.

Module documentation
====================

Constants
---------

.. autodata:: UNITS
    :annotation:

.. literalinclude:: ../papersize/__init__.py
   :start-at: UNITS =
   :end-at: }

.. autodata:: UNITS_HELP
    :annotation:

.. autodata:: SIZES
    :annotation:

.. literalinclude:: ../papersize/__init__.py
   :start-at: SIZES =
   :end-at: }

.. autodata:: SIZES_HELP
    :annotation:

.. autodata:: PORTRAIT
    :annotation:

.. autodata:: LANDSCAPE
    :annotation:

Unit conversion
---------------

.. autofunction:: convert_length

Parsers
-------

.. autofunction:: parse_length

.. autofunction:: parse_couple

.. autofunction:: parse_papersize

Paper orientation
-----------------

.. autofunction:: is_portrait

.. autofunction:: is_landscape

.. autofunction:: is_square

.. autofunction:: rotate

Exceptions
----------

.. autoclass:: PapersizeException

.. autoclass:: CouldNotParse

.. autoclass:: UnknownOrientation


.. _i18n:

Internationalisation
====================

Constants :data:`SIZES_HELP` and :py:data:`UNITS_HELP` are translated. If your application is not translated, just ignore it. If it is translated (using :mod:`gettext` or `babel <https://babel.pocoo.org>`__ for instance), translations are provided.

How to use it?
--------------

This module provides :func:`translation_directory`:

.. autofunction:: translation_directory

Example with :mod:`gettext`
"""""""""""""""""""""""""""

.. testcode::

   with papersize.translation_directory() as directory:
        gettext.bindtextdomain("papersize", localedir=directory)
        gettext.textdomain("papersize")
        _ = gettext.gettext
        print(_("centimeter"))

.. testoutput::

   centimètre

Everlasting translation directory
"""""""""""""""""""""""""""""""""

Function :func:`translation_directory` is a context manager, so the directory it returns is only guaranteed to last until its end. If you need the (maybe temporary) directory to last until your application exists, you can use the following example (`source <https://importlib-resources.readthedocs.io/en/latest/migration.html#pkg-resources-resource-filename>`__).

.. code-block::

    import contextlib
    import atexit

    def papersizetranslations():
        file_manager = contextlib.ExitStack()
        atexit.register(file_manager.close)
        return file_manager.enter_context(papersize.translation_directory())


Languages
---------

Right now, only French translations are provided. Translations in other languages are gladly accepted.

Contributing
============

Translation
-----------

Install `babel <https://babel.pocoo.org>`__, and cd to the root of the :mod:`papersize` repository. Then:

- Extract strings to translate::

    pybabel extract -F babel.cfg -o papersize.pot .

- Update French translations catalog (replace ``update`` with ``init`` for first translation of a new language)::

    pybabel update -i papersize.pot -d papersize/translations --domain papersize -l fr

- Manually update translations::

    $EDITOR papersize/translations/fr/LC_MESSAGES/papersize.po

- Compile translations::

    pybabel compile -d papersize/translations --domain papersize


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
