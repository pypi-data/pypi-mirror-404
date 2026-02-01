.. _spkg_ipython_pygments_lexers:

ipython_pygments_lexers: Defines a variety of Pygments lexers for highlighting IPython code
===========================================================================================

Description
-----------

Defines a variety of Pygments lexers for highlighting IPython code

License
-------

Upstream Contact
----------------

https://pypi.org/project/ipython-pygments-lexers/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- :ref:`spkg_pip`

Version Information
-------------------

package-version.txt::

    1.1.1

version_requirements.txt::

    ipython-pygments-lexers

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install ipython-pygments-lexers

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i ipython_pygments_lexers


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
