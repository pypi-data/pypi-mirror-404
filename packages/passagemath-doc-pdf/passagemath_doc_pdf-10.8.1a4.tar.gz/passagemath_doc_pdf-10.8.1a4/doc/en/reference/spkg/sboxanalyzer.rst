.. _spkg_sboxanalyzer:

sboxanalyzer: Tool for analyzing S-boxes and Boolean functions against differential, linear, differential-linear, boomerang, and integral attacks
=================================================================================================================================================

Description
-----------

Tool for analyzing S-boxes and Boolean functions against differential, linear, differential-linear, boomerang, and integral attacks

License
-------

MIT

Upstream Contact
----------------

https://pypi.org/project/sboxanalyzer/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_sagelib`

Version Information
-------------------

requirements.txt::

    sboxanalyzer

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sboxanalyzer

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sboxanalyzer


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
