.. _spkg_sagemath_m4ri_m4rie:

=========================================================================
sagemath_m4ri_m4rie: Linear Algebra with m4ri and m4rie
=========================================================================


This pip-installable distribution ``passagemath-m4ri-m4rie``
provides modules that depend on the libraries
`m4ri <https://bitbucket.org/malb/m4ri/src/master/>`_,
`m4rie <https://bitbucket.org/malb/m4rie/src/master/>`_.


What is included
----------------

- `Dense matrices over GF(2) using the M4RI library <https://passagemath.org/docs/latest/html/en/reference/matrices/sage/matrix/matrix_mod2_dense.html>`__

- `Dense matrices over GF(2**e) for e from 2 to 16 using the M4RIE library <https://passagemath.org/docs/latest/html/en/reference/matrices/sage/matrix/matrix_gf2e_dense.html>`__

- `Vectors with elements in GF(2) <https://passagemath.org/docs/latest/html/en/reference/modules/sage/modules/vector_mod2_dense.html>`__


Type
----

standard


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_cysignals`
- :ref:`spkg_cython`
- :ref:`spkg_gmp`
- :ref:`spkg_libgd`
- :ref:`spkg_m4ri`
- :ref:`spkg_m4rie`
- :ref:`spkg_memory_allocator`
- :ref:`spkg_numpy`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.8.1.alpha4

version_requirements.txt::

    passagemath-m4ri-m4rie == 10.8.1.alpha4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-m4ri-m4rie==10.8.1.alpha4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_m4ri_m4rie


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
