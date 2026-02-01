.. _spkg_python_json_logger:

python_json_logger: Python library adding a json log formatter
==============================================================

Description
-----------

Python library adding a json log formatter

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/python-json-logger/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    2.0.7

version_requirements.txt::

    python-json-logger

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install python-json-logger

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i python_json_logger

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-python-json-logger


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
