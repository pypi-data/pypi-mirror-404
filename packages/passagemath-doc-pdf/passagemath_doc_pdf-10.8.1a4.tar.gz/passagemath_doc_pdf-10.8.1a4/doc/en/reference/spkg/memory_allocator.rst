.. _spkg_memory_allocator:

memory\_allocator: An extension class to allocate memory easily with Cython
===========================================================================

This extension class started as part of the Sage software.

Description
-----------

development website: https://github.com/sagemath/memory_allocator

PyPI page: https://pypi.org/project/memory_allocator

License
-------

GPL-3.0

Upstream Contact
----------------

https://github.com/sagemath/memory_allocator



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cython`

Version Information
-------------------

package-version.txt::

    0.1.4

pyproject.toml::

    memory_allocator <0.2

version_requirements.txt::

    memory_allocator < 0.2

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install memory_allocator\<0.2

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i memory_allocator

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install memory-allocator

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/memory-allocator

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-memory-allocator


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
