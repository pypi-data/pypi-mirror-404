.. _spkg_hypothesis:

hypothesis: A library for property-based testing
================================================

Description
-----------

A library for property-based testing

License
-------

MPL-2.0

Upstream Contact
----------------

https://pypi.org/project/hypothesis/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_attrs`
- :ref:`spkg_pip`
- :ref:`spkg_sortedcontainers`

Version Information
-------------------

package-version.txt::

    6.125.2

version_requirements.txt::

    hypothesis>=6.123.0

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install hypothesis\>=6.123.0

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i hypothesis

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S python-hypothesis

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install python-hypothesis

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python-hypothesis

.. tab:: FreeBSD:

   .. CODE-BLOCK:: bash

       $ sudo pkg install devel/py-hypothesis

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/hypothesis

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-hypothesis

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install python-hypothesis

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-hypothesis


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
