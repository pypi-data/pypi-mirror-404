.. _spkg_eigenmorphic:

eigenmorphic: Eigenvalues of morphic subshifts
==============================================

Description
-----------

Eigenvalues of morphic subshifts

License
-------

GPLv3.0

Upstream Contact
----------------

- https://pypi.org/project/eigenmorphic/
- https://github.com/passagemath/passagemath-pkg-eigenmorphic


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_groups`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_pari`
- :ref:`spkg_sagemath_plot`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`

Version Information
-------------------

package-version.txt::

    0.2.8

requirements.txt::

    eigenmorphic @ git+https://github.com/passagemath/passagemath-pkg-eigenmorphic.git

version_requirements.txt::

    eigenmorphic

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install eigenmorphic@git+https://github.com/passagemath/passagemath-pkg-eigenmorphic.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i eigenmorphic


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
