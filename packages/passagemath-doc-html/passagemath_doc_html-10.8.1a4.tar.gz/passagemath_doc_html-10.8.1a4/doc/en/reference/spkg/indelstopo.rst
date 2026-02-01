.. _spkg_indelstopo:

indelstopo: Analyzing topological properties of sets of words using the Insertion Chain Complex framework
=========================================================================================================

Description
-----------

Python package to analyze topological properties of sets of words when their main source of variation are insertions and deletions, using the Insertion Chain Complex framework

License
-------

MIT

Upstream Contact
----------------

- https://pypi.org/project/InDelsTopo/
- https://github.com/passagemath/passagemath-pkg-InDelsTopo


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_repl`

Version Information
-------------------

requirements.txt::

    InDelsTopo @ git+https://github.com/passagemath/passagemath-pkg-InDelsTopo.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install InDelsTopo@git+https://github.com/passagemath/passagemath-pkg-InDelsTopo.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i indelstopo


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
