.. _spkg_moment_cone:

moment_cone: Kronecker and fermionic moment cones
=================================================

Description
-----------

Computations with Kronecker and fermionic moment cones.

License
-------

MIT

Upstream Contact
----------------

- https://github.com/ea-icj/moment_cone


Type
----

optional


Dependencies
------------

- $(PYTHON)
- $(PYTHON_TOOLCHAIN)
- :ref:`spkg_lrcalc_python`
- :ref:`spkg_numpy`
- :ref:`spkg_sagemath_combinat`
- :ref:`spkg_sagemath_modules`
- :ref:`spkg_sagemath_polyhedra`
- :ref:`spkg_sagemath_repl`
- :ref:`spkg_sagemath_singular`
- :ref:`spkg_sympy`

Version Information
-------------------

requirements.txt::

    moment_cone @ git+https://github.com/ea-icj/moment_cone.git

Installation commands
---------------------

.. tab:: PyPI:

   .. CODE-BLOCK:: bash

       $ pip install moment_cone@git+https://github.com/ea-icj/moment_cone.git

.. tab:: Sage distribution:

   .. CODE-BLOCK:: bash

       $ sage -i moment_cone


However, these system packages will not be used for building Sage
because ``spkg-configure.m4`` has not been written for this package;
see :issue:`27330` for more information.
