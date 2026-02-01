.. _spkg_sign_crn:

sign_crn: SageMath package for (chemical) reaction networks using sign vector conditions
========================================================================================

Description
-----------

SageMath package for (chemical) reaction networks using sign vector conditions

License
-------

GPL-3.0-or-later

Upstream Contact
----------------

https://pypi.org/project/sign-crn/



Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_certlin`
- :ref:`spkg_elementary_vectors`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_graphs`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_symbolics`
- :ref:`spkg_sign_vectors`

Version Information
-------------------

requirements.txt::

    sign-crn

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install sign-crn

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sign_crn


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
