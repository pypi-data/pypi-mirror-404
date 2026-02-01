.. _spkg_khoca:

khoca: Khoca as pip installable package
=======================================

Description
-----------

Khoca as pip installable package

License
-------

GPLv2+

Upstream Contact
----------------

https://pypi.org/project/khoca/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`
- :ref:`spkg_pari`

Version Information
-------------------

package-version.txt::

    1.4

requirements.txt::

    khoca

version_requirements.txt::

    khoca

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install khoca

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i khoca


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
