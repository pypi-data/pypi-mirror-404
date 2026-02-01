.. _spkg_pytest_mock:

pytest_mock: Thin-wrapper around the mock package for easier use with pytest
============================================================================

Description
-----------

Thin-wrapper around the mock package for easier use with pytest

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/pytest-mock/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`
- :ref:`spkg_pytest`

Version Information
-------------------

package-version.txt::

    3.14.0

version_requirements.txt::

    pytest-mock

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install pytest-mock

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i pytest_mock

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install pytest-mock

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-pytest-mock


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
