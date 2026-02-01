.. _spkg_sagemath_pari_nftables:

====================================================================================================
sagemath_pari_nftables: Computational Number Theory with PARI/GP: Number field tables
====================================================================================================


This pip-installable distribution ``passagemath-pari-nftables`` is a
distribution of data for use with ``passagemath-pari``.


What is included
----------------

- Wheels on PyPI include the nftables files


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pari_nftables`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.8.1.alpha4

version_requirements.txt::

    passagemath-pari-nftables == 10.8.1.alpha4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-pari-nftables==10.8.1.alpha4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_pari_nftables


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
