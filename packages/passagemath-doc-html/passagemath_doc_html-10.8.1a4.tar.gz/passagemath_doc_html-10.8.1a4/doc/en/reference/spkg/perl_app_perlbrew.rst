.. _spkg_perl_app_perlbrew:

perl_app_perlbrew: Perl installation management tool
====================================================

perlbrew is an admin-free perl installation management tool.


License
-------

MIT


Upstream Contact
----------------

- https://perlbrew.pl/
- https://metacpan.org/pod/App::perlbrew
- https://github.com/gugod/App-perlbrew


Type
----

optional


Dependencies
------------

- :ref:`spkg_gdbm`

Version Information
-------------------

package-version.txt::

    1.02

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i perl_app_perlbrew


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
