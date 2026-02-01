.. _spkg_sagemath_iml:

==============================================================
sagemath_iml: Linear Algebra with IML
==============================================================


This pip-installable distribution ``passagemath-iml``
provides modules that depend on the library
`IML <https://cs.uwaterloo.ca/~astorjoh/iml.html>`_.


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_iml`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.8.1.alpha4

version_requirements.txt::

    passagemath-iml == 10.8.1.alpha4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-iml==10.8.1.alpha4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_iml


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
