.. _spkg_nbclient:

nbclient: Client library for executing notebooks. Formerly nbconvert's ExecutePreprocessor
==========================================================================================

Description
-----------

Client library for executing notebooks. Formerly nbconvert's ExecutePreprocessor

License
-------

BSD

Upstream Contact
----------------

https://pypi.org/project/nbclient/



Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_jupyter_client`
- :ref:`spkg_nbformat`
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    0.10.4

version_requirements.txt::

    nbclient

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install nbclient

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i nbclient

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install nbclient

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install python3-nbclient

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-python/nbclient

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-python-jupyter-nbclient

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install python3-nbclient


If the system package is installed and if the (experimental) option
``--enable-system-site-packages`` is passed to ``./configure``, then 
``./configure`` will check if the system package can be used.
