.. _spkg_sagemath_polymake:

========================================================================
sagemath_polymake: Polyhedral geometry with polymake
========================================================================


This pip-installable distribution ``passagemath-polymake``
provides an interface to `polymake <https://passagemath.org/docs/latest/html/en/reference/spkg/polymake.html#spkg-polymake>`__.

Upon installation of this source-only distribution package, an existing suitable
system installation of polymake will be detected, or polymake will be built from source.

What is included
----------------

- `Interface to polymake via JuPyMake <https://passagemath.org/docs/latest/html/en/reference/interfaces/sage/interfaces/polymake.html#module-sage.interfaces.polymake>`__

- the `JuPyMake feature <https://passagemath.org/docs/latest/html/en/reference/spkg/sage/features/polymake.html>`__ (via passagemath-environment)

- the `JuPyMake <https://pypi.org/project/JuPyMake/>`__ API

Examples
--------

Using polymake on the command line::

    $ pipx run --pip-args="--prefer-binary" --spec "passagemath-polymake" sage -polymake


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_pexpect`
- :ref:`spkg_pkgconf`
- :ref:`spkg_pkgconfig`
- :ref:`spkg_polymake`
- :ref:`spkg_sage_conf`
- :ref:`spkg_sage_setup`
- :ref:`spkg_sagemath_categories`
- :ref:`spkg_sagemath_environment`
- :ref:`spkg_setuptools`

Version Information
-------------------

package-version.txt::

    10.8.1.alpha4

version_requirements.txt::

    passagemath-polymake == 10.8.1.alpha4

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install passagemath-polymake==10.8.1.alpha4

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i sagemath_polymake


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
