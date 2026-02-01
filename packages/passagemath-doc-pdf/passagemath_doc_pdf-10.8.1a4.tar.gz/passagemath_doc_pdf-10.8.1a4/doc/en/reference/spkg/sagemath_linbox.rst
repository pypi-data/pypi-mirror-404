.. _spkg_sagemath_linbox:

=======================================================================================
sagemath_linbox: Linear Algebra with Givaro, fflas-ffpack, LinBox
=======================================================================================


This pip-installable distribution ``passagemath-linbox``
provides modules that depend on the `LinBox suite <https://linalg.org/>`_
(Givaro, fflas-ffpack, LinBox).


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_givaro`
- :ref:`spkg_gmp`
- :ref:`spkg_linbox`
- :ref:`spkg_memory_allocator`
- :ref:`spkg_mpc`
- :ref:`spkg_mpfr`
- :ref:`spkg_numpy`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_flint`
- :ref:`spkg_sagemath_iml`
- :ref:`spkg_sagemath_m4ri_m4rie`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.8.1.alpha4

version_requirements.txt::

    passagemath-linbox == 10.8.1.alpha4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-linbox==10.8.1.alpha4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_linbox


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
