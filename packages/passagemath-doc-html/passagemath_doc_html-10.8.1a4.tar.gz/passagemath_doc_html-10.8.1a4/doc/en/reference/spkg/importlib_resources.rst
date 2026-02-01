.. _spkg_importlib_resources:

importlib_resources: Read resources from Python packages
========================================================

Description
-----------

Read resources from Python packages

License
-------

Apache2

Upstream Contact
----------------

https://pypi.org/project/importlib-resources/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`
- :ref:`spkg_zipp`

Version Information
-------------------

package-version.txt::

    6.5.2

version_requirements.txt::

    importlib_resources >= 5.12; python_version<'3.12'

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install importlib_resources\>=5.12\;python_version\<\"3.12\"

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i importlib_resources

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install importlib-resources

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python3-importlib-resources

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-importlib_resources


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
