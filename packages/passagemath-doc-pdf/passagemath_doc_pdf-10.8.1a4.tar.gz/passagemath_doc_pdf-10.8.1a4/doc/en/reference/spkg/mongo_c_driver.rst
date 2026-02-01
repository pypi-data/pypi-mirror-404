.. _spkg_mongo_c_driver:

mongo_c_driver: MongoDB Client Library for C
============================================

Description
-----------

The MongoDB C Driver, also known as “libmongoc”, is a library for using MongoDB from C applications,
and for writing MongoDB drivers in higher-level languages.

In passagemath, it is used as a prerequisite of polymake's polyDB.


License
-------

Apache 2.0


Upstream Contact
----------------

https://mongoc.org/


Type
----

optional


Dependencies
------------

- :ref:`spkg_cmake`
- :ref:`spkg_ninja_build`
- :ref:`spkg_openssl`

Version Information
-------------------

package-version.txt::

    1.30.6

See https://repology.org/project/mongo-c-driver/versions

Installation commands
---------------------

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i mongo_c_driver

.. tab:: Alpine:

   .. CODE-BLOCK:: bash

       $ apk add mongo-c-driver-dev

.. tab:: Arch Linux:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S mongo-c-driver

.. tab:: conda-forge:

   .. CODE-BLOCK:: bash

       $ conda install libmongoc

.. tab:: Debian/Ubuntu:

   .. CODE-BLOCK:: bash

       $ sudo apt-get install libmongoc-dev

.. tab:: Fedora/Redhat/CentOS:

   .. CODE-BLOCK:: bash

       $ sudo dnf install libmongoc-devel

.. tab:: Gentoo Linux:

   .. CODE-BLOCK:: bash

       $ sudo emerge dev-libs/mongo-c-driver

.. tab:: Homebrew:

   .. CODE-BLOCK:: bash

       $ brew install mongo-c-driver

.. tab:: MacPorts:

   .. CODE-BLOCK:: bash

       $ sudo port install mongo-c-driver

.. tab:: mingw-w64:

   .. CODE-BLOCK:: bash

       $ sudo pacman -S ${MINGW_PACKAGE_PREFIX}-mongo-c-driver

.. tab:: Nixpkgs:

   .. CODE-BLOCK:: bash

       $ nix-env -f \'\<nixpkgs\>\' --install --attr mongoc

.. tab:: openSUSE:

   .. CODE-BLOCK:: bash

       $ sudo zypper install mongo-c-driver

.. tab:: Void Linux:

   .. CODE-BLOCK:: bash

       $ sudo xbps-install mongo-c-driver-devel


If the system package is installed, ``./configure`` will check if it can be used.
